#!/bin/bash
# Test script to verify CI/CD workflow isolation
# This script validates that workflows trigger correctly based on file changes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "======================================"
echo "CI/CD Workflow Isolation Test"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test 1: Verify paths-ignore in ci.yml
echo "Test 1: Checking paths-ignore in ci.yml..."
if grep -q "paths-ignore:" "$REPO_ROOT/.github/workflows/ci.yml" && \
   grep -q "prompt-vault" "$REPO_ROOT/.github/workflows/ci.yml"; then
    echo -e "${GREEN}✓ PASS: ci.yml has paths-ignore for prompt-vault/**${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL: ci.yml missing paths-ignore for prompt-vault/**${NC}"
    ((FAILED++))
fi

# Test 2: Verify paths-ignore in build.yml
echo "Test 2: Checking paths-ignore in build.yml..."
if grep -q "paths-ignore:" "$REPO_ROOT/.github/workflows/build.yml" && \
   grep -q "prompt-vault" "$REPO_ROOT/.github/workflows/build.yml"; then
    echo -e "${GREEN}✓ PASS: build.yml has paths-ignore for prompt-vault/**${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL: build.yml missing paths-ignore for prompt-vault/**${NC}"
    ((FAILED++))
fi

# Test 3: Verify paths-ignore in terraform.yml
echo "Test 3: Checking paths-ignore in terraform.yml..."
if grep -q "paths-ignore:" "$REPO_ROOT/.github/workflows/terraform.yml" && \
   grep -q "prompt-vault" "$REPO_ROOT/.github/workflows/terraform.yml"; then
    echo -e "${GREEN}✓ PASS: terraform.yml has paths-ignore for prompt-vault/**${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL: terraform.yml missing paths-ignore for prompt-vault/**${NC}"
    ((FAILED++))
fi

# Test 4: Verify build-prompt-vault.yml exists
echo "Test 4: Checking build-prompt-vault.yml exists..."
if [ -f "$REPO_ROOT/.github/workflows/build-prompt-vault.yml" ]; then
    echo -e "${GREEN}✓ PASS: build-prompt-vault.yml exists${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL: build-prompt-vault.yml does not exist${NC}"
    ((FAILED++))
fi

# Test 5: Verify build-prompt-vault.yml has correct path filter
echo "Test 5: Checking build-prompt-vault.yml path filter..."
if [ -f "$REPO_ROOT/.github/workflows/build-prompt-vault.yml" ]; then
    if grep -q "paths:" "$REPO_ROOT/.github/workflows/build-prompt-vault.yml" && \
       grep -q "prompt-vault" "$REPO_ROOT/.github/workflows/build-prompt-vault.yml"; then
        echo -e "${GREEN}✓ PASS: build-prompt-vault.yml has correct path filter${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL: build-prompt-vault.yml missing correct path filter${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ SKIP: build-prompt-vault.yml does not exist${NC}"
fi

# Test 6: Verify YAML syntax for all workflow files
echo "Test 6: Validating YAML syntax..."
YAML_ERRORS=0

for workflow in "$REPO_ROOT/.github/workflows"/*.yml; do
    workflow_name=$(basename "$workflow")
    if ! python3 -c "import yaml; yaml.safe_load(open('$workflow'))" >/dev/null 2>&1; then
        echo -e "${RED}  ✗ Invalid YAML syntax in $workflow_name${NC}"
        ((YAML_ERRORS++))
    fi
done

if [ "$YAML_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS: All workflow files have valid YAML syntax${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL: $YAML_ERRORS workflow file(s) have invalid YAML${NC}"
    ((FAILED++))
fi

# Test 7: Verify no prompt-vault references in agentnav path filters
echo "Test 7: Checking agentnav workflows don't explicitly include prompt-vault..."
EXPLICIT_INCLUDES=0

for workflow in ci.yml build.yml terraform.yml; do
    if [ -f "$REPO_ROOT/.github/workflows/$workflow" ]; then
        # Extract paths: sections (not paths-ignore:) and check for prompt-vault references
        # This verifies that prompt-vault is not explicitly included in the paths filter
        PATHS_SECTION=$(grep -A 10 "^  paths:" "$REPO_ROOT/.github/workflows/$workflow" || true)
        IGNORE_SECTION=$(grep -A 5 "^  paths-ignore:" "$REPO_ROOT/.github/workflows/$workflow" || true)
        
        # If paths section contains prompt-vault but ignore section doesn't, it's an explicit include
        if echo "$PATHS_SECTION" | grep -q "prompt-vault"; then
            if ! echo "$IGNORE_SECTION" | grep -q "prompt-vault"; then
                echo -e "${RED}  ✗ $workflow explicitly includes prompt-vault in paths${NC}"
                ((EXPLICIT_INCLUDES++))
            fi
        fi
    fi
done

if [ "$EXPLICIT_INCLUDES" -eq 0 ]; then
    echo -e "${GREEN}✓ PASS: Agentnav workflows don't explicitly include prompt-vault${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL: Found $EXPLICIT_INCLUDES workflow(s) explicitly including prompt-vault${NC}"
    ((FAILED++))
fi

# Test 8: Verify prompt-vault workflow has quality gate
echo "Test 8: Checking prompt-vault workflow has quality gate..."
if [ -f "$REPO_ROOT/.github/workflows/build-prompt-vault.yml" ]; then
    if grep -q "PROMPT_VAULT_QUALITY_GATE" "$REPO_ROOT/.github/workflows/build-prompt-vault.yml"; then
        echo -e "${GREEN}✓ PASS: build-prompt-vault.yml has PROMPT_VAULT_QUALITY_GATE${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL: build-prompt-vault.yml missing PROMPT_VAULT_QUALITY_GATE${NC}"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠ SKIP: build-prompt-vault.yml does not exist${NC}"
fi

# Summary
echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! CI/CD workflow isolation is properly configured.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review the configuration.${NC}"
    exit 1
fi
