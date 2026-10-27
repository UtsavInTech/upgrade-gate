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
    args = ap.parse_args()

    base_ref = os.environ.get("GITHUB_BASE_REF")
    baseline = args.baseline or (model_at("origin/" + base_ref) if base_ref else model_at("HEAD~1"))
    candidate = model_at()
    name = "upgrade-gate / %s" % args.suite
    if baseline == candidate:
        write_summary("### %s: nothing to gate\n\nThe model is unchanged (`%s`)." % (name, candidate))
        return 0

    evidence = os.path.join(ROOT, "evidence", args.suite)
    have = Counter(r["candidate"] for r in read_jsonl(os.path.join(evidence, "scores.jsonl")))
    if baseline not in have or candidate not in have:
        write_summary("### %s: INCONCLUSIVE\n\nNo saved answers for `%s` → `%s` in `evidence/%s`. "
                      "Run `upgrade-gate all` with an API key to collect them." % (name, baseline, candidate, args.suite))
        return 3

    run_dir = os.path.join(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir(), "upgrade-gate-" + args.suite)
    shutil.rmtree(run_dir, ignore_errors=True)
    shutil.copytree(evidence, run_dir)
    code = cli.main(["gate", run_dir, "--baseline", baseline, "--candidate", candidate])
    with open(os.path.join(run_dir, "gate.json"), encoding="utf-8") as f:
        gate = json.load(f)
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
        lines += ["", "| Input | Tasks | Wrong or blank, no warning | Says it can't answer |", "|---|---|---|---|"]
        for m, g in sorted(beh.items()):
            lines.append("| %s | %d | %d → %d%s | %d → %d |" % (
                g["label"], g["tasks"], g["silent"]["baseline"], g["silent"]["candidate"],
                " ⚠" if g.get("flagged") else "", g["abstain"]["baseline"], g["abstain"]["candidate"]))
    if code != 0:
        ex = failing_example(run_dir, baseline, candidate)
        if ex:
            lines += ["", "**One failing case** (`%s`): the answer is filled in, so a required-fields check passes it."
                      % ex["id"], "", "> %s" % ex["said"].replace("\n", " "), "",
                      "- Correct: `%s`" % json.dumps(ex["expected"], ensure_ascii=False),
                      "- `%s`: `%s`" % (baseline, ex["base"][:200].replace("\n", " ")),
                      "- `%s`: `%s`" % (candidate, ex["cand"][:200].replace("\n", " "))]
    write_summary("\n".join(lines) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
