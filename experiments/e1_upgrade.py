"""E1 — the headline gate: Muse Spark 1.2 -> 1.3 across every pack and modality.

Question: does 1.3 improve on average while regressing on some slice?
  python3 experiments/e1_upgrade.py --n 40            # dry run, prints cost
  python3 experiments/e1_upgrade.py --n 40 --yes      # spend
"""
from __future__ import annotations

from common import base_args, compare, majority, pairs, run_and_score, table, tasks_by_id, write_result
import os

PACKS = ["math-pairs", "extract-pairs", "intent", "ifeval", "docs-synth"]
A, B = "spark-1.2@low", "spark-1.3@low"


def _rows(maj, tasks):
    rows = [compare(pairs(maj, tasks, A, B), "overall")]
    for key in ("category", "lang", "modality"):
        for val in sorted({t[key] for t in tasks.values()}):
            ids = [i for i, t in tasks.items() if t[key] == val]
            ps = pairs(maj, ids, A, B)
            if len(ps) >= 10:
                rows.append(compare(ps, "%s=%s" % (key, val)))
    return rows


def analyse(run_dir: str) -> None:
    path = os.path.join(run_dir, "scores.jsonl")
    tasks = tasks_by_id(run_dir)
    content = _rows(majority(path), tasks)
    strict = _rows(majority(path, "strict_passed"), tasks)
    text = ("# E1 — %s vs %s\n\nRun: `%s`\n\n"
            "## Correct answer (content score)\n\nSpelling variants count (Somwar = Somvar, साई = साईं); "
            "a clear answer inside extra text counts.\n\n%s\n\n"
            "## Correct answer in the exact format asked (strict score)\n\nNo extra words, bold, "
            "explanations or code fences around the answer.\n\n%s"
            % (A, B, run_dir, table(content), table(strict)))
    write_result("e1_upgrade", text, {"run_dir": run_dir, "rows": content, "strict_rows": strict})


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes, "e1-upgrade")
    analyse(rd)
