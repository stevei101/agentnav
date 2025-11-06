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

# Copy entrypoint script (before switching to non-root user)
# Build context is ./backend, so entrypoint.sh is at root of context
COPY entrypoint.sh /app/entrypoint.sh

# Create non-root user for security (Cloud Run best practice)
# Set permissions for scripts before switching to non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chmod +x start.sh /app/entrypoint.sh && \
    chown -R appuser:appuser $APP_HOME

# Switch to non-root user
USER appuser

# Expose port (Cloud Run will set PORT env var automatically)
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')" || exit 1

# Run FastAPI app directly (Cloud Run sets PORT env var automatically)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

