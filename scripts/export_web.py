"""Export saved runs into web/public/data/site.json (+ the example audio clips) for the web app.

Reads only saved files under results/ and the experiment code's own analysis, so the site shows
the same numbers as experiments/out/*.md. Makes no API calls.

    PYTHONPATH=. python3 scripts/export_web.py
"""
from __future__ import annotations

import collections
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from common import compare, majority, pairs, tasks_by_id  # noqa: E402
from upgrade_gate import spend  # noqa: E402
from upgrade_gate.schema import read_jsonl  # noqa: E402

RESULTS = os.path.join(ROOT, "results")
OUT_DIR = os.path.join(ROOT, "web", "public")
A, B = "spark-1.2@low", "spark-1.3@low"


def _load(run: str, name: str):
    path = os.path.join(RESULTS, run, name)
    return list(read_jsonl(path)) if os.path.exists(path) else []


def _json(run: str, name: str):
    path = os.path.join(RESULTS, run, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _run_cost(run: str) -> dict:
    rows = _load(run, "responses.jsonl")
    fresh = sum(r.get("cost_usd") or 0.0 for r in rows if not r.get("cached"))
    return {"calls": len(rows), "fresh_cost_usd": round(fresh, 4),
            "reused_answers": sum(1 for r in rows if r.get("cached"))}


def _slim(c: dict) -> dict:
    keep = ("slice", "n", "delta", "ci", "regressions", "improvements", "p")
    return {k: c[k] for k in keep if k in c}


def _per_answer(run: str, field: str = "passed") -> dict:
    out = collections.defaultdict(lambda: {"correct": 0, "total": 0})
    for s in _load(run, "scores.jsonl"):
        if s.get(field) is None:
            continue
        out[s["candidate"]]["total"] += 1
        out[s["candidate"]]["correct"] += bool(s[field])
    return dict(out)


# ------------------------------------------------------------------ E1

def e1() -> dict:
    run = "e1-upgrade"
    if not os.path.exists(os.path.join(RESULTS, run, "scores.jsonl")):
        return {}
    d = os.path.join(RESULTS, run)
    tasks = tasks_by_id(d)
    after = majority(os.path.join(d, "scores.jsonl"))
    strict = majority(os.path.join(d, "scores.jsonl"), "strict_passed")
    old_path = os.path.join(d, "scores.before-rescore.jsonl")
    before = majority(old_path) if os.path.exists(old_path) else {}
    out = {
        "run": run, "baseline": A, "candidate": B, **_run_cost(run),
        "decision": (_json(run, "gate.json") or {}).get("decision"),
        "before": _slim(compare(pairs(before, tasks, A, B), "overall")) if before else None,
        "after": _slim(compare(pairs(after, tasks, A, B), "overall")),
        "strict": _slim(compare(pairs(strict, tasks, A, B), "overall")),
        "per_answer": _per_answer(run), "per_answer_strict": _per_answer(run, "strict_passed"),
        "slices": [],
        "examples": [],
    }
    for key in ("lang", "category", "modality"):
        for val in sorted({t[key] for t in tasks.values()}):
            ids = [i for i, t in tasks.items() if t[key] == val]
            row = {"key": key, "value": val, "n": len(ids)}
            for name, maj in (("before", before), ("after", after)):
                if maj:
                    row[name] = _slim(compare(pairs(maj, ids, A, B), "%s=%s" % (key, val)))
            out["slices"].append(row)
    # answers that the old scorer failed and the content scorer passes: the "invented improvement"
    if os.path.exists(old_path):
        old = {(s["task_id"], s["candidate"], s["repeat"]): s for s in read_jsonl(old_path)}
        resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in _load(run, "responses.jsonl")}
        seen = set()
        for s in _load(run, "scores.jsonl"):
            k = (s["task_id"], s["candidate"], s["repeat"])
            o = old.get(k)
            if not o or o["passed"] is not False or s["passed"] is not True:
                continue
            t = tasks[s["task_id"]]
            text = (resp[k].get("text") or "").strip()
            sig = (t["lang"], o["detail"][:24])
            if sig in seen or len(text) > 140:
                continue
            seen.add(sig)
            out["examples"].append({
                "task_id": s["task_id"], "candidate": s["candidate"], "lang": t["lang"], "category": t["category"],
                "prompt": t["prompt"], "answer": text, "accepted": _accepted(t),
                "old": o["detail"], "new": s["detail"] or "exact match", "strict": s.get("strict_passed")})
            if len(out["examples"]) >= 6:
                break
    return out


