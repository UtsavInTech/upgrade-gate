"""E6 — does Muse Spark 1.3 listen worse than 1.2? (Meta's docs warn about 1.3 audio.)

135 spoken clips (English / Hindi / Hinglish voice notes, spoken math) with known answers, each
with a text twin carrying the same words. An audio-specific regression shows up as: 1.3 loses
on audio tasks while the text twins stay level.

  python3 experiments/e6_audio.py                 # dry run, prints cost
  python3 experiments/e6_audio.py --yes --budget 8
"""
from __future__ import annotations

import os

from common import base_args, compare, majority, pairs, run_and_score, table, tasks_by_id, write_result

PACKS = ["audio-synth"]
A, B = "spark-1.2@low", "spark-1.3@low"


def _rows(maj, tasks):
    rows = []
    for mod in ("audio", "text"):
        ids = [i for i, t in tasks.items() if t["modality"] == mod]
        rows.append(compare(pairs(maj, ids, A, B), "%s: overall" % mod))
        for key in ("lang", "category"):
            for val in sorted({t[key] for t in tasks.values()}):
                sub = [i for i in ids if tasks[i][key] == val]
                ps = pairs(maj, sub, A, B)
                if len(ps) >= 10:
                    rows.append(compare(ps, "%s: %s=%s" % (mod, key, val)))
    return rows


def _listening_failures(maj, tasks, cand):
    """Audio task failed while its text twin passed: the model understood the words but not the clip."""
    out = []
    for i, t in tasks.items():
        twin = t["meta"].get("twin")
        if t["modality"] != "audio" or twin not in tasks:
            continue
        if maj.get((i, cand)) is False and maj.get((twin, cand)) is True:
            out.append(i)
    return sorted(out)


def analyse(run_dir: str) -> None:
    path = os.path.join(run_dir, "scores.jsonl")
    tasks = tasks_by_id(run_dir)
    maj = majority(path)
    rows = _rows(maj, tasks)
    strict = _rows(majority(path, "strict_passed"), tasks)
    lf = {c: _listening_failures(maj, tasks, c) for c in (A, B)}
    lines = ["# E6 — audio: %s vs %s" % (A, B), "", "Run: `%s`" % run_dir, "",
             "## Correct answer (content score)", "", table(rows), "",
             "## Exact format (strict score)", "", table(strict), "",
             "## Listening failures (audio wrong, text twin right, majority of repeats)", ""]
    for c in (A, B):
        lines.append("- **%s**: %d — %s" % (c, len(lf[c]), ", ".join(lf[c]) or "none"))
    write_result("e6_audio", "\n".join(lines), {"run_dir": run_dir, "rows": rows, "strict_rows": strict,
                                                "listening_failures": lf})


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes, "e6-audio")
    analyse(rd)
