"""OpenAI-shape Chat Completions client for the Meta Model API. Stdlib only.

- POST {base}/chat/completions with Bearer auth.
- Retries (exp backoff + jitter, honours Retry-After) on 408/429/5xx/timeouts/connection errors.
- Per-model concurrency semaphore and per-model requests-per-minute limiter.
- Disk cache keyed on (model_id, messages, params, cache_salt). Errors are never cached.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import mimetypes
import os
import random
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from . import config, pricing

log = logging.getLogger(__name__)

DEFAULT_RPM_STANDARD = 2500
DEFAULT_RPM_CONTRIBUTOR = 140
RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529}

_IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
               ".webp": "image/webp", ".gif": "image/gif"}


@dataclass
class ChatResult:
    text: Optional[str]
    usage: Dict[str, int]   # input_tokens, output_tokens, reasoning_tokens, cached_tokens
    cost_usd: float
    latency_ms: int
    error: Optional[str]
    returned_model: Optional[str]
    cached: bool
    raw: Optional[dict] = None


def _empty_usage() -> Dict[str, int]:
    return {"input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "cached_tokens": 0}


def map_usage(u: Optional[dict]) -> Dict[str, int]:
    """OpenAI usage block -> our usage dict (missing -> 0)."""
    out = _empty_usage()
    if not isinstance(u, dict):
        return out
    out["input_tokens"] = int(u.get("prompt_tokens") or u.get("input_tokens") or 0)
    out["output_tokens"] = int(u.get("completion_tokens") or u.get("output_tokens") or 0)
    ctd = u.get("completion_tokens_details") or u.get("output_tokens_details") or {}
    ptd = u.get("prompt_tokens_details") or u.get("input_tokens_details") or {}
    out["reasoning_tokens"] = int((ctd or {}).get("reasoning_tokens") or 0)
    out["cached_tokens"] = int((ptd or {}).get("cached_tokens") or 0)
    return out


def _extract_text(data: dict) -> Optional[str]:
    choices = data.get("choices") or []
    if not choices:
        return None
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):  # content parts
        parts = [p.get("text", "") for p in content if isinstance(p, dict)]
        return "".join(parts)
    return content


def cache_key(model_id: str, messages: list, params: Optional[dict], cache_salt: str = "") -> str:
    blob = json.dumps(
        [model_id, messages, sorted((params or {}).items()), cache_salt],
        sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class _RateLimiter:
    """Spaces requests evenly: at most `rpm` starts per minute. rpm <= 0 disables."""

    def __init__(self, rpm: float):
        self.interval = 60.0 / rpm if rpm and rpm > 0 else 0.0
        self._next = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        if not self.interval:
            return
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next)
            self._next = slot + self.interval
        wait = slot - now
        if wait > 0:
            time.sleep(wait)


class ModelClient:
    def __init__(self, base_url=None, api_key=None, cache_dir=".cache/responses", max_concurrency=8,
                 rpm: Optional[Dict[str, float]] = None, timeout: float = 180.0, max_attempts: int = 5,
                 backoff_base: float = 1.0, backoff_max: float = 60.0):
        """rpm: optional {model_id: requests_per_minute}; key "*" sets the default for any
        model. Without it: 140 for *-contributor models, 2500 otherwise. 0 disables limiting."""
        self.base_url = (base_url or config.model_api_base()).rstrip("/")
        self._api_key = api_key if api_key is not None else config.model_api_key()
        self.cache_dir = cache_dir
        self.max_concurrency = max(1, int(max_concurrency))
        self.rpm = dict(rpm or {})
        self.timeout = timeout
        self.max_attempts = max(1, int(max_attempts))
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self._lock = threading.Lock()
        self._sems: Dict[str, threading.Semaphore] = {}
        self._limiters: Dict[str, _RateLimiter] = {}
        self._warned: set = set()

    def __repr__(self) -> str:  # never show the key
        return "ModelClient(base_url=%r, key=%s)" % (self.base_url, "set" if self._api_key else "unset")

    # ------------------------------------------------------------ per-model controls
    def _rpm_for(self, model_id: str) -> float:
        if model_id in self.rpm:
            return self.rpm[model_id]
        if "*" in self.rpm:
            return self.rpm["*"]
        return DEFAULT_RPM_CONTRIBUTOR if model_id.endswith("-contributor") else DEFAULT_RPM_STANDARD

    def _controls(self, model_id: str):
        with self._lock:
            if model_id not in self._sems:
                self._sems[model_id] = threading.Semaphore(self.max_concurrency)
                self._limiters[model_id] = _RateLimiter(self._rpm_for(model_id))
            return self._sems[model_id], self._limiters[model_id]

    # ------------------------------------------------------------ cache
    def _cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, key[:2], key + ".json")

    def _cache_get(self, key: str) -> Optional[dict]:
        if not self.cache_dir:
            return None
        try:
            with open(self._cache_path(key), encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def _cache_put(self, key: str, entry: dict) -> None:
        if not self.cache_dir:
            return
        path = self._cache_path(key)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = "%s.%d.%d.tmp" % (path, os.getpid(), threading.get_ident())
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False)
            os.replace(tmp, path)
        except OSError as e:  # cache is best-effort
            log.warning("cache write failed: %s", e)

    # ------------------------------------------------------------ http
    def _backoff(self, attempt: int, retry_after: Optional[float]) -> float:
        if retry_after is not None and retry_after >= 0:
            return min(retry_after, self.backoff_max)
        d = min(self.backoff_max, self.backoff_base * (2 ** attempt))
        return d * (0.5 + random.random() * 0.5)

    @staticmethod
    def _retry_after(headers) -> Optional[float]:
        if headers is None:
            return None
        v = headers.get("Retry-After")
        if not v:
            return None
        try:
            return float(v)
        except ValueError:
            return None

    def _post(self, body: dict) -> tuple:
        """Returns (data|None, error|None, latency_ms)."""
        url = self.base_url + "/chat/completions"
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = "Bearer " + self._api_key
        _, limiter = self._controls(body["model"])
        last_err = "no attempt made"
        latency = 0
        for attempt in range(self.max_attempts):
            limiter.acquire()
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            t0 = time.monotonic()
            retry_after = None
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                latency = int((time.monotonic() - t0) * 1000)
                try:
                    return json.loads(raw.decode("utf-8")), None, latency
                except ValueError:
                    last_err = "invalid JSON response: %r" % raw[:200]
                    # treat as transient
            except urllib.error.HTTPError as e:
                latency = int((time.monotonic() - t0) * 1000)
                try:
                    detail = e.read().decode("utf-8", "replace")[:1000]
                except Exception:
                    detail = ""
                last_err = "HTTP %d: %s" % (e.code, detail)
                if e.code not in RETRYABLE_STATUS:
                    return None, last_err, latency
                retry_after = self._retry_after(e.headers)
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as e:
                latency = int((time.monotonic() - t0) * 1000)
                reason = getattr(e, "reason", e)
                last_err = "%s: %s" % (type(e).__name__, reason)
            if attempt + 1 < self.max_attempts:
                time.sleep(self._backoff(attempt, retry_after))
        return None, "gave up after %d attempts: %s" % (self.max_attempts, last_err), latency

    # ------------------------------------------------------------ public
    def chat(self, model_id: str, messages: list, params: Optional[dict] = None,
             use_cache: bool = True, cache_salt: str = "") -> ChatResult:
        params = dict(params or {})
        key = cache_key(model_id, messages, params, cache_salt)
        if use_cache:
            hit = self._cache_get(key)
            if hit is not None:
                return ChatResult(text=hit.get("text"), usage=hit.get("usage") or _empty_usage(),
                                  cost_usd=float(hit.get("cost_usd") or 0.0),
                                  latency_ms=int(hit.get("latency_ms") or 0), error=None,
                                  returned_model=hit.get("returned_model"), cached=True, raw=hit.get("raw"))

        if not pricing.is_known(model_id) and model_id not in self._warned:
            self._warned.add(model_id)
            log.warning("no price for model %s: cost will be recorded as 0", model_id)

        body = {"model": model_id, "messages": messages}
        body.update(params)
        sem, _ = self._controls(model_id)
        with sem:
            data, err, latency = self._post(body)
        if err is not None:
            return ChatResult(text=None, usage=_empty_usage(), cost_usd=0.0, latency_ms=latency,
                              error=err, returned_model=None, cached=False, raw=None)
        if isinstance(data, dict) and data.get("error"):
            e = data["error"]
            msg = e.get("message") if isinstance(e, dict) else str(e)
            return ChatResult(text=None, usage=_empty_usage(), cost_usd=0.0, latency_ms=latency,
                              error="API error: %s" % msg, returned_model=data.get("model"), cached=False, raw=data)
        usage = map_usage(data.get("usage"))
        text = _extract_text(data)
        cost = pricing.cost(model_id, usage)
        returned_model = data.get("model")
        if text is None:
            return ChatResult(text=None, usage=usage, cost_usd=cost, latency_ms=latency,
                              error="no message content in response", returned_model=returned_model,
                              cached=False, raw=data)
        if use_cache:
            self._cache_put(key, {"model_id": model_id, "text": text, "usage": usage, "cost_usd": cost,
                                  "latency_ms": latency, "returned_model": returned_model, "raw": data,
                                  "ts": time.time()})
        return ChatResult(text=text, usage=usage, cost_usd=cost, latency_ms=latency, error=None,
                          returned_model=returned_model, cached=False, raw=data)


# ---------------------------------------------------------------- messages

def _resolve(path: str) -> str:
    if os.path.isabs(path) or os.path.exists(path):
        return path
    alt = os.path.join(config.REPO_ROOT, path)
    return alt if os.path.exists(alt) else path


def _data_url(path: str, mime: str) -> str:
    with open(_resolve(path), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode("ascii"))


def attachment_part(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()
    if ext in _IMAGE_MIME:
        return {"type": "image_url", "image_url": {"url": _data_url(path, _IMAGE_MIME[ext])}}
    if ext == ".pdf":
        return {"type": "file", "file": {"filename": os.path.basename(path),
                                         "file_data": _data_url(path, "application/pdf")}}
    mime = mimetypes.guess_type(path)[0]
    if mime and mime.startswith("image/"):
        return {"type": "image_url", "image_url": {"url": _data_url(path, mime)}}
    raise ValueError("unsupported attachment type: %s" % path)


def _get(task: Any, name: str, default=None):
    if isinstance(task, dict):
        return task.get(name, default)
    return getattr(task, name, default)


def build_messages(task: Any, system: Optional[str] = None) -> list:
    """Task (dataclass or dict) -> chat messages. Text first, then attachment parts."""
    msgs: List[dict] = []
    if system:
        msgs.append({"role": "system", "content": system})
    prompt = _get(task, "prompt", "") or ""
    attachments = _get(task, "attachments", None) or []
    if not attachments:
        msgs.append({"role": "user", "content": prompt})
    else:
        parts: List[dict] = [{"type": "text", "text": prompt}]
        parts.extend(attachment_part(p) for p in attachments)
        msgs.append({"role": "user", "content": parts})
    return msgs
