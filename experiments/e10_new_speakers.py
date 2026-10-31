"""E10 — new real speakers (pre-registered in findings/LOG.md before the recordings were downloaded).

Test A: Spark 1.2 vs Spark 1.3, both listening, on every real-voice clip (Utsav's answers come from the
        cache, $0). Primary = new speakers only; Utsav and the pooled set are reported alongside.
Test B: Spark 1.2 listening vs Voice Transcribe -> Spark 1.3 (the E9 route, same prompt, 3 full-pipeline
        tries) on the new speakers, and pooled with Utsav's E9 answers.
Frozen: behaviour rules + release/policy.json (commit b053453), E6/E7 prompt and scorer, effort low.

  python3 experiments/e10_new_speakers.py              # dry run
  python3 experiments/e10_new_speakers.py --yes --budget 3
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from common import run_and_score  # noqa: E402
import e9_route  # noqa: E402
from upgrade_gate.schema import read_jsonl  # noqa: E402

A, B, ROUTE = "spark-1.2@low", "spark-1.3@low", "transcribe+spark-1.3@low"
OLD = {"utsav"}  # used to write E7's rules: never in the primary population


def subset(src: str, dst: str, keep) -> str:
    """Copy a run dir keeping only tasks whose speaker passes `keep`."""
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    tasks = [t for t in read_jsonl(os.path.join(src, "tasks.jsonl")) if keep(t["meta"].get("speaker"))]
    ids = {t["id"] for t in tasks}
    shutil.copy(os.path.join(src, "run.json"), os.path.join(dst, "run.json"))
    for name, rows in (("tasks.jsonl", tasks),
                       ("responses.jsonl", [r for r in read_jsonl(os.path.join(src, "responses.jsonl")) if r["task_id"] in ids]),
                       ("scores.jsonl", [r for r in read_jsonl(os.path.join(src, "scores.jsonl")) if r["task_id"] in ids])):
        with open(os.path.join(dst, name), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return dst


def add_route(run_dir: str, budget: float) -> None:
    """Add the transcribe route's answers to a run dir (same code as E9), then rescore."""
    tasks = list(read_jsonl(os.path.join(run_dir, "tasks.jsonl")))
    trs = e9_route.transcribe_all(tasks)
    print("  transcription errors:", sum(1 for v in trs.values() if v.get("error")))
    saved = e9_route.ROUTES
    e9_route.ROUTES = {ROUTE: B}  # only the pre-registered route
    try:
        rows = e9_route.spark_all(tasks, trs, budget)
    finally:
        e9_route.ROUTES = saved
    with open(os.path.join(run_dir, "responses.jsonl"), "a", encoding="utf-8") as f:
        for r in rows:
            r["run_id"] = "e10"
            r.get("stages", {}).get("transcribe", {}).pop("transcript", None)  # real voices: keep text private
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(run_dir, "run.json"), encoding="utf-8") as f:
        info = json.load(f)
    info["candidates"].append({"name": ROUTE, "model_id": "muse-voice-transcribe-1.0>muse-spark-1.3",
                               "params": {"reasoning_effort": "low"}})
    with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    from upgrade_gate.scoring import score_run
    score_run(run_dir)


def gate(run_dir: str, cand: str) -> dict:
    text, g = e9_route.gate(run_dir, cand)
    return {"decision": g["decision"], "reasons": g.get("reasons", []), "stdout": text,
            "overall": {k: (g.get("overall") or {}).get(k) for k in ("delta", "ci_low", "ci_high", "n")}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--budget", type=float, default=3.0)
    args = ap.parse_args()

    full = run_and_score(["audio-real"], [A, B], None, 3, args.budget, args.yes, "e10-real-voices")
    speakers = sorted({t["meta"]["speaker"] for t in read_jsonl(os.path.join(full, "tasks.jsonl"))})
    new = [s for s in speakers if s not in OLD]
    print("speakers:", speakers, "| new:", new)

    res = os.path.join(ROOT, "results")
    add_route(full, args.budget)  # Utsav's route answers come from the E9 cache
    sets = {"new": subset(full, os.path.join(res, "e10-new"), lambda s: s not in OLD),
            "pooled": full}
    for s in speakers:
        sets["speaker:" + s] = subset(full, os.path.join(res, "e10-" + s), lambda x, s=s: x == s)

    out = {"speakers": speakers, "new": new, "sets": {}}
    for name, d in sets.items():
        tasks = list(read_jsonl(os.path.join(d, "tasks.jsonl")))
        out["sets"][name] = {"run_dir": os.path.relpath(d, ROOT), "clips": len(tasks),
                             "testA": gate(d, B), "testB": gate(d, ROUTE),
                             "describe": e9_route.describe(d, tasks)}
        print("\n[%s] %d clips | A (1.2 -> 1.3 listening): %s | B (1.2 -> transcribe route): %s" % (
            name, len(tasks), out["sets"][name]["testA"]["decision"].upper(), out["sets"][name]["testB"]["decision"].upper()))
        for k in ("testA", "testB"):
            print("  %s:" % k, out["sets"][name][k]["stdout"].replace("\n", "\n    "))
    path = os.path.join(ROOT, "experiments", "out", "e10_new_speakers.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\nwrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
