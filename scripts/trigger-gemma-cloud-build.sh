#!/bin/bash
# Trigger Cloud Build for Gemma service to push to Google Artifact Registry
# This script submits a Cloud Build job that builds and pushes the Gemma image to GAR

set -euo pipefail

# Configuration - defaults from Terraform variables
PROJECT_ID="${GCP_PROJECT_ID:-}"
ARTIFACT_REGION="${ARTIFACT_REGION:-europe-west1}"
GAR_REPO="${GAR_REPO:-agentnav-containers}"
SERVICE_NAME="${SERVICE_NAME:-gemma-service}"
REGION="${REGION:-europe-west1}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-}"

# Get project ID if not set
if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
  if [[ -z "$PROJECT_ID" ]]; then
    echo "❌ Error: GCP_PROJECT_ID not set and unable to get from gcloud config"
    echo "   Please set: export GCP_PROJECT_ID=your-project-id"
    exit 1
  fi
  echo "ℹ️  Using project from gcloud config: ${PROJECT_ID}"
fi

# Get service account if not set (try to find Cloud Run service account)
if [[ -z "$SERVICE_ACCOUNT" ]]; then
  SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
  echo "ℹ️  Using default service account: ${SERVICE_ACCOUNT}"
fi

echo "🚀 Triggering Cloud Build for Gemma service"
echo "   Project: ${PROJECT_ID}"
echo "   Artifact Registry: ${ARTIFACT_REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPO}"
echo "   Service: ${SERVICE_NAME}"
echo "   Region: ${REGION}"
echo ""

# Get commit SHA for image tagging
COMMIT_SHA="${COMMIT_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
echo "   Commit SHA: ${COMMIT_SHA}"

# Submit Cloud Build job
gcloud builds submit \
  --config=cloudbuild-gemma.yaml \
  --substitutions=_PROJECT_ID=${PROJECT_ID},_GAR_REPO=${GAR_REPO},_ARTIFACT_REGION=${ARTIFACT_REGION},_SERVICE_NAME=${SERVICE_NAME},_REGION=${REGION},_SERVICE_ACCOUNT=${SERVICE_ACCOUNT},COMMIT_SHA=${COMMIT_SHA} \
  --project="${PROJECT_ID}" \
  --region="${ARTIFACT_REGION}"

echo ""
echo "✅ Cloud Build submitted successfully!"
echo ""
echo "📊 View build status:"
echo "   gcloud builds list --limit=1 --project=${PROJECT_ID} --region=${ARTIFACT_REGION}"
echo ""
echo "📋 Follow logs:"
echo "   gcloud builds log \$(gcloud builds list --limit=1 --format='value(id)' --project=${PROJECT_ID} --region=${ARTIFACT_REGION}) --project=${PROJECT_ID} --region=${ARTIFACT_REGION}"

