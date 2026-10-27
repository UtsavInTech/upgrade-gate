"""CI entry point: gate a change to release/model.json against saved evidence.

    python scripts/ci_gate.py voice-notes            # in GitHub Actions (reads the base branch)
    python scripts/ci_gate.py voice-notes --baseline spark-1.2@low   # locally

Baseline = release/model.json on the base branch; candidate = release/model.json in the PR.
The evidence in evidence/<suite>/ holds both versions' saved answers, so no API call is made.
(In a live setup the same step runs `upgrade-gate all` with MODEL_API_KEY instead.)
Exit code: 0 GO, 2 NO-GO, 3 inconclusive or no evidence for this model pair.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate import cli  # noqa: E402
from upgrade_gate.behaviour import answer_type  # noqa: E402
from upgrade_gate.schema import read_jsonl  # noqa: E402


# Small fresh samples for live mode (real-voices has no public clips, so it stays replay-only).
LIVE_PACKS = {"voice-notes": "audio-clips", "text-and-documents": "math-pairs,extract-pairs,intent"}


def model_at(ref: str = None) -> str:
    path = os.path.join(ROOT, "release", "model.json")
    if ref:
        raw = subprocess.run(["git", "show", "%s:release/model.json" % ref], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout
        return json.loads(raw)["model"]
    with open(path, encoding="utf-8") as f:
        return json.load(f)["model"]


def summary_path():
    return os.environ.get("GITHUB_STEP_SUMMARY")


def write_summary(text: str) -> None:
    print(text)
    p = summary_path()
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def failing_example(run_dir: str, base: str, cand: str):
    """A task the old version got right and the new one got wrong with a filled-in answer
    (so a simple 'required fields present' check would not catch it)."""
    tasks = {t["id"]: t for t in read_jsonl(os.path.join(run_dir, "tasks.jsonl"))}
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in read_jsonl(os.path.join(run_dir, "responses.jsonl"))}
    by = defaultdict(list)
    for s in read_jsonl(os.path.join(run_dir, "scores.jsonl")):
        r = resp.get((s["task_id"], s["candidate"], s["repeat"]), {})
        by[(s["task_id"], s["candidate"])].append((answer_type(r.get("text"), r.get("error"), s.get("passed")),
                                                   (r.get("text") or "").strip()))
    best = None
    for tid in sorted(tasks):
        b, c = by.get((tid, base)), by.get((tid, cand))
        if not b or not c:
            continue
        if sum(t == "correct" for t, _ in b) * 2 > len(b) and sum(t == "wrong" for t, _ in c) * 2 > len(c):
            score = (tasks[tid].get("modality") == "audio", tasks[tid].get("lang") == "hi")
            if best is None or score > best[0]:
                best = (score, tid, next(x for t, x in b if t == "correct"), next(x for t, x in c if t == "wrong"))
    if not best:
        return None
    _, tid, good, bad = best
    t = tasks[tid]
    return {"id": tid, "said": (t.get("meta") or {}).get("transcript") or t["prompt"], "expected": t.get("reference"),
            "base": good, "cand": bad}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("suite")
    ap.add_argument("--baseline", default=None, help="model before the change (default: base branch)")
    ap.add_argument("--candidate", default=None, help="model after the change (default: release/model.json)")
    ap.add_argument("--evidence", default=None, help="saved run to replay (default: evidence/<suite>)")
    ap.add_argument("--live", action="store_true",
                    help="run a small fresh sample on both models instead of replaying (needs MODEL_API_KEY)")
    ap.add_argument("--packs", default=None, help="live: task packs or a .jsonl file (default per suite)")
    ap.add_argument("--n", type=int, default=10, help="live: tasks per pack (default 10)")
    ap.add_argument("--budget", type=float, default=1.0, help="live: strict spending cap in USD (default 1)")
    ap.add_argument("--policy", default=None, help="release policy (default: release/policy.json)")
    args = ap.parse_args()

    base_ref = os.environ.get("GITHUB_BASE_REF")
    baseline = args.baseline or (model_at("origin/" + base_ref) if base_ref else model_at("HEAD~1"))
    candidate = args.candidate or model_at()
    name = "upgrade-gate / %s%s" % (args.suite, " (live)" if args.live else "")
    # "default" = built-in policy (used by the reusable Action when the caller has no policy file)
    policy_path = None if args.policy == "default" else (args.policy or os.path.join(ROOT, "release", "policy.json"))
    try:  # a broken policy must fail the check, not silently fall back to defaults
        from upgrade_gate.behaviour import load_policy
        load_policy(policy_path if policy_path and os.path.exists(policy_path) else None)
    except (ValueError, json.JSONDecodeError) as e:
        write_summary("### %s: policy error\n\n`release/policy.json` is invalid: %s" % (name, e))
        return 1
    if baseline == candidate:
        write_summary("### %s: nothing to gate\n\nThe model is unchanged (`%s`). The release policy is valid."
                      % (name, candidate))
        return 0

    tmp_root = os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()
    policy = policy_path if policy_path and os.path.exists(policy_path) else None
    if args.live:
        if not os.environ.get("MODEL_API_KEY"):
            write_summary("### %s: skipped\n\nNo `MODEL_API_KEY` secret, so no live sample was run." % name)
            return 0
        packs = args.packs or LIVE_PACKS.get(args.suite)
        if not packs:
            write_summary("### %s: skipped\n\nNo live task set for this suite." % name)
            return 0
        os.environ.setdefault("MAX_TOTAL_SPEND_USD", str(args.budget))
        os.environ.setdefault("CANARY_BUDGET_USD", "0")
        out = os.path.join(tmp_root, "upgrade-gate-live")
        run_id = "live-" + args.suite
        shutil.rmtree(os.path.join(out, run_id), ignore_errors=True)
        all_args = ["all", "--packs", packs, "--n", str(args.n), "-b", baseline, "-c", candidate, "--repeats", "3",
                    "--budget", str(args.budget), "--yes", "--out", out, "--run-id", run_id, "--workers", "8"]
        if policy:
            all_args += ["--policy", policy]
        code = cli.main(all_args)
        run_dir = os.path.join(out, run_id)
    else:
        evidence = args.evidence or os.path.join(ROOT, "evidence", args.suite)
        have = Counter(r["candidate"] for r in read_jsonl(os.path.join(evidence, "scores.jsonl")))
        if baseline not in have or candidate not in have:
            write_summary("### %s: INCONCLUSIVE\n\nNo saved answers for `%s` → `%s` in `%s`. Run with `--live` "
                          "(and MODEL_API_KEY) to collect them." % (name, baseline, candidate, evidence))
            return 3
        run_dir = os.path.join(tmp_root, "upgrade-gate-" + args.suite)
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.copytree(evidence, run_dir)
        gate_args = ["gate", run_dir, "--baseline", baseline, "--candidate", candidate]
        if policy:
            gate_args += ["--policy", policy]
        code = cli.main(gate_args)
    with open(os.path.join(run_dir, "gate.json"), encoding="utf-8") as f:
        gate = json.load(f)
    if not args.live:  # `all` already wrote the report in live mode
        try:
            cli.main(["report", run_dir])
        except Exception as e:  # the decision stands even if the HTML report can't be built
            print("report skipped:", e)

    decision = gate["decision"].upper()
    lines = ["### %s: %s" % (name, decision), "",
             "`%s` → `%s` · %s" % (baseline, candidate, gate.get("run_id", args.suite)), ""]
    if gate.get("accuracy_decision") and gate["accuracy_decision"] != gate["decision"]:
        lines.append("Accuracy alone: **%s**. The failure-type check changed the decision." %
                     gate["accuracy_decision"].upper())
        lines.append("")
    lines += ["- " + r for r in gate.get("reasons", [])]
    beh = (gate.get("behaviour") or {}).get("by_input") or {}
    if beh:
        lines += ["", "| Input | Tasks | Wrong or blank, no warning | Grouped by item | Says it can't answer |",
                  "|---|---|---|---|---|"]
        for m, g in sorted(beh.items()):
            it = g["silent"].get("items")
            lines.append("| %s | %d | %d → %d%s | %s | %d → %d |" % (
                g["label"], g["tasks"], g["silent"]["baseline"], g["silent"]["candidate"],
                " ⚠" if g.get("flagged") else "",
                "%d of %d items worse, %d better (p = %.2g)" % (it["worse"], it["n"], it["better"], it["p"]) if it else "–",
                g["abstain"]["baseline"], g["abstain"]["candidate"]))
    if gate.get("policy_why"):
        lines += ["", "**Release policy** (`release/policy.json`): %s" % gate["policy_why"]]
    if code != 0:
        ex = failing_example(run_dir, baseline, candidate)
        if ex:
            lines += ["", "**One failing case** (`%s`): the answer is filled in, so a required-fields check passes it."
                      % ex["id"], "", "> %s" % ex["said"].replace("\n", " "), "",
                      "- Correct: `%s`" % json.dumps(ex["expected"], ensure_ascii=False),
                      "- `%s`: `%s`" % (baseline, ex["base"][:200].replace("\n", " ")),
                      "- `%s`: `%s`" % (candidate, ex["cand"][:200].replace("\n", " "))]
    if args.live:
        lines += ["", "_Live sample: %s tasks per pack × 3 tries, capped at $%.2f. A small sample is often inconclusive; "
                  "only a NO-GO fails this check._" % (args.n, args.budget)]
    write_summary("\n".join(lines) + "\n")
    if args.live and code == 3:
        return 0
    return code


if __name__ == "__main__":
    sys.exit(main())
