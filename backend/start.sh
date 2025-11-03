#!/bin/bash
# Startup script for Cloud Run backend service
set -e

# Get PORT from environment variable (Cloud Run sets this automatically)
PORT="${PORT:-8080}"

echo "🚀 Starting Agentic Navigator Backend on port ${PORT}"
echo "📍 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"

# Start uvicorn with the PORT from environment
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --log-level info \
    --no-access-log

# Made with Bob
