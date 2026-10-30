"""What would each route cost a shop? An illustrative scenario, not measured savings.

  python3 scripts/loss_scenario.py evidence/voice-notes            # 1.2 vs 1.3 listening directly
  python3 scripts/loss_scenario.py results/e9-route-synth          # adds the transcribe routes

Only the order voice notes count (the 'extract' tasks: order number, pincode, city). Every answer
(each try) goes through VoiceOrder's own save checks (voiceorder/server.py: checks), the same format
rules a typical shop form applies. Outcomes:

  correct          saved, and all three fields are right
  wrong but saved  passes every format check with a wrong order number or pincode: the error ships
  rejected         blank or malformed: the form refuses it; the shop has to follow up by hand
  asked to type    the model said it couldn't hear; the app asks the customer to type it

Only "wrong but saved" is priced, as one failed delivery each, at ASSUMED_RTO_INR: the logistics
part of a return-to-origin (forward + return shipping, repacking), Rs 180-240 per the industry estimate
on Amazon Shipping's India blog. That leaves out customer support, refunds and the lost sale, and
assumes every wrong-but-saved order fails delivery. Read the rupee figure as a scenario.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate.schema import read_jsonl  # noqa: E402
from voiceorder.server import checks  # noqa: E402

ASSUMED_RTO_INR = (180, 240)
SOURCE = "https://shipping.amazon.in/blog/what-is-rto-how-to-reduce-return-to-origin"


def _order(text):
    import re
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        obj = json.loads(m.group(0)) if m else None
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def _digits(x) -> str:
    return "".join(ch for ch in str(x or "") if ch.isdigit())


def outcome(task: dict, resp: dict) -> str:
    if resp.get("error") and not resp.get("text"):
        return "rejected"
    text = resp.get("text") or ""
    order = _order(text)
    c = checks(order, text)
    if c["status"] == "ask_customer":
        return "asked to type"
    if c["status"] == "rejected":
        return "rejected"
    ref = task["reference"]
    right = (_digits(order.get("order_number")) == str(ref["order_number"])
             and _digits(order.get("pincode")) == str(ref["pincode"]))
    return "correct" if right else "wrong but saved"


def scenario(run_dir: str) -> dict:
    tasks = {t["id"]: t for t in read_jsonl(os.path.join(run_dir, "tasks.jsonl"))
             if t.get("modality") == "audio" and (t.get("meta") or {}).get("kind") == "extract"}
    counts = defaultdict(Counter)
    for r in read_jsonl(os.path.join(run_dir, "responses.jsonl")):
        t = tasks.get(r["task_id"])
        if t:
            counts[r["candidate"]][outcome(t, r)] += 1
    out = {}
    for cand, c in sorted(counts.items()):
        n = sum(c.values())
        per_k = {k: round(1000 * v / n) for k, v in c.items()}
        wrong = 1000 * c["wrong but saved"] / n
        out[cand] = {"answers": n, "counts": dict(c), "per_1000_orders": per_k,
                     "inr_per_1000_orders": [round(wrong * ASSUMED_RTO_INR[0]), round(wrong * ASSUMED_RTO_INR[1])]}
    return {"run_dir": os.path.relpath(run_dir, ROOT), "order_notes": len(tasks),
            "assumption": "each wrong-but-saved order = one failed delivery at Rs %d-%d (logistics only; %s)"
                          % (ASSUMED_RTO_INR + (SOURCE,)), "by_route": out}


def main() -> int:
    run_dir = os.path.join(ROOT, sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "evidence", "voice-notes")
    res = scenario(run_dir)
    print("Order voice notes: %d clips, every try counted. %s\n" % (res["order_notes"], res["assumption"]))
    print("| Route | correct | wrong but saved | rejected | asked to type | Rs per 1,000 orders (scenario) |")
    print("|---|---|---|---|---|---|")
    for cand, v in res["by_route"].items():
        p = v["per_1000_orders"]
        print("| %s | %d | %d | %d | %d | %s–%s |" % (
            cand, p.get("correct", 0), p.get("wrong but saved", 0), p.get("rejected", 0), p.get("asked to type", 0),
            "{:,}".format(v["inr_per_1000_orders"][0]), "{:,}".format(v["inr_per_1000_orders"][1])))
    out = os.path.join(ROOT, "experiments", "out", "loss_scenario_%s.json" % os.path.basename(run_dir.rstrip("/")))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print("\nwrote", os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
