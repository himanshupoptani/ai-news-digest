#!/bin/sh
# Railway startup script — reads $PORT env var properly
PORT=${PORT:-8000}
echo "Starting server on port $PORT"
exec uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 1
