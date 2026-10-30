"""E9 — is there a safe upgrade route for voice notes? (pre-registered in findings/LOG.md)

Route: clip -> muse-voice-transcribe-1.0 -> transcript -> Spark (text). Compared with today's
production route, Spark 1.2 listening to the clip, using the saved E6 / E7 answers ($0) and the
unchanged production gate + release/policy.json.

  python3 experiments/e9_route.py                       # dry run: counts and cost estimate
  python3 experiments/e9_route.py --yes --budget 3      # synth (primary) + real voice (secondary)
  python3 experiments/e9_route.py --set synth --run-only   # rebuild tables from cache, no calls

Each of the 3 tries is a full pipeline: the clip is transcribed 3 times; try k uses transcript k.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate.behaviour import answer_type  # noqa: E402
from upgrade_gate.schema import read_jsonl  # noqa: E402

SETS = {"synth": "evidence/voice-notes", "real": "evidence/real-voices"}
BASE, DIRECT13 = "spark-1.2@low", "spark-1.3@low"
ROUTES = {"transcribe+spark-1.3@low": "spark-1.3@low", "transcribe+spark-1.2@low": "spark-1.2@low"}
PRIMARY = "transcribe+spark-1.3@low"
from upgrade_gate.transcribe import ROUTE_LEAD as LEAD, route_prompt as _route_prompt  # noqa: E402
REPEATS = 3


def ask(task: dict) -> str:
    """The E6 instruction without its 'Listen to the attached audio.' opener."""
    p = task["prompt"]
    pre = "Listen to the attached audio. "
    return p[len(pre):] if p.startswith(pre) else p


def route_prompt(task: dict, transcript: str) -> str:
    return _route_prompt(ask(task), transcript)


def load(set_name: str):
    d = os.path.join(ROOT, SETS[set_name])
    tasks = [t for t in read_jsonl(os.path.join(d, "tasks.jsonl")) if t["modality"] == "audio"]
    ids = {t["id"] for t in tasks}
    resp = [r for r in read_jsonl(os.path.join(d, "responses.jsonl")) if r["task_id"] in ids]
    return tasks, resp


def transcribe_all(tasks, workers=4):
    from upgrade_gate.transcribe import transcribe
    jobs = [(t["id"], t["attachments"][0], k) for t in tasks for k in range(REPEATS)]
    out = {}
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(transcribe, os.path.join(ROOT, p), k): (tid, k) for tid, p, k in jobs}
        for i, f in enumerate(cf.as_completed(futs), 1):
            out[futs[f]] = f.result()
            if i % 50 == 0:
                print("  transcribed %d/%d" % (i, len(jobs)))
    return out


def spark_all(tasks, transcripts, budget):
    from upgrade_gate.cli import parse_candidate
    from upgrade_gate.client import ModelClient
    client = ModelClient(max_concurrency=8, run_budget_usd=budget)
    rows = []
    jobs = []
    for route, cand_name in ROUTES.items():
        cand = parse_candidate(cand_name)
        for t in tasks:
            for k in range(REPEATS):
                jobs.append((route, cand, t, k))

    def do(job):
        route, cand, t, k = job
        tr = transcripts[(t["id"], k)]
        base = {"run_id": "e9-route", "task_id": t["id"], "candidate": route, "repeat": k + 1,
                "ts_utc": None, "cached": False}
        if tr.get("error") or tr.get("transcript") is None:
            return dict(base, text=None, usage={}, cost_usd=tr.get("cost_usd", 0.0),
                        latency_ms=tr.get("latency_ms", 0), error="transcription failed: %s" % tr.get("error"),
                        returned_model=None, stages={"transcribe": tr})
        msgs = [{"role": "user", "content": route_prompt(t, tr["transcript"])}]
        res = client.chat(cand.model_id, msgs, params=cand.params, cache_salt="e9-rep%d" % (k + 1))
        return dict(base, text=res.text, usage=res.usage, error=res.error, returned_model=res.returned_model,
                    cost_usd=round(tr["cost_usd"] + res.cost_usd, 8),
                    latency_ms=int(tr["latency_ms"] + res.latency_ms), cached=res.cached,
                    stages={"transcribe": {"cost_usd": tr["cost_usd"], "latency_ms": tr["latency_ms"],
                                           "audio_ms": tr.get("audio_ms"), "transcript": tr["transcript"]},
                            "spark": {"model": cand.model_id, "cost_usd": res.cost_usd, "latency_ms": res.latency_ms}})

    with cf.ThreadPoolExecutor(8) as ex:
        for i, row in enumerate(ex.map(do, jobs), 1):
            rows.append(row)
            if i % 100 == 0:
                print("  spark %d/%d" % (i, len(jobs)))
    return rows


def build_run(set_name, tasks, saved, new_rows):
    run_dir = os.path.join(ROOT, "results", "e9-route-%s" % set_name)
    shutil.rmtree(run_dir, ignore_errors=True)
    os.makedirs(run_dir)
    with open(os.path.join(ROOT, SETS[set_name], "run.json"), encoding="utf-8") as f:
        src = json.load(f)
    cands = list(src["candidates"]) + [{"name": r, "model_id": "%s>%s" % ("muse-voice-transcribe-1.0", m),
                                         "params": {"reasoning_effort": "low"}} for r, m in ROUTES.items()]
    info = {"run_id": "e9-route-%s" % set_name, "candidates": cands, "baseline": BASE,
            "packs": src.get("packs"), "n_tasks": len(tasks), "repeats": REPEATS,
            "notes": "E9: saved %s answers for %s and %s; transcribe routes run fresh" % (SETS[set_name], BASE, DIRECT13)}
    with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    for name, rows in (("tasks.jsonl", tasks), ("responses.jsonl", saved + new_rows)):
        with open(os.path.join(run_dir, name), "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from upgrade_gate.scoring import score_run
    score_run(run_dir)
    return run_dir


def gate(run_dir, candidate):
    exe = os.path.join(ROOT, ".venv", "bin", "upgrade-gate")
    p = subprocess.run([exe, "gate", run_dir, "--baseline", BASE, "--candidate", candidate,
                        "--policy", os.path.join(ROOT, "release", "policy.json")],
                       capture_output=True, text=True, cwd=ROOT)
    with open(os.path.join(run_dir, "gate.json"), encoding="utf-8") as f:
        g = json.load(f)
    shutil.copy(os.path.join(run_dir, "gate.json"), os.path.join(run_dir, "gate-%s.json" % candidate))
    return p.stdout.strip(), g


def describe(run_dir, tasks):
    """Descriptive numbers: correct, answer types, digit fields, latency, cost per candidate."""
    tmap = {t["id"]: t for t in tasks}
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in read_jsonl(os.path.join(run_dir, "responses.jsonl"))}
    scores = list(read_jsonl(os.path.join(run_dir, "scores.jsonl")))
    by = defaultdict(lambda: {"n": 0, "correct": 0, "types": Counter(), "lat": [], "cost": 0.0,
                              "asr_cost": 0.0, "fields": Counter(), "fields_n": Counter()})
    maj = defaultdict(list)
    for s in scores:
        r = resp[(s["task_id"], s["candidate"], s["repeat"])]
        b = by[s["candidate"]]
        b["n"] += 1
        b["correct"] += s["passed"] is True
        b["types"][answer_type(r.get("text"), r.get("error"), s.get("passed"))] += 1
        b["lat"].append(r.get("latency_ms") or 0)
        b["cost"] += r.get("cost_usd") or 0.0
        b["asr_cost"] += ((r.get("stages") or {}).get("transcribe") or {}).get("cost_usd") or 0.0
        maj[(s["task_id"], s["candidate"])].append(s["passed"] is True)
        t = tmap[s["task_id"]]
        if (t.get("meta") or {}).get("kind") == "extract":
            got = _json(r.get("text"))
            for field in ("order_number", "pincode"):
                b["fields_n"][field] += 1
                want = str(t["reference"][field])
                b["fields"][field] += isinstance(got, dict) and "".join(ch for ch in str(got.get(field, "")) if ch.isdigit()) == want
    out = {}
    for c, b in by.items():
        clips = len({tid for tid, cc in maj if cc == c})
        lat = sorted(b["lat"])
        out[c] = {"answers": b["n"], "correct": b["correct"],
                  "clips_correct_majority": sum(sum(v) * 2 > len(v) for (tid, cc), v in maj.items() if cc == c),
                  "clips": clips, "types": dict(b["types"]),
                  "order_number_right": "%d/%d" % (b["fields"]["order_number"], b["fields_n"]["order_number"]),
                  "pincode_right": "%d/%d" % (b["fields"]["pincode"], b["fields_n"]["pincode"]),
                  "latency_ms_median": int(statistics.median(lat)) if lat else None,
                  "latency_ms_p90": lat[int(0.9 * (len(lat) - 1))] if lat else None,
                  "usd_per_1000_clips": round(1000 * b["cost"] / max(1, b["n"]), 3),
                  "asr_usd_per_1000_clips": round(1000 * b["asr_cost"] / max(1, b["n"]), 3)}
    return out


def _json(text):
    import re
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--set", choices=["synth", "real", "all"], default="all")
    ap.add_argument("--yes", action="store_true", help="actually spend money")
    ap.add_argument("--budget", type=float, default=3.0)
    args = ap.parse_args()
    sets = ["synth", "real"] if args.set == "all" else [args.set]

    from upgrade_gate.transcribe import USD_PER_SECOND, _seconds
    for s in sets:
        tasks, _ = load(s)
        secs = sum(_seconds(os.path.join(ROOT, t["attachments"][0])) for t in tasks)
        print("%s: %d clips, %.1f min audio; transcription ~$%.3f for %d tries; Spark text calls: %d" % (
            s, len(tasks), secs / 60, secs * USD_PER_SECOND * REPEATS, REPEATS, len(tasks) * REPEATS * len(ROUTES)))
    if not args.yes:
        raise SystemExit("Dry run. Add --yes to spend (cap $%.2f)." % args.budget)

    summary = {}
    for s in sets:
        tasks, saved = load(s)
        print("== %s: transcribing" % s)
        trs = transcribe_all(tasks)
        bad = sum(1 for v in trs.values() if v.get("error"))
        print("  transcription errors: %d" % bad)
        print("== %s: Spark on transcripts" % s)
        rows = spark_all(tasks, trs, args.budget)
        run_dir = build_run(s, tasks, saved, rows)
        res = {"run_dir": os.path.relpath(run_dir, ROOT), "describe": describe(run_dir, tasks), "gates": {}}
        for cand in (PRIMARY, "transcribe+spark-1.2@low", DIRECT13):
            text, g = gate(run_dir, cand)
            res["gates"][cand] = {"decision": g["decision"], "reasons": g.get("reasons", []), "stdout": text}
            print("\n[%s] %s -> %s: %s" % (s, BASE, cand, g["decision"].upper()))
            print(text)
        summary[s] = res
    out = os.path.join(ROOT, "experiments", "out", "e9_route.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("\nwrote", os.path.relpath(out, ROOT))
    print(json.dumps({s: v["describe"] for s, v in summary.items()}, indent=1))


if __name__ == "__main__":
    main()
