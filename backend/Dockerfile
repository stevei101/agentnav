# Backend Development Dockerfile
# Python 3.11+ with uv for fast dependency management

FROM python:3.11-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
# Note: Build context is ./backend, so paths are relative to backend/
COPY pyproject.toml uv.lock* requirements.txt* ./
RUN uv venv && \
    if [ -f requirements.txt ]; then \
        uv pip install --system -r requirements.txt; \
    else \
        uv pip install --system fastapi uvicorn[standard] python-dotenv google-cloud-firestore pydantic; \
    fi

# Development stage
FROM base AS development
EXPOSE 8080

# Copy source code (will be mounted as volume in compose)
# Build context is ./backend, so copy everything from current directory
COPY . .

# Run FastAPI dev server with hot-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

