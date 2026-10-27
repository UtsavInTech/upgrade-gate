"""Run the canary suite once against one or more models and save every raw response.

Uses only the Python standard library.

Environment variables:
  MODEL_API_KEY      required. Your Meta Model API key. Never commit it.
  MODEL_API_BASE     API base URL. The request goes to {base}/chat/completions.
                     ASSUMPTION: the Meta Model API is OpenAI-compatible. Check this on
                     your first call. If it isn't, only call_model() needs changing.
  CANARY_MODELS      comma-separated model IDs, e.g. "muse-spark-1.2,muse-spark-1.3".
                     Use the exact pinned IDs from Meta's model list.
  CANARY_REPEATS     repeats per prompt per run (default 3).
  CANARY_MAX_TOKENS  max output tokens (default 400). Set to 0 to leave it out.
  CANARY_EXTRA_JSON  optional JSON merged into each request body,
                     e.g. '{"reasoning_effort": "low"}'.
  CANARY_WORKERS     parallel requests (default 4).

Usage:
  python3 canary/run.py            # full run
  python3 canary/run.py --limit 3  # smoke test on the first 3 prompts, 1 repeat
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from checks import check  # noqa: E402

SYSTEM_PROMPT = "You are a helpful assistant. Follow the user's formatting instructions exactly."
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
MAX_RETRIES = 4


def call_model(base, key, model, prompt, max_tokens, extra):
    """One chat request. Returns a dict with text, usage and transport metadata."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
    }
    if max_tokens:
        body["max_tokens"] = max_tokens
    body.update(extra)
    data = json.dumps(body).encode("utf-8")
    url = base.rstrip("/") + "/chat/completions"

    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
            method="POST",
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
                latency = int((time.time() - t0) * 1000)
                payload = json.loads(raw)
                choice = (payload.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                return {
                    "status": resp.status,
                    "text": msg.get("content"),
                    "finish_reason": choice.get("finish_reason"),
                    "returned_model": payload.get("model"),
                    "system_fingerprint": payload.get("system_fingerprint"),
                    "usage": payload.get("usage"),
                    "latency_ms": latency,
                    "headers": dict(resp.headers.items()),
                    "attempts": attempt,
                    "error": None,
                }
        except urllib.error.HTTPError as e:
            status = e.code
            err = e.read().decode("utf-8", "replace")[:500]
            headers = dict(e.headers.items()) if e.headers else {}
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            status, err, headers = None, repr(e)[:500], {}

        retryable = status in (408, 429, 500, 502, 503, 504) or status is None
        if not retryable or attempt >= MAX_RETRIES:
            return {
                "status": status,
                "text": None,
                "latency_ms": int((time.time() - t0) * 1000),
                "headers": headers,
                "attempts": attempt,
                "error": err,
            }
        time.sleep(min(60, 2 ** attempt + random.random()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the first N prompts, 1 repeat")
    args = ap.parse_args()

    key = os.environ.get("MODEL_API_KEY")
    base = os.environ.get("MODEL_API_BASE")
    models = [m.strip() for m in os.environ.get("CANARY_MODELS", "").split(",") if m.strip()]
    if not key or not base or not models:
        sys.exit("Set MODEL_API_KEY, MODEL_API_BASE and CANARY_MODELS first (see top of run.py).")
    repeats = 1 if args.limit else int(os.environ.get("CANARY_REPEATS", "3"))
    max_tokens = int(os.environ.get("CANARY_MAX_TOKENS", "400"))
    extra = json.loads(os.environ.get("CANARY_EXTRA_JSON", "{}"))
    workers = int(os.environ.get("CANARY_WORKERS", "4"))

    with open(os.path.join(HERE, "prompts.json"), encoding="utf-8") as f:
        prompts = json.load(f)
    if args.limit:
        prompts = prompts[: args.limit]

    started = dt.datetime.now(dt.timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ")
    seed = random.randrange(1 << 30)
    jobs = [(m, p, r) for m in models for p in prompts for r in range(repeats)]
    random.Random(seed).shuffle(jobs)  # random order so position in the run isn't a confound

    out_dir = os.path.join(HERE, "data", started.astimezone(IST).strftime("%Y-%m-%d"))
    os.makedirs(out_dir, exist_ok=True)
    suffix = "-smoke" if args.limit else ""
    out_path = os.path.join(out_dir, "run-%s%s.jsonl" % (run_id, suffix))

    def work(job):
        model, p, rep = job
        t = dt.datetime.now(dt.timezone.utc)
        res = call_model(base, key, model, p["prompt"], max_tokens, extra)
        passed, reason = check(res["text"], p["check"]) if res["text"] is not None else (None, "api error")
        return {
            "run_id": run_id,
            "seed": seed,
            "ts_utc": t.isoformat(),
            "ist_hour": t.astimezone(IST).hour,
            "model": model,
            "prompt_id": p["id"],
            "category": p["category"],
            "lang": p["lang"],
            "pair": p.get("pair"),
            "repeat": rep,
            "request": {"temperature": 0, "max_tokens": max_tokens or None, "extra": extra},
            "passed": passed,
            "reason": "" if passed else reason,
            **res,
        }

    done = errors = passes = 0
    with open(out_path, "w", encoding="utf-8") as out, cf.ThreadPoolExecutor(workers) as pool:
        for row in pool.map(work, jobs):
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            done += 1
            errors += row["passed"] is None
            passes += row["passed"] is True
            if done % 25 == 0 or done == len(jobs):
                print("%d/%d done, %d passed, %d API errors" % (done, len(jobs), passes, errors), flush=True)

    print("Saved", os.path.relpath(out_path, os.path.dirname(HERE)))
    if errors == len(jobs):
        sys.exit("Every call failed. Check the key, base URL and model IDs in the saved file.")


if __name__ == "__main__":
    main()
