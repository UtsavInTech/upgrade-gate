"""Score a run directory: responses.jsonl + tasks.jsonl -> scores.jsonl (ScoreRecord dicts).

Modes:
  deterministic  passed from the task's deterministic scorer.
  judge          passed from the first judge in `judges` (a Judge or a Cascade); every
                 other judge still votes and is recorded.
  both           passed stays deterministic (ground truth); every judge votes on every
                 response and all votes go in judge_votes. This is the H1 setup.

judge_agreement(scores_path) compares judge votes with deterministic truth, overall and
split by the candidate that produced the answer (the version-preference signal).
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, fields
from typing import Any, Dict, List, Optional, Sequence

from upgrade_gate.schema import ScoreRecord, Task, read_jsonl, write_jsonl
from upgrade_gate.scorers import has_scorer, score_text

MODES = ("deterministic", "judge", "both")
_TASK_FIELDS = {f.name for f in fields(Task)}


def _load_tasks(run_dir: str) -> Dict[str, Task]:
    out = {}
    for d in read_jsonl(os.path.join(run_dir, "tasks.jsonl")):
        out[d["id"]] = Task(**{k: v for k, v in d.items() if k in _TASK_FIELDS})
    return out


def _run_id(run_dir: str) -> str:
    p = os.path.join(run_dir, "run.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            rid = json.load(f).get("run_id")
            if rid:
                return rid
    return os.path.basename(os.path.normpath(run_dir))


def _safe_vote(judge: Any, task: Task, text: str) -> Dict[str, Any]:
    try:
        v = judge.vote(task, text)
    except Exception as e:  # a crashing judge must not kill the whole run
        v = {"judge": getattr(judge, "name", "judge"), "passed": None, "confidence": 0.0,
             "rationale": "judge error: %s: %s" % (type(e).__name__, e), "cost_usd": 0.0}
    return v


def _flatten(vote: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Cascade votes -> underlying votes + the cascade's final vote (marked final=True)."""
    inner = vote.get("votes")
    if not inner:
        return [vote]
    top = {k: v for k, v in vote.items() if k != "votes"}
    top["final"] = True
    top["cost_usd"] = 0.0  # cost already counted in the inner votes
    return [dict(v) for v in inner] + [top]


def _method_for(judge: Any) -> str:
    name = getattr(judge, "name", "judge")
    return name if name.startswith("cascade:") else "judge:%s" % name


def score_run(run_dir: str, judges: Optional[Sequence[Any]] = None, mode: str = "deterministic",
              workers: int = 16, out_name: str = "scores.jsonl") -> str:
    if mode not in MODES:
        raise ValueError("mode must be one of %s" % (MODES,))
    judges = list(judges or [])
    if mode in ("judge", "both") and not judges:
        raise ValueError("mode %r needs at least one judge" % mode)
    tasks = _load_tasks(run_dir)
    responses = list(read_jsonl(os.path.join(run_dir, "responses.jsonl")))
    run_id = _run_id(run_dir)

    # deterministic pass
    det: List[Optional[tuple]] = []
    for r in responses:
        t = tasks.get(r["task_id"])
        if t is None or r.get("text") is None or not has_scorer(t):
            det.append(None)
        else:
            det.append(score_text(t, r["text"]))

    # judge pass (threaded): votes[i][j] = vote of judge j on response i
    votes: List[List[Optional[Dict[str, Any]]]] = [[None] * len(judges) for _ in responses]
    if mode in ("judge", "both"):
        jobs = [(i, j) for i, r in enumerate(responses)
                if r.get("text") is not None and r["task_id"] in tasks
                for j in range(len(judges))]

        def work(ij):
            i, j = ij
            return i, j, _safe_vote(judges[j], tasks[responses[i]["task_id"]], responses[i]["text"])

        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            for i, j, v in ex.map(work, jobs):
                votes[i][j] = v

    records = []
    for i, r in enumerate(responses):
        base = dict(run_id=r.get("run_id") or run_id, task_id=r["task_id"],
                    candidate=r["candidate"], repeat=int(r.get("repeat", 0)))
        method = "deterministic" if mode != "judge" else _method_for(judges[0])
        if r.get("text") is None:
            records.append(ScoreRecord(passed=None, score=None, method=method,
                                       detail="api error" + (": %s" % r["error"] if r.get("error") else ""),
                                       **base))
            continue
        if r["task_id"] not in tasks:
            records.append(ScoreRecord(passed=None, score=None, method=method, detail="unknown task", **base))
            continue
        flat: List[Dict[str, Any]] = []
        for v in votes[i]:
            if v is not None:
                flat.extend(_flatten(v))
        cost = sum(float(v.get("cost_usd") or 0.0) for v in flat)
        d = det[i]
        if mode == "judge":
            primary = votes[i][0] or {}
            p = primary.get("passed")
            detail = "judge: %s" % str(primary.get("rationale", ""))[:200]
            if d is not None:
                detail += " | det=%s" % ("pass" if d[0] else "fail")
            records.append(ScoreRecord(passed=p, score=None if p is None else float(p), method=method,
                                       detail=detail, judge_votes=flat, cost_usd=cost, **base))
        else:
            if d is None:
                records.append(ScoreRecord(passed=None, score=None, method="deterministic",
                                           detail="no scorer", judge_votes=flat, cost_usd=cost, **base))
            else:
                records.append(ScoreRecord(passed=d[0], score=d[1], method="deterministic",
                                           detail=d[2], judge_votes=flat, cost_usd=cost, **base))

    path = os.path.join(run_dir, out_name)
    write_jsonl(path, [asdict(x) for x in records])
    return path


