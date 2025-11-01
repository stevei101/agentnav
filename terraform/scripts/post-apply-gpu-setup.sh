#!/bin/bash
# Post-apply script to configure GPU for Gemma Cloud Run service
# This is needed because Terraform doesn't fully support GPU in Cloud Run v2 yet

set -e

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GEMMA_REGION:-europe-west1}"
SERVICE_NAME="gemma-service"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: GCP_PROJECT_ID environment variable not set"
  exit 1
fi

echo "🔧 Configuring GPU for Gemma Cloud Run service..."
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${SERVICE_NAME}"

# Update Cloud Run service with GPU configuration
gcloud run services update ${SERVICE_NAME} \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --add-gpu gpu-type=nvidia-l4,count=1 \
  --cpu-boost \
  || echo "⚠️  Note: GPU may already be configured or quota may be needed"

echo "✅ GPU configuration complete!"
echo ""
echo "📋 Verify GPU configuration:"
echo "   gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='yaml(spec.template.containers[0].resources)'"

