#!/bin/bash
# Find the correct GAR_REPO value by checking Artifact Registry

set -e

REGION="${REGION:-europe-west1}"
PROJECT_ID="${GCP_PROJECT_ID:-}"

if [ -z "$PROJECT_ID" ]; then
  echo "⚠️  GCP_PROJECT_ID not set, using default project"
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
fi

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Error: Could not determine project ID"
  echo "   Set: export GCP_PROJECT_ID=your-project-id"
  exit 1
fi

echo "🔍 Finding Artifact Registry repositories..."
echo "   Project: ${PROJECT_ID}"
echo "   Region: ${REGION}"
echo ""

# List repositories
REPOS=$(gcloud artifacts repositories list \
  --location=${REGION} \
  --project=${PROJECT_ID} \
  --format="value(name)" 2>/dev/null || echo "")

if [ -z "$REPOS" ]; then
  echo "❌ No repositories found in ${REGION}"
  echo ""
  echo "💡 You may need to:"
  echo "   1. Create repository via Terraform: cd terraform && terraform apply"
  echo "   2. Or create manually:"
  echo "      gcloud artifacts repositories create agentnav-containers \\"
  echo "        --repository-format=docker \\"
  echo "        --location=${REGION} \\"
  echo "        --project=${PROJECT_ID}"
  exit 1
fi

echo "✅ Found repositories:"
echo ""
for REPO in $REPOS; do
  # Extract just the repository ID (last part after the last /)
  REPO_ID=$(echo $REPO | awk -F'/' '{print $NF}')
  echo "   📦 Repository ID: ${REPO_ID}"
  echo "      Full name: ${REPO}"
  echo ""
done

echo "📝 Use this value for GAR_REPO:"
FIRST_REPO=$(echo $REPOS | head -1 | awk -F'/' '{print $NF}')
echo ""
echo "   export GAR_REPO=${FIRST_REPO}"
echo ""

