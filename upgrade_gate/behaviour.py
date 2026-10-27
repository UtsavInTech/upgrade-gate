"""Failure-type check: did the new version start failing *silently*?

Accuracy tells you how often a model is wrong. It doesn't tell you whether the model still says
so. An upgrade that turns "I can't hear this audio" into a confident wrong answer can leave the
pass rate unchanged while making a product worse: an honest "I can't" can be caught, a wrong
order number can't.

Every scored answer gets one type:
  correct    passed the scorer
  abstain    did not answer and said so ("I can't hear the audio", "I'm not sure", a refusal)
  no answer  the call returned nothing (error, token limit)
  blank      an answer with nothing in it: empty text, or JSON whose values are all empty
  wrong      a confident answer that is wrong
"Silent failure" = blank or wrong. Per task and version the majority over repeats is used, and
the two versions are compared with an exact McNemar test on the paired tasks.

The gate turns NO-GO when silent failures rise by more than `max_rise` with p < alpha.
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .schema import read_jsonl
from .scorers import REFUSAL_PATTERNS, extract_json

ABSTAIN = re.compile(
    r"(can'?t|cannot|unable to|don'?t have the ability to|do not have the ability to|not able to)\s+"
    r"(listen|hear|access|process|play|see|view|open|read)"
    r"|no (audio|image|file|attachment|document)s? (was |were |is )?(included|attached|provided|found)"
    r"|\bI (don'?t|do not) know\b|\bI'?m not sure\b|\bnot enough information\b"
    r"|pahunch nahi|सुन नहीं|सुनाई नहीं",
    re.I,
)
TYPES = ["correct", "abstain", "no answer", "blank", "wrong"]
SILENT = ("blank", "wrong")


def answer_type(text: Optional[str], error: Optional[str], passed: Optional[bool]) -> str:
    if error or text is None:
        return "no answer"
    if passed:
        return "correct"
    t = text.strip()
    if ABSTAIN.search(t) or REFUSAL_PATTERNS.search(t):
        return "abstain"
    if not t:
        return "blank"
    try:
        obj, _ = extract_json(t)
        if isinstance(obj, dict) and obj and all(v in ("", None, [], {}) for v in obj.values()):
            return "blank"
    except ValueError:
        pass
    return "wrong"


def _mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)


def check(run_dir: str, baseline: str, candidate: str, alpha: float = 0.05, max_rise: float = 0.02) -> Dict:
    """Compare answer types between two versions in a scored run. Never makes API calls."""
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r
            for r in read_jsonl(os.path.join(run_dir, "responses.jsonl"))}
    types: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for s in read_jsonl(os.path.join(run_dir, "scores.jsonl")):
        if s["candidate"] not in (baseline, candidate):
            continue
        r = resp.get((s["task_id"], s["candidate"], s["repeat"]), {})
        types[(s["task_id"], s["candidate"])].append(answer_type(r.get("text"), r.get("error"), s.get("passed")))

    counts = {c: {t: 0 for t in TYPES} for c in (baseline, candidate)}
    for (_, c), ts in types.items():
        for t in ts:
            counts[c][t] += 1

    def majority(ts: List[str], wanted) -> bool:
        return sum(t in wanted for t in ts) * 2 > len(ts)

    tasks = sorted({tid for tid, _ in types})
    paired = [t for t in tasks if types.get((t, baseline)) and types.get((t, candidate))]
    out: Dict = {"tasks": len(paired), "answers": counts}
    for name, wanted in (("silent", SILENT), ("abstain", ("abstain",))):
        a = [majority(types[(t, baseline)], wanted) for t in paired]
        b = [majority(types[(t, candidate)], wanted) for t in paired]
        only_base = sum(x and not y for x, y in zip(a, b))
        only_cand = sum(y and not x for x, y in zip(a, b))
        out[name] = {"baseline": sum(a), "candidate": sum(b), "only_baseline": only_base,
                     "only_candidate": only_cand, "p": _mcnemar_exact(only_base, only_cand),
                     "rise": (sum(b) - sum(a)) / len(paired) if paired else 0.0}
    s = out["silent"]
    out["flagged"] = bool(paired) and s["rise"] > max_rise and s["p"] < alpha
    out["alpha"], out["max_rise"] = alpha, max_rise
    if out["flagged"]:
        ab = out["abstain"]
        out["reason"] = (
            "Silent failures rose from %d to %d of %d tasks (p = %.1g): the new version answers wrong or blank "
            "without saying so%s." % (
                s["baseline"], s["candidate"], len(paired), s["p"],
                "; tasks where it admits it can't answer fell from %d to %d" % (ab["baseline"], ab["candidate"])
                if ab["baseline"] > ab["candidate"] else ""))
    return out


def apply_to_gate(run_dir: str, alpha: float = 0.05, max_rise: float = 0.02) -> Dict:
    """Add the failure-type check to an existing gate.json; a flagged rise makes the decision NO-GO."""
    path = os.path.join(run_dir, "gate.json")
    with open(path, encoding="utf-8") as f:
        gate = json.load(f)
    res = check(run_dir, gate["baseline"], gate["candidate"], alpha=alpha, max_rise=max_rise)
    gate["behaviour"] = res
    if res["flagged"]:
        gate["accuracy_decision"] = gate.get("accuracy_decision", gate["decision"])
        gate["decision"] = "no-go"
        reasons = [r for r in gate.get("reasons", []) if not r.startswith("Silent failures rose")]
        gate["reasons"] = [res["reason"]] + reasons
    with open(path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    return gate
