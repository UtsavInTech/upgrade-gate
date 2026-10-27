# Canary (H5)

Sends the same 50 prompts to pinned Muse Spark model IDs 4 times a day and checks every answer with fixed rules (no AI judge). Over ~8 days this shows whether a pinned version changes behaviour (H5), whether answers depend on time of day / server load (H5b), and how Hindi compares with matched English prompts (H6).

## The suite — [prompts.json](prompts.json)

| Group | Count | What's checked |
|---|---|---|
| Math / logic (`m`) | 10 | Bare number or exact answer |
| JSON extraction (`j`) | 10 | Valid JSON + exact field values |
| Instruction following (`i`) | 10 | Bullets, word count, no commas, all caps, line count, exact echo |
| Code / format (`c`) | 7 | Exact output (includes `0.1 + 0.2`) |
| Over-refusal (`s`) | 3 | Harmless questions must not be refused |
| Hindi / Hinglish (`h`) | 10 | 9 have a matched English twin (`pair` field) for H6 |

Each prompt has a `gold` answer. [test_checks.py](test_checks.py) checks that every gold answer passes and that refusals and wrong answers fail.

**Freeze the suite once the canary starts.** Changing prompts mid-study breaks the day-to-day comparison. Fixing a *check* is fine, because `summarize.py` re-scores old raw text.

## Before Oct 28 (only you can do these)

1. **First API call.** Confirm the base URL, whether the API is OpenAI-compatible, and the exact pinned model IDs. Check whether Muse Spark 1.1 still works (it's marked deprecated).
2. **Smoke test locally:**
   ```bash
   export MODEL_API_KEY=...            # never commit this
   export MODEL_API_BASE=https://...   # from Meta's docs
   export CANARY_MODELS=muse-spark-1.2,muse-spark-1.3
   python3 canary/run.py --limit 3
   ```
   Open the saved `-smoke.jsonl` and read the raw `text`. If a reasoning model's answers are cut off, raise `CANARY_MAX_TOKENS`.
3. **Turn on the schedule** in the GitHub repo settings:
   - Secrets → Actions → add `MODEL_API_KEY` (your Meta key, or your OpenRouter key)
   - Variables → Actions → add `MODEL_API_BASE` (`https://openrouter.ai/api/v1` for OpenRouter) and `CANARY_MODELS` (e.g. `muse-spark-1.2,muse-spark-1.3`; the `meta/` prefix is added for OpenRouter) (optional: `CANARY_EXTRA_JSON`, e.g. `{"reasoning_effort":"low"}`)
   - Actions tab → **canary** → **Run workflow** once to check it works.
4. Set a spend alert on your Meta account.

## Cost

50 prompts × 3 repeats × N models = 150·N calls per run, ×4 runs a day. With 2 models that's 1,200 calls/day, about 9,600 over 8 days. Prompts are short (about 50 input tokens), so cost is mostly output tokens and reasoning tokens. Check `usage` in the smoke file and multiply before you switch it on.

## Reading results

```bash
python3 canary/summarize.py
```
Writes [reports/summary.md](reports/summary.md) with:
- pass rate by day and by IST hour
- Hindi vs matched English
- the **noise floor**: how often the same prompt gives different answers inside one run
- every prompt whose most common answer changed between days

Drift only counts if it's bigger than the noise floor. API errors are logged and left out of pass rates.

## What each row stores

Timestamp, IST hour, model ID asked for and model ID returned, `system_fingerprint`, raw text, pass/fail + reason, token usage, latency, all response headers, retry count. The run order is shuffled with a recorded seed.
