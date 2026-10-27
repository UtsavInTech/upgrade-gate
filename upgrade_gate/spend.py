"""Lifetime spending cap for the Meta Model API. Stdlib only (the canary imports it on CI).

How it works:
- Every real (non-cached, non-mock) call first *reserves* its worst case: the whole prompt
  priced as input plus `max_completion_tokens` priced as output. If spent + reserved would
  pass the limit, the call is refused before anything is sent.
- After the call, the reservation is swapped for the real cost and appended to
  `.spend/ledger.jsonl` (gitignored). That file is the running total across every run,
  experiment and process on this machine. Do not delete it.
- The canary runs on GitHub, so it gets its own budget (CANARY_BUDGET_USD). Its spend is read
  from the committed canary/data files, and the local tool always sets aside the full canary
  budget, so local + canary together stay under the limit.

Settings (.env or environment):
  MAX_TOTAL_SPEND_USD   lifetime limit, default 90. Values above 100 are clamped to 100.
  CANARY_BUDGET_USD     part of the limit reserved for the canary, default 15. Use 0 if you
                        never turn the canary on.
"""
from __future__ import annotations

import glob
import json
import os
import threading
import time
from typing import Iterable, Optional
from urllib.parse import urlparse

from . import pricing

HARD_CEILING_USD = 100.0      # never exceeded, whatever the settings say
DEFAULT_LIMIT_USD = 90.0      # $10 margin for rounding/billing differences vs Meta's invoice
DEFAULT_CANARY_BUDGET_USD = 15.0
DEFAULT_MAX_OUTPUT_TOKENS = 32000  # assumed when a request sets no max_completion_tokens

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


class SpendCapError(RuntimeError):
    pass


def _setting(name: str, default: float) -> float:
    v = os.environ.get(name)
    if not v:
        try:
            from . import config
            v = config.get(name)
        except Exception:
            v = None
    try:
        return float(v) if v not in (None, "") else default
    except ValueError:
        return default


def limit_usd() -> float:
    return max(0.0, min(_setting("MAX_TOTAL_SPEND_USD", DEFAULT_LIMIT_USD), HARD_CEILING_USD))


def canary_budget_usd() -> float:
    return max(0.0, min(_setting("CANARY_BUDGET_USD", DEFAULT_CANARY_BUDGET_USD), limit_usd()))


def is_billable(base_url: str) -> bool:
    """Mock servers on this machine cost nothing; everything else counts."""
    host = (urlparse(base_url).hostname or "").lower()
    return host not in LOCAL_HOSTS


# ------------------------------------------------------------------ cost helpers

def usage_from_api(u: Optional[dict]) -> dict:
    """OpenAI-shape usage block -> pricing usage dict."""
    u = u if isinstance(u, dict) else {}
    ctd = u.get("completion_tokens_details") or {}
    ptd = u.get("prompt_tokens_details") or {}
    return {"input_tokens": int(u.get("prompt_tokens") or 0),
            "output_tokens": int(u.get("completion_tokens") or 0),
            "reasoning_tokens": int(ctd.get("reasoning_tokens") or 0),
            "cached_tokens": int(ptd.get("cached_tokens") or 0)}


def worst_case_usd(model_id: str, messages: list, params: Optional[dict] = None) -> float:
    """Upper bound for one call. Input: 1 token per 2 bytes of the JSON body (real ratio is ~4,
    so this over-reserves). Output: the full max_completion_tokens."""
    (_, p_in, p_out), known = pricing.price_for(model_id)
    if not known:
        raise SpendCapError("no price for model %r, so its cost can't be capped. Add it to "
                            "upgrade_gate/pricing.py first." % model_id)
    params = params or {}
    in_tokens = len(json.dumps(messages, ensure_ascii=False).encode("utf-8")) / 2.0
    out_tokens = params.get("max_completion_tokens") or params.get("max_tokens") or DEFAULT_MAX_OUTPUT_TOKENS
    return (in_tokens * p_in + float(out_tokens) * p_out) / 1_000_000


