"""Write web/public/data/voiceorder.json so VoiceOrder's sample notes work on the hosted (static) site.

Uses only answers already saved in the caches (the first try of the E6 run; for the transcribe route, the
first try of E9). It never calls the
API: a sample with no saved answer for both models is left out and reported.

    PYTHONPATH=. .venv/bin/python scripts/export_voiceorder.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from upgrade_gate.cli import parse_candidate  # noqa: E402
from upgrade_gate.client import ModelClient, build_messages, cache_key  # noqa: E402
from voiceorder import server  # noqa: E402

OUT = os.path.join(ROOT, "web", "public", "data", "voiceorder.json")


class CacheOnly(ModelClient):
    """A client that answers from the cache and refuses to send anything."""

    def chat(self, model_id, messages, params=None, use_cache=True, cache_salt=""):
        key = cache_key(model_id, messages, params, cache_salt, base_url=self.base_url)
        if self._cache_get(key) is None:
            raise LookupError("not cached")
        return super().chat(model_id, messages, params, use_cache=True, cache_salt=cache_salt)


def main() -> None:
    import upgrade_gate.transcribe as tr
    tr.config.model_api_key = lambda: None  # a transcript that isn't cached fails instead of calling the API
    client = CacheOnly(api_key="cache-only")
    shipping, cand, route = server.shipping_model(), server.CANDIDATE, server.ROUTE
    samples, results, missing = [], {}, []
    for tid, t in sorted(server.samples().items(), key=lambda kv: (kv[1].lang != "hi", kv[0])):
        try:
            res = {m: server.parse(client, m, task=t) for m in dict.fromkeys((shipping, cand, route))}
        except (LookupError, SystemExit):
            missing.append(tid)
            continue
        for r in res.values():
            r["latency_ms"] = None  # a replay has no meaningful latency
        clip = os.path.splitext(os.path.basename(t.attachments[0]))[0]
        samples.append({"id": tid, "lang": t.lang, "transcript": t.meta.get("transcript"), "audio": "att/%s.m4a" % clip})
        results[tid] = res
    data = {"shipping": shipping, "candidate": cand, "route": route, "route_url": server.E9_URL, "pr": server.PR_URL, "samples": samples, "results": results,
            "static": True}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote %s: %d samples%s" % (os.path.relpath(OUT, ROOT), len(samples),
                                       (", missing %d: %s" % (len(missing), ", ".join(missing))) if missing else ""))


if __name__ == "__main__":
    main()
