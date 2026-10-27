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


if __name__ == "__main__":
    ap = base_args(__doc__)
    ap.add_argument("--open", action="store_true", help="also use hosted Muse Spark Open as a judge")
    args = ap.parse_args()
    judges = ["spark-1.2", "spark-1.3", "wonder"] + (["open"] if args.open else [])
    rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes,
                                       "e2-judge-version", judges=judges, mode="both")
    analyse(rd)
