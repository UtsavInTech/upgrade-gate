"""Judge interface, blind judge prompt and verdict parsing.

A judge sees the task prompt, the reference answer and the candidate text. It never
sees which model produced the text (blind), so H1 (judge-version bias) can be measured.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from upgrade_gate.scorers import extract_json, strip_think

JUDGE_SYSTEM = (
    "You are a strict grader. You are given a task, the reference (correct) answer, and a "
    "candidate response. Decide whether the candidate response is correct: it must agree "
    "with the reference answer on every point that matters and follow the task's format "
    "instructions. Ignore style. Do not guess who wrote the response.\n"
    "Reply with JSON only: {\"correct\": true|false, \"confidence\": <0..1>, "
    "\"rationale\": \"<one or two sentences>\"}"
)

VERDICT_SCHEMA: Dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "judge_verdict",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "correct": {"type": "boolean"},
                "confidence": {"type": "number"},
                "rationale": {"type": "string"},
            },
            "required": ["correct", "confidence", "rationale"],
            "additionalProperties": False,
        },
    },
}

MAX_CANDIDATE_CHARS = 12000


def _get(task: Any, key: str, default: Any = None) -> Any:
    if isinstance(task, dict):
        return task.get(key, default)
    return getattr(task, key, default)


def _fmt_ref(ref: Any) -> str:
    if isinstance(ref, str):
        return ref
    return json.dumps(ref, ensure_ascii=False)


def build_judge_messages(task: Any, text: str) -> List[Dict[str, Any]]:
    """Blind judge prompt. Uses only prompt, reference and the candidate text."""
    cand = strip_think(text or "").strip()
    if len(cand) > MAX_CANDIDATE_CHARS:
        cand = cand[:MAX_CANDIDATE_CHARS] + "\n[...truncated]"
    user = (
        "## Task\n%s\n\n## Reference answer\n%s\n\n## Candidate response\n%s\n\n"
        "Is the candidate response correct? Answer with the JSON object only."
        % (_get(task, "prompt", ""), _fmt_ref(_get(task, "reference")), cand)
    )
    return [{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}]


def parse_verdict(text: Optional[str]) -> Tuple[Optional[bool], float, str]:
    """-> (passed, confidence, rationale). passed None when the verdict can't be parsed."""
    if not text:
        return None, 0.0, "parse error: empty judge output"
    try:
        obj, _ = extract_json(text)
    except ValueError:
        return None, 0.0, "parse error: %s" % text.strip()[:120]
    if not isinstance(obj, dict):
        return None, 0.0, "parse error: not an object"
    low = {str(k).casefold(): v for k, v in obj.items()}
    c = low.get("correct", low.get("passed"))
    if isinstance(c, str) and c.strip().casefold() in ("true", "yes", "false", "no"):
        c = c.strip().casefold() in ("true", "yes")
    if not isinstance(c, bool):
        return None, 0.0, "parse error: no boolean 'correct'"
    conf = low.get("confidence", 0.5)
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        conf = 0.5
    if conf > 1.0 and conf <= 100.0:  # 0-100 scale
        conf = conf / 100.0
    conf = min(1.0, max(0.0, conf))
    return c, conf, str(low.get("rationale", ""))[:500]


def make_vote(judge: str, passed: Optional[bool], confidence: float, rationale: str,
              cost_usd: float = 0.0, **extra: Any) -> Dict[str, Any]:
    v = {"judge": judge, "passed": passed, "confidence": confidence,
         "rationale": rationale, "cost_usd": float(cost_usd or 0.0)}
    v.update(extra)
    return v


class Judge:
    """Base judge. Subclasses implement vote()."""

    name: str = "judge"

    def vote(self, task: Any, text: str) -> Dict[str, Any]:
        """-> {"judge", "passed", "confidence", "rationale", "cost_usd"}"""
        raise NotImplementedError

    def __repr__(self) -> str:
        return "<%s %s>" % (type(self).__name__, self.name)
