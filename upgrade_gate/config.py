"""Settings from the environment, falling back to a `.env` file at the repo root.

Never print or log key values. Use `describe()` for a redacted view.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_API_BASE = "https://api.meta.ai/v1"

KEYS = ("MODEL_API_KEY", "MODEL_API_BASE", "OPEN_JUDGE_BASE", "OPEN_JUDGE_KEY", "OPEN_JUDGE_MODEL")
_DEFAULTS = {"MODEL_API_BASE": DEFAULT_MODEL_API_BASE}

_dotenv_cache: Optional[Dict[str, str]] = None


def parse_dotenv(path: str) -> Dict[str, str]:
    """Minimal KEY=VALUE parser. Ignores blanks/comments, strips quotes and `export `."""
    out: Dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
            v = v[1:-1]
        elif " #" in v:
            v = v.split(" #", 1)[0].rstrip()
        if k:
            out[k] = v
    return out


def _dotenv() -> Dict[str, str]:
    global _dotenv_cache
    if _dotenv_cache is None:
        _dotenv_cache = parse_dotenv(os.path.join(REPO_ROOT, ".env"))
    return _dotenv_cache


def reload() -> None:
    """Forget the parsed .env (re-read on next access)."""
    global _dotenv_cache
    _dotenv_cache = None


def get(key: str, default: Optional[str] = None) -> Optional[str]:
    """Env first, then .env, then built-in default, then `default`."""
    v = os.environ.get(key)
    if v:
        return v
    v = _dotenv().get(key)
    if v:
        return v
    if key in _DEFAULTS:
        return _DEFAULTS[key]
    return default


def model_api_key() -> Optional[str]:
    return get("MODEL_API_KEY")


def model_api_base() -> str:
    return (get("MODEL_API_BASE") or DEFAULT_MODEL_API_BASE).rstrip("/")


def open_judge() -> Dict[str, Optional[str]]:
    return {"base": get("OPEN_JUDGE_BASE"), "key": get("OPEN_JUDGE_KEY"), "model": get("OPEN_JUDGE_MODEL")}


def describe() -> Dict[str, str]:
    """Redacted summary, safe to print: secrets show only set/unset."""
    out = {}
    for k in KEYS:
        v = get(k)
        if k.endswith("_KEY"):
            out[k] = "set" if v else "unset"
        else:
            out[k] = v or "unset"
    return out
