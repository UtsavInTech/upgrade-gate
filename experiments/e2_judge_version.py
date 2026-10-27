"""E2 / H1 — judge-version bias in upgrade gates.

Generate answers with 1.2 and 1.3, grade every answer with several judges (1.2, 1.3, Wonder,
optionally hosted Spark Open) AND with the deterministic ground truth. Then ask:
  - how often does each judge pass a wrong answer (false pass)?
  - does a judge's false-pass rate depend on WHICH version wrote the answer?
  - would the gate's go/no-go decision flip if you used judge X instead of the truth?

  python3 experiments/e2_judge_version.py --n 40 [--open] --yes
"""
from __future__ import annotations

import collections
import os

from common import (base_args, compare, mcnemar_exact, pairs, run_and_score, table, tasks_by_id,
                    write_result)
from upgrade_gate.schema import read_jsonl

# Packs where the answer is free-form enough that teams really would use a judge.
PACKS = ["extract-pairs", "math-pairs", "docs-synth"]
A, B = "spark-1.2@low", "spark-1.3@low"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def analyse(run_dir: str) -> None:
    rows = list(read_jsonl(os.path.join(run_dir, "scores.jsonl")))
    tasks = tasks_by_id(run_dir)
    # per judge x producer: confusion vs truth
    conf = collections.defaultdict(lambda: collections.Counter())
    judge_maj = collections.defaultdict(lambda: collections.defaultdict(list))  # judge -> (task,cand) -> votes
    truth_maj = collections.defaultdict(list)
    for r in rows:
        if r.get("passed") is None:
            continue
        truth = bool(r["passed"])
        truth_maj[(r["task_id"], r["candidate"])].append(truth)
        for v in r.get("judge_votes") or []:
            if v.get("passed") is None:
                conf[(v["judge"], r["candidate"])]["unparsed"] += 1
                continue
            j = bool(v["passed"])
            judge_maj[v["judge"]][(r["task_id"], r["candidate"])].append(j)
            key = "TP" if (j and truth) else "FP" if (j and not truth) else "FN" if truth else "TN"
            conf[(v["judge"], r["candidate"])][key] += 1

    lines = ["# E2 — judge-version bias (H1)", "", "Run: `%s`" % run_dir, "",
             "## False-pass rate by judge and by which version wrote the answer", "",
             "False pass = judge says correct, ground truth says wrong. Lower is better.", "",
             "| Judge | Producer | wrong answers | false passes | false-pass rate | false-fail rate |",
             "|---|---|---|---|---|---|"]
    data = {"run_dir": run_dir, "confusion": {}, "gate_by_judge": []}
    for (judge, prod), c in sorted(conf.items()):
        wrong = c["FP"] + c["TN"]
        right = c["TP"] + c["FN"]
        fpr = c["FP"] / wrong if wrong else float("nan")
        fnr = c["FN"] / right if right else float("nan")
        data["confusion"]["%s|%s" % (judge, prod)] = dict(c)
        lines.append("| %s | %s | %d | %d | %.1f%% | %.1f%% |" % (judge, prod, wrong, c["FP"], 100 * fpr, 100 * fnr))

    # Self-preference: does each judge let more of ITS OWN version's mistakes through?
    from scipy.stats import fisher_exact
    lines += ["", "## Does a judge go easier on its own version's mistakes?", "",
              "Fisher exact test on wrong answers (answer level; repeats of one task are not independent, "
              "so treat p as a guide).", "",
              "| Judge | false passes on 1.2's wrong answers | on 1.3's wrong answers | p |", "|---|---|---|---|"]
    data["self_preference"] = []
    for judge in sorted({j for j, _ in conf}):
        a, b = conf.get((judge, A), {}), conf.get((judge, B), {})
        fa, wa = a.get("FP", 0), a.get("FP", 0) + a.get("TN", 0)
        fb, wb = b.get("FP", 0), b.get("FP", 0) + b.get("TN", 0)
        p = fisher_exact([[fa, wa - fa], [fb, wb - fb]])[1] if wa and wb else float("nan")
        lines.append("| %s | %d / %d (%.1f%%) | %d / %d (%.1f%%) | %.2g |" % (
            judge, fa, wa, 100 * fa / wa if wa else 0, fb, wb, 100 * fb / wb if wb else 0, p))
        data["self_preference"].append({"judge": judge, "fp_base": fa, "wrong_base": wa, "fp_cand": fb,
                                        "wrong_cand": wb, "p": p})

    # Version preference: for each judge, compare its false-pass rate on A-answers vs B-answers (Fisher-ish via 2x2 counts)
    lines += ["", "## Would the gate decision change with this judge?", ""]
    maj_truth = {k: sum(v) * 2 > len(v) for k, v in truth_maj.items()}
    gate_rows = [compare(pairs(maj_truth, tasks, A, B), "ground truth")]
    for judge, votes in sorted(judge_maj.items()):
        mj = {k: sum(v) * 2 > len(v) for k, v in votes.items() if v}
        gate_rows.append(compare(pairs(mj, tasks, A, B), "judge=" + judge))
    lines.append(table(gate_rows))
    lines += ["", "A judge is biased toward the upgrade if its Δ is clearly above the ground-truth Δ."]
    data["gate_by_judge"] = gate_rows
    write_result("e2_judge_version", "\n".join(lines), data)


def judge_saved_run(src_run: str, judges) -> str:
    """Copy a saved run's audio answers (both versions) into a new run dir and score them with judges.
    No new model answers are generated; only judge calls are made."""
    import json
    import shutil
    from upgrade_gate.cli import make_judges
    from upgrade_gate.scoring import score_run

    src = os.path.join(ROOT, "results", src_run)
    dst = os.path.join(ROOT, "results", "e2-judges-" + src_run)
    os.makedirs(dst, exist_ok=True)
    shutil.copyfile(os.path.join(src, "run.json"), os.path.join(dst, "run.json"))
    keep = set()
    with open(os.path.join(src, "tasks.jsonl"), encoding="utf-8") as f, \
            open(os.path.join(dst, "tasks.jsonl"), "w", encoding="utf-8") as out:
        for line in f:
            t = json.loads(line)
            if t.get("modality") == "audio":
                keep.add(t["id"])
                out.write(line)
    with open(os.path.join(src, "responses.jsonl"), encoding="utf-8") as f, \
            open(os.path.join(dst, "responses.jsonl"), "w", encoding="utf-8") as out:
        for line in f:
            r = json.loads(line)
            if r["task_id"] in keep and r["candidate"] in (A, B):
                out.write(line)
    score_run(dst, judges=make_judges(judges), mode="both")
    return dst


if __name__ == "__main__":
    ap = base_args(__doc__)
    ap.add_argument("--open", action="store_true", help="also use hosted Muse Spark Open as a judge")
    ap.add_argument("--judges", default="spark-1.2-c,spark-1.3-c",
                    help="judge presets; Contributor versions by default (same weights, ~1/18 the price)")
    ap.add_argument("--from-run", default=None,
                    help="judge a saved run's audio answers instead of generating new ones (e.g. e6-audio)")
    args = ap.parse_args()
    judges = [j for j in args.judges.split(",") if j] + (["open"] if args.open else [])
    if args.from_run:
        if not args.yes:
            raise SystemExit("Judging %s costs judge calls only. Add --yes to spend." % args.from_run)
        rd = judge_saved_run(args.from_run, judges)
    else:
        rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes,
                                           "e2-judge-version", judges=judges, mode="both")
    analyse(rd)
