"""LLM judges built on ModelClient (Meta API) or any OpenAI-compatible endpoint."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from upgrade_gate.judges.base import (VERDICT_SCHEMA, Judge, build_judge_messages,
                                      make_vote, parse_verdict)


def _attr(res: Any, key: str, default: Any = None) -> Any:
    if isinstance(res, dict):
        return res.get(key, default)
    return getattr(res, key, default)


def _looks_like_rf_rejection(err: str) -> bool:
    e = err.lower()
    return any(k in e for k in ("400", "422", "response_format", "json_schema", "unsupported", "not supported"))


class LLMJudge(Judge):
    """Judge = one model behind a ModelClient-like object with
    ``chat(model_id, messages, params) -> ChatResult(text, cost_usd, error, ...)``."""

    def __init__(self, name: str, model_id: str, client: Any, params: Optional[Dict[str, Any]] = None,
                 use_response_format: bool = True):
        self.name = name
        self.model_id = model_id
        self.client = client
        self.params = dict(params or {})
        self.use_response_format = use_response_format

    def _call(self, messages, with_rf: bool):
        p = dict(self.params)
        if with_rf:
            p["response_format"] = VERDICT_SCHEMA
        return self.client.chat(self.model_id, messages, p)

    def vote(self, task: Any, text: str) -> Dict[str, Any]:
        messages = build_judge_messages(task, text)
        cost = 0.0
        res = self._call(messages, self.use_response_format)
        cost += float(_attr(res, "cost_usd", 0.0) or 0.0)
        err = _attr(res, "error")
        if self.use_response_format and err and _looks_like_rf_rejection(str(err)):
            # provider may reject response_format -> retry once without it, and stop sending it
            res2 = self._call(messages, False)
            cost += float(_attr(res2, "cost_usd", 0.0) or 0.0)
            if not _attr(res2, "error") and _attr(res2, "text") is not None:
                self.use_response_format = False
            res, err = res2, _attr(res2, "error")
        out = _attr(res, "text")
        if err or out is None:
            return make_vote(self.name, None, 0.0, "api error: %s" % (err or "no text"), cost)
        passed, conf, why = parse_verdict(out)
        return make_vote(self.name, passed, conf, why, cost)


# ---------------------------------------------------------------- OpenAI-compatible endpoint

def _env(key: str) -> Optional[str]:
    if os.environ.get(key):
        return os.environ[key]
    try:
        with open(".env", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return None


class _Result(object):
    def __init__(self, text=None, cost_usd=0.0, error=None, usage=None, raw=None):
        self.text, self.cost_usd, self.error = text, cost_usd, error
        self.usage, self.raw = usage or {}, raw


class UrllibChatClient(object):
    """Minimal stdlib Chat Completions client (no cache, no pricing)."""

    def __init__(self, base_url: str, api_key: Optional[str], timeout: float = 120.0, retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries

    def chat(self, model_id: str, messages: list, params: Optional[dict] = None, **_: Any) -> _Result:
        body = {"model": model_id, "messages": messages}
        body.update(params or {})
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        url = self.base_url + "/chat/completions"
        last = None
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(url, json.dumps(body).encode("utf-8"), headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = json.loads(r.read().decode("utf-8"))
                text = data["choices"][0]["message"].get("content")
                return _Result(text=text, usage=data.get("usage") or {}, raw=data)
            except urllib.error.HTTPError as e:
                last = "HTTP %s: %s" % (e.code, e.read()[:300].decode("utf-8", "replace"))
                if e.code < 500 and e.code != 429:
                    break
            except Exception as e:  # network, json
                last = "%s: %s" % (type(e).__name__, e)
            time.sleep(1.5 * (attempt + 1))
        return _Result(error=last)


class OpenAICompatJudge(LLMJudge):
    """Judge on a hosted OpenAI-compatible endpoint, e.g. Muse Spark Open.
    Defaults come from OPEN_JUDGE_BASE / OPEN_JUDGE_KEY / OPEN_JUDGE_MODEL."""

    def __init__(self, name: str = "spark-open", base_url: Optional[str] = None,
                 api_key: Optional[str] = None, model: Optional[str] = None,
                 params: Optional[Dict[str, Any]] = None, client: Any = None):
        base_url = base_url or _env("OPEN_JUDGE_BASE")
        api_key = api_key or _env("OPEN_JUDGE_KEY")
        model = model or _env("OPEN_JUDGE_MODEL")
        if client is None:
            if not base_url or not model:
                raise ValueError("OpenAICompatJudge needs base_url and model (OPEN_JUDGE_BASE / OPEN_JUDGE_MODEL)")
            client = self._make_client(base_url, api_key)
        super().__init__(name, model or "", client, params)
        self.base_url = base_url

    @staticmethod
    def _make_client(base_url: str, api_key: Optional[str]):
        try:
            from upgrade_gate.client import ModelClient  # lazy: built by another agent
            return ModelClient(base_url=base_url, api_key=api_key)
        except Exception:
            return UrllibChatClient(base_url, api_key)
