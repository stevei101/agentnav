#!/bin/bash
# Quick helper to sync GEMINI_API_KEY from GitHub Secrets to GCP Secret Manager
# This uses GitHub CLI to get the secret value (if possible) or prompts for it

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-linear-archway-476722-v0}"
SECRET_NAME="GEMINI_API_KEY"

echo "🔄 Syncing ${SECRET_NAME} to GCP Secret Manager"
echo "   Project: ${PROJECT_ID}"
echo ""
echo "ℹ️  Note: GitHub Secrets cannot be read via API for security reasons"
echo "   You'll need to copy the value from GitHub Secrets UI"
echo ""
echo "📍 Get your secret from:"
echo "   https://github.com/stevei101/agentnav/settings/secrets/actions"
echo ""
read -sp "Enter ${SECRET_NAME} value: " SECRET_VALUE
echo ""

if [[ -z "$SECRET_VALUE" ]]; then
  echo "❌ Error: Secret value cannot be empty"
  exit 1
fi

echo "📤 Syncing to GCP Secret Manager..."

# Create secret if it doesn't exist
if ! gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "📝 Creating ${SECRET_NAME} secret..."
  gcloud secrets create "${SECRET_NAME}" \
    --project="${PROJECT_ID}" \
    --replication-policy="automatic"
fi

# Add secret version
echo -n "${SECRET_VALUE}" | gcloud secrets versions add "${SECRET_NAME}" \
  --project="${PROJECT_ID}" \
  --data-file=-

echo ""
echo "✅ ${SECRET_NAME} synced successfully!"
echo ""
echo "🔍 Verifying..."
gcloud secrets versions list "${SECRET_NAME}" \
  --project="${PROJECT_ID}" \
  --format="table(name,state,createTime)"

