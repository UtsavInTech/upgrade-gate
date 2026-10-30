"""Speech to text with Meta's muse-voice-transcribe-1.0 (file endpoint, POST /v1/asr/transcribe).

Used by the "transcribe route": clip -> transcript -> Spark on text. Every call goes through the
same lifetime spending cap as chat calls, and every transcript is cached on disk, so reruns are free.

  from upgrade_gate.transcribe import transcribe
  t = transcribe("data/audio-synth/audio-extract-00-hi.wav", attempt=0)
  t["transcript"], t["cost_usd"], t["latency_ms"]

Price: $3.00 per 1,000 minutes of audio (Meta model page, Sep 2026), billed on audio length.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.error
import urllib.request
import uuid
import wave
from typing import Dict, Optional

from . import config, spend

MODEL = "muse-voice-transcribe-1.0"
USD_PER_SECOND = 3.00 / 1000 / 60
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "results", "transcripts")
RETRY = {429, 500, 502, 503, 504}

# The transcribe route (E9): clip -> this model -> transcript -> Spark on text. A candidate named
# "transcribe+spark-1.3@low" means that route. The wording is the one E9 tested; keep it identical.
ROUTE_PREFIX = "transcribe+"
ROUTE_LEAD = ("This is a speech-to-text transcript of a customer's voice note. It may contain recognition "
              "errors, and numbers may be written as words. ")


def route_prompt(instruction: str, transcript: str) -> str:
    """Spark's prompt on the transcribe route: lead line + the task's own instruction + the transcript."""
    return ROUTE_LEAD + instruction + "\n\nTranscript:\n" + transcript


def _seconds(path: str) -> float:
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def _multipart(wav: bytes) -> (bytes, str):
    b = uuid.uuid4().hex
    req = json.dumps({"model": MODEL, "audioEncoding": "WAV", "mode": "PUSH_TO_TALK"})
    body = (("--%s\r\nContent-Disposition: form-data; name=\"request\"\r\n"
             "Content-Type: application/json\r\n\r\n%s\r\n"
             "--%s\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"clip.wav\"\r\n"
             "Content-Type: audio/wav\r\n\r\n") % (b, req, b)).encode() + wav + ("\r\n--%s--\r\n" % b).encode()
    return body, "multipart/form-data; boundary=" + b


def transcribe(path: str, attempt: int = 0, use_cache: bool = True, max_tries: int = 5,
               base_url: Optional[str] = None) -> Dict:
    """Transcribe one WAV. `attempt` separates repeated transcriptions of the same clip in the
    cache (each try of an experiment gets its own transcript). Returns transcript, audio_ms,
    latency_ms, cost_usd, error, cached."""
    with open(path, "rb") as f:
        wav = f.read()
    key = "%s-%d" % (hashlib.sha1(wav).hexdigest()[:16], attempt)
    cpath = os.path.join(CACHE, key + ".json")
    if use_cache and os.path.exists(cpath):
        with open(cpath, encoding="utf-8") as f:
            out = json.load(f)
        out["cached"] = True
        return out

    api_key = config.model_api_key()
    if not api_key:
        raise SystemExit("MODEL_API_KEY is not set. Put it in .env at the repo root (see .env.example).")
    base = (base_url or config.model_api_base()).rstrip("/")
    seconds = _seconds(path)
    guard = spend.ledger() if spend.is_billable(base) else None
    reserved = guard.reserve(seconds * USD_PER_SECOND * 1.5 + 0.0005) if guard else 0.0

    body, ctype = _multipart(wav)
    out: Dict = {"transcript": None, "audio_ms": None, "latency_ms": 0, "cost_usd": 0.0, "error": None}
    t0 = time.monotonic()
    try:
        for i in range(max_tries):
            req = urllib.request.Request(base + "/asr/transcribe", data=body, method="POST", headers={
                "Authorization": "Bearer " + api_key, "Accept": "application/json", "Content-Type": ctype})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.loads(r.read().decode("utf-8"))
                out["transcript"] = data.get("transcript") or ""
                out["audio_ms"] = data.get("audioDurationMs")
                out["session_id"] = data.get("sessionId")
                out["error"] = None
                break
            except urllib.error.HTTPError as e:
                out["error"] = "HTTP %d: %s" % (e.code, e.read().decode("utf-8", "replace")[:300])
                if e.code not in RETRY:
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                out["error"] = "%s: %s" % (type(e).__name__, e)
            time.sleep(min(30, 2 ** i + random.random()))
        out["latency_ms"] = int((time.monotonic() - t0) * 1000)
    finally:
        billed_s = (out["audio_ms"] / 1000.0) if out.get("audio_ms") else (seconds if out["transcript"] is not None else 0)
        out["cost_usd"] = round(billed_s * USD_PER_SECOND, 8)
        if guard:
            guard.settle(reserved, out["cost_usd"], MODEL, source="transcribe")
    out["cached"] = False
    if out["error"] is None:
        os.makedirs(CACHE, exist_ok=True)
        with open(cpath, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
    return out
