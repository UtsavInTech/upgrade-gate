"""Shared data shapes. This file is the contract between every part of Upgrade Gate.

Owner: Claude side. Codex side reads it but must not change it. If you need a change,
write it in docs/CONTRACT_REQUESTS.md.

All records are plain dicts on disk (JSON / JSONL). These dataclasses document the
fields and give helpers to convert. Python 3.9 compatible.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Optional

# ---------------------------------------------------------------- tasks

@dataclass
class Task:
    """One test item with a known correct answer."""
    id: str                      # unique across all packs, e.g. "banking77-0042"
    pack: str                    # pack name, e.g. "banking77", "docs-synth", "hindi-pairs"
    category: str                # slice used in per-category stats, e.g. "classification"
    lang: str                    # "en" | "hi" | "hinglish"
    modality: str                # "text" | "image" | "pdf"
    prompt: str                  # user message text
    reference: Any               # ground truth (str, number, dict, list)
    scorer: Dict[str, Any]       # deterministic scorer spec, see upgrade_gate/scorers.py
    attachments: List[str] = field(default_factory=list)  # file paths for image/pdf tasks
    pair_id: Optional[str] = None  # id of the matched task in another language (H6)
    meta: Dict[str, Any] = field(default_factory=dict)

# ---------------------------------------------------------------- candidates

@dataclass
class Candidate:
    """A model configuration under test."""
    name: str                    # short label used everywhere, e.g. "spark-1.2@low"
    model_id: str                # exact pinned API model id
    params: Dict[str, Any] = field(default_factory=dict)  # e.g. {"reasoning_effort": "low"}

# ---------------------------------------------------------------- results on disk
#
# results/<run_id>/
#   run.json          RunInfo
#   responses.jsonl   one ResponseRecord per line
#   scores.jsonl      one ScoreRecord per line
#   gate.json         GateResult (written by stats/gate code)
#   report.md / report.html   (written by report code)
#   exports/          promptfoo YAML + pytest (written by export code)

@dataclass
class RunInfo:
    run_id: str
    created_utc: str
    candidates: List[Dict[str, Any]]   # Candidate dicts
    baseline: str                      # candidate name used as "old"
    packs: List[str]
    n_tasks: int
    repeats: int
    budget_usd: Optional[float] = None
    notes: str = ""


@dataclass
class ResponseRecord:
    run_id: str
    task_id: str
    candidate: str               # Candidate.name
    repeat: int                  # 0-based
    text: Optional[str]          # raw model output; None if the call failed
    usage: Dict[str, int]        # {"input_tokens", "output_tokens", "reasoning_tokens"} (missing -> 0)
    cost_usd: float
    latency_ms: int
    error: Optional[str] = None
    ts_utc: str = ""
    returned_model: Optional[str] = None
    cached: bool = False         # served from local cache


@dataclass
class ScoreRecord:
    run_id: str
    task_id: str
    candidate: str
    repeat: int
    passed: Optional[bool]       # None = could not score (API error)
    score: Optional[float]       # 0..1; equals float(passed) for binary scorers
    method: str                  # "deterministic" | "judge:<judge-name>" | "cascade:<a>-><b>"
    detail: str = ""             # short human-readable reason
    judge_votes: List[Dict[str, Any]] = field(default_factory=list)  # [{"judge", "passed", "confidence", "rationale"}]
    cost_usd: float = 0.0        # judge cost for this score


# ---------------------------------------------------------------- gate output (written by Codex-side stats)

@dataclass
class Comparison:
    """Paired comparison of candidate vs baseline over one slice of tasks."""
    slice: str                   # "overall" | "category=<x>" | "lang=<x>" | "modality=<x>"
    n: int                       # number of paired tasks
    base_rate: float
    cand_rate: float
    delta: float                 # cand_rate - base_rate
    ci_low: float                # 95% CI for delta (paired bootstrap)
    ci_high: float
    b: int                       # base pass, cand fail  (regressions)
    c: int                       # base fail, cand pass  (improvements)
    p_value: float               # exact McNemar
    p_adjusted: Optional[float] = None  # Holm-adjusted across slices
    verdict: str = ""            # "regression" | "improvement" | "no-change" | "inconclusive"


@dataclass
class GateResult:
    run_id: str
    baseline: str
    candidate: str
    decision: str                # "go" | "no-go" | "inconclusive"
    reasons: List[str]
    overall: Dict[str, Any]      # Comparison dict
    slices: List[Dict[str, Any]] # Comparison dicts
    regressions: List[Dict[str, Any]]  # [{"task_id", "category", "lang", "base_text", "cand_text", "reference", "evidence"}]
    cost: Dict[str, Any]         # {"base_usd", "cand_usd", "delta_pct", "judge_usd"}
    thresholds: Dict[str, Any]   # {"max_drop", "alpha", "min_n"}
    created_utc: str = ""


# ---------------------------------------------------------------- helpers

def to_dict(obj: Any) -> Dict[str, Any]:
    return asdict(obj)


def write_jsonl(path: str, rows: Iterable[Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            d = r if isinstance(r, dict) else asdict(r)
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def append_jsonl(path: str, row: Any) -> None:
    d = row if isinstance(row, dict) else asdict(row)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
