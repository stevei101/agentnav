# Gemma GPU Service Dockerfile - Cloud Run Optimized
# Multi-stage build for minimal image size and fast deployments
# GPU-enabled container for Cloud Run deployment with NVIDIA L4 GPU
# Region: europe-west1
# GPU: NVIDIA L4 (1 GPU)
# Memory: 16Gi
#
# Multi-stage build strategy:
# 1. Builder stage: Install all dependencies and build artifacts
# 2. Runtime stage: Copy only necessary files for a slim final image

# Stage 1: Builder - Install dependencies
# Use PyTorch base image with CUDA support for building
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime AS builder

WORKDIR /build

# Install system dependencies needed for build
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to /install directory
# Only install packages not already in the base image to avoid disk space issues
RUN pip install --no-cache-dir --target=/install \
    transformers>=4.40.0 \
    accelerate>=0.30.0 \
    bitsandbytes>=0.41.0 \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.30.0 \
    pydantic>=2.0.0 \
    python-dotenv>=1.0.0 \
    huggingface-hub>=0.23.0

# Stage 2: Runtime - Minimal production image
# Use the same PyTorch base for runtime (GPU support required)
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime AS runtime

WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /install /install

# Set PYTHONPATH to include installed dependencies
ENV PYTHONPATH=/install:$PYTHONPATH

# Install minimal runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Gemma service code
COPY gemma_service/ ./gemma_service/

# Copy entrypoint script and make it executable
COPY gemma_service/entrypoint.sh /app/entrypoint.sh

# Create non-root user for security (Cloud Run best practice)
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MODEL_NAME=google/gemma-7b-it

# Expose port (Cloud Run sets PORT env var automatically)
EXPOSE 8080

# Health check (Cloud Run uses this)
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

# Run FastAPI app with entrypoint script for proper signal handling
ENTRYPOINT ["/app/entrypoint.sh"]
