"""E4 / H4 — is more reasoning effort ever worse?

Runs Muse Spark 1.3 at every effort level on the same tasks and reports accuracy and cost per
level, plus the pairwise change between neighbouring levels by category.

  python3 experiments/e4_effort.py --n 30 --yes
"""
from __future__ import annotations

import collections
import os

from common import base_args, compare, majority, pairs, run_and_score, table, tasks_by_id, write_result
from upgrade_gate.schema import read_jsonl

PACKS = ["math-pairs", "ifeval", "extract-pairs"]
LEVELS = ["minimal", "low", "medium", "high", "xhigh", "max"]
CANDS = ["spark-1.3@" + l for l in LEVELS]


def analyse(run_dir: str) -> None:
    maj = majority(os.path.join(run_dir, "scores.jsonl"))
    tasks = tasks_by_id(run_dir)
    cost = collections.Counter()
    out_tok = collections.Counter()
    for r in read_jsonl(os.path.join(run_dir, "responses.jsonl")):
        cost[r["candidate"]] += r.get("cost_usd") or 0
        out_tok[r["candidate"]] += (r.get("usage") or {}).get("output_tokens", 0)
    lines = ["# E4 — reasoning effort ladder on muse-spark-1.3", "", "Run: `%s`" % run_dir, "",
             "| Effort | accuracy | cost $ | output tokens |", "|---|---|---|---|"]
    for c in CANDS:
        vals = [v for (t, cand), v in maj.items() if cand == c]
        acc = sum(vals) / len(vals) if vals else float("nan")
        lines.append("| %s | %.1f%% | %.3f | %d |" % (c.split("@")[1], 100 * acc, cost[c], out_tok[c]))
    rows = []
    for lo, hi in zip(CANDS, CANDS[1:]):
        for cat in sorted({t["category"] for t in tasks.values()}):
            ps = pairs(maj, [i for i, t in tasks.items() if t["category"] == cat], lo, hi)
            if len(ps) >= 10:
                rows.append(compare(ps, "%s→%s %s" % (lo.split("@")[1], hi.split("@")[1], cat)))
    lines += ["", "## Step-ups (negative Δ = more effort was worse)", "", table(rows)]
    write_result("e4_effort", "\n".join(lines), {"run_dir": run_dir, "steps": rows})


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, CANDS, args.n, args.repeats, args.budget, args.yes, "e4-effort")
    analyse(rd)
