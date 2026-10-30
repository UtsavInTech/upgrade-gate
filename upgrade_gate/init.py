"""`upgrade-gate init`: set up a repo to gate its own model upgrades in a few minutes.

Writes (never overwrites unless --force):
  release/model.json                  the model your app ships; a PR that changes it opens the gate
  release/policy.json                 what counts as a harmful failure, and why (edit the "why")
  tasks/my_tasks.jsonl                five example tasks to replace with 20-50 of your own
  .github/workflows/upgrade-gate.yml  runs the gate on that PR, capped at $1, using MODEL_API_KEY
"""
from __future__ import annotations

import json
import os
from typing import Dict, List

EXAMPLE_TASKS: List[Dict] = [
    {"id": "refund-01", "category": "support",
     "prompt": "Classify this message as one of: refund, delivery, cancel. Reply with the label only.\n\n"
               "I sent the shoes back last week and still have no money.",
     "scorer": {"type": "label", "value": "refund", "labels": ["refund", "delivery", "cancel"]}},
    {"id": "refund-02", "category": "support", "lang": "hinglish",
     "prompt": "Classify this message as one of: refund, delivery, cancel. Reply with the label only.\n\n"
               "Mera parcel kal aana tha, abhi tak nahi aaya.",
     "scorer": {"type": "label", "value": "delivery", "labels": ["refund", "delivery", "cancel"]}},
    {"id": "order-01", "category": "extraction",
     "prompt": "Reply with only a JSON object with keys order_number and city.\n\nHi, order 58213, I'm in Pune.",
     "scorer": {"type": "json_fields", "fields": {"order_number": ["58213", 58213], "city": ["Pune"]}}},
    {"id": "math-01", "category": "math",
     "prompt": "3 kg rice at 64 rupees per kg, paid with a 500 note. How much change? Reply with the number only.",
     "scorer": {"type": "number", "value": 308}},
    {"id": "exact-01", "prompt": "What is the capital of Rajasthan? One word.", "reference": "Jaipur"},
]

POLICY = {
    "why": "EDIT ME: one sentence on what a wrong answer costs your users, e.g. 'A wrong order number "
           "ships to the wrong customer; an honest \"I'm not sure\" is fine because we ask again.'",
    "accuracy": {"max_drop": 0.02, "alpha": 0.05},
    "silent_failures": {"count": ["wrong", "blank"], "max_rise": 0.02, "alpha": 0.05, "unit": "item"},
}

WORKFLOW = """name: upgrade-gate

# Made by `upgrade-gate init`. Runs when a pull request changes the model in release/model.json:
# asks both models your tasks (tasks/my_tasks.jsonl), 3 tries each, capped at $1, and fails the check on
# NO-GO (less accurate, or more wrong/blank answers with no warning). Needs a MODEL_API_KEY repo secret.
on:
  pull_request:
    paths:
      - "release/model.json"
      - "release/policy.json"
      - "tasks/**"

permissions:
  contents: read

jobs:
  gate:
    name: upgrade-gate
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Read the model change
        id: models
        run: |
          echo "candidate=$(python3 -c 'import json;print(json.load(open("release/model.json"))["model"])')" >> "$GITHUB_OUTPUT"
          echo "baseline=$(git show origin/${{ github.base_ref }}:release/model.json | python3 -c 'import json,sys;print(json.load(sys.stdin)["model"])')" >> "$GITHUB_OUTPUT"
      - uses: UtsavInTech/upgrade-gate@main
        with:
          name: my-tasks
          mode: live
          tasks: tasks/my_tasks.jsonl
          n: "50"
          budget: "1"
          policy: release/policy.json
          baseline: ${{ steps.models.outputs.baseline }}
          candidate: ${{ steps.models.outputs.candidate }}
          api-key: ${{ secrets.MODEL_API_KEY }}
"""


def files(model: str) -> Dict[str, str]:
    return {
        "release/model.json": json.dumps({"model": model, "note": "The model this app ships. A pull request "
                                          "that changes it runs the upgrade gate."}, indent=2) + "\n",
        "release/policy.json": json.dumps(POLICY, indent=2) + "\n",
        "tasks/my_tasks.jsonl": "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in EXAMPLE_TASKS),
        ".github/workflows/upgrade-gate.yml": WORKFLOW,
    }


def init(root: str, model: str, candidate: str, force: bool = False) -> int:
    written, kept = [], []
    for rel, text in files(model).items():
        path = os.path.join(root, rel)
        if os.path.exists(path) and not force:
            kept.append(rel)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        written.append(rel)
    for rel in written:
        print("  wrote   %s" % rel)
    for rel in kept:
        print("  kept    %s (already there; --force to replace)" % rel)
    print("""
Next:
  1. Replace tasks/my_tasks.jsonl with 20-50 real tasks from your app, each with its known answer
     (format: https://github.com/UtsavInTech/upgrade-gate/blob/main/docs/BRING_YOUR_OWN_TASKS.md).
  2. Edit the "why" in release/policy.json: what does a wrong answer cost your users?
  3. Free cost check:   upgrade-gate estimate --packs tasks/my_tasks.jsonl -b {b} -c {c}
  4. Try it now:        upgrade-gate all --packs tasks/my_tasks.jsonl -b {b} -c {c} --budget 1 --yes
     (needs MODEL_API_KEY in your environment or a .env file)
  5. On GitHub: add a MODEL_API_KEY repo secret, then open a PR that changes release/model.json
     to {c}. The upgrade-gate check fails on NO-GO.""".format(b=model, c=candidate))
    return 0
