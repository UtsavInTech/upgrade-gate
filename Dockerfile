# Upgrade Gate: the site and its API in one image (Railway). Linux-only steps; the macOS audio
# tools are never needed here because the demo audio and data exports are committed in web/public.

# 1. Build the web app
FROM node:22-slim AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# 2. Runtime: Python, stdlib server + the upgrade_gate package
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data \
    LIVE_INFERENCE=0
COPY pyproject.toml README.md ./
COPY upgrade_gate/ upgrade_gate/
RUN pip install --quiet .
COPY voiceorder/ voiceorder/
COPY release/ release/
COPY serve.py ./
COPY --from=web /app/web/dist web/dist
# Runs as root: Railway mounts volumes owned by root, and the app writes to DATA_DIR on the volume.
RUN mkdir -p /data
EXPOSE 8080
CMD ["python", "serve.py"]
