"""Production web server for Upgrade Gate (Railway): the built site and its APIs from one origin.

    python serve.py                      # PORT (default 8080), binds 0.0.0.0

Stdlib only, one process. It reuses VoiceOrder's own logic (voiceorder/server.py) and replaces the
Vite dev-only endpoints (recording, audit) with versions that write to DATA_DIR, a Railway volume.

Routes
  GET  /healthz                                  {"ok": true}
  GET  /api/voiceorder/config                    saved samples + answers, the shipping model, live on/off
  POST /api/voiceorder/parse?model=&sample=      a saved sample: answered from the committed export, $0
  POST /api/voiceorder/parse?model=              a new recording (WAV body): only if LIVE_INFERENCE=1
  POST /api/record?speaker=&clip=                a consented research recording -> DATA_DIR/audio-real
  GET  /api/recorded?speaker=                    which lines that speaker has recorded
  GET/POST /api/audit?labeler=                   blind label audit -> DATA_DIR/audit
  everything else                                files from web/dist (index.html for "/")

Saved samples never call a model: a sample with no saved answer is an error, not a paid request.
Live requests are off unless LIVE_INFERENCE=1, rate-limited per client, and go through the same
lifetime spending cap (ledger in DATA_DIR). Keys stay server-side.
"""
from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

DIST = os.environ.get("WEB_DIST", os.path.join(ROOT, "web", "dist"))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(ROOT, "data-runtime"))
LIVE = os.environ.get("LIVE_INFERENCE", "0") == "1"
LIVE_PER_HOUR = int(os.environ.get("LIVE_REQUESTS_PER_HOUR", "6"))  # per client
RECORDINGS_MAX_MB = float(os.environ.get("RECORDINGS_MAX_MB", "500"))
MAX_WAV = 10_000_000
NAME = re.compile(r"^[a-z0-9-]{1,32}$")

# The ledger and response cache live on the volume, so spending survives restarts.
os.environ.setdefault("UPGRADE_GATE_LEDGER", os.path.join(DATA_DIR, "spend", "ledger.jsonl"))
os.environ.setdefault("UPGRADE_GATE_CACHE_DIR", os.path.join(DATA_DIR, "cache"))
os.environ.setdefault("CANARY_BUDGET_USD", "0")  # the canary runs on GitHub, not here

from voiceorder import server as vo  # noqa: E402

mimetypes.add_type("audio/mp4", ".m4a")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("application/json", ".json")


def _load_json(*parts):
    with open(os.path.join(DIST, *parts), encoding="utf-8") as f:
        return json.load(f)


SAVED = _load_json("data", "voiceorder.json")
CLIPS = {r["clip_id"] for f in ("record.json", "record-corrections.json") for r in _load_json("data", f)}
_hits = defaultdict(deque)
_lock = threading.Lock()


def _rate_ok(client: str) -> bool:
    now = time.time()
    with _lock:
        q = _hits[client]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= LIVE_PER_HOUR:
            return False
        q.append(now)
        return True


def _dir_mb(path: str) -> float:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / 1e6


