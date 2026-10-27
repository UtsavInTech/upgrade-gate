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


def _sign_test(pos: int, neg: int) -> float:
    n = pos + neg
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(pos, neg) + 1)) / 2 ** n)


def _paired(types, tasks, baseline, candidate, wanted, cluster_of=None, seed=0, boot=4000):
    """Per-task majority flags for both versions; exact McNemar over tasks, plus an item-level
    sign test and a bootstrap range that resample whole items (e.g. the English, Hindi and Hinglish
    versions of one voice note), because those are not independent."""
    def majority(ts: List[str]) -> bool:
        return sum(t in wanted for t in ts) * 2 > len(ts)
    a = [majority(types[(t, baseline)]) for t in tasks]
    b = [majority(types[(t, candidate)]) for t in tasks]
    only_base = sum(x and not y for x, y in zip(a, b))
    only_cand = sum(y and not x for x, y in zip(a, b))
    out = {"baseline": sum(a), "candidate": sum(b), "only_baseline": only_base, "only_candidate": only_cand,
           "p": _mcnemar_exact(only_base, only_cand), "rise": (sum(b) - sum(a)) / len(tasks) if tasks else 0.0}
    if cluster_of:
        clusters: Dict[str, List[int]] = defaultdict(lambda: [0, 0])
        for t, x, y in zip(tasks, a, b):
            c = clusters[cluster_of.get(t, t)]
            c[0] += x
            c[1] += y
        if len(clusters) < len(tasks):  # only meaningful when some tasks share an item
            diffs = [y - x for x, y in clusters.values()]
            pos, neg = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
            import random
            rng = random.Random(seed)
            vals = list(clusters.values())
            rises = sorted(sum(y - x for x, y in (rng.choice(vals) for _ in vals)) / len(tasks)
                           for _ in range(boot))
            out["items"] = {"n": len(clusters), "worse": pos, "better": neg, "p": _sign_test(pos, neg),
                            "rise_ci": [rises[int(0.025 * boot)], rises[int(0.975 * boot) - 1]]}
    return out


INPUT_LABEL = {"audio": "audio input", "text": "text input", "image": "image input", "pdf": "PDF input"}

DEFAULT_POLICY = {
    "accuracy": {"max_drop": 0.02, "alpha": 0.05},
    "silent_failures": {"count": ["wrong", "blank"], "max_rise": 0.02, "alpha": 0.05, "unit": "item"},
}


def load_policy(path: Optional[str]) -> Dict:
    """Release policy (release/policy.json). Missing keys fall back to DEFAULT_POLICY."""
    pol = json.loads(json.dumps(DEFAULT_POLICY))
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(pol.get(k), dict):
                pol[k].update(v)
            else:
                pol[k] = v
    sf = pol["silent_failures"]
    bad = set(sf["count"]) - {"wrong", "blank", "no answer"}
    if bad or not sf["count"]:
        raise ValueError("silent_failures.count must list some of: wrong, blank, no answer (got %s)" % sf["count"])
    if sf["unit"] not in ("item", "task"):
        raise ValueError("silent_failures.unit must be 'item' or 'task'")
    return pol


