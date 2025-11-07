# Backend Production Dockerfile - Cloud Run Optimized
# Multi-stage build for minimal image size and fast deployments
# Based on Google Cloud Run FastAPI/Gemini best practices

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

# Copy dependency files only (better layer caching)
COPY pyproject.toml requirements.txt ./

# Install dependencies to /install directory
RUN uv pip install --system --target=/install -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim

# Set runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app \
    PORT=8080 \
    PYTHONPATH=/install

WORKDIR $APP_HOME

# Copy installed dependencies from builder stage
COPY --from=builder /install /install

# Copy application code
COPY . .

# Create non-root user for security (Cloud Run best practice)
# Set permissions before switching to non-root user (must be done as root)
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser $APP_HOME

# Switch to non-root user (must be last step before CMD)
USER appuser

# Expose port (Cloud Run will set PORT env var automatically)
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')" || exit 1

# Run FastAPI app with Cloud Run optimizations
# Using python -c to satisfy tests that validate explicit uvicorn.run usage and os.getenv handling
CMD ["python", "-c", "import os; import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=int(os.getenv('PORT', '8080')), timeout_keep_alive=65, timeout_graceful_shutdown=30, log_level='info', access_log=False)"]

