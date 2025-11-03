#!/bin/bash
# Manual script to sync a GitHub Secret to GCP Secret Manager
# Usage: ./sync-github-secret-to-gcp.sh SECRET_NAME SECRET_VALUE

set -euo pipefail

SECRET_NAME="${1:-}"
SECRET_VALUE="${2:-}"

if [[ -z "$SECRET_NAME" ]]; then
  echo "❌ Error: Secret name required"
  echo "Usage: $0 SECRET_NAME SECRET_VALUE"
  echo ""
  echo "Example:"
  echo "  $0 HUGGINGFACE_TOKEN \"your-token-here\""
  exit 1
fi

if [[ -z "$SECRET_VALUE" ]]; then
  echo "❌ Error: Secret value required"
  echo "Usage: $0 SECRET_NAME SECRET_VALUE"
  exit 1
fi

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ Error: GCP_PROJECT_ID not set and unable to get from gcloud config"
  echo "   Please set: export GCP_PROJECT_ID=your-project-id"
  exit 1
fi

echo "🔄 Syncing ${SECRET_NAME} to GCP Secret Manager"
echo "   Project: ${PROJECT_ID}"
echo ""

# Create secret if it doesn't exist
if ! gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "📝 Creating ${SECRET_NAME} secret..."
  gcloud secrets create "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --replication-policy="automatic"
  echo "✅ Secret created"
fi

# Add secret version
echo "📤 Adding secret version..."
echo -n "${SECRET_VALUE}" | gcloud secrets versions add "${SECRET_NAME}" \
  --project="${PROJECT_ID}" \
  --data-file=-

echo ""
echo "✅ ${SECRET_NAME} synced successfully to GCP Secret Manager"
echo ""
echo "📋 Verify:"
echo "   gcloud secrets versions access latest --secret=${SECRET_NAME} --project=${PROJECT_ID}"

