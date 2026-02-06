#!/usr/bin/env bash
set -euo pipefail

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