def _accepted(t: dict):
    sc = t.get("scorer") or {}
    if sc.get("type") == "one_of":
        return sc.get("values")
    if sc.get("type") == "number":
        return [sc.get("value")]
    if sc.get("type") == "json_fields":
        return {k: v for k, v in (sc.get("fields") or {}).items()}
    return sc.get("value")


# ------------------------------------------------------------------ E6 audio

def e6() -> dict:
    run = "e6-audio"
    d = os.path.join(RESULTS, run)
    if not os.path.exists(os.path.join(d, "scores.jsonl")):
        return {}
    import e6_audio as ex  # experiments/e6_audio.py: same rules as the logged result
    tasks = tasks_by_id(d)
    counts, deny_ans, tests = ex.failure_modes(d, tasks)
    gate = _json(run, "gate.json") or {}
    need = None
    for r in gate.get("reasons") or []:
        m = re.search(r"Approximately (\d+) more", r)
        if m:
            need = int(m.group(1))
    acc = collections.defaultdict(lambda: {"correct": 0, "total": 0})
    for s in _load(run, "scores.jsonl"):
        t = tasks[s["task_id"]]
        if s["passed"] is None and not t:
            continue
        a = acc["%s|%s" % (s["candidate"], t["modality"])]
        a["total"] += 1
        a["correct"] += s["passed"] is True
    out = {
        "run": run, "baseline": A, "candidate": B, **_run_cost(run),
        "decision": gate.get("accuracy_decision", gate.get("decision")),
        "gate_decision": gate.get("decision"), "behaviour": gate.get("behaviour"),
        "gate_reason": next((r for r in gate.get("reasons") or [] if r.startswith("CI ")), ""),
        "tasks_needed": need, "accuracy": dict(acc),
        "modes": ex.MODES,
        "mode_counts": {"%s|%s|%s" % k: v for k, v in counts.items()},
        "deny_with_answer": dict(deny_ans),
        "tests": tests,
        "examples": _audio_examples(d, tasks, ex),
        "clips": _clip_outcomes(d, tasks, ex),
    }
    return out


def _clip_outcomes(d: str, tasks: dict, ex) -> list:
    """One row per audio clip and version, using the same majority rule as the paired tests:
    wrong-or-blank in 2 of 3 tries -> that failure; otherwise correct / can't hear / no answer
    if 2 of 3; otherwise "mixed". So the grid's counts match the published test counts."""
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in read_jsonl(os.path.join(d, "responses.jsonl"))}
    modes = collections.defaultdict(list)
    for s in read_jsonl(os.path.join(d, "scores.jsonl")):
        t = tasks[s["task_id"]]
        if t["modality"] != "audio":
            continue
        r = resp[(s["task_id"], s["candidate"], s["repeat"])]
        modes[(s["task_id"], s["candidate"])].append(ex._mode(t, r, s["passed"] is True))

    def outcome(ms):
        c = collections.Counter(ms)
        half = len(ms) / 2
        if c["confident wrong"] + c["silent blank"] > half:
            return "silent blank" if c["silent blank"] > c["confident wrong"] else "confident wrong"
        for m in ("correct", "says it can't hear", "no answer (token limit)"):
            if c[m] > half:
                return m
        return "mixed"

    out = []
    for tid, t in sorted(tasks.items(), key=lambda kv: (kv[1]["lang"], kv[1]["meta"]["kind"], kv[0])):
        if t["modality"] != "audio" or not modes.get((tid, A)) or not modes.get((tid, B)):
            continue
        out.append({"id": tid, "lang": t["lang"], "kind": t["meta"]["kind"],
                    A: outcome(modes[(tid, A)]), B: outcome(modes[(tid, B)])})
    return out


