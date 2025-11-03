#!/bin/bash
# Entrypoint script for Gemma GPU Service
# Handles proper startup with signal handling and environment variable validation

set -e

# Get PORT from environment, default to 8080
PORT=${PORT:-8080}

# Validate PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT must be a valid number, got: $PORT" >&2
    exit 1
fi

echo "Starting Gemma GPU Service..."
echo "  Host: 0.0.0.0"
echo "  Port: $PORT"
echo "  Model: ${MODEL_NAME:-google/gemma-7b-it}"
echo "  8-bit Quantization: ${USE_8BIT_QUANTIZATION:-false}"

# Run uvicorn with proper signal handling
# The 'exec' ensures the uvicorn process replaces the shell process
# This allows Docker to properly send signals (SIGTERM) to uvicorn
exec uvicorn gemma_service.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --access-log