def canary_spent_usd(data_dir: Optional[str] = None) -> float:
    """Sum of every canary call saved under canary/data (committed by the GitHub workflow)."""
    data_dir = data_dir or os.path.join(REPO_ROOT, "canary", "data")
    total = 0.0
    for path in glob.glob(os.path.join(data_dir, "**", "*.jsonl"), recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue
                    if row.get("usage"):
                        total += pricing.cost(row.get("model", ""), usage_from_api(row["usage"]))
        except OSError:
            continue
    return total


# ------------------------------------------------------------------ ledger

class Ledger:
    """Append-only lifetime ledger shared by every process on this machine."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or os.environ.get("UPGRADE_GATE_LEDGER") or os.path.join(REPO_ROOT, ".spend", "ledger.jsonl")
        self._lock = threading.Lock()
        self._offset = 0
        self._spent = 0.0
        self._reserved = 0.0

    def _refresh(self) -> None:
        """Read lines other processes appended since last time."""
        try:
            with open(self.path, "rb") as f:
                f.seek(self._offset)
                chunk = f.read()
        except OSError:
            return
        end = chunk.rfind(b"\n") + 1  # ignore a half-written last line
        for line in chunk[:end].splitlines():
            try:
                self._spent += float(json.loads(line.decode("utf-8")).get("usd") or 0.0)
            except ValueError:
                continue
        self._offset += end

    def spent(self) -> float:
        with self._lock:
            self._refresh()
            return self._spent

    def committed(self, extra_reserved: float = 0.0) -> float:
        """Local spend + in-flight reservations + the canary's share (full budget, or what it
        actually spent if that is somehow higher)."""
        canary = max(canary_budget_usd(), canary_spent_usd())
        return self._spent + self._reserved + canary + extra_reserved

    def reserve(self, usd: float) -> float:
        with self._lock:
            self._refresh()
            lim = limit_usd()
            if self.committed(usd) > lim:
                raise SpendCapError(
                    "spend cap reached: $%.2f spent + $%.2f in flight + $%.2f canary share + $%.4f "
                    "for this call > limit $%.2f. Raise MAX_TOTAL_SPEND_USD (max $%.0f) or lower "
                    "CANARY_BUDGET_USD to continue." % (
                        self._spent, self._reserved, max(canary_budget_usd(), canary_spent_usd()),
                        usd, lim, HARD_CEILING_USD))
            self._reserved += usd
            return usd

    def settle(self, reserved: float, actual_usd: float, model_id: str, source: str = "") -> None:
        with self._lock:
            self._reserved = max(0.0, self._reserved - reserved)
            if actual_usd <= 0:
                return
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            line = json.dumps({"ts": time.time(), "model": model_id, "usd": round(actual_usd, 8),
                               "source": source}) + "\n"
            with open(self.path, "a", encoding="utf-8") as f:  # one small write: atomic append
                f.write(line)
            self._refresh()


_ledger: Optional[Ledger] = None
_ledger_lock = threading.Lock()


def ledger() -> Ledger:
    global _ledger
    with _ledger_lock:
        if _ledger is None:
            _ledger = Ledger()
        return _ledger


def status() -> dict:
    lg = ledger()
    spent = lg.spent()
    canary_share = max(canary_budget_usd(), canary_spent_usd())
    lim = limit_usd()
    return {"limit_usd": lim, "hard_ceiling_usd": HARD_CEILING_USD, "local_spent_usd": round(spent, 4),
            "canary_spent_usd": round(canary_spent_usd(), 4), "canary_reserved_usd": round(canary_share, 2),
            "left_usd": round(max(0.0, lim - spent - canary_share), 4), "ledger": lg.path}


class CanaryBudget:
    """Budget for one canary run: spent-so-far from canary/data plus this run's calls."""

    def __init__(self, data_dir: Optional[str] = None):
        self.budget = canary_budget_usd()
        self.spent = canary_spent_usd(data_dir)
        self.reserved = 0.0
        self._lock = threading.Lock()

    def reserve(self, usd: float) -> float:
        with self._lock:
            if self.spent + self.reserved + usd > self.budget:
                raise SpendCapError("canary budget reached: $%.2f spent of $%.2f (CANARY_BUDGET_USD)"
                                    % (self.spent, self.budget))
            self.reserved += usd
            return usd

    def settle(self, reserved: float, actual_usd: float) -> None:
        with self._lock:
            self.reserved = max(0.0, self.reserved - reserved)
            self.spent += max(0.0, actual_usd)
