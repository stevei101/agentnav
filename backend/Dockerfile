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

# Copy entrypoint script first (before changing user)
# Build context is ./backend, so entrypoint.sh is at root of context
COPY entrypoint.sh /app/entrypoint.sh

# Create non-root user for security (Cloud Run best practice)
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser $APP_HOME && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port (Cloud Run will set PORT env var automatically)
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')" || exit 1

# Run FastAPI app with entrypoint script for proper signal handling
ENTRYPOINT ["/app/entrypoint.sh"]