def _audio_examples(d: str, tasks: dict, ex) -> list:
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in read_jsonl(os.path.join(d, "responses.jsonl"))}
    scores = {(s["task_id"], s["candidate"], s["repeat"]): s for s in read_jsonl(os.path.join(d, "scores.jsonl"))}
    by_task = collections.defaultdict(lambda: collections.defaultdict(list))
    for (tid, cand, rep), s in sorted(scores.items()):
        t = tasks[tid]
        if t["modality"] != "audio":
            continue
        r = resp[(tid, cand, rep)]
        by_task[tid][cand].append({"text": (r.get("text") or r.get("error") or "").strip()[:420],
                                   "mode": ex._mode(t, r, s["passed"] is True),
                                   "says_cant_hear": bool(ex.DENY.search(r.get("text") or ""))})

    def worst(answers):
        return collections.Counter(a["mode"] for a in answers).most_common(1)[0][0]

    picks, used = [], collections.Counter()
    # 1) 1.2 right, 1.3 fails without warning (the headline pattern), spread over kind x language
    order = sorted(by_task, key=lambda i: (tasks[i]["lang"] != "hi", i))
    for tid in order:
        a, b = by_task[tid][A], by_task[tid][B]
        t = tasks[tid]
        key = (t["meta"]["kind"], t["lang"])
        if worst(a) == "correct" and worst(b) in ("confident wrong", "silent blank") and used[key] < 1:
            used[key] += 1
            picks.append((tid, "silent"))
    # 2) 1.2 says it can't hear, then answers from the words it heard
    n = 0
    for tid in order:
        if n >= 2:
            break
        if any(x["says_cant_hear"] and x["mode"] == "correct" for x in by_task[tid][A]) and tid not in dict(picks):
            picks.append((tid, "denies-but-hears"))
            n += 1
    out = []
    for tid, why in picks:
        t = tasks[tid]
        wav = t["attachments"][0]
        out.append({"task_id": tid, "why": why, "kind": t["meta"]["kind"], "lang": t["lang"],
                    "voice": t["meta"]["voice"], "transcript": t["meta"]["transcript"], "prompt": t["prompt"],
                    "expected": t["reference"], "audio": _attachment(wav, True),
                    "answers": {A: by_task[tid][A], B: by_task[tid][B]}})
    return out


# ------------------------------------------------------------------ E3 contributor

def e3() -> dict:
    run = "e3-contributor"
    d = os.path.join(RESULTS, run)
    out_json = os.path.join(ROOT, "experiments", "out", "e3_contributor.json")
    if not os.path.exists(os.path.join(d, "scores.jsonl")):
        return {"status": "running" if os.path.exists(os.path.join(d, "responses.jsonl")) else "not run"}
    std, con = "spark-1.3@low", "spark-1.3-c@low"
    tasks = tasks_by_id(d)
    maj = majority(os.path.join(d, "scores.jsonl"))
    rows = _load(run, "responses.jsonl")
    cost = collections.defaultdict(lambda: [0.0, 0])
    for r in rows:
        c = cost[r["candidate"]]
        c[0] += r.get("cost_usd") or 0.0
        c[1] += 1
    res = {"status": "done", "run": run, "standard": std, "contributor": con, **_run_cost(run),
           "decision": (_json(run, "gate.json") or {}).get("decision"),
           "overall": _slim(compare(pairs(maj, tasks, std, con), "overall")),
           "per_answer": _per_answer(run),
           "cost_per_1000": {k: round(v[0] / v[1] * 1000, 4) for k, v in cost.items() if v[1]},
           "slices": []}
    for key in ("lang", "category", "modality"):
        for val in sorted({t[key] for t in tasks.values()}):
            ids = [i for i, t in tasks.items() if t[key] == val]
            res["slices"].append({"key": key, "value": val,
                                  **_slim(compare(pairs(maj, ids, std, con), "%s=%s" % (key, val)))})
    if os.path.exists(out_json):
        with open(out_json, encoding="utf-8") as f:
            res["equivalence"] = {k: v for k, v in json.load(f).items() if k not in ("run_dir", "rows")}
    return res


# ------------------------------------------------------------------ E4 effort ladder on voice clips

