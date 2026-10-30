"""Add the transcribe route ("transcribe+spark-1.3@low", E9) to the saved evidence the PR checks replay.

  python3 scripts/add_route_evidence.py          # rewrites evidence/*/responses.jsonl and scores.jsonl

How each saved row is made, so the replayed check is about exactly what the route does:
  - audio input (voice-notes, real-voices): the E9 answers from results/e9-route-<set>/ (Voice
    Transcribe, then Spark 1.3 on the transcript; 3 full-pipeline tries). For real voices the transcript
    text is left out: those recordings are private.
  - any other input (the text twins of voice notes, text, documents, images): the route only changes
    how audio is read, so these are Spark 1.3's own saved answers, relabelled. Nothing is re-run.
Running it twice gives the same files (old route rows are dropped first). No API calls.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate.schema import read_jsonl  # noqa: E402

ROUTE, PLAIN = "transcribe+spark-1.3@low", "spark-1.3@low"
SUITES = {"voice-notes": "results/e9-route-synth", "real-voices": "results/e9-route-real", "text-and-documents": None}
PRIVATE = {"real-voices"}


def write(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    for suite, e9 in SUITES.items():
        d = os.path.join(ROOT, "evidence", suite)
        tasks = {t["id"]: t for t in read_jsonl(os.path.join(d, "tasks.jsonl"))}
        audio = {i for i, t in tasks.items() if t.get("modality") == "audio"}
        resp = [r for r in read_jsonl(os.path.join(d, "responses.jsonl")) if r["candidate"] != ROUTE]
        scores = [s for s in read_jsonl(os.path.join(d, "scores.jsonl")) if s["candidate"] != ROUTE]

        new_r, new_s = [], []
        # non-audio input: Spark 1.3's own answers
        for r in resp:
            if r["candidate"] == PLAIN and r["task_id"] not in audio:
                new_r.append(dict(r, candidate=ROUTE, note="non-audio input: the route is Spark 1.3 itself"))
        for s in scores:
            if s["candidate"] == PLAIN and s["task_id"] not in audio:
                new_s.append(dict(s, candidate=ROUTE))
        # audio input: E9's route answers
        if audio:
            src = os.path.join(ROOT, e9)
            for r in read_jsonl(os.path.join(src, "responses.jsonl")):
                if r["candidate"] == ROUTE and r["task_id"] in audio:
                    r = dict(r, run_id="e9-route")
                    if suite in PRIVATE and r.get("stages", {}).get("transcribe"):
                        r["stages"] = dict(r["stages"], transcribe={k: v for k, v in r["stages"]["transcribe"].items()
                                                                     if k != "transcript"})
                    new_r.append(r)
            for s in read_jsonl(os.path.join(src, "scores.jsonl")):
                if s["candidate"] == ROUTE and s["task_id"] in audio:
                    new_s.append(s)

        write(os.path.join(d, "responses.jsonl"), resp + new_r)
        write(os.path.join(d, "scores.jsonl"), scores + new_s)
        with open(os.path.join(d, "run.json"), encoding="utf-8") as f:
            run = json.load(f)
        run["candidates"] = [c for c in run["candidates"] if c["name"] != ROUTE] + [
            {"name": ROUTE, "model_id": "muse-voice-transcribe-1.0>muse-spark-1.3",
             "params": {"reasoning_effort": "low"},
             "note": "audio: E9 answers; other input: Spark 1.3's saved answers (scripts/add_route_evidence.py)"}]
        with open(os.path.join(d, "run.json"), "w", encoding="utf-8") as f:
            json.dump(run, f, indent=2, ensure_ascii=False)
            f.write("\n")
        n_audio = sum(1 for r in new_r if r["task_id"] in audio)
        print("%s: +%d route answers (%d audio from E9, %d from Spark 1.3), +%d scores"
              % (suite, len(new_r), n_audio, len(new_r) - n_audio, len(new_s)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
