"""E3 / H3 — Contributor mode vs Standard mode, same model version.

Contributor costs ~1/12 input and ~1/21 output. Is the quality really the same?
Tested as an EQUIVALENCE question: we want the CI on the difference to sit inside ±2 pts.

  python3 experiments/e3_contributor.py --n 40 --yes
Contributor is capped at 150 RPM, so this run is slower.
"""
from __future__ import annotations

import os

from common import base_args, compare, majority, pairs, run_and_score, table, tasks_by_id, write_result

PACKS = ["math-pairs", "extract-pairs", "intent", "ifeval", "docs-synth"]
STD, CON = "spark-1.3@low", "spark-1.3-c@low"
MARGIN = 0.02


def analyse(run_dir: str) -> None:
    maj = majority(os.path.join(run_dir, "scores.jsonl"))
    tasks = tasks_by_id(run_dir)
    rows = [compare(pairs(maj, tasks, STD, CON), "overall")]
    for key in ("category", "lang", "modality"):
        for val in sorted({t[key] for t in tasks.values()}):
            ps = pairs(maj, [i for i, t in tasks.items() if t[key] == val], STD, CON)
            if len(ps) >= 10:
                rows.append(compare(ps, "%s=%s" % (key, val)))
    o = rows[0]
    if o["ci"][0] > -MARGIN and o["ci"][1] < MARGIN:
        verdict = "EQUIVALENT within ±%d pts overall." % (100 * MARGIN)
    elif o["ci"][1] < -MARGIN:
        verdict = "Contributor is WORSE overall."
    else:
        verdict = "Not shown equivalent (CI too wide or crosses the margin)."
    text = "# E3 — Standard vs Contributor (%s vs %s)\n\nRun: `%s`\n\n**%s**\n\n%s" % (STD, CON, run_dir, verdict, table(rows))
    write_result("e3_contributor", text, {"run_dir": run_dir, "rows": rows, "verdict": verdict})


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, [STD, CON], args.n, args.repeats, args.budget, args.yes, "e3-contributor")
    analyse(rd)
