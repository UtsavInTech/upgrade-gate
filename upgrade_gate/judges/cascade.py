"""Cheap-then-strong judge cascade."""
from __future__ import annotations

from typing import Any, Dict

from upgrade_gate.judges.base import Judge, make_vote


class Cascade(Judge):
    """Run `cheap`; escalate to `strong` when cheap is unsure (confidence < escalate_below)
    or failed to give a verdict. When escalated, the final verdict is strong's.

    The returned vote carries ``votes`` (every underlying vote) and ``escalated``."""

    def __init__(self, cheap: Judge, strong: Judge, escalate_below: float = 0.8):
        self.cheap = cheap
        self.strong = strong
        self.escalate_below = escalate_below
        self.name = "cascade:%s->%s" % (cheap.name, strong.name)

    def vote(self, task: Any, text: str) -> Dict[str, Any]:
        c = self.cheap.vote(task, text)
        votes = [c]
        final = c
        escalated = c.get("passed") is None or float(c.get("confidence") or 0.0) < self.escalate_below
        if escalated:
            s = self.strong.vote(task, text)
            votes.append(s)
            final = s
        cost = sum(float(v.get("cost_usd") or 0.0) for v in votes)
        return make_vote(self.name, final.get("passed"), float(final.get("confidence") or 0.0),
                         final.get("rationale", ""), cost, votes=votes, escalated=escalated)