class App(BaseHTTPRequestHandler):
    server_version = "UpgradeGate"
    client = None  # ModelClient, created on the first live request

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path.split("?")[0]))

    # ---------------------------------------------------------------- helpers
    def _send(self, code: int, body: bytes, ctype: str, cache: str = "no-store") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _body(self, limit: int):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > limit:
            return None
        return self.rfile.read(n)

    def _client_id(self) -> str:
        fwd = self.headers.get("X-Forwarded-For")
        return (fwd.split(",")[0].strip() if fwd else self.client_address[0]) or "?"

    # ---------------------------------------------------------------- routing
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url = urlparse(self.path)
        p = url.path
        try:
            if p == "/healthz":
                return self._json(200, {"ok": True, "live": LIVE})
            if p == "/api/voiceorder/config":
                return self._json(200, self._config())
            if p == "/api/recorded":
                return self._recorded(parse_qs(url.query))
            if p == "/api/audit":
                return self._audit_get(parse_qs(url.query))
            if p.startswith("/api/"):
                return self._json(404, {"error": "No such API endpoint: %s" % p})
            return self._static(p)
        except Exception as e:  # noqa: BLE001 - an API error must still be JSON
            return self._json(500, {"error": "Server error: %s" % type(e).__name__})

    def do_POST(self):
        url = urlparse(self.path)
        q = parse_qs(url.query)
        try:
            if url.path == "/api/voiceorder/parse":
                return self._parse(q)
            if url.path == "/api/record":
                return self._record(q)
            if url.path == "/api/audit":
                return self._audit_post(q)
            return self._json(404, {"error": "No such API endpoint: %s" % url.path})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"error": "Server error: %s" % type(e).__name__})

    # ---------------------------------------------------------------- static files
    def _static(self, path: str):
        rel = unquote(path).lstrip("/") or "index.html"
        full = os.path.realpath(os.path.join(DIST, rel))
        if not full.startswith(os.path.realpath(DIST) + os.sep) or not os.path.isfile(full):
            if "." not in os.path.basename(rel):  # an unknown page: the app handles routing (#/...)
                full = os.path.join(DIST, "index.html")
            else:
                return self._send(404, b"Not found", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        cache = "public, max-age=31536000, immutable" if "/assets/" in full else "no-cache"
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype, cache)

    # ---------------------------------------------------------------- VoiceOrder
    def _config(self) -> dict:
        cfg = dict(SAVED)
        cfg["shipping"] = vo.shipping_model()  # read at runtime: never hardcoded
        cfg["candidate"], cfg["route"], cfg["route_url"], cfg["pr"] = vo.CANDIDATE, vo.ROUTE, vo.E9_URL, vo.PR_URL
        cfg["static"] = True  # samples are always the saved answers
        cfg["live"] = LIVE
        return cfg

    def _parse(self, q):
        model = (q.get("model") or [""])[0]
        sample = (q.get("sample") or [""])[0]
        if sample:
            saved = (SAVED.get("results") or {}).get(sample, {}).get(model)
            if saved is None:
                return self._json(404, {"error": "No saved answer for this note and model. Saved examples never "
                                                 "start a paid request; choose another note."})
            return self._json(200, saved)
        if not LIVE:
            return self._json(403, {"error": "Live requests are off on this server. Saved examples work; to try "
                                             "your own voice, run VoiceOrder locally (see the README)."})
        if model not in (vo.shipping_model(), vo.CANDIDATE, vo.ROUTE):
            return self._json(400, {"error": "Unknown model."})
        if not _rate_ok(self._client_id()):
            return self._json(429, {"error": "Too many live requests from you this hour. Try a saved example."})
        wav = self._body(MAX_WAV)
        if not wav or wav[:4] != b"RIFF":
            return self._json(400, {"error": "Send a WAV recording up to 10 MB."})
        if App.client is None:
            from upgrade_gate.client import ModelClient
            App.client = ModelClient(max_concurrency=2)
        try:
            return self._json(200, vo.parse(App.client, model, wav=wav))
        except vo.SpendCapError:
            return self._json(402, {"error": "This demo's spending cap is reached. Saved examples still work."})

    # ---------------------------------------------------------------- research recordings
    def _record(self, q):
        speaker = (q.get("speaker") or [""])[0].lower()
        clip = (q.get("clip") or [""])[0]
        if not NAME.match(speaker) or clip not in CLIPS:
            return self._json(400, {"error": "Unknown speaker name or line."})
        base = os.path.join(DATA_DIR, "audio-real")
        if _dir_mb(base) > RECORDINGS_MAX_MB:
            return self._json(507, {"error": "Recording storage is full. Use Download all instead."})
        wav = self._body(MAX_WAV)
        if not wav or len(wav) < 44 or wav[:4] != b"RIFF":
            return self._json(400, {"error": "Not a WAV recording."})
        folder = os.path.join(base, speaker)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, clip + ".wav"), "wb") as f:
            f.write(wav)
        with open(os.path.join(base, "manifest.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"speaker": speaker, "clip_id": clip, "wav": "data/audio-real/%s/%s.wav" % (speaker, clip),
                                "ts": datetime.now(timezone.utc).isoformat(), "source": "web"}) + "\n")
        return self._json(200, {"ok": True})

    def _recorded(self, q):
        speaker = (q.get("speaker") or [""])[0].lower()
        folder = os.path.join(DATA_DIR, "audio-real", speaker)
        done = sorted(f[:-4] for f in os.listdir(folder) if f.endswith(".wav")) \
            if NAME.match(speaker) and os.path.isdir(folder) else []
        return self._json(200, done)

    # ---------------------------------------------------------------- label audit
    def _audit_file(self, q):
        labeler = (q.get("labeler") or [""])[0].lower()
        return os.path.join(DATA_DIR, "audit", "labels-%s.jsonl" % labeler) if NAME.match(labeler) else None

    def _audit_get(self, q):
        path = self._audit_file(q)
        if not path:
            return self._json(400, {"error": "Bad labeler name."})
        out = {}
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                if line.strip():
                    r = json.loads(line)
                    out[r["id"]] = r["label"]
        return self._json(200, out)

    def _audit_post(self, q):
        path = self._audit_file(q)
        raw = self._body(10_000)
        try:
            r = json.loads(raw or b"")
        except ValueError:
            r = None
        ok = ("correct", "abstain", "blank", "wrong", "unsure")
        if not path or not isinstance(r, dict) or not re.match(r"^a\d{2}$", str(r.get("id"))) or r.get("label") not in ok:
            return self._json(400, {"error": "Bad label."})
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": r["id"], "label": r["label"], "note": str(r.get("note") or "")[:300],
                                "ts": datetime.now(timezone.utc).isoformat()}) + "\n")
        return self._json(200, {"ok": True})


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    os.makedirs(DATA_DIR, exist_ok=True)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), App)
    print("Upgrade Gate on 0.0.0.0:%d (live inference %s, data in %s)" % (port, "ON" if LIVE else "off", DATA_DIR),
          flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
