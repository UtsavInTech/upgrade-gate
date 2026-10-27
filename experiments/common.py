"""Shared helpers for the pre-registered experiments (see findings/LOG.md).

Stats here are small stdlib versions so experiments don't depend on the gate module.
The gate itself uses Codex's upgrade_gate/stats.py.
"""
from __future__ import annotations

import collections
import json
import math
import os
import random
import sys
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate.schema import read_jsonl  # noqa: E402

OUT = os.path.join(ROOT, "experiments", "out")


def majority(scores_path: str, field: str = "passed") -> Dict[Tuple[str, str], Optional[bool]]:
    """(task_id, candidate) -> majority pass over repeats. Ties = fail. None rows ignored.
    field="strict_passed" gives the strict-format score instead of the content score."""
    votes: Dict[Tuple[str, str], List[bool]] = collections.defaultdict(list)
    for r in read_jsonl(scores_path):
        if r.get(field) is not None:
            votes[(r["task_id"], r["candidate"])].append(bool(r[field]))
    return {k: (sum(v) * 2 > len(v)) for k, v in votes.items() if v}


def tasks_by_id(run_dir: str) -> Dict[str, dict]:
    return {t["id"]: t for t in read_jsonl(os.path.join(run_dir, "tasks.jsonl"))}


def pairs(maj, task_ids: Iterable[str], a: str, b: str) -> List[Tuple[str, bool, bool]]:
    out = []
    for t in task_ids:
        if (t, a) in maj and (t, b) in maj:
            out.append((t, maj[(t, a)], maj[(t, b)]))
    return out


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def delta(ps: List[Tuple[str, bool, bool]]) -> float:
    if not ps:
        return float("nan")
    return (sum(y for _, _, y in ps) - sum(x for _, x, _ in ps)) / len(ps)


def bootstrap(fn, items: list, n_boot: int = 5000, seed: int = 0) -> Tuple[float, float]:
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        sample = [items[rng.randrange(len(items))] for _ in items]
        v = fn(sample)
        if not math.isnan(v):
            vals.append(v)
    vals.sort()
    if not vals:
        return float("nan"), float("nan")
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def compare(ps, label: str) -> dict:
    b = sum(1 for _, x, y in ps if x and not y)
    c = sum(1 for _, x, y in ps if y and not x)
    lo, hi = bootstrap(delta, ps) if ps else (float("nan"), float("nan"))
    return {"slice": label, "n": len(ps), "delta": delta(ps), "ci": [lo, hi],
            "regressions": b, "improvements": c, "p": mcnemar_exact(b, c)}


def fmt_pts(x: float) -> str:
    return "—" if x != x else "%+.1f" % (100 * x)


def table(rows: List[dict]) -> str:
    out = ["| Slice | n | Δ pts | 95% CI | lost | gained | McNemar p |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| %s | %d | %s | %s to %s | %d | %d | %.3g |" % (
            r["slice"], r["n"], fmt_pts(r["delta"]), fmt_pts(r["ci"][0]), fmt_pts(r["ci"][1]),
            r["regressions"], r["improvements"], r["p"]))
    return "\n".join(out)


def write_result(name: str, text: str, data: dict) -> str:
    os.makedirs(OUT, exist_ok=True)
    md = os.path.join(OUT, name + ".md")
    with open(md, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(text)
    print("\nwrote", os.path.relpath(md, ROOT))
    return md


def run_and_score(packs: List[str], candidates: List[str], n: Optional[int], repeats: int,
                  budget: float, yes: bool, run_id: str, judges: Optional[List[str]] = None,
                  mode: str = "deterministic") -> str:
    """Estimate, then (only with yes=True) run and score. Returns run_dir."""
    from upgrade_gate.cli import load_tasks, make_judges, parse_candidate
    from upgrade_gate.runner import estimate_cost, run
    from upgrade_gate.scoring import score_run

    tasks = load_tasks(packs, n, seed=0)
    cands = [parse_candidate(c) for c in candidates]
    est = estimate_cost(tasks, cands, repeats)
    print("%s: %d tasks × %d candidates × %d repeats" % (run_id, len(tasks), len(cands), repeats))
    print("estimate:", json.dumps(est))
    if not yes:
        raise SystemExit("Dry run only. Add --yes to spend (budget cap $%.2f)." % budget)
    run_dir = run(tasks, cands, baseline=cands[0].name, repeats=repeats, run_id=run_id,
                  budget_usd=budget, notes="experiment " + run_id)
    js = make_judges(judges) if judges else None
    score_run(run_dir, judges=js, mode=mode)
    return run_dir


def base_args(desc: str):
    import argparse
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--yes", action="store_true", help="actually spend money")
    ap.add_argument("--budget", type=float, default=10.0, help="hard stop in USD")
    ap.add_argument("--n", type=int, default=None, help="max tasks per pack")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--run-dir", default=None, help="analyse an existing run instead of running")
    return ap
