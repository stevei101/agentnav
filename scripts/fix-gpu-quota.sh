#!/bin/bash
# Fix GPU quota exceeded error by checking and updating existing services

set -e

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-gemma-service}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: GCP_PROJECT_ID environment variable not set"
  exit 1
fi

echo "🔧 Fixing GPU Quota Issue"
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo "   Service: ${SERVICE_NAME}"
echo ""

# Check if service exists
if gcloud run services describe ${SERVICE_NAME} --region=${REGION} --project=${PROJECT_ID} &>/dev/null; then
  echo "✅ Service '${SERVICE_NAME}' exists"
  
  # Check current GPU configuration
  echo ""
  echo "🔍 Checking current GPU configuration..."
  GPU_COUNT=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(spec.template.containers[0].resources.gpu)" 2>/dev/null || echo "0")
  
  if [ -n "$GPU_COUNT" ] && [ "$GPU_COUNT" != "0" ]; then
    echo "   ⚠️  Service already has GPU configured: ${GPU_COUNT}"
    echo ""
    echo "💡 Options:"
    echo "   1. Update existing service (recommended)"
    echo "   2. Remove GPU from existing service first, then redeploy"
    echo ""
    read -p "Update existing service? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "🔄 Updating existing service (without changing GPU)..."
      echo "   (Use deploy-gemma.sh to update image only)"
      exit 0
    fi
  else
    echo "   ✅ Service exists but has no GPU"
    echo "   This means GPU quota is used by another service"
  fi
else
  echo "❌ Service '${SERVICE_NAME}' does not exist"
  echo "   Checking for other services using GPU..."
fi

echo ""
echo "🔍 Finding services with GPU configuration..."

# Find all services with GPUs
FOUND_GPU=false
while IFS= read -r SERVICE; do
  GPU_CONFIG=$(gcloud run services describe "${SERVICE}" \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(spec.template.containers[0].resources.gpu)" 2>/dev/null || echo "")
  
  if [ -n "$GPU_CONFIG" ] && [ "$GPU_CONFIG" != "" ] && [ "$GPU_CONFIG" != "0" ]; then
    echo "   ⚠️  Found: ${SERVICE} is using GPU"
    FOUND_GPU=true
    
    echo ""
    echo "💡 Solution: Remove GPU from ${SERVICE} first"
    echo ""
    read -p "Remove GPU from ${SERVICE}? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "🔄 Removing GPU from ${SERVICE}..."
      gcloud run services update "${SERVICE}" \
        --region=${REGION} \
        --project=${PROJECT_ID} \
        --clear-gpu \
        --cpu 4 \
        || echo "⚠️  Failed to remove GPU (may need manual removal)"
      
      echo "✅ GPU removed. You can now deploy gemma-service."
      exit 0
    fi
  fi
done < <(gcloud run services list --region=${REGION} --project=${PROJECT_ID} --format="value(metadata.name)" 2>/dev/null)

if [ "$FOUND_GPU" = false ]; then
  echo "   ✅ No services found with GPU configured"
  echo ""
  echo "💡 Possible causes:"
  echo "   1. Quota is temporarily locked from a recent deployment"
  echo "   2. Quota needs to be increased"
  echo ""
  echo "📋 Check quota and request increase:"
  echo "   gcloud compute project-info describe --project=${PROJECT_ID} | grep GPU"
  echo "   Or visit: https://console.cloud.google.com/iam-admin/quotas"
  echo "   Filter: 'NVIDIA L4 GPUs' in ${REGION}"
fi

