# Gemma GPU Service Dockerfile
# GPU-enabled container for Cloud Run deployment with NVIDIA L4 GPU
# Region: europe-west1
# GPU: NVIDIA L4 (1 GPU)
# Memory: 16Gi

# Use PyTorch base image with CUDA support
# This image includes PyTorch with CUDA 12.1 support
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install additional Python dependencies (PyTorch already in base image)
# Only install packages not already in the base image to avoid disk space issues
RUN pip install --no-cache-dir \
    transformers>=4.40.0 \
    accelerate>=0.30.0 \
    bitsandbytes>=0.41.0 \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.30.0 \
    pydantic>=2.0.0 \
    python-dotenv>=1.0.0 \
    huggingface-hub>=0.23.0

# Copy Gemma service code
COPY gemma_service/ ./gemma_service/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV MODEL_NAME=google/gemma-7b-it

# Expose port (Cloud Run sets PORT env var automatically)
EXPOSE 8080

# Health check (Cloud Run uses this)
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

# Run FastAPI app
# Cloud Run sets PORT env var automatically, read it dynamically
CMD python -c "import os; port = int(os.getenv('PORT', 8080)); import uvicorn; uvicorn.run('gemma_service.main:app', host='0.0.0.0', port=port)"

