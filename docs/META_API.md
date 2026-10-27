# Meta Model API — facts we build on

Read from dev.meta.ai/docs on Oct 27, 2026. Re-check before quoting numbers in the submission.

## Basics
- Base URL `https://api.meta.ai/v1`, Bearer auth with `MODEL_API_KEY`.
- Drop-in compatible with the OpenAI SDK (Chat Completions + Responses) and the Anthropic SDK (Messages). We use **Chat Completions**: `POST /v1/chat/completions`.

## Models
| Model ID | Mode | Inputs | Notes |
|---|---|---|---|
| `muse-spark-1.3` | Standard | text, image, video, audio, PDF | Latest. Supports `max` effort. **Docs: audio understanding "not fully supported", quality may be degraded** |
| `muse-spark-1.3-contributor` | Contributor | same | No `max` effort |
| `muse-spark-1.2` | Standard | same | Docs recommend it for audio |
| `muse-spark-1.2-contributor` | Contributor | same | |
| `muse-spark-1.1` | Standard only | same | Deprecated on Artificial Analysis; no date in Meta docs |
| `muse-wonder-1.0` | Standard | | Strongest. Use as the strong judge |
| Muse Spark Open / Glimmer | self-host / hosted provider | | Open weights → cheap judge + $10K open-weights prize |

## Prices (per 1M tokens)
| | Cached in | Input | Output |
|---|---|---|---|
| Spark 1.1 / 1.2 / 1.3 Standard | $0.15 | $1.25 | $4.25 |
| Spark 1.2 / 1.3 **Contributor** | $0.002 | $0.10 | $0.20 |
| Wonder 1.0 | $0.20 | $4.00 | $20.00 |

Contributor is **12.5× cheaper on input and ~21× cheaper on output**, but Meta may train on the content. Use it only for public data.
Reasoning tokens are billed as output tokens.

## Rate limits (per team)
Standard Spark/Wonder: 3,000 RPM, 4M TPM. Contributor: **150 RPM**, 3M TPM.

## Request details (Chat Completions)
- `reasoning_effort`: `minimal | low | medium | high | xhigh | max` (`max` only on 1.3 Standard and Wonder). `none` → HTTP 400. Omitted → the model picks.
- `temperature` 0–2, default 1.0. Docs recommend leaving it unset. Don't send it together with `top_p`.
- `max_completion_tokens` (the deprecated `max_tokens` is still accepted). **Reasoning tokens count toward it.**
- Rejected with HTTP 400: `stop`, `n>1`, `logprobs`, `logit_bias`, `prediction`, `web_search_options`, `modalities`, `audio`. `seed` is deprecated.
- Usage: `prompt_tokens`, `completion_tokens`, `completion_tokens_details.reasoning_tokens`, cached tokens under `prompt_tokens_details.cached_tokens` (OpenAI shape).
- Structured output: `response_format: {"type": "json_schema", "json_schema": {"name", "schema", "strict"}}`.
- Image part: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`, up to 50 images, 50 MB inline.
- PDF part: `{"type": "file", "file": {"filename": "x.pdf", "file_data": "data:application/pdf;base64,..."}}`. Text from the first 100 pages, images of the first 50.

## What this means for the study
- **H3 Contributor vs Standard** is now concrete: the same model at ~1/20 the price. If quality matches, that's a strong cost finding. If it doesn't, the cheap mode is quietly worse.
- **Effort ladder**: `minimal → max` gives 6 levels on 1.3, so we can test whether more effort is ever worse (H4).
- **Meta's own docs admit a 1.3 regression (audio)**. Our gate should catch it unprompted. That's a ready-made validation case for the demo.
