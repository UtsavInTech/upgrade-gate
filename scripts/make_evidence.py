"""Copy saved runs into evidence/ (committed) so CI can gate a model change without API calls.

Keeps tasks, scores and answers; drops raw API payloads. Real-voice recordings are not copied
(tasks only reference them; the gate never needs the audio).

    PYTHONPATH=. python3 scripts/make_evidence.py
"""
from __future__ import annotations

import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUITES = {  # CI check name -> saved run
    "voice-notes": "e6-audio",
    "real-voices": "e7-real-voices",
    "text-and-documents": "e1-upgrade",
}


def main() -> None:
    for suite, run in SUITES.items():
        src = os.path.join(ROOT, "results", run)
        dst = os.path.join(ROOT, "evidence", suite)
        os.makedirs(dst, exist_ok=True)
        shutil.copyfile(os.path.join(src, "run.json"), os.path.join(dst, "run.json"))
        shutil.copyfile(os.path.join(src, "tasks.jsonl"), os.path.join(dst, "tasks.jsonl"))
        shutil.copyfile(os.path.join(src, "scores.jsonl"), os.path.join(dst, "scores.jsonl"))
        with open(os.path.join(src, "responses.jsonl"), encoding="utf-8") as f, \
                open(os.path.join(dst, "responses.jsonl"), "w", encoding="utf-8") as out:
            for line in f:
                r = json.loads(line)
                r.pop("raw", None)
                out.write(json.dumps(r, ensure_ascii=False) + "\n")
        size = sum(os.path.getsize(os.path.join(dst, n)) for n in os.listdir(dst))
        print("%-20s <- results/%-16s %.1f MB" % (suite, run, size / 1e6))


if __name__ == "__main__":
    main()