def e4() -> dict:
    run = "e4-effort"
    d = os.path.join(RESULTS, run)
    if not os.path.exists(os.path.join(d, "scores.jsonl")):
        return {"status": "not run"}
    import e6_audio as ex
    tasks = tasks_by_id(d)
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in _load(run, "responses.jsonl")}
    levels = ["minimal", "low", "medium", "high", "xhigh"]
    cand = {l: "spark-1.3-c@%s/16000" % l for l in levels}
    stats = {l: {"answers": 0, "correct": 0, "modes": collections.Counter(), "cost": 0.0, "out_tokens": 0}
             for l in levels}
    lvl = {v: k for k, v in cand.items()}
    for s in _load(run, "scores.jsonl"):
        l = lvl.get(s["candidate"])
        if not l:
            continue
        r = resp.get((s["task_id"], s["candidate"], s["repeat"]), {})
        st = stats[l]
        st["answers"] += 1
        st["correct"] += s["passed"] is True
        st["modes"][ex._mode(tasks[s["task_id"]], r, s["passed"] is True)] += 1
        st["cost"] += r.get("cost_usd") or 0.0
        st["out_tokens"] += (r.get("usage") or {}).get("output_tokens", 0)
    maj = majority(os.path.join(d, "scores.jsonl"))
    end = _slim(compare(pairs(maj, tasks, cand["minimal"], cand["xhigh"]), "minimal->xhigh"))
    return {"status": "done", "model": "spark-1.3 Contributor", "clips": len(tasks), **_run_cost(run),
            "levels": [{"level": l, "answers": stats[l]["answers"], "correct": stats[l]["correct"],
                        "modes": dict(stats[l]["modes"]),
                        "cost_per_1000": round(stats[l]["cost"] / max(1, stats[l]["answers"]) * 1000, 4),
                        "avg_output_tokens": stats[l]["out_tokens"] // max(1, stats[l]["answers"])} for l in levels],
            "minimal_vs_xhigh": end}


# ------------------------------------------------------------------ E7 real voices

def e7() -> dict:
    run = "e7-real-voices"
    d = os.path.join(RESULTS, run)
    out_json = os.path.join(ROOT, "experiments", "out", "e7_real_voices.json")
    if not os.path.exists(os.path.join(d, "scores.jsonl")) or not os.path.exists(out_json):
        return {"status": "not run"}
    import e6_audio as ex
    with open(out_json, encoding="utf-8") as f:
        res = json.load(f)
    counts, _, tests = ex.failure_modes(d, tasks_by_id(d))
    gate = _json(run, "gate.json") or {}
    main = next(t for t in tests if t["flag"] == "confident wrong or blank" and t["lang"] == "all")
    overall = next((r for r in res["rows"] if r["slice"] == "overall"), None)
    return {"status": "done", "speakers": res.get("speakers"), "clips": main["tasks"], **_run_cost(run),
            "confirmed": res.get("confirmed"), "silent": {"baseline": main[A], "candidate": main[B], "p": main["p"]},
            "blank_answers": {c: counts[(c, "all", "silent blank")] for c in (A, B)},
            "accuracy": _slim(overall) if overall else None,
            "decision": gate.get("decision"), "accuracy_decision": gate.get("accuracy_decision", gate.get("decision"))}


# ------------------------------------------------------------------ report view: one file per run

RUNS = [
    ("e6-audio", "Voice notes", "Spoken English, Hindi and Hinglish clips, each with a text twin"),
    ("e1-upgrade", "Text, documents, Hindi", "Maths, extraction, intent, instructions, invoice images and PDFs"),
    ("e3-contributor", "Contributor mode", "Same model, cheaper serving mode"),
    ("e7-real-voices", "Real voices", "The voice-note lines read aloud by a person (45 clips, English, Hindi, Hinglish)"),
]
# Runs whose audio is a real person's voice: results are published, the recordings are not
# (the repo becomes public). Pass --publish-real-voice to include them.
PRIVATE_AUDIO = {"e7-real-voices"}


def _attachment(path: str, keep: bool):
    """Copy an attachment the report can show. Audio becomes small AAC (browser-playable);
    images/PDFs are copied only for tasks worth opening, to keep the site light."""
    if not path:
        return None
    src = os.path.join(ROOT, path)
    if not os.path.exists(src):
        return None
    att = os.path.join(OUT_DIR, "att")
    os.makedirs(att, exist_ok=True)
    name, ext = os.path.splitext(os.path.basename(path))
    if ext.lower() in (".wav", ".mp3"):
        dst = os.path.join(att, name + ".m4a")
        if not os.path.exists(dst):
            import subprocess
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "48000", src, dst],
                           check=True, capture_output=True)
        return "att/" + name + ".m4a"
    if not keep:
        return None
    dst = os.path.join(att, os.path.basename(path))
    if not os.path.exists(dst):
        shutil.copyfile(src, dst)
    return "att/" + os.path.basename(path)


def _display(v) -> str:
    if isinstance(v, dict):
        return " · ".join("%s: %s" % (k, x[0] if isinstance(x, list) else x) for k, x in v.items())
    if isinstance(v, list):
        return " / ".join(str(x) for x in v)
    return str(v)


