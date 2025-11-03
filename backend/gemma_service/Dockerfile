# Gemma GPU Service Dockerfile - Cloud Run Optimized
# Multi-stage build for minimal image size and fast deployments
# GPU-enabled container for Cloud Run deployment with NVIDIA L4 GPU
# Region: europe-west1
# GPU: NVIDIA L4 (1 GPU)
# Memory: 16Gi

# Stage 1: Builder - Install dependencies
# Use PyTorch base image with CUDA support for building
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime AS builder

WORKDIR /build

# Install system dependencies needed for build
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to /install directory
# Only install packages not already in the base image to avoid disk space issues
RUN pip install --no-cache-dir --prefix=/install \
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

# Set PYTHONPATH to include installed dependencies from prefix install
# With --prefix=/install, packages are in /install/lib/pythonX.X/site-packages
ENV PYTHONPATH=/install/lib/python3.10/site-packages:$PYTHONPATH

# Install minimal runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Gemma service code
COPY gemma_service/ ./gemma_service/

# Create non-root user for security (Cloud Run best practice)
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app

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

# Run FastAPI app
# Cloud Run sets PORT env var automatically, read it dynamically
CMD python -c "import os; port = int(os.getenv('PORT', 8080)); import uvicorn; uvicorn.run('gemma_service.main:app', host='0.0.0.0', port=port)"
