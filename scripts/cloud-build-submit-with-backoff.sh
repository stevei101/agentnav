#!/bin/bash
# Cloud Build submission script with exponential backoff for status polling
# This script solves the quota issue by reducing the frequency of build status checks
# Issue: FR#185 - Cloud Build Quota Remediation

set -euo pipefail

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
CONFIG_FILE="${CONFIG_FILE:-cloudbuild-gemma.yaml}"
SUBSTITUTIONS="${SUBSTITUTIONS:-}"
REGION="${REGION:-europe-west1}"

# Backoff configuration
INITIAL_WAIT=5        # Start with 5 second wait
MAX_WAIT=60           # Maximum wait time between checks (1 minute)
BACKOFF_MULTIPLIER=1.5 # Multiply wait time by this factor each iteration
TIMEOUT_MINUTES=20    # Overall timeout in minutes

# Validate required parameters
if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
  if [[ -z "$PROJECT_ID" ]]; then
    echo "❌ Error: GCP_PROJECT_ID not set and unable to get from gcloud config"
    exit 1
  fi
fi

if [[ -z "$SUBSTITUTIONS" ]]; then
  echo "❌ Error: SUBSTITUTIONS environment variable is required"
  echo "   Example: export SUBSTITUTIONS='COMMIT_SHA=abc123,_PROJECT_ID=my-project'"
  exit 1
fi

echo "🚀 Starting Cloud Build with exponential backoff polling"
echo "   Project: ${PROJECT_ID}"
echo "   Config: ${CONFIG_FILE}"
echo "   Region: ${REGION}"
echo "   Timeout: ${TIMEOUT_MINUTES} minutes"
echo ""

# Submit the build asynchronously (--async flag prevents automatic polling)
echo "📤 Submitting Cloud Build job..."
BUILD_OUTPUT=$(gcloud builds submit \
  --config="${CONFIG_FILE}" \
  --substitutions="${SUBSTITUTIONS}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --async \
  --format="value(id)" 2>&1)

# Extract build ID from output
BUILD_ID=$(echo "$BUILD_OUTPUT" | tail -1 | tr -d '[:space:]')

if [[ -z "$BUILD_ID" ]]; then
  echo "❌ Error: Failed to extract build ID from gcloud output"
  echo "Output was: $BUILD_OUTPUT"
  exit 1
fi

echo "✅ Build submitted successfully"
echo "   Build ID: ${BUILD_ID}"
echo ""
echo "🔄 Monitoring build status with exponential backoff..."

# Calculate timeout timestamp
START_TIME=$(date +%s)
TIMEOUT_SECONDS=$((TIMEOUT_MINUTES * 60))
END_TIME=$((START_TIME + TIMEOUT_SECONDS))

# Initialize backoff
WAIT_TIME=$INITIAL_WAIT
CHECK_COUNT=0

# Poll build status with exponential backoff
while true; do
  CHECK_COUNT=$((CHECK_COUNT + 1))
  CURRENT_TIME=$(date +%s)
  
  # Check for timeout
  if [[ $CURRENT_TIME -ge $END_TIME ]]; then
    echo "❌ Error: Build timed out after ${TIMEOUT_MINUTES} minutes"
    exit 1
  fi
  
  # Get build status
  # Use --format to minimize API calls and get only what we need
  BUILD_STATUS=$(gcloud builds describe "${BUILD_ID}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --format="value(status)" 2>/dev/null || echo "ERROR")
  
  ELAPSED=$((CURRENT_TIME - START_TIME))
  ELAPSED_MIN=$((ELAPSED / 60))
  ELAPSED_SEC=$((ELAPSED % 60))
  
  echo "   Check #${CHECK_COUNT} (${ELAPSED_MIN}m ${ELAPSED_SEC}s elapsed): Status = ${BUILD_STATUS}, Next check in ${WAIT_TIME}s"
  
  # Check if build is complete
  case "$BUILD_STATUS" in
    SUCCESS)
      echo ""
      echo "✅ Build completed successfully!"
      echo "   Build ID: ${BUILD_ID}"
      echo "   Total time: ${ELAPSED_MIN}m ${ELAPSED_SEC}s"
      echo "   Total status checks: ${CHECK_COUNT}"
      echo ""
      echo "📋 View full logs:"
      echo "   gcloud builds log ${BUILD_ID} --project=${PROJECT_ID} --region=${REGION}"
      exit 0
      ;;
    FAILURE|CANCELLED|EXPIRED)
      echo ""
      echo "❌ Build failed with status: ${BUILD_STATUS}"
      echo "   Build ID: ${BUILD_ID}"
      echo ""
      echo "📋 View logs for details:"
      echo "   gcloud builds log ${BUILD_ID} --project=${PROJECT_ID} --region=${REGION}"
      exit 1
      ;;
    QUEUED|WORKING)
      # Build is still in progress, continue polling
      ;;
    ERROR)
      echo "❌ Error: Unable to get build status (API error)"
      exit 1
      ;;
    *)
      echo "⚠️  Unknown status: ${BUILD_STATUS}"
      ;;
  esac
  
  # Wait before next check (exponential backoff)
  sleep "$WAIT_TIME"
  
  # Calculate next wait time with exponential backoff
  WAIT_TIME=$(awk "BEGIN {print int($WAIT_TIME * $BACKOFF_MULTIPLIER)}")
  
  # Cap at maximum wait time
  if [[ $WAIT_TIME -gt $MAX_WAIT ]]; then
    WAIT_TIME=$MAX_WAIT
  fi
done