def run_detail(run: str, title: str, blurb: str):
    d = os.path.join(RESULTS, run)
    gate = _json(run, "gate.json")
    if not gate or not os.path.exists(os.path.join(d, "scores.jsonl")):
        return None
    import e6_audio as ex
    base, cand = gate["baseline"], gate["candidate"]
    tasks = tasks_by_id(d)
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r for r in _load(run, "responses.jsonl")}
    per = collections.defaultdict(list)
    for s in _load(run, "scores.jsonl"):
        if s["candidate"] not in (base, cand):
            continue
        t = tasks.get(s["task_id"])
        r = resp.get((s["task_id"], s["candidate"], s["repeat"]), {})
        if t and t["modality"] == "audio":
            mode = ex._mode(t, r, s["passed"] is True)
        elif r.get("error"):
            mode = "no answer (token limit)" if "max_completion_tokens" in (r.get("error") or "") else "error"
        else:
            mode = "correct" if s["passed"] else "confident wrong"
        per[(s["task_id"], s["candidate"])].append({
            "repeat": s["repeat"], "passed": s["passed"], "strict": s.get("strict_passed"),
            "detail": (s.get("detail") or "")[:160], "mode": mode,
            "text": ((r.get("text") or r.get("error") or "").strip())[:600],
        })

    def side(tid, c):
        ans = sorted(per.get((tid, c), []), key=lambda a: a["repeat"])
        votes = [a["passed"] for a in ans if a["passed"] is not None]
        maj = (sum(votes) * 2 > len(votes)) if votes else None
        modes = collections.Counter(a["mode"] for a in ans)
        return {"pass": maj, "mode": modes.most_common(1)[0][0] if modes else None, "answers": ans}

    rows = []
    for tid, t in tasks.items():
        b, c = side(tid, base), side(tid, cand)
        if b["pass"] is None and c["pass"] is None:
            continue
        status = ("regression" if b["pass"] and not c["pass"] else "improvement" if c["pass"] and not b["pass"]
                  else "both pass" if b["pass"] else "both fail")
        interesting = status != "both pass" or b["mode"] != c["mode"]
        att = (t.get("attachments") or [None])[0]
        if run in PRIVATE_AUDIO and "--publish-real-voice" not in sys.argv:
            att = None
        rows.append({
            "id": tid, "category": t["category"], "lang": t["lang"], "modality": t["modality"],
            "prompt": t["prompt"][:900], "transcript": (t.get("meta") or {}).get("transcript"),
            "expected": _display(_accepted(t) if _accepted(t) is not None else t.get("reference")),
            "attachment": _attachment(att, interesting), "status": status, "base": b, "cand": c,
        })
    order = {"regression": 0, "improvement": 1, "both fail": 2, "both pass": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["id"]))
    info = _json(run, "run.json") or {}
    meta = {"run": run, "title": title, "blurb": blurb, "baseline": base, "candidate": cand,
            "decision": gate["decision"], "reasons": gate.get("reasons") or [], "created_utc": info.get("created_utc"),
            "overall": gate.get("overall"), "slices": gate.get("slices") or [], **_run_cost(run),
            "accuracy_decision": gate.get("accuracy_decision", gate["decision"]), "behaviour": gate.get("behaviour"),
            "counts": dict(collections.Counter(r["status"] for r in rows))}
    path = os.path.join(OUT_DIR, "data", "runs", run + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "tasks": rows}, f, ensure_ascii=False, separators=(",", ":"), default=float)
    print("wrote", os.path.relpath(path, ROOT), "(%d KB, %d tasks)" % (os.path.getsize(path) // 1024, len(rows)))
    return {k: meta[k] for k in ("run", "title", "blurb", "baseline", "candidate", "decision", "calls",
                                 "fresh_cost_usd", "created_utc", "counts")}


def main() -> None:
    os.makedirs(os.path.join(OUT_DIR, "data"), exist_ok=True)
    index = [x for x in (run_detail(*r) for r in RUNS) if x]
    with open(os.path.join(OUT_DIR, "data", "runs.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    s = spend.status()
    site = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spend": {"total_usd": round(s["local_spent_usd"] + s["canary_spent_usd"], 2), "limit_usd": s["limit_usd"]},
        "e1": e1(), "e6": e6(), "e3": e3(), "e7": e7(), "e4": e4(),
    }
    path = os.path.join(OUT_DIR, "data", "site.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(site, f, ensure_ascii=False, indent=1, default=float)
    print("wrote", os.path.relpath(path, ROOT), "(%d KB)" % (os.path.getsize(path) // 1024))
    print("audio examples:", len(site["e6"].get("examples", [])), "| e1 examples:", len(site["e1"].get("examples", [])),
          "| e3:", site["e3"].get("status"))


if __name__ == "__main__":
    main()
