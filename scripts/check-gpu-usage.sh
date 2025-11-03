#!/bin/bash
# Check GPU usage across Cloud Run services in europe-west1

set -e

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${REGION:-europe-west1}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: GCP_PROJECT_ID environment variable not set"
  exit 1
fi

echo "🔍 Checking GPU usage in ${REGION}..."
echo ""

# List all Cloud Run services in the region
echo "📋 Cloud Run services in ${REGION}:"
gcloud run services list --region=${REGION} --project=${PROJECT_ID} --format="table(metadata.name,status.url)"

echo ""
echo "🔍 Checking which services have GPUs configured..."

# Check each service for GPU configuration
for SERVICE in $(gcloud run services list --region=${REGION} --project=${PROJECT_ID} --format="value(metadata.name)"); do
  echo ""
  echo "📌 Service: ${SERVICE}"
  GPU_CONFIG=$(gcloud run services describe ${SERVICE} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(spec.template.containers[0].resources.gpu)" 2>/dev/null || echo "none")
  
  if [ "$GPU_CONFIG" != "none" ] && [ -n "$GPU_CONFIG" ]; then
    echo "   ✅ GPU configured: ${GPU_CONFIG}"
    echo "   ⚠️  This service is using GPU quota!"
  else
    echo "   ❌ No GPU configured"
  fi
done

echo ""
echo "📊 Current GPU Quota:"
gcloud compute project-info describe --project=${PROJECT_ID} \
  --format="table(quotas.metric,quotas.limit,quotas.usage)" \
  --filter="quotas.metric:'NVIDIA_L4_GPUS'" 2>/dev/null || \
  echo "Run: gcloud compute project-info describe --project=${PROJECT_ID} | grep -A5 GPU"