# ---------------------------------------------------------------- judge vs truth

def _rates(c: Dict[str, int]) -> Dict[str, Any]:
    n = c["tp"] + c["tn"] + c["fp"] + c["fn"]
    neg = c["tn"] + c["fp"]   # truth = fail
    pos = c["tp"] + c["fn"]   # truth = pass

    def div(a, b):
        return (a / b) if b else None

    judge_rate = div(c["tp"] + c["fp"], n)
    truth_rate = div(pos, n)
    return dict(c, n=n,
                accuracy=div(c["tp"] + c["tn"], n),
                false_pass_rate=div(c["fp"], neg),   # judge says correct, truth says wrong
                false_fail_rate=div(c["fn"], pos),   # judge says wrong, truth says correct
                judge_pass_rate=judge_rate, truth_pass_rate=truth_rate,
                inflation=None if judge_rate is None else judge_rate - truth_rate)


def _zero() -> Dict[str, int]:
    return {"tp": 0, "tn": 0, "fp": 0, "fn": 0, "unparsed": 0}


def judge_agreement(scores_path: str) -> Dict[str, Any]:
    """Per judge: accuracy vs deterministic truth, false-pass / false-fail rates, and the same
    split by candidate. `inflation` = judge pass rate - true pass rate; `preference` is the
    spread of inflation across candidates (max - min), the H1 version-preference signal."""
    counts: Dict[str, Dict[str, int]] = {}
    by_cand: Dict[str, Dict[str, Dict[str, int]]] = {}
    n_truth = 0
    for rec in read_jsonl(scores_path):
        if rec.get("method") != "deterministic" or rec.get("passed") is None:
            continue
        n_truth += 1
        truth = bool(rec["passed"])
        cand = rec.get("candidate", "?")
        for v in rec.get("judge_votes") or []:
            name = v.get("judge", "?")
            c = counts.setdefault(name, _zero())
            cc = by_cand.setdefault(name, {}).setdefault(cand, _zero())
            p = v.get("passed")
            if p is None:
                key = "unparsed"
            elif p and truth:
                key = "tp"
            elif p and not truth:
                key = "fp"
            elif not p and truth:
                key = "fn"
            else:
                key = "tn"
            c[key] += 1
            cc[key] += 1
    judges_out = {}
    for name, c in counts.items():
        r = _rates(c)
        r["by_candidate"] = {cand: _rates(cc) for cand, cc in sorted(by_cand[name].items())}
        infl = {k: x["inflation"] for k, x in r["by_candidate"].items() if x["inflation"] is not None}
        r["preference"] = (max(infl.values()) - min(infl.values())) if len(infl) >= 2 else None
        r["favoured"] = max(infl, key=lambda k: infl[k]) if len(infl) >= 2 and r["preference"] else None
        judges_out[name] = r
    return {"scores_path": scores_path, "n_truth_records": n_truth, "judges": judges_out}
