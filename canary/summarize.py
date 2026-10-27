"""Summarise all canary runs into canary/reports/summary.md.

Answers the H5 questions:
  - Does the pass rate move between days, beyond the noise inside a single run?
  - Does it move with time of day (H5b, server load)?
  - Which prompts changed their answer between days?
  - Is Hindi/Hinglish behaving differently from the matched English prompts (H6)?

Usage: python3 canary/summarize.py
Smoke runs (files ending -smoke.jsonl) are skipped. Checks are re-scored from the raw
text, so fixing a check in checks.py updates old results too.
"""
import collections
import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from checks import check, strip_wrapping  # noqa: E402


def load():
    with open(os.path.join(HERE, "prompts.json"), encoding="utf-8") as f:
        specs = {p["id"]: p for p in json.load(f)}
    rows = []
    for path in sorted(glob.glob(os.path.join(HERE, "data", "*", "run-*.jsonl"))):
        if path.endswith("-smoke.jsonl"):
            continue
        day = os.path.basename(os.path.dirname(path))
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                r["day"] = day
                spec = specs.get(r["prompt_id"])
                if spec and r.get("text") is not None:
                    r["passed"] = check(r["text"], spec["check"])[0]
                rows.append(r)
    return rows, specs


def rate(rs):
    scored = [r for r in rs if r.get("passed") is not None]
    if not scored:
        return None, 0
    return sum(r["passed"] for r in scored) / len(scored), len(scored)


def ci95(p, n):
    if n == 0 or p is None:
        return ""
    half = 1.96 * math.sqrt(max(p * (1 - p), 1e-9) / n)
    return "±%.1f" % (100 * half)


def fmt(p, n):
    return "—" if p is None else "%.1f%% %s (n=%d)" % (100 * p, ci95(p, n), n)


def norm(text):
    return " ".join(strip_wrapping(text or "").split()).casefold()


def main():
    rows, specs = load()
    if not rows:
        sys.exit("No runs found in canary/data/. Run canary/run.py first.")
    models = sorted({r["model"] for r in rows})
    out = ["# Canary summary", ""]
    total_err = sum(1 for r in rows if r.get("passed") is None)
    out.append("%d responses, %d runs, %d API errors (excluded from pass rates)." % (
        len(rows), len({r["run_id"] for r in rows}), total_err))

    for model in models:
        mr = [r for r in rows if r["model"] == model]
        out += ["", "## %s" % model, ""]

        out += ["### Pass rate by day", "", "| Day | Pass rate |", "|---|---|"]
        for day in sorted({r["day"] for r in mr}):
            out.append("| %s | %s |" % (day, fmt(*rate([r for r in mr if r["day"] == day]))))

        out += ["", "### Pass rate by IST hour (H5b)", "", "| IST hour | Pass rate | Median latency ms |", "|---|---|---|"]
        for h in sorted({r["ist_hour"] for r in mr}):
            hr = [r for r in mr if r["ist_hour"] == h]
            lats = sorted(r["latency_ms"] for r in hr if r.get("latency_ms") is not None)
            med = lats[len(lats) // 2] if lats else "—"
            out.append("| %02d:00 | %s | %s |" % (h, fmt(*rate(hr)), med))

        out += ["", "### Language (H6)", "", "| Group | Pass rate |", "|---|---|"]
        hi = [r for r in mr if r["lang"] in ("hi", "hinglish")]
        paired_en_ids = {specs[r["prompt_id"]].get("pair") for r in hi if r["prompt_id"] in specs}
        en_pairs = [r for r in mr if r["prompt_id"] in paired_en_ids]
        out.append("| Hindi + Hinglish (all 10) | %s |" % fmt(*rate(hi)))
        out.append("| Hindi/Hinglish with an English pair | %s |" % fmt(*rate([r for r in hi if r.get("pair")])))
        out.append("| Their matched English prompts | %s |" % fmt(*rate(en_pairs)))
        out.append("| All English | %s |" % fmt(*rate([r for r in mr if r["lang"] == "en"])))

        # Noise floor vs drift: distinct answers inside one run vs across runs.
        by_run = collections.defaultdict(list)
        by_prompt = collections.defaultdict(list)
        for r in mr:
            if r.get("text") is not None:
                by_run[(r["run_id"], r["prompt_id"])].append(norm(r["text"]))
                by_prompt[r["prompt_id"]].append(r)
        within = [len(set(v)) > 1 for v in by_run.values() if len(v) > 1]
        out += ["", "### Consistency", ""]
        if within:
            out.append("- Prompt-runs with more than one distinct answer inside the same run: **%.1f%%** (%d of %d). This is the noise floor." % (
                100 * sum(within) / len(within), sum(within), len(within)))

        changed = []
        for pid, rs in sorted(by_prompt.items()):
            per_day = collections.defaultdict(list)
            for r in rs:
                per_day[r["day"]].append(norm(r["text"]))
            majority = {d: collections.Counter(v).most_common(1)[0][0] for d, v in per_day.items()}
            if len(set(majority.values())) > 1:
                days = ", ".join("%s: %r" % (d, majority[d][:40]) for d in sorted(majority))
                changed.append("- `%s` (%s) %s" % (pid, specs.get(pid, {}).get("lang", "?"), days))
        out.append("- Prompts whose most common answer changed between days: **%d**" % len(changed))
        out += changed

        failing = collections.Counter(r["prompt_id"] for r in mr if r.get("passed") is False)
        if failing:
            out += ["", "### Most-failed prompts", ""]
            for pid, n in failing.most_common(10):
                ex = next(r for r in mr if r["prompt_id"] == pid and r.get("passed") is False)
                out.append("- `%s` failed %d× — e.g. %r" % (pid, n, (ex.get("text") or "")[:80]))

    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
    path = os.path.join(HERE, "reports", "summary.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print("\nWrote", os.path.relpath(path, os.path.dirname(HERE)))


if __name__ == "__main__":
    main()
