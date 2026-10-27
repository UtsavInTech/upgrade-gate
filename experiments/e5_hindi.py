"""E5 / H6 — does the 1.2 -> 1.3 upgrade help English but not Hindi / Hinglish?

Uses matched pairs (the same item in English and in Hindi/Hinglish via pair_id). The key number is
the INTERACTION: (Δ Hindi) − (Δ English) on matched items, with a paired bootstrap CI.

  python3 experiments/e5_hindi.py --n 60 --yes
"""
from __future__ import annotations

import os

from common import (base_args, bootstrap, compare, fmt_pts, majority, pairs, run_and_score, table,
                    tasks_by_id, write_result)

PACKS = ["math-pairs", "extract-pairs", "intent", "ifeval"]
A, B = "spark-1.2@low", "spark-1.3@low"


def analyse(run_dir: str) -> None:
    maj = majority(os.path.join(run_dir, "scores.jsonl"))
    tasks = tasks_by_id(run_dir)
    lines = ["# E5 — Hindi / Hinglish vs English across the upgrade (H6)", "", "Run: `%s`" % run_dir, ""]
    data = {"run_dir": run_dir, "interaction": {}}
    rows = []
    for lang in ("hi", "hinglish"):
        quads = []  # (en_a, en_b, xx_a, xx_b) for matched items scored on both models
        for tid, t in tasks.items():
            if t["lang"] != lang or not t.get("pair_id") or t["pair_id"] not in tasks:
                continue
            en = t["pair_id"]
            keys = [(en, A), (en, B), (tid, A), (tid, B)]
            if all(k in maj for k in keys):
                quads.append(tuple(maj[k] for k in keys))
        if len(quads) < 10:
            continue

        def inter(qs):
            n = len(qs)
            d_en = sum(q[1] - q[0] for q in qs) / n
            d_xx = sum(q[3] - q[2] for q in qs) / n
            return d_xx - d_en

        est = inter(quads)
        lo, hi = bootstrap(inter, quads)
        data["interaction"][lang] = {"n": len(quads), "estimate": est, "ci": [lo, hi]}
        rows.append(compare([(str(i), q[0], q[1]) for i, q in enumerate(quads)], "en (matched to %s)" % lang))
        rows.append(compare([(str(i), q[2], q[3]) for i, q in enumerate(quads)], lang))
        lines.append("- **%s − English upgrade gap: %s pts** (95%% CI %s to %s, n=%d matched items)" % (
            lang, fmt_pts(est), fmt_pts(lo), fmt_pts(hi), len(quads)))
    lines += ["", table(rows), "",
              "A negative gap whose CI excludes 0 means the upgrade helped English more than this language (H6 supported)."]
    data["rows"] = rows
    write_result("e5_hindi", "\n".join(lines), data)


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes, "e5-hindi")
    analyse(rd)
