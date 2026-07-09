#!/usr/bin/env bash
set -e

cd /app
exec /app/.venv/bin/uvicorn homeassistant.addon.server:app --host 0.0.0.0 --port 8080