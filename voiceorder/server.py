"""VoiceOrder: a voice-order helper for an Indian online shop, guarded by Upgrade Gate.

A customer leaves a voice note (Hindi, Hinglish or English) with their order number, pincode and city.
The app asks Meta Muse Spark to turn it into an order, using exactly the model in release/model.json and
exactly the prompt the gate tests (audio-synth "extract" tasks), so the gate's verdict applies to this app.

    PYTHONPATH=. .venv/bin/python -m voiceorder.server        # http://127.0.0.1:5192 (API only)

The web app (web/, #/voiceorder) talks to it through the Vite dev server, which starts it for you.

Endpoints
  GET  /api/voiceorder/config                         shipping + candidate model, sample notes
  POST /api/voiceorder/parse?model=<spec>&sample=<id> parse a sample note (saved answers reused: free)
  POST /api/voiceorder/parse?model=<spec>             parse an uploaded WAV note (body = audio/wav, ~$0.005)
Only the shipping and candidate models are allowed, every paid call goes through the spending cap,
and uploaded notes are never stored.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate.behaviour import ABSTAIN  # noqa: E402
from upgrade_gate.cli import parse_candidate  # noqa: E402
from upgrade_gate.client import ModelClient, build_messages  # noqa: E402
from upgrade_gate.packs import load_pack  # noqa: E402
from upgrade_gate.packs.audio_synth import ASK  # noqa: E402
from upgrade_gate.scorers import extract_json, score_text  # noqa: E402
from upgrade_gate.spend import SpendCapError  # noqa: E402

CANDIDATE = "spark-1.3@low"
PR_URL = "https://github.com/UtsavInTech/upgrade-gate/pull/1"
PROMPT = "Listen to the attached audio. " + ASK["extract"]
MAX_BODY = 10_000_000


def shipping_model() -> str:
    with open(os.path.join(ROOT, "release", "model.json"), encoding="utf-8") as f:
        return json.load(f)["model"]


_SAMPLES: Dict[str, object] = {}


def samples() -> Dict[str, object]:
    """The spoken order notes from the audio pack, keyed by task id (same tasks the gate replays)."""
    if not _SAMPLES:
        for t in load_pack("audio-clips"):
            if t.meta.get("kind") == "extract":
                _SAMPLES[t.id] = t
    return _SAMPLES


def checks(order: Optional[dict], text: str) -> dict:
    """What a typical shop backend validates before saving an order. None of these can tell a
    correctly shaped wrong pincode from the right one; that is the gap the gate covers."""
    if ABSTAIN.search(text or ""):
        return {"status": "ask_customer", "message": "The model says it couldn't hear the note. Ask the customer to type it.",
                "fields": {}}
    if not isinstance(order, dict):
        return {"status": "rejected", "message": "No order could be read from the reply.", "fields": {}}
    on = str(order.get("order_number") or "").strip()
    pin = str(order.get("pincode") or "").strip()
    city = str(order.get("city") or "").strip()
    fields = {
        "order_number": bool(re.fullmatch(r"\d{4,10}", on)),
        "pincode": bool(re.fullmatch(r"[1-9]\d{5}", pin)),
        "city": bool(city),
    }
    if all(fields.values()):
        return {"status": "saved", "message": "Passes the shop's checks. The order would be saved.", "fields": fields}
    if not (on or pin or city):
        return {"status": "rejected", "message": "Every field is blank. The form rejects it, so the order is lost.",
                "fields": fields}
    return {"status": "rejected", "message": "Some fields fail the format check. The form rejects it.", "fields": fields}


def parse(client: ModelClient, model_spec: str, task=None, wav: Optional[bytes] = None) -> dict:
    cand = parse_candidate(model_spec)
    if task is not None:
        messages = build_messages(task)
        salt = "rep0"  # the first try from the saved run: same task, prompt and settings, so it is reused
    else:
        part = {"type": "input_audio", "input_audio": {"data": base64.b64encode(wav).decode("ascii"), "format": "wav"}}
        messages = [{"role": "user", "content": [{"type": "text", "text": PROMPT}, part]}]
        salt = "live-%d" % time.time_ns()  # never reuse an answer for a new recording
    t0 = time.monotonic()
    res = client.chat(cand.model_id, messages, cand.params, cache_salt=salt)
    text = (res.text or "").strip()
    try:
        order, _ = extract_json(text) if text else (None, False)
    except ValueError:
        order = None
    out = {"model": model_spec, "text": text, "error": res.error, "order": order if isinstance(order, dict) else None,
           "checks": checks(order if isinstance(order, dict) else None, text),
           "cost_usd": 0.0 if res.cached else round(res.cost_usd, 5), "reused": res.cached,
           "latency_ms": res.latency_ms if not res.cached else int((time.monotonic() - t0) * 1000)}
    if task is not None:
        ok = score_text(task, text)[0] if text else False
        out["truth"] = {"correct": bool(ok), "expected": {k: (v[0] if isinstance(v, list) else v)
                                                          for k, v in (task.reference or {}).items()}}
    return out


class Handler(BaseHTTPRequestHandler):
    client: ModelClient = None  # set in serve()

    def log_message(self, fmt, *args):  # quiet
        pass

    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/api/voiceorder/config":
            return self._json(404, {"error": "not found"})
        items = []
        for tid, t in sorted(samples().items(), key=lambda kv: (kv[1].lang != "hi", kv[0])):
            clip = os.path.splitext(os.path.basename(t.attachments[0]))[0]
            items.append({"id": tid, "lang": t.lang, "transcript": t.meta.get("transcript"),
                          "audio": "att/%s.m4a" % clip})
        self._json(200, {"shipping": shipping_model(), "candidate": CANDIDATE, "pr": PR_URL, "samples": items})

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/api/voiceorder/parse":
            return self._json(404, {"error": "not found"})
        q = parse_qs(url.query)
        model = (q.get("model") or [""])[0]
        if model not in (shipping_model(), CANDIDATE):
            return self._json(400, {"error": "model must be the shipping model or %s" % CANDIDATE})
        sample = (q.get("sample") or [""])[0]
        try:
            if sample:
                task = samples().get(sample)
                if task is None:
                    return self._json(400, {"error": "unknown sample"})
                return self._json(200, parse(self.client, model, task=task))
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 44 or n > MAX_BODY:
                return self._json(400, {"error": "send a WAV body up to 10 MB"})
            wav = self.rfile.read(n)
            if wav[:4] != b"RIFF":
                return self._json(400, {"error": "not a WAV file"})
            return self._json(200, parse(self.client, model, wav=wav))
        except SpendCapError as e:
            return self._json(402, {"error": "spending cap reached: %s" % e})


def serve(port: int = 5192, client: Optional[ModelClient] = None) -> ThreadingHTTPServer:
    Handler.client = client or ModelClient(max_concurrency=4)
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    port = int(os.environ.get("VOICEORDER_PORT", "5192"))
    srv = serve(port)
    print("VoiceOrder API on http://127.0.0.1:%d (shipping %s, candidate %s)" % (port, shipping_model(), CANDIDATE),
          flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
