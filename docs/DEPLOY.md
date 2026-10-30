# Deploying Upgrade Gate on Railway

Live: https://web-production-00176.up.railway.app (project `upgrade-gate`, service `web`, region ams).

One service, one process: `serve.py` serves the built site (`web/dist`) and its API from the same HTTPS origin.
Saved examples and all evidence work without any API key and cost nothing.

## What is already set up

| Setting | Value |
|---|---|
| Source | GitHub `UtsavInTech/upgrade-gate`, branch `main` (deploys on every push) |
| Build | `Dockerfile` (Node stage builds `web/`, Python 3.11 runtime), from `railway.json` |
| Start | `python serve.py`, listens on `0.0.0.0:$PORT` |
| Healthcheck | `GET /healthz` → `{"ok": true, "live": false}` |
| Replicas | 1 (keeps one coherent spend ledger) |
| Volume | `upgrade-gate-data` mounted at `/data` |
| Variables | `PORT=8080`, `DATA_DIR=/data`, `LIVE_INFERENCE=0`, `RECORDINGS_MAX_MB=500` |
| Domain | `web-production-00176.up.railway.app` → port 8080 |

What goes on the volume (`/data`): research recordings from `#/record` (`audio-real/`), blind-audit labels
(`audit/`), the spend ledger (`spend/ledger.jsonl`) and the response cache (`cache/`). These survive restarts and
redeploys. Audio sent for a live VoiceOrder request is never stored.

## From scratch (another account)

1. Railway → New project → Deploy from GitHub repo → this repo. Railway reads `railway.json` and builds the Dockerfile.
2. Service → Variables: `PORT=8080`, `DATA_DIR=/data`, `LIVE_INFERENCE=0`.
3. Service → Settings → Volumes → add a volume mounted at `/data`.
4. Service → Settings → Networking → Generate domain (target port 8080).
5. Check `https://<domain>/healthz`, then open `https://<domain>/#/voiceorder`.

## Turning on live requests (optional, paid)

Visitors can then record their own note on `#/voiceorder`. Each note costs about $0.02.

- Add `MODEL_API_KEY` (a Railway secret; it never reaches the browser), `LIVE_INFERENCE=1`, and a low
  `MAX_TOTAL_SPEND_USD` (for example `5`). Every call reserves its worst-case cost against that cap first.
- `LIVE_REQUESTS_PER_HOUR` (default 6) limits each visitor.
- Saved examples stay free and deterministic either way: a missing saved answer returns an error, never a paid call.

## Local check of the production server

```bash
npm --prefix web run build
DATA_DIR=./data-runtime .venv/bin/python serve.py
```

Then open http://127.0.0.1:8080. `tests/test_serve.py` covers the routes.
