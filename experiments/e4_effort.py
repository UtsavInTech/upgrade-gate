"""E4 / H4 — is more reasoning effort ever worse?

Runs Muse Spark 1.3 (Contributor mode, ~1/18 the price) at every effort level on the same tasks.
Every level gets the same 16,000-token limit, because reasoning tokens count toward it: with the
old 4,000 limit, high effort could run out before answering and look "worse" for the wrong reason.
Answers cut off by the limit are counted separately, never as wrong answers.

  python3 experiments/e4_effort.py --n 10 --repeats 1          # pilot estimate
  python3 experiments/e4_effort.py --n 10 --repeats 1 --yes --budget 2
  python3 experiments/e4_effort.py --n 30 --yes --budget 6      # full run
("max" effort exists only in Standard mode, so the Contributor ladder stops at xhigh.)
"""
from __future__ import annotations

import collections
import os

from common import base_args, compare, majority, pairs, run_and_score, table, tasks_by_id, write_result
from upgrade_gate.schema import read_jsonl

# The text packs sit at 100% at every effort level (pilot, 28 Oct), so the ladder runs where the
# model actually struggles: the 135 spoken clips. Pass --packs to change it.
PACKS = ["audio-clips"]
LEVELS = ["minimal", "low", "medium", "high", "xhigh"]
LIMIT = 16000
CANDS = ["spark-1.3-c@%s/%d" % (l, LIMIT) for l in LEVELS]


def _level(c: str) -> str:
    return c.split("@")[1].split("/")[0]


def analyse(run_dir: str) -> None:
    tasks = tasks_by_id(run_dir)
    cost, out_tok, calls, cut = (collections.Counter() for _ in range(4))
    for r in read_jsonl(os.path.join(run_dir, "responses.jsonl")):
        c = r["candidate"]
        calls[c] += 1
        cost[c] += r.get("cost_usd") or 0
        out_tok[c] += (r.get("usage") or {}).get("output_tokens", 0)
        if "max_completion_tokens" in (r.get("error") or ""):
            cut[c] += 1
    # Accuracy two ways: among answers that finished, and counting cut-offs as failures.
    answered = collections.defaultdict(lambda: [0, 0])
    for s in read_jsonl(os.path.join(run_dir, "scores.jsonl")):
        if s.get("passed") is None:
            continue
        a = answered[s["candidate"]]
        a[0] += bool(s["passed"])
        a[1] += 1
    lines = ["# E4 — reasoning effort ladder on muse-spark-1.3 Contributor (limit %d tokens)" % LIMIT, "",
             "Run: `%s`" % run_dir, "",
             "| Effort | correct (finished answers) | correct (cut-offs as fail) | cut off | avg output tokens | cost $ |",
             "|---|---|---|---|---|---|"]
    for c in CANDS:
        ok, n = answered[c]
        total = calls[c] or 1
        lines.append("| %s | %s | %.1f%% | %d / %d | %d | %.3f |" % (
            _level(c), "%.1f%%" % (100 * ok / n) if n else "–", 100 * ok / total, cut[c], calls[c],
            out_tok[c] // total, cost[c]))
    maj = majority(os.path.join(run_dir, "scores.jsonl"))
    rows = []
    for lo, hi in zip(CANDS, CANDS[1:]):
        for cat in sorted({t["category"] for t in tasks.values()}):
            ps = pairs(maj, [i for i, t in tasks.items() if t["category"] == cat], lo, hi)
            if len(ps) >= 10 or (len(ps) >= 5 and len(tasks) < 200):
                rows.append(compare(ps, "%s→%s %s" % (_level(lo), _level(hi), cat)))
    lines += ["", "## Step-ups (negative Δ = more effort was worse; cut-offs excluded)", "", table(rows)]
    write_result("e4_effort", "\n".join(lines), {"run_dir": run_dir, "steps": rows,
                                                 "cut_off": dict(cut), "calls": dict(calls)})


if __name__ == "__main__":
    ap = base_args(__doc__)
    ap.add_argument("--packs", default=",".join(PACKS))
    args = ap.parse_args()
    packs = [p for p in args.packs.split(",") if p]
    run_id = "e4-effort" if packs == PACKS else "e4-effort-" + "-".join(packs)
    rd = args.run_dir or run_and_score(packs, CANDS, args.n, args.repeats, args.budget, args.yes, run_id)
    analyse(rd)
