"""Replay tasks through candidate model configs and record raw responses.

Writes results/<run_id>/run.json (RunInfo), tasks.jsonl (Task dicts) and
responses.jsonl (ResponseRecord, appended as calls complete).
"""
from __future__ import annotations

import json
import os
import random
import secrets
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from . import pricing
from .client import ChatResult, ModelClient, build_messages
from .schema import ResponseRecord, RunInfo, read_jsonl, write_jsonl
from .spend import SpendCapError

IMAGE_TOKENS = 1000      # rough per-image input estimate
PDF_TOKENS = 3000        # rough per-PDF input estimate


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _as_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return dict(obj)
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError("expected dict or dataclass, got %r" % type(obj))


def _norm_candidate(c: Any) -> Dict[str, Any]:
    d = _as_dict(c)
    d.setdefault("params", {})
    d["params"] = dict(d["params"] or {})
    return {"name": d["name"], "model_id": d["model_id"], "params": d["params"]}


def _input_tokens_estimate(task: Dict[str, Any]) -> int:
    n = len(task.get("prompt") or "") // 4 + 8
    for a in task.get("attachments") or []:
        n += PDF_TOKENS if str(a).lower().endswith(".pdf") else IMAGE_TOKENS
    return n


def estimate_cost(tasks: Sequence[Any], candidates: Sequence[Any], repeats: int = 3,
                  avg_output_tokens: int = 300) -> dict:
    """Rough pre-run estimate: input = chars/4 (+1000 per image, +3000 per PDF),
    output = avg_output_tokens per call (reasoning included). Cache discounts ignored."""
    tds = [_as_dict(t) for t in tasks]
    cands = [_norm_candidate(c) for c in candidates]
    in_tok = sum(_input_tokens_estimate(t) for t in tds)
    per_cand: Dict[str, float] = {}
    unknown: List[str] = []
    for c in cands:
        usage = {"input_tokens": in_tok * repeats, "output_tokens": avg_output_tokens * len(tds) * repeats}
        per_cand[c["name"]] = round(pricing.cost(c["model_id"], usage), 6)
        if not pricing.is_known(c["model_id"]):
            unknown.append(c["model_id"])
    return {
        "n_tasks": len(tds),
        "n_candidates": len(cands),
        "repeats": repeats,
        "n_calls": len(tds) * len(cands) * repeats,
        "input_tokens_per_pass": in_tok,
        "avg_output_tokens": avg_output_tokens,
        "per_candidate_usd": per_cand,
        "total_usd": round(sum(per_cand.values()), 6),
        "unknown_price_models": unknown,
    }


def _new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)


def _load_done(path: str, retry_errors: bool) -> Set[Tuple[str, str, int]]:
    """Keys already recorded. With retry_errors, error rows are dropped from the file
    (rewritten) so they get re-run and each key appears once."""
    if not os.path.exists(path):
        return set()
    rows = list(read_jsonl(path))
    if retry_errors:
        kept = [r for r in rows if not r.get("error")]
        if len(kept) != len(rows):
            write_jsonl(path, kept)
        rows = kept
    return {(r["task_id"], r["candidate"], int(r["repeat"])) for r in rows}


