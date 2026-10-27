"""Compare a person's blind labels (web #/audit) with the automatic answer-type rules.

    PYTHONPATH=. python3 scripts/audit_report.py            # every labeller found in data/audit/
    PYTHONPATH=. python3 scripts/audit_report.py --labeler utsav

Reports Cohen's kappa over the four types, kappa for the decision the gate uses (silent failure =
blank or wrong, vs not), a confusion table, and every disagreement with the answer text.
Writes experiments/out/audit.md and .json.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPES = ["correct", "abstain", "blank", "wrong"]
NAMES = {"correct": "correct", "abstain": "says it can't answer", "blank": "blank", "wrong": "wrong, no warning"}


def kappa(pairs, cats) -> float:
    n = len(pairs)
    if not n:
        return float("nan")
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in cats) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def latest_labels(path: str) -> dict:
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r["label"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeler", default=None)
    args = ap.parse_args()
    with open(os.path.join(ROOT, "data", "audit", "key.json"), encoding="utf-8") as f:
        key = json.load(f)["items"]
    with open(os.path.join(ROOT, "web", "public", "data", "audit.json"), encoding="utf-8") as f:
        shown = {x["id"]: x for x in json.load(f)}
    files = sorted(glob.glob(os.path.join(ROOT, "data", "audit", "labels-*.jsonl")))
    if args.labeler:
        files = [p for p in files if os.path.basename(p) == "labels-%s.jsonl" % args.labeler]
    if not files:
        raise SystemExit("No labels yet. Label the sample at web #/audit first.")

    lines = ["# Label audit: a person vs the automatic answer-type rules", "",
             "Sample: %d voice-note answers (E6 synthetic + E7 real voice), %d per automatic type, drawn with a "
             "fixed seed by `scripts/make_audit.py`. Shown blind: no model name, no automatic label." % (
                 len(key), len(key) // 4), ""]
    data = {"labelers": []}
    for path in files:
        who = os.path.basename(path)[len("labels-"):-len(".jsonl")]
        human = latest_labels(path)
        unsure = [i for i, l in human.items() if l == "unsure"]
        pairs = [(key[i]["auto"], human[i]) for i in key if i in human and human[i] != "unsure"]
        k4 = kappa(pairs, TYPES)
        silent = lambda x: "silent" if x in ("blank", "wrong") else "not"  # noqa: E731
        k2 = kappa([(silent(a), silent(b)) for a, b in pairs], ["silent", "not"])
        agree = sum(a == b for a, b in pairs)
        lines += ["## Labeller: %s" % who, "",
                  "- Labelled %d of %d; %d marked \"can't tell\" (left out)." % (len(human), len(key), len(unsure)),
                  "- Agreement on all four types: **%d of %d (%.0f%%), Cohen's κ = %.2f**." % (
                      agree, len(pairs), 100 * agree / max(1, len(pairs)), k4),
                  "- Agreement on the gate's decision (silent failure = blank or wrong, vs not): **κ = %.2f**." % k2,
                  "", "| Rules said ↓ / person said → | " + " | ".join(NAMES[t] for t in TYPES) + " |",
                  "|---|" + "---|" * len(TYPES)]
        conf = Counter(pairs)
        for a in TYPES:
            lines.append("| %s | %s |" % (NAMES[a], " | ".join(str(conf[(a, b)]) for b in TYPES)))
        dis = [i for i in sorted(key) if i in human and human[i] not in ("unsure", key[i]["auto"])]
        lines += ["", "### Disagreements (%d)" % len(dis), ""]
        for i in dis:
            x = shown[i]
            lines.append("- `%s` (%s, %s): rules **%s**, person **%s**. Reply: `%s`" % (
                i, key[i]["run"], key[i]["task_id"], NAMES[key[i]["auto"]], NAMES.get(human[i], human[i]),
                x["answer"][:160].replace("\n", " ").replace("`", "'")))
        lines.append("")
        data["labelers"].append({"labeler": who, "labelled": len(human), "unsure": len(unsure), "agree": agree,
                                 "n": len(pairs), "kappa_4": k4, "kappa_silent": k2,
                                 "confusion": {"%s|%s" % k: v for k, v in conf.items()}, "disagreements": dis})
    out = os.path.join(ROOT, "experiments", "out")
    with open(os.path.join(out, "audit.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(out, "audit.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
