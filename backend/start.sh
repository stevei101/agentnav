#!/bin/bash
# Startup script for Cloud Run backend service
# Optimized for production deployment with proper worker configuration
set -e

# Get PORT from environment variable (Cloud Run sets this automatically)
PORT="${PORT:-8080}"

# Calculate optimal worker count for Cloud Run
# Cloud Run allocates CPU dynamically, so we use 1 worker + async workers
# For Cloud Run, single worker with async is optimal for FastAPI
WORKERS="${WEB_CONCURRENCY:-1}"

echo "🚀 Starting Agentic Navigator Backend on port ${PORT}"
echo "📍 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "👷 Workers: ${WORKERS}"

# Start uvicorn with Cloud Run optimized settings
# --workers: Single worker optimal for Cloud Run's CPU allocation
# --host 0.0.0.0: Required for Cloud Run container networking
# --port: Uses PORT env var from Cloud Run
# --timeout-keep-alive: Increased for Cloud Run's load balancer (default: 5s)
# --timeout-graceful-shutdown: Allows graceful shutdown on SIGTERM
# --log-level: Production logging level
# --no-access-log: Reduce log volume, Cloud Run captures all logs
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --timeout-keep-alive 65 \
    --timeout-graceful-shutdown 30 \
    --log-level info \
    --no-access-log
