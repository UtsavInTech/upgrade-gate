"""Per-1M-token prices (docs/META_API.md, read Oct 27 2026) and cost math."""
from __future__ import annotations

from typing import Dict, Mapping, Tuple

# (cached_input, input, output) USD per 1M tokens
_STANDARD = (0.15, 1.25, 4.25)
_CONTRIBUTOR = (0.002, 0.10, 0.20)
_WONDER = (0.20, 4.00, 20.00)

PRICES: Dict[str, Tuple[float, float, float]] = {
    "muse-spark-1.1": _STANDARD,
    "muse-spark-1.2": _STANDARD,
    "muse-spark-1.3": _STANDARD,
    "muse-spark-1.2-contributor": _CONTRIBUTOR,
    "muse-spark-1.3-contributor": _CONTRIBUTOR,
    "muse-wonder-1.0": _WONDER,
}


def price_for(model_id: str) -> Tuple[Tuple[float, float, float], bool]:
    """Return ((cached, input, output), known). Unknown models price at 0, known=False."""
    if model_id in PRICES:
        return PRICES[model_id], True
    return (0.0, 0.0, 0.0), False


def is_known(model_id: str) -> bool:
    return price_for(model_id)[1]


def cost_detail(model_id: str, usage: Mapping[str, int]) -> Dict[str, object]:
    """{"cost_usd", "known", "warning"}; warning is set for unknown models."""
    (p_cached, p_in, p_out), known = price_for(model_id)
    inp = int(usage.get("input_tokens", 0) or 0)
    cached = min(int(usage.get("cached_tokens", 0) or 0), inp)
    out = int(usage.get("output_tokens", 0) or 0)
    reasoning = int(usage.get("reasoning_tokens", 0) or 0)
    # OpenAI shape: completion_tokens already includes reasoning tokens. If a provider
    # reports reasoning separately (> output), bill the larger so reasoning is never free.
    billed_out = max(out, reasoning)
    usd = ((inp - cached) * p_in + cached * p_cached + billed_out * p_out) / 1_000_000
    return {
        "cost_usd": usd,
        "known": known,
        "warning": None if known else "unknown model %s: priced at 0" % model_id,
    }


def cost(model_id: str, usage: Mapping[str, int]) -> float:
    """USD cost. Cached tokens bill at the cached rate; reasoning bills as output."""
    return float(cost_detail(model_id, usage)["cost_usd"])
