"""Command line for Upgrade Gate.

  upgrade-gate check                         one tiny call per model to confirm the key works
  upgrade-gate estimate --packs ... -c ...   cost estimate, spends nothing
  upgrade-gate run --packs ... -b spark-1.2 -c spark-1.3 [--n 50] [--repeats 3] [--budget 20] --yes
  upgrade-gate score RUN_DIR [--mode deterministic|judge|both] [--judges spark-1.2,spark-1.3,wonder]
  upgrade-gate gate RUN_DIR                  go / no-go (writes gate.json)
  upgrade-gate report RUN_DIR                report.md + report.html
  upgrade-gate export RUN_DIR                promptfoo.yaml + pytest regressions
  upgrade-gate all ... --yes                 run -> score -> gate -> report -> export

Candidates are preset names with an optional effort suffix:
  spark-1.1, spark-1.2, spark-1.3, spark-1.2-c, spark-1.3-c (Contributor mode), wonder
  e.g. spark-1.3@high  ->  muse-spark-1.3 with reasoning_effort=high
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional

from .schema import Candidate

PRESETS: Dict[str, str] = {
    "spark-1.1": "muse-spark-1.1",
    "spark-1.2": "muse-spark-1.2",
    "spark-1.3": "muse-spark-1.3",
    "spark-1.2-c": "muse-spark-1.2-contributor",
    "spark-1.3-c": "muse-spark-1.3-contributor",
    "wonder": "muse-wonder-1.0",
}
EFFORTS = ("minimal", "low", "medium", "high", "xhigh", "max")
DEFAULT_PARAMS = {"max_completion_tokens": 4000}


def parse_candidate(spec: str) -> Candidate:
    """'spark-1.3@high' -> Candidate(name='spark-1.3@high', model_id='muse-spark-1.3', params={...}).
    A raw model id (e.g. 'muse-spark-1.3') is also accepted."""
    base, _, effort = spec.partition("@")
    model_id = PRESETS.get(base, base)
    params = dict(DEFAULT_PARAMS)
    if effort:
        if effort not in EFFORTS:
            raise SystemExit("unknown effort %r (use one of %s)" % (effort, ", ".join(EFFORTS)))
        if effort == "max" and model_id not in ("muse-spark-1.3", "muse-wonder-1.0"):
            raise SystemExit("effort 'max' is only supported by muse-spark-1.3 and muse-wonder-1.0")
        params["reasoning_effort"] = effort
    return Candidate(name=spec, model_id=model_id, params=params)


def load_tasks(packs: List[str], n: Optional[int], seed: int):
    from .packs import load_pack
    tasks = []
    for name in packs:
        tasks.extend(load_pack(name, n=n, seed=seed))
    return tasks


def _split(s: Optional[str]) -> List[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def make_judges(names: List[str]):
    """Judge names: any candidate preset (e.g. spark-1.3, wonder) or 'open' for hosted Muse Spark Open."""
    from .client import ModelClient
    from .judges.llm import LLMJudge, OpenAICompatJudge
    from . import config

    client = ModelClient()
    judges = []
    for n in names:
        if n == "open":
            cfg = config.load()
            judges.append(OpenAICompatJudge("open", cfg.get("OPEN_JUDGE_BASE"), cfg.get("OPEN_JUDGE_KEY"),
                                            cfg.get("OPEN_JUDGE_MODEL")))
        else:
            c = parse_candidate(n)
            judges.append(LLMJudge(c.name, c.model_id, client, params={"reasoning_effort": "low",
                                                                       "max_completion_tokens": 2000}))
    return judges


# ---------------------------------------------------------------- commands

def print_spend() -> None:
    from . import spend
    s = spend.status()
    print("Spend: $%.2f used locally + $%.2f set aside for the canary ($%.2f used) of $%.2f limit "
          "-> $%.2f left (hard ceiling $%.0f)" % (s["local_spent_usd"], s["canary_reserved_usd"],
                                                 s["canary_spent_usd"], s["limit_usd"], s["left_usd"],
                                                 s["hard_ceiling_usd"]))


def cmd_spend(args) -> int:
    print_spend()
    return 0


def cmd_check(args) -> int:
    from .client import ModelClient
    from . import config, spend
    if not config.model_api_key():
        print("MODEL_API_KEY is not set. Put it in .env at the repo root (see .env.example).")
        return 1
    print_spend()
    client = ModelClient()
    ok = True
    for spec in _split(args.models) or ["spark-1.2", "spark-1.3", "spark-1.3-c"]:
        c = parse_candidate(spec)
        try:
            res = client.chat(c.model_id, [{"role": "user", "content": "Reply with the word ok."}],
                              # reasoning tokens count toward the limit; 200 left 1.1/1.3 with no answer
                              {"max_completion_tokens": 2000, "reasoning_effort": "low"}, use_cache=False)
        except spend.SpendCapError as e:
            print("STOP", e)
            return 1
        status = "OK " if res.error is None else "ERR"
        ok &= res.error is None
        print("%s %-28s %s  (%d ms, $%.5f)" % (status, c.model_id,
                                              (res.text or res.error or "")[:60].replace("\n", " "),
                                              res.latency_ms, res.cost_usd))
    return 0 if ok else 1


def cmd_estimate(args) -> int:
    from .runner import estimate_cost
    tasks = load_tasks(_split(args.packs), args.n, args.seed)
    cands = [parse_candidate(x) for x in [args.baseline] + _split(args.candidate)]
    est = estimate_cost(tasks, cands, args.repeats)
    print(json.dumps(est, indent=2))
    print_spend()
    return 0


def cmd_run(args) -> str:
    from .runner import estimate_cost, run
    tasks = load_tasks(_split(args.packs), args.n, args.seed)
    cands = [parse_candidate(x) for x in [args.baseline] + _split(args.candidate)]
    est = estimate_cost(tasks, cands, args.repeats)
    print("Tasks: %d  candidates: %s  repeats: %d" % (len(tasks), ", ".join(c.name for c in cands), args.repeats))
    print("Estimated cost: %s" % json.dumps(est))
    print_spend()
    if not args.yes:
        raise SystemExit("Add --yes to spend money on this run.")
    run_dir = run(tasks, cands, baseline=cands[0].name, repeats=args.repeats, out_root=args.out,
                  run_id=args.run_id, budget_usd=args.budget, workers=args.workers, notes=args.notes or "")
    print("Run saved to", run_dir)
    return run_dir


def cmd_score(args) -> int:
    from .scoring import score_run
    judges = make_judges(_split(args.judges)) if args.judges else None
    path = score_run(args.run_dir, judges=judges, mode=args.mode)
    print("Scores written to", path)
    if judges:
        from .scoring import judge_agreement
        print(json.dumps(judge_agreement(path), indent=2))
    return 0


def _run_names(run_dir: str):
    with open(os.path.join(run_dir, "run.json"), encoding="utf-8") as f:
        info = json.load(f)
    names = [c["name"] for c in info["candidates"]]
    return info["baseline"], [n for n in names if n != info["baseline"]]


def cmd_gate(args) -> int:
    from .gate import evaluate_run
    baseline, others = _run_names(args.run_dir)
    candidate = (_split(args.candidate) or others)[0]
    res = evaluate_run(args.run_dir, baseline=args.baseline or baseline, candidate=candidate,
                       max_drop=args.max_drop, alpha=args.alpha)
    print("%s  (%s -> %s)" % (res["decision"].upper(), res["baseline"], res["candidate"]))
    for r in res.get("reasons", []):
        print("  -", r)
    return 0 if res["decision"] == "go" else (2 if res["decision"] == "no-go" else 3)


def cmd_report(args) -> int:
    from .report import write_report
    for p in write_report(args.run_dir):
        print("wrote", p)
    return 0


def cmd_export(args) -> int:
    from .export import export_regressions
    for p in export_regressions(args.run_dir):
        print("wrote", p)
    return 0


def cmd_all(args) -> int:
    run_dir = cmd_run(args)
    args.run_dir = run_dir
    cmd_score(args)
    code = cmd_gate(args)
    cmd_report(args)
    cmd_export(args)
    return code


# ---------------------------------------------------------------- parser

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="upgrade-gate", description="Go / no-go gate for LLM model upgrades.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def run_opts(sp):
        sp.add_argument("--packs", required=True, help="comma-separated pack names")
        sp.add_argument("-b", "--baseline", default="spark-1.2")
        sp.add_argument("-c", "--candidate", default="spark-1.3", help="one or more, comma-separated")
        sp.add_argument("--n", type=int, default=None, help="max tasks per pack")
        sp.add_argument("--seed", type=int, default=0)
        sp.add_argument("--repeats", type=int, default=3)

    sp = sub.add_parser("spend", help="show lifetime spend vs the cap, spends nothing")
    sp.set_defaults(fn=cmd_spend)

    sp = sub.add_parser("check", help="one tiny call per model")
    sp.add_argument("--models", default="")
    sp.set_defaults(fn=cmd_check)

    sp = sub.add_parser("estimate", help="estimate cost, spends nothing")
    run_opts(sp)
    sp.set_defaults(fn=cmd_estimate)

    for name, fn in (("run", cmd_run), ("all", cmd_all)):
        sp = sub.add_parser(name)
        run_opts(sp)
        sp.add_argument("--budget", type=float, default=None, help="stop after this many USD")
        sp.add_argument("--workers", type=int, default=16)
        sp.add_argument("--out", default="results")
        sp.add_argument("--run-id", default=None)
        sp.add_argument("--notes", default="")
        sp.add_argument("--yes", action="store_true", help="confirm spending")
        if name == "all":
            sp.add_argument("--mode", default="deterministic", choices=["deterministic", "judge", "both"])
            sp.add_argument("--judges", default="")
            sp.add_argument("--max-drop", type=float, default=0.02)
            sp.add_argument("--alpha", type=float, default=0.05)
        sp.set_defaults(fn=fn)

    sp = sub.add_parser("score")
    sp.add_argument("run_dir")
    sp.add_argument("--mode", default="deterministic", choices=["deterministic", "judge", "both"])
    sp.add_argument("--judges", default="", help="e.g. spark-1.2,spark-1.3,wonder,open")
    sp.set_defaults(fn=cmd_score)

    sp = sub.add_parser("gate")
    sp.add_argument("run_dir")
    sp.add_argument("--baseline", default=None)
    sp.add_argument("--candidate", default=None)
    sp.add_argument("--max-drop", type=float, default=0.02)
    sp.add_argument("--alpha", type=float, default=0.05)
    sp.set_defaults(fn=cmd_gate)

    for name, fn in (("report", cmd_report), ("export", cmd_export)):
        sp = sub.add_parser(name)
        sp.add_argument("run_dir")
        sp.set_defaults(fn=fn)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    rv = args.fn(args)
    return rv if isinstance(rv, int) else 0


if __name__ == "__main__":
    sys.exit(main())
