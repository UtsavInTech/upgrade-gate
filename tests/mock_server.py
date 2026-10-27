"""Tiny threaded OpenAI-compatible Chat Completions mock for tests.

    with mock_server(answer="42", fail_first=2) as srv:
        client = ModelClient(base_url=srv.base_url, api_key="test", cache_dir=tmp)
        ...
        srv.calls  # number of requests received (including injected failures)
"""
from __future__ import annotations

import contextlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Union


class MockState:
    def __init__(self, answer: Union[str, Callable[[dict], str]] = "ok",
                 usage: Optional[dict] = None, fail_first: int = 0, fail_status: int = 429,
                 fail_every: int = 0, retry_after: Optional[str] = "0",
                 status_for_model: Optional[Dict[str, int]] = None, delay: float = 0.0):
        self.answer = answer
        self.usage = usage or {"prompt_tokens": 100, "completion_tokens": 50,
                               "completion_tokens_details": {"reasoning_tokens": 20},
                               "prompt_tokens_details": {"cached_tokens": 10}}
        self.fail_first = fail_first          # first N requests get fail_status
        self.fail_status = fail_status
        self.fail_every = fail_every          # every Nth request (after fail_first) gets 429
        self.retry_after = retry_after
        self.status_for_model = status_for_model or {}  # model -> forced status (e.g. 400)
        self.delay = delay
        self.lock = threading.Lock()
        self.calls = 0
        self.requests: List[dict] = []
        self.headers: List[Dict[str, str]] = []
        self.base_url = ""


def _handler(state: MockState):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # silence
            pass

        def _send(self, code: int, obj: Any, extra: Optional[Dict[str, str]] = None):
            body = json.dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n)
            try:
                req = json.loads(raw.decode("utf-8"))
            except ValueError:
                return self._send(400, {"error": {"message": "bad json"}})
            with state.lock:
                state.calls += 1
                k = state.calls
                state.requests.append(req)
                state.headers.append({"Authorization": self.headers.get("Authorization", "")})
            if not self.path.rstrip("/").endswith("/chat/completions"):
                return self._send(404, {"error": {"message": "not found"}})
            if state.delay:
                import time
                time.sleep(state.delay)
            forced = state.status_for_model.get(req.get("model", ""))
            if forced:
                return self._send(forced, {"error": {"message": "forced %d" % forced}})
            fail = k <= state.fail_first or (state.fail_every and (k - state.fail_first) % state.fail_every == 0)
            if fail:
                extra = {"Retry-After": state.retry_after} if state.retry_after is not None else {}
                return self._send(state.fail_status, {"error": {"message": "rate limited"}}, extra)
            ans = state.answer(req) if callable(state.answer) else state.answer
            self._send(200, {
                "id": "cmpl-%d" % k, "object": "chat.completion", "model": req.get("model", ""),
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": ans}}],
                "usage": state.usage,
            })

    return H


@contextlib.contextmanager
def mock_server(**kwargs):
    """Start the mock on a free localhost port; yields MockState with .base_url."""
    state = MockState(**kwargs)
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _handler(state))
    srv.daemon_threads = True
    state.base_url = "http://127.0.0.1:%d/v1" % srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        yield state
    finally:
        srv.shutdown()
        srv.server_close()
