#!/bin/bash
# Setup Branch Protection for Main Branch
# Implements FR#100: Comprehensive GitHub Status Checks for All Branches

set -euo pipefail

REPO="stevei101/agentnav"
BRANCH="main"

echo "🔒 Setting up branch protection for ${BRANCH} branch"
echo ""

# Read required checks from documentation
REQUIRED_CHECKS=(
  "CODE_QUALITY"
  "SECURITY_AUDIT"
  "INFRA_VERIFICATION"
)

echo "Required status checks:"
for check in "${REQUIRED_CHECKS[@]}"; do
  echo "  ✓ ${check}"
done
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
  echo "❌ Error: GitHub CLI (gh) is not installed"
  echo "   Install from: https://cli.github.com/"
  exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
  echo "❌ Error: Not authenticated to GitHub"
  echo "   Run: gh auth login"
  exit 1
fi

echo "📋 Configuring branch protection..."
echo ""

# Create or update branch protection rule
# Note: This uses the GitHub API directly as gh CLI may not have full support
echo "⚠️  Manual setup required via GitHub UI:"
echo ""
echo "1. Go to: https://github.com/${REPO}/settings/branches"
echo "2. Click 'Add rule' or edit existing rule for '${BRANCH}'"
echo "3. Configure the following:"
echo ""
echo "   Branch name pattern: ${BRANCH}"
echo ""
echo "   ✅ Enable 'Require a pull request before merging'"
echo "      - Required approving reviews: 1"
echo "      - Dismiss stale pull request approvals when new commits are pushed"
echo ""
echo "   ✅ Enable 'Require status checks to pass before merging'"
echo "      - Required status checks:"
for check in "${REQUIRED_CHECKS[@]}"; do
  echo "        • ${check}"
done
echo "      - Require branches to be up to date before merging"
echo ""
echo "   ✅ Enable 'Require conversation resolution before merging'"
echo ""
echo "   ✅ Enable 'Do not allow bypassing the above settings'"
echo ""
echo "4. Click 'Create' or 'Save changes'"
echo ""
echo "📝 API Alternative (requires admin permissions):"
echo ""
echo "curl -X PUT \\"
echo "  -H \"Authorization: token \${GITHUB_TOKEN}\" \\"
echo "  -H \"Accept: application/vnd.github+json\" \\"
echo "  https://api.github.com/repos/${REPO}/branches/${BRANCH}/protection \\"
echo "  -d '{"
echo "    \"required_status_checks\": {"
echo "      \"strict\": true,"
echo "      \"contexts\": ["
for i in "${!REQUIRED_CHECKS[@]}"; do
  if [ $i -eq $((${#REQUIRED_CHECKS[@]} - 1)) ]; then
    echo "        \"${REQUIRED_CHECKS[$i]}\""
  else
    echo "        \"${REQUIRED_CHECKS[$i]}\","
  fi
done
echo "      ]"
echo "    },"
echo "    \"enforce_admins\": true,"
echo "    \"required_pull_request_reviews\": {"
echo "      \"required_approving_review_count\": 1,"
echo "      \"dismiss_stale_reviews\": true,"
echo "      \"require_code_owner_reviews\": false"
echo "    },"
echo "    \"restrictions\": null"
echo "  }'"
echo ""

echo "✅ Branch protection documentation complete"
echo ""
echo "📚 See docs/CONTRIBUTION_QUALITY_GATES.md for full details"

