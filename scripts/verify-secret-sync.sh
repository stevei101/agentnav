#!/bin/bash
# Verify that secrets are properly synced from GitHub to GCP Secret Manager

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ Error: GCP_PROJECT_ID not set and unable to get from gcloud config"
  echo "   Please set: export GCP_PROJECT_ID=your-project-id"
  exit 1
fi

echo "🔍 Verifying Secret Sync Status"
echo "   Project: ${PROJECT_ID}"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check secret
check_secret() {
  local secret_name=$1
  local display_name=$2
  
  echo "📋 Checking ${display_name} (${secret_name})..."
  
  # Check if secret exists
  if ! gcloud secrets describe "${secret_name}" --project="${PROJECT_ID}" &>/dev/null; then
    echo -e "   ${RED}❌ Secret does not exist${NC}"
    echo "   Run: terraform apply (or create manually)"
    return 1
  fi
  
  echo -e "   ${GREEN}✅ Secret exists${NC}"
  
  # Check if secret has versions
  local version_count=$(gcloud secrets versions list "${secret_name}" \
    --project="${PROJECT_ID}" \
    --format="value(name)" \
    --filter="state=ENABLED" 2>/dev/null | wc -l | tr -d ' ')
  
  if [[ "$version_count" -eq 0 ]]; then
    echo -e "   ${RED}❌ No versions found${NC}"
    echo "   Run: ./scripts/sync-github-secret-to-gcp.sh ${secret_name} \"your-value\""
    return 1
  fi
  
  echo -e "   ${GREEN}✅ Has ${version_count} version(s)${NC}"
  
  # Check latest version
  local latest_version=$(gcloud secrets versions list "${secret_name}" \
    --project="${PROJECT_ID}" \
    --format="value(name)" \
    --filter="state=ENABLED" \
    --limit=1 2>/dev/null | head -1)
  
  if [[ -n "$latest_version" ]]; then
    local version_date=$(gcloud secrets versions describe "${latest_version}" \
      --project="${PROJECT_ID}" \
      --format="value(createTime)" 2>/dev/null || echo "unknown")
    echo "   Latest version: ${latest_version}"
    echo "   Created: ${version_date}"
  fi
  
  # Check IAM permissions
  echo "   Checking IAM permissions..."
  local iam_count=$(gcloud secrets get-iam-policy "${secret_name}" \
    --project="${PROJECT_ID}" \
    --format="value(bindings.members)" 2>/dev/null | wc -l | tr -d ' ')
  
  if [[ "$iam_count" -gt 0 ]]; then
    echo -e "   ${GREEN}✅ IAM bindings configured (${iam_count})${NC}"
  else
    echo -e "   ${YELLOW}⚠️  No IAM bindings found${NC}"
    echo "   Run: terraform apply to set up IAM"
  fi
  
  echo ""
  return 0
}

# Check required secrets
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_secret "HUGGINGFACE_TOKEN" "Hugging Face Token"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_secret "GEMINI_API_KEY" "Gemini API Key"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_secret "FIRESTORE_CREDENTIALS" "Firestore Credentials"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Summary
echo "📊 Summary:"
echo ""
echo "To sync secrets from GitHub:"
echo "  1. Use GitHub Actions workflow:"
echo "     Actions → Sync Secrets from GitHub to GCP Secret Manager → Run workflow"
echo ""
echo "  2. Use manual script:"
echo "     ./scripts/sync-github-secret-to-gcp.sh SECRET_NAME \"value\""
echo ""
echo "  3. Use gcloud directly:"
echo "     echo -n \"value\" | gcloud secrets versions add SECRET_NAME --data-file=-"
echo ""

