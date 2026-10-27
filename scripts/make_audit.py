"""Draw the blind label-audit sample: 60 audio answers, 15 per automatic answer type.

Writes:
  web/public/data/audit.json  what the labeller sees: clip text, correct answer, model reply (no model name,
                              no automatic label), in random order
  data/audit/key.json         the automatic label for each item (the labeller should not open this)

Fixed seed, so the sample is the same every time. No API calls.

    PYTHONPATH=. python3 scripts/make_audit.py
"""
from __future__ import annotations

import json
import os
import random
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from upgrade_gate.behaviour import answer_type  # noqa: E402
from upgrade_gate.schema import read_jsonl  # noqa: E402

RUNS = ["evidence/voice-notes", "evidence/real-voices"]
PER_TYPE = 15
TYPES = ["correct", "abstain", "blank", "wrong"]
SEED = 20261028


def _expected(t: dict) -> str:
    ref = t.get("reference")
    if isinstance(ref, dict):
        return ", ".join("%s: %s" % (k, v[0] if isinstance(v, list) else v) for k, v in ref.items())
    return str(ref)


def main() -> None:
    pool = defaultdict(list)
    for run in RUNS:
        d = os.path.join(ROOT, run)
        tasks = {t["id"]: t for t in read_jsonl(os.path.join(d, "tasks.jsonl"))}
        resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in read_jsonl(os.path.join(d, "responses.jsonl"))}
        for s in read_jsonl(os.path.join(d, "scores.jsonl")):
            t = tasks.get(s["task_id"])
            if not t or t.get("modality") != "audio":
                continue
            r = resp[(s["task_id"], s["candidate"], s["repeat"])]
            kind = answer_type(r.get("text"), r.get("error"), s.get("passed"))
            if kind not in TYPES:
                continue
            pool[kind].append({"run": run.split("/")[-1], "task_id": s["task_id"], "candidate": s["candidate"],
                               "repeat": s["repeat"], "said": (t.get("meta") or {}).get("transcript") or "",
                               "instruction": t["prompt"], "expected": _expected(t),
                               "answer": (r.get("text") or "").strip()[:900], "auto": kind})
    rng = random.Random(SEED)
    sample = []
    for kind in TYPES:
        items = sorted(pool[kind], key=lambda x: (x["run"], x["task_id"], x["candidate"], x["repeat"]))
        sample += rng.sample(items, min(PER_TYPE, len(items)))
    rng.shuffle(sample)
    shown, key = [], {}
    for i, x in enumerate(sample, 1):
        aid = "a%02d" % i
        key[aid] = {k: x[k] for k in ("auto", "run", "task_id", "candidate", "repeat")}
        shown.append({"id": aid, "said": x["said"], "instruction": x["instruction"], "expected": x["expected"],
                      "answer": x["answer"]})
    os.makedirs(os.path.join(ROOT, "data", "audit"), exist_ok=True)
    with open(os.path.join(ROOT, "web", "public", "data", "audit.json"), "w", encoding="utf-8") as f:
        json.dump(shown, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, "data", "audit", "key.json"), "w", encoding="utf-8") as f:
        json.dump({"seed": SEED, "per_type": PER_TYPE, "items": key}, f, ensure_ascii=False, indent=1)
    print("sample:", {k: sum(1 for v in key.values() if v["auto"] == k) for k in TYPES}, "| total", len(shown))


if __name__ == "__main__":
    main()
