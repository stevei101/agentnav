# Gemma GPU Service Dockerfile - Cloud Run Optimized
# Uses pre-built base image for fast deployments
# GPU-enabled container for Cloud Run deployment with NVIDIA L4 GPU
# Region: europe-west1
# GPU: NVIDIA L4 (1 GPU)
# Memory: 16Gi
# Base Image: Built from Dockerfile.base and pushed to GAR as gemma-base:latest

# Use pre-built base image from GAR
# This contains all heavy dependencies (PyTorch, CUDA, Python packages)
ARG BASE_IMAGE_REGION=europe-west1
ARG GCP_PROJECT_ID
ARG GAR_REPO=agentnav-containers
FROM ${BASE_IMAGE_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GAR_REPO}/gemma-base:latest

WORKDIR /app

# Copy Gemma service code
COPY gemma_service/ ./gemma_service/

# Change ownership of app directory to appuser (base image already created the user)
RUN chown -R appuser:appuser /app

# Switch to non-root user (already created in base image)
USER appuser

# Set environment variables (PYTHONUNBUFFERED already set in base image)
ENV PORT=8080 \
    MODEL_NAME=google/gemma-7b-it

# Expose port (Cloud Run sets PORT env var automatically)
EXPOSE 8080

# Health check (Cloud Run uses this)
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:${PORT}/healthz || exit 1

# Run FastAPI app
# Cloud Run sets PORT env var automatically, read it dynamically
CMD python -c "import os; port = int(os.getenv('PORT', 8080)); import uvicorn; uvicorn.run('gemma_service.main:app', host='0.0.0.0', port=port)"