def check(run_dir: str, baseline: str, candidate: str, alpha: float = 0.05, max_rise: float = 0.02,
          count=SILENT, unit: str = "item") -> Dict:
    """Compare answer types between two versions in a scored run, separately for each input type
    (audio, text, image, PDF), with Holm correction across them. `count` = answer types that count
    as harmful; `unit` = "item" tests whole items (related translations together) when tasks share
    an item, "task" tests each task. Never makes API calls."""
    count = tuple(count)
    modality: Dict[str, str] = {}
    cluster_of: Dict[str, str] = {}
    tpath = os.path.join(run_dir, "tasks.jsonl")
    if os.path.exists(tpath):
        for t in read_jsonl(tpath):
            modality[t["id"]] = t.get("modality", "text")
            meta = t.get("meta") or {}
            cluster_of[t["id"]] = str(meta.get("item") or meta.get("group") or t["id"])
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
        silent = _paired(types, ids, baseline, candidate, count, cluster_of)
        test_p = silent["items"]["p"] if unit == "item" and "items" in silent else silent["p"]
        by_input[m] = {"label": INPUT_LABEL.get(m, m), "tasks": len(ids), "answers": counts,
                       "silent": silent, "test_p": test_p,
                       "test_unit": "item" if unit == "item" and "items" in silent else "task",
                       "blank": _paired(types, ids, baseline, candidate, ("blank",)),
                       "wrong_no_warning": _paired(types, ids, baseline, candidate, ("wrong",)),
                       "abstain": _paired(types, ids, baseline, candidate, ("abstain",))}
    # Holm across input types on the chosen test.
    order = sorted(by_input, key=lambda m: by_input[m]["test_p"])
    k = len(order)
    running = 0.0
    for i, m in enumerate(order):
        running = max(running, min(1.0, (k - i) * by_input[m]["test_p"]))
        g = by_input[m]
        g["silent"]["p_adjusted"] = running
        g["flagged"] = g["silent"]["rise"] > max_rise and running < alpha
    flagged = [m for m in order if by_input[m]["flagged"]]
    worst = flagged[0] if flagged else (order[0] if order else None)

    out: Dict = {"by_input": by_input, "alpha": alpha, "max_rise": max_rise, "count": list(count), "unit": unit,
                 "flagged": bool(flagged), "population": by_input[worst]["label"] if worst else None}
    if worst:  # top-level fields describe the most affected input type (kept for older readers)
        g = by_input[worst]
        out.update({"tasks": g["tasks"], "answers": g["answers"], "silent": g["silent"], "abstain": g["abstain"],
                    "blank": g["blank"], "wrong_no_warning": g["wrong_no_warning"]})
    what = " or ".join({"wrong": "wrong", "blank": "blank", "no answer": "missing"}[c] for c in count)
    if flagged:
        parts = []
        for m in flagged:
            g = by_input[m]
            sl, bl, ab = g["silent"], g["blank"], g["abstain"]
            it = sl.get("items")
            test = ("%d items worse, %d better, p = %.1g" % (it["worse"], it["better"], it["p"])
                    if g["test_unit"] == "item" else "p = %.1g" % sl["p"])
            parts.append(
                "%s: answers that are %s with no warning rose from %d to %d of %d tasks (%s; blank %d \u2192 %d)%s" % (
                    g["label"].capitalize(), what, sl["baseline"], sl["candidate"], g["tasks"], test,
                    bl["baseline"], bl["candidate"],
                    "; answers admitting it can't answer fell from %d to %d" % (ab["baseline"], ab["candidate"])
                    if ab["baseline"] > ab["candidate"] else ""))
        out["reason"] = "Silent failures rose. " + " | ".join(parts) + "."
    else:  # say so when a per-task rise doesn't hold up once related tasks are grouped
        notes = []
        for m, g in by_input.items():
            sl = g["silent"]
            if g["test_unit"] == "item" and sl["rise"] > max_rise and sl["p"] < alpha:
                it = sl["items"]
                notes.append("%s: %s answers rose %d \u2192 %d per task (p = %.1g), but not when related tasks are "
                             "grouped into %d items (%d worse, %d better, p = %.2g)" % (
                                 g["label"].capitalize(), what, sl["baseline"], sl["candidate"], sl["p"],
                                 it["n"], it["worse"], it["better"], it["p"]))
        if notes:
            out["note"] = "Not robust: " + " | ".join(notes) + "."
    return out


def apply_to_gate(run_dir: str, alpha: float = 0.05, max_rise: float = 0.02, policy: Optional[Dict] = None) -> Dict:
    """Add the failure-type check to an existing gate.json; a flagged rise makes the decision NO-GO."""
    path = os.path.join(run_dir, "gate.json")
    with open(path, encoding="utf-8") as f:
        gate = json.load(f)
    sf = (policy or DEFAULT_POLICY)["silent_failures"]
    res = check(run_dir, gate["baseline"], gate["candidate"], alpha=sf.get("alpha", alpha),
                max_rise=sf.get("max_rise", max_rise), count=sf.get("count", SILENT), unit=sf.get("unit", "item"))
    gate["behaviour"] = res
    if policy and policy.get("why"):
        gate["policy_why"] = policy["why"]
    gate["reasons"] = [r for r in gate.get("reasons", []) if not r.startswith("Not robust:")]
    if res.get("note"):
        gate["reasons"].append(res["note"])
    if res["flagged"]:
        gate["accuracy_decision"] = gate.get("accuracy_decision", gate["decision"])
        gate["decision"] = "no-go"
        reasons = [r for r in gate.get("reasons", []) if not r.startswith("Silent failures rose")]
        gate["reasons"] = [res["reason"]] + reasons
    with open(path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    return gate
