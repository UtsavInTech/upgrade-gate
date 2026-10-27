"""E6 — does Muse Spark 1.3 listen worse than 1.2? (Meta's docs warn about 1.3 audio.)

135 spoken clips (English / Hindi / Hinglish voice notes, spoken math) with known answers, each
with a text twin carrying the same words. An audio-specific regression shows up as: 1.3 loses
on audio tasks while the text twins stay level.

  python3 experiments/e6_audio.py                 # dry run, prints cost
  python3 experiments/e6_audio.py --yes --budget 8
"""
from __future__ import annotations

import collections
import json
import os
import re

from common import (base_args, compare, majority, mcnemar_exact, pairs, run_and_score, table, tasks_by_id,
                    write_result)
from upgrade_gate.schema import read_jsonl

# "I can't listen to audio" in English / Hinglish (1.2 says this while quoting the spoken words)
DENY = re.compile(
    r"(can'?t|cannot|unable to|don'?t have the ability to|not able to)\s+(listen|hear|access|process|play)"
    r"|no audio|audio (file|attachment)s? (tak|was not|wasn'?t)|pahunch nahi",
    re.I,
)
MODES = ["correct", "says it can't hear", "confident wrong", "silent blank", "no answer (token limit)"]


def _mode(task, resp, passed) -> str:
    """Failure type of one audio answer. Order matters: a correct answer that also claims it can't
    hear stays 'correct' for accuracy but is counted in deny_with_answer."""
    if resp.get("error"):
        return "no answer (token limit)"
    text = resp.get("text") or ""
    if passed:
        return "correct"
    if DENY.search(text):
        return "says it can't hear"
    if task["meta"]["kind"] == "extract":
        m = re.search(r"\{.*\}", text, re.S)
        try:
            obj = json.loads(m.group(0)) if m else None
        except ValueError:
            obj = None
        if isinstance(obj, dict) and obj and all(v in ("", None) for v in obj.values()):
            return "silent blank"
    return "confident wrong"


def failure_modes(run_dir: str, tasks):
    """Per-answer counts by failure type, and paired McNemar tests on per-task majorities for
    'confident wrong or blank' and 'says it can't hear'."""
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in read_jsonl(os.path.join(run_dir, "responses.jsonl"))}
    counts = collections.Counter()
    deny_with_answer = collections.Counter()
    flags = collections.defaultdict(lambda: collections.defaultdict(list))  # flag -> (task, cand) -> [bool]
    for s in read_jsonl(os.path.join(run_dir, "scores.jsonl")):
        t = tasks.get(s["task_id"])
        if not t or t["modality"] != "audio":
            continue
        r = resp[(s["task_id"], s["candidate"], s["repeat"])]
        m = _mode(t, r, s["passed"] is True)
        counts[(s["candidate"], t["lang"], m)] += 1
        counts[(s["candidate"], "all", m)] += 1
        denies = bool(DENY.search(r.get("text") or ""))
        if denies and s["passed"] is True:
            deny_with_answer[s["candidate"]] += 1
        flags["confident wrong or blank"][(s["task_id"], s["candidate"])].append(m in ("confident wrong", "silent blank"))
        flags["says it can't hear"][(s["task_id"], s["candidate"])].append(denies)
    tests = []
    for name, store in flags.items():
        for lang in ("all", "en", "hi", "hinglish"):
            n = a_n = b_n = only_a = only_b = 0
            for tid, t in tasks.items():
                if t["modality"] != "audio" or (lang != "all" and t["lang"] != lang):
                    continue
                x, y = store.get((tid, A)), store.get((tid, B))
                if not x or not y:
                    continue
                mx, my = sum(x) * 2 > len(x), sum(y) * 2 > len(y)
                n += 1
                a_n += mx
                b_n += my
                only_a += mx and not my
                only_b += my and not mx
            tests.append({"flag": name, "lang": lang, "tasks": n, A: a_n, B: b_n,
                          "only_" + A: only_a, "only_" + B: only_b, "p": mcnemar_exact(only_a, only_b)})
    return counts, deny_with_answer, tests

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

    counts, deny_ans, tests = failure_modes(run_dir, tasks)
    lines += ["", "## How each version fails (every audio answer, 3 repeats)", "",
              "| Version | Language | " + " | ".join(MODES) + " |", "|---|---|" + "---|" * len(MODES)]
    for c in (A, B):
        for lang in ("all", "en", "hi", "hinglish"):
            lines.append("| %s | %s | %s |" % (c, lang, " | ".join(str(counts[(c, lang, m)]) for m in MODES)))
    lines += ["", "Correct answers that ALSO claimed the model can't hear audio (it quoted the spoken words): "
              + ", ".join("%s %d" % (c, deny_ans[c]) for c in (A, B)), "",
              "## Did the failure type change? (paired, majority of repeats per task, exact McNemar)", "",
              "| Flag | Language | Tasks | %s | %s | only %s | only %s | p |" % (A, B, A, B), "|---|---|---|---|---|---|---|---|"]
    for t in tests:
        lines.append("| %s | %s | %d | %d | %d | %d | %d | %.2g |" % (
            t["flag"], t["lang"], t["tasks"], t[A], t[B], t["only_" + A], t["only_" + B], t["p"]))
    write_result("e6_audio", "\n".join(lines), {
        "run_dir": run_dir, "rows": rows, "strict_rows": strict, "listening_failures": lf,
        "failure_modes": {"%s|%s|%s" % k: v for k, v in counts.items()},
        "deny_with_answer": dict(deny_ans), "failure_tests": tests})


if __name__ == "__main__":
    args = base_args(__doc__).parse_args()
    rd = args.run_dir or run_and_score(PACKS, [A, B], args.n, args.repeats, args.budget, args.yes, "e6-audio")
    analyse(rd)
