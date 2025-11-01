#!/bin/bash
# Deploy Gemma GPU Service to Cloud Run
# Region: europe-west1
# GPU: NVIDIA L4 (1 GPU)
# Memory: 16Gi

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="europe-west1"
SERVICE_NAME="gemma-service"
IMAGE_NAME="gemma-service"
GAR_REPO="${GAR_REPO:-docker-repo}"  # Google Artifact Registry repository
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Full image path
IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPO}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "🚀 Deploying Gemma GPU Service to Cloud Run"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${SERVICE_NAME}"
echo "   Image: ${IMAGE_PATH}"

# Build image with Podman
echo ""
echo "📦 Building container image..."
cd "$(dirname "$0")/../backend"
# Build context is ./backend, Dockerfile expects files relative to that
podman build -f Dockerfile.gemma -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Tag for GAR
podman tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_PATH}

# Push to GAR (requires authentication)
echo ""
echo "📤 Pushing to Google Artifact Registry..."
podman push ${IMAGE_PATH}

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_PATH} \
    --region ${REGION} \
    --platform managed \
    --cpu gpu \
    --memory 16Gi \
    --gpu-type nvidia-l4 \
    --gpu-count 1 \
    --port 8080 \
    --timeout 300s \
    --min-instances 0 \
    --max-instances 2 \
    --allow-unauthenticated \
    --set-env-vars "MODEL_NAME=google/gemma-7b-it" \
    --set-secrets "HUGGINGFACE_TOKEN=HUGGINGFACE_TOKEN:latest" \
    || echo "⚠️  Note: Set HUGGINGFACE_TOKEN secret if needed"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Service URL:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format="value(status.url)"
echo ""
echo "🧪 Test health endpoint:"
echo "curl \$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')/healthz"

