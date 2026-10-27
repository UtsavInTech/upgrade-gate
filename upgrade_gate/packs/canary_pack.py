"""canary: the 50-prompt canary suite (canary/prompts.json) wrapped as Tasks.

The canary `check` dict is used as the scorer spec unchanged (same type names and fields as
canary/checks.py). `pair` in prompts.json becomes pair_id.
"""
from __future__ import annotations

import json
import os
from typing import List

from ..schema import Task

PACK = "canary"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPTS = os.path.join(ROOT, "canary", "prompts.json")


def _tid(cid: str) -> str:
    return "canary-" + cid


def build() -> List[Task]:
    with open(PROMPTS, encoding="utf-8") as f:
        rows = json.load(f)
    tasks = []
    for row in rows:
        pair = row.get("pair")
        tasks.append(Task(
            id=_tid(row["id"]), pack=PACK, category=row["category"], lang=row["lang"], modality="text",
            prompt=row["prompt"], reference=row.get("gold"), scorer=dict(row["check"]),
            pair_id=_tid(pair) if pair else None,
            meta={"group": _tid(pair) if pair else _tid(row["id"]), "canary_id": row["id"]},
        ))
    return tasks
