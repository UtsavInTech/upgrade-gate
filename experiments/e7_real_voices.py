"""E7 — confirm E6 on real human voices (recorded with web/#/record).

Pre-registered before any real clip existed (27 Oct 2026):
  - Same models and settings as E6: spark-1.2@low vs spark-1.3@low, 3 repeats.
  - Same failure-type rules as E6, unchanged: experiments/e6_audio.py DENY pattern, "all fields blank".
  - Prediction: 1.3 gives more "confident wrong or blank" answers than 1.2 (paired, per clip, majority
    of 3 tries), and says "I can't hear" less often. Confirmed if the first holds at p < 0.05.
  - If it does not hold, E6 is reported as a finding about synthetic voices only.

  python3 experiments/e7_real_voices.py                  # dry run, prints cost
  python3 experiments/e7_real_voices.py --yes --budget 4
"""
from __future__ import annotations

import os

from common import base_args, compare, majority, pairs, run_and_score, table, tasks_by_id, write_result
from e6_audio import A, B, MODES, failure_modes

PACKS = ["audio-real"]


def analyse(run_dir: str) -> None:
    path = os.path.join(run_dir, "scores.jsonl")
    tasks = tasks_by_id(run_dir)
    maj = majority(path)
    rows = [compare(pairs(maj, tasks, A, B), "overall")]
    for key in ("lang", "category"):
        for val in sorted({t[key] for t in tasks.values()}):
            ps = pairs(maj, [i for i, t in tasks.items() if t[key] == val], A, B)
            if len(ps) >= 5:
                rows.append(compare(ps, "%s=%s" % (key, val)))
    counts, deny_ans, tests = failure_modes(run_dir, tasks)
    speakers = sorted({t["meta"]["speaker"] for t in tasks.values()})
    lines = ["# E7 — real voices: %s vs %s" % (A, B), "", "Run: `%s` · speakers: %s · clips: %d" % (
        run_dir, ", ".join(speakers), len(tasks)), "", "## Correct answer", "", table(rows), "",
        "## How each version fails (every answer)", "",
        "| Version | Language | " + " | ".join(MODES) + " |", "|---|---|" + "---|" * len(MODES)]
    for c in (A, B):
        for lang in ("all", "en", "hi", "hinglish"):
            lines.append("| %s | %s | %s |" % (c, lang, " | ".join(str(counts[(c, lang, m)]) for m in MODES)))
    lines += ["", "## Pre-registered test (paired, majority of 3 tries, exact McNemar)", "",
              "| Flag | Language | Tasks | %s | %s | p |" % (A, B), "|---|---|---|---|---|---|"]
    for t in tests:
        lines.append("| %s | %s | %d | %d | %d | %.2g |" % (t["flag"], t["lang"], t["tasks"], t[A], t[B], t["p"]))
    main = next(t for t in tests if t["flag"] == "confident wrong or blank" and t["lang"] == "all")
    held = main[B] > main[A] and main["p"] < 0.05
    lines += ["", "**Prediction %s:** confident wrong or blank %d → %d tasks, p = %.2g." % (
        "CONFIRMED" if held else "NOT CONFIRMED", main[A], main[B], main["p"])]
    write_result("e7_real_voices", "\n".join(lines), {"run_dir": run_dir, "rows": rows, "tests": tests,
                                                      "speakers": speakers, "confirmed": held})


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes, "e7-real-voices")
    analyse(rd)
