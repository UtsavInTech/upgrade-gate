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


def _paired(types, tasks, baseline, candidate, wanted):
    def majority(ts: List[str]) -> bool:
        return sum(t in wanted for t in ts) * 2 > len(ts)
    a = [majority(types[(t, baseline)]) for t in tasks]
    b = [majority(types[(t, candidate)]) for t in tasks]
    only_base = sum(x and not y for x, y in zip(a, b))
    only_cand = sum(y and not x for x, y in zip(a, b))
    return {"baseline": sum(a), "candidate": sum(b), "only_baseline": only_base, "only_candidate": only_cand,
            "p": _mcnemar_exact(only_base, only_cand), "rise": (sum(b) - sum(a)) / len(tasks) if tasks else 0.0}


INPUT_LABEL = {"audio": "audio input", "text": "text input", "image": "image input", "pdf": "PDF input"}


def check(run_dir: str, baseline: str, candidate: str, alpha: float = 0.05, max_rise: float = 0.02) -> Dict:
    """Compare answer types between two versions in a scored run, separately for each input type
    (audio, text, image, PDF), with Holm correction across them. Never makes API calls."""
    modality: Dict[str, str] = {}
    tpath = os.path.join(run_dir, "tasks.jsonl")
    if os.path.exists(tpath):
        modality = {t["id"]: t.get("modality", "text") for t in read_jsonl(tpath)}
    resp = {(r["task_id"], r["candidate"], r["repeat"]): r
            for r in read_jsonl(os.path.join(run_dir, "responses.jsonl"))}
    types: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for s in read_jsonl(os.path.join(run_dir, "scores.jsonl")):
        if s["candidate"] not in (baseline, candidate):
            continue
        r = resp.get((s["task_id"], s["candidate"], s["repeat"]), {})
        types[(s["task_id"], s["candidate"])].append(answer_type(r.get("text"), r.get("error"), s.get("passed")))

    paired = sorted({t for t, _ in types if types.get((t, baseline)) and types.get((t, candidate))})
    groups: Dict[str, List[str]] = defaultdict(list)
    for t in paired:
        groups[modality.get(t, "text")].append(t)

    by_input = {}
    for m, ids in sorted(groups.items()):
        counts = {c: {k: 0 for k in TYPES} for c in (baseline, candidate)}
        for t in ids:
            for c in (baseline, candidate):
                for x in types[(t, c)]:
                    counts[c][x] += 1
        by_input[m] = {"label": INPUT_LABEL.get(m, m), "tasks": len(ids), "answers": counts,
                       "silent": _paired(types, ids, baseline, candidate, SILENT),
                       "blank": _paired(types, ids, baseline, candidate, ("blank",)),
                       "wrong_no_warning": _paired(types, ids, baseline, candidate, ("wrong",)),
                       "abstain": _paired(types, ids, baseline, candidate, ("abstain",))}
    # Holm across input types: a rise counts only if it survives the correction.
    order = sorted(by_input, key=lambda m: by_input[m]["silent"]["p"])
    k = len(order)
    running = 0.0
    for i, m in enumerate(order):
        running = max(running, min(1.0, (k - i) * by_input[m]["silent"]["p"]))
        g = by_input[m]
        g["silent"]["p_adjusted"] = running
        g["flagged"] = g["silent"]["rise"] > max_rise and running < alpha
    flagged = [m for m in order if by_input[m]["flagged"]]
    worst = flagged[0] if flagged else (order[0] if order else None)

    out: Dict = {"by_input": by_input, "alpha": alpha, "max_rise": max_rise, "flagged": bool(flagged),
                 "population": by_input[worst]["label"] if worst else None}
    if worst:  # top-level fields describe the most affected input type (kept for older readers)
        g = by_input[worst]
        out.update({"tasks": g["tasks"], "answers": g["answers"], "silent": g["silent"], "abstain": g["abstain"],
                    "blank": g["blank"], "wrong_no_warning": g["wrong_no_warning"]})
    if flagged:
        parts = []
        for m in flagged:
            g = by_input[m]
            sl, bl, ab = g["silent"], g["blank"], g["abstain"]
            parts.append(
                "%s: answers that are wrong or blank with no warning rose from %d to %d of %d tasks "
                "(p = %.1g; blank %d \u2192 %d)%s" % (
                    g["label"].capitalize(), sl["baseline"], sl["candidate"], g["tasks"], sl["p"],
                    bl["baseline"], bl["candidate"],
                    "; answers admitting it can't answer fell from %d to %d" % (ab["baseline"], ab["candidate"])
                    if ab["baseline"] > ab["candidate"] else ""))
        out["reason"] = "Silent failures rose. " + " | ".join(parts) + "."
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