def run(tasks, candidates, baseline, repeats=3, out_root="results", run_id=None, budget_usd=None,
        workers=16, client=None, notes="", seed=None, retry_errors=True, verbose=True) -> str:
    """Run every (task, candidate, repeat) once and return the run directory.

    Repeats use cache_salt=f"rep{repeat}" so they are independent API calls, while
    re-running the same run hits the cache. If the run dir already exists, keys already in
    responses.jsonl are skipped (resume). Stops scheduling once spent cost > budget_usd.
    """
    tds = [_as_dict(t) for t in tasks]
    cands = [_norm_candidate(c) for c in candidates]
    names = [c["name"] for c in cands]
    if len(set(names)) != len(names):
        raise ValueError("candidate names must be unique: %r" % names)
    if baseline not in names:
        raise ValueError("baseline %r is not one of the candidates %r" % (baseline, names))
    ids = [t["id"] for t in tds]
    if len(set(ids)) != len(ids):
        raise ValueError("task ids must be unique")

    run_id = run_id or _new_run_id()
    run_dir = os.path.join(out_root, run_id)
    os.makedirs(run_dir, exist_ok=True)
    run_json = os.path.join(run_dir, "run.json")
    resp_path = os.path.join(run_dir, "responses.jsonl")

    created = _now()
    resumed = os.path.exists(resp_path)
    if os.path.exists(run_json):
        try:
            with open(run_json, encoding="utf-8") as f:
                prev = json.load(f)
            created = prev.get("created_utc") or created
        except (OSError, ValueError):
            pass

    if seed is None:
        seed = random.SystemRandom().randrange(2 ** 31)

    write_jsonl(os.path.join(run_dir, "tasks.jsonl"), tds)
    done = _load_done(resp_path, retry_errors)

    note_parts = [notes] if notes else []
    note_parts.append("shuffle_seed=%d" % seed)

    def write_info(extra: List[str]) -> None:
        info = RunInfo(run_id=run_id, created_utc=created, candidates=cands, baseline=baseline,
                       packs=sorted({t.get("pack", "") for t in tds}), n_tasks=len(tds), repeats=repeats,
                       budget_usd=budget_usd, notes="; ".join(note_parts + extra))
        tmp = run_json + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(asdict(info), f, ensure_ascii=False, indent=2)
        os.replace(tmp, run_json)

    write_info(["resumed"] if resumed else [])

    jobs = [(t, c, r) for r in range(repeats) for t in tds for c in cands
            if (t["id"], c["name"], r) not in done]
    random.Random(seed).shuffle(jobs)

    client = client or ModelClient(max_concurrency=workers)
    lock = threading.Lock()
    state = {"done": 0, "spent": 0.0, "cost": 0.0, "errors": 0, "cached": 0, "next_pct": 5}
    total = len(jobs)
    t_start = time.monotonic()

    def do(job) -> None:
        task, cand, rep = job
        try:
            msgs = build_messages(task)
            res = client.chat(cand["model_id"], msgs, params=cand["params"], cache_salt="rep%d" % rep)
        except SpendCapError as e:  # not recorded, so a resume after raising the cap redoes it
            with lock:
                if not state.get("cap"):
                    state["cap"] = str(e)
                    print("[%s] %s" % (run_id, e), flush=True)
            return
        except Exception as e:  # bad attachment etc. -> record, never crash the run
            res = ChatResult(text=None, usage={"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0,
                                               "cached_tokens": 0},
                             cost_usd=0.0, latency_ms=0, error="%s: %s" % (type(e).__name__, e),
                             returned_model=None, cached=False)
        rec = ResponseRecord(run_id=run_id, task_id=task["id"], candidate=cand["name"], repeat=rep,
                             text=res.text, usage=dict(res.usage), cost_usd=res.cost_usd,
                             latency_ms=res.latency_ms, error=res.error, ts_utc=_now(),
                             returned_model=res.returned_model, cached=res.cached)
        line = json.dumps(asdict(rec), ensure_ascii=False) + "\n"
        with lock:
            with open(resp_path, "a", encoding="utf-8") as f:
                f.write(line)
            state["done"] += 1
            state["cost"] += res.cost_usd
            if not res.cached:
                state["spent"] += res.cost_usd
            else:
                state["cached"] += 1
            if res.error:
                state["errors"] += 1
            pct = 100.0 * state["done"] / total if total else 100.0
            if verbose and (pct >= state["next_pct"] or state["done"] == total):
                while state["next_pct"] <= pct:
                    state["next_pct"] += 5
                print("[%s] %d/%d (%.0f%%) spent=$%.4f errors=%d cached=%d %.0fs" % (
                    run_id, state["done"], total, pct, state["spent"], state["errors"], state["cached"],
                    time.monotonic() - t_start), flush=True)

    budget_hit = False
    skipped = 0
    if verbose:
        print("[%s] %d jobs (%d already done) -> %s" % (run_id, total, len(done), run_dir), flush=True)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        inflight = set()
        it = iter(jobs)
        for i, job in enumerate(it):
            with lock:
                over = budget_usd is not None and state["spent"] > budget_usd
                capped = bool(state.get("cap"))
            if capped:
                skipped = total - i
                break
            if over:
                budget_hit = True
                skipped = total - i
                break
            inflight.add(pool.submit(do, job))
            if len(inflight) >= max(1, workers):
                finished, inflight = wait(inflight, return_when=FIRST_COMPLETED)
                for fut in finished:
                    fut.result()
        for fut in inflight:
            fut.result()

    extra = ["resumed"] if resumed else []
    if state.get("cap"):
        extra.append("stopped by lifetime spend cap (%d jobs not scheduled): %s" % (skipped, state["cap"]))
    if budget_hit:
        extra.append("budget stop: spent $%.4f > budget $%.4f; %d of %d jobs not scheduled"
                     % (state["spent"], budget_usd, skipped, total))
        if verbose:
            print("[%s] budget reached, stopped scheduling (%d jobs skipped)" % (run_id, skipped), flush=True)
    write_info(extra)
    return run_dir
