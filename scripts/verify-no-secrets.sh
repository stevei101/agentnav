#!/bin/bash
# Security verification script to ensure no .env files exist in Git history
# Part of FR#095: Critical Security Fix - Purge .env from Git History

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "======================================"
echo "Secret Security Verification Script"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

echo "1. Checking for .env files in Git history..."
# More efficient approach using git log's built-in filtering
if git log --all --name-only --pretty=format: -- '.env' | grep -q '^.env$'; then
    ENV_COUNT=$(git log --all --name-only --pretty=format: -- '.env' | grep -c '^.env$')
    echo -e "${RED}✗ FAIL: Found $ENV_COUNT .env file(s) in Git history${NC}"
    FAILED=1
    echo "   Run the following to see details:"
    echo "   git log --all --full-history -- .env"
else
    echo -e "${GREEN}✓ PASS: No .env files found in Git history${NC}"
fi

echo ""
echo "2. Verifying .gitignore contains .env pattern..."
if grep -q "^\.env$" .gitignore; then
    echo -e "${GREEN}✓ PASS: .env pattern found in .gitignore${NC}"
else
    echo -e "${RED}✗ FAIL: .env pattern NOT found in .gitignore${NC}"
    FAILED=1
fi

echo ""
echo "3. Checking for .env files in working directory..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠ WARNING: .env file exists in working directory${NC}"
    echo "   This is OK for local development, but ensure it's in .gitignore"
    # Check if git would ignore it
    if git check-ignore .env > /dev/null 2>&1; then
        echo -e "${GREEN}✓ File is properly ignored by Git${NC}"
    else
        echo -e "${RED}✗ FAIL: .env file is NOT ignored by Git!${NC}"
        FAILED=1
    fi
else
    echo -e "${GREEN}✓ PASS: No .env file in working directory${NC}"
fi

echo ""
echo "4. Checking for other sensitive file patterns..."
# Production/development sensitive files (strict check)
PRODUCTION_FILES=(.env.local .env.production .env.development)
FOUND_PRODUCTION=0

# Check production files - these should never be in history
for pattern in "${PRODUCTION_FILES[@]}"; do
    if git log --all --name-only --pretty=format: -- "$pattern" | grep -q "^${pattern}$"; then
        COUNT=$(git log --all --name-only --pretty=format: -- "$pattern" | grep -c "^${pattern}$")
        echo -e "${RED}✗ Found $pattern in Git history ($COUNT occurrences)${NC}"
        echo "   This file may contain production secrets and must be removed from history!"
        FOUND_PRODUCTION=1
        FAILED=1
    fi
done

# Special handling for .env.test - warn but don't fail if it's in .gitignore
# Note: .env.test files typically contain only test data, not production secrets
if git log --all --name-only --pretty=format: -- '.env.test' | grep -q '^.env.test$'; then
    COUNT=$(git log --all --name-only --pretty=format: -- '.env.test' | grep -c '^.env.test$')
    if grep -q "^\.env\.test$" .gitignore 2>/dev/null; then
        echo -e "${YELLOW}⚠ Found .env.test in Git history ($COUNT occurrences)${NC}"
        echo "   This is OK if it only contains test data. Ensure it's never committed again."
        echo "   ✓ .env.test is in .gitignore"
    else
        echo -e "${RED}✗ Found .env.test in Git history ($COUNT occurrences)${NC}"
        echo "   ✗ .env.test is NOT in .gitignore - this is a security risk!"
        FOUND_PRODUCTION=1
        FAILED=1
    fi
fi

if [ "$FOUND_PRODUCTION" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS: No sensitive environment files found in history${NC}"
fi

echo ""
echo "======================================"
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All security checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Security verification FAILED${NC}"
    echo ""
    echo "To fix issues with files in Git history:"
    echo "  1. Install git-filter-repo: pip install git-filter-repo"
    echo "  2. Create a fresh clone (important!): git clone <repo-url> temp-repo"
    echo "  3. cd temp-repo"
    echo "  4. Run: git filter-repo --path .env --invert-paths"
    echo "  5. Force push: git push origin --force --all"
    echo ""
    echo "WARNING: This rewrites history. Coordinate with all team members!"
    exit 1
fi
