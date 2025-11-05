#!/bin/bash
# Test script for Supabase infrastructure changes
# This script validates the Terraform configuration for the Prompt Management App

# Don't exit on error - we want to run all tests
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "Supabase Infrastructure Tests"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Test 1: Terraform validation
echo "Test 1: Validating Terraform configuration..."
cd "$TERRAFORM_DIR"
terraform validate > /dev/null 2>&1
print_result $? "Terraform configuration is valid"

# Test 2: Check for Supabase secrets
echo ""
echo "Test 2: Checking for Supabase secret definitions..."
if grep -q 'resource "google_secret_manager_secret" "supabase_url"' secret_manager.tf && \
   grep -q 'resource "google_secret_manager_secret" "supabase_anon_key"' secret_manager.tf && \
   grep -q 'resource "google_secret_manager_secret" "supabase_service_key"' secret_manager.tf; then
    print_result 0 "All Supabase secrets are defined"
else
    print_result 1 "Missing Supabase secret definitions"
fi

# Test 3: Check for prompt management service account
echo ""
echo "Test 3: Checking for prompt management service account..."
if grep -q 'resource "google_service_account" "cloud_run_prompt_mgmt"' iam.tf; then
    print_result 0 "Prompt management service account is defined"
else
    print_result 1 "Prompt management service account is missing"
fi

# Test 4: Check for Cloud Run service
echo ""
echo "Test 4: Checking for prompt management Cloud Run service..."
if grep -q 'resource "google_cloud_run_v2_service" "prompt_mgmt"' cloud_run.tf; then
    print_result 0 "Prompt management Cloud Run service is defined"
else
    print_result 1 "Prompt management Cloud Run service is missing"
fi

# Test 5: Check for IAM bindings
echo ""
echo "Test 5: Checking for IAM bindings..."
if grep -q 'prompt_mgmt_supabase_url' secret_manager.tf && \
   grep -q 'prompt_mgmt_supabase_anon_key' secret_manager.tf && \
   grep -q 'prompt_mgmt_supabase_service_key' secret_manager.tf; then
    print_result 0 "Supabase secret IAM bindings are configured"
else
    print_result 1 "Missing Supabase secret IAM bindings"
fi

# Test 6: Check for service account permissions
echo ""
echo "Test 6: Checking for service account permissions..."
if grep -q 'prompt_mgmt_secret_accessor' iam.tf && \
   grep -q 'prompt_mgmt_service_invoker' iam.tf; then
    print_result 0 "Service account has required permissions"
else
    print_result 1 "Missing service account permissions"
fi

# Test 7: Check for output definitions
echo ""
echo "Test 7: Checking for Terraform outputs..."
if grep -q 'output "prompt_mgmt_service_url"' outputs.tf && \
   grep -q 'supabase_url' outputs.tf && \
   grep -q 'supabase_anon_key' outputs.tf && \
   grep -q 'supabase_service_key' outputs.tf; then
    print_result 0 "All required outputs are defined"
else
    print_result 1 "Missing required outputs"
fi

# Test 8: Check for proper environment variable configuration
echo ""
echo "Test 8: Checking Cloud Run environment variables..."
if grep -q "NEXT_PUBLIC_SUPABASE_URL" cloud_run.tf && \
   grep -q "NEXT_PUBLIC_SUPABASE_ANON_KEY" cloud_run.tf && \
   grep -q "SUPABASE_SERVICE_KEY" cloud_run.tf; then
    print_result 0 "Environment variables are properly configured"
else
    print_result 1 "Missing or misconfigured environment variables"
fi

# Test 9: Verify service account reference in Cloud Run
echo ""
echo "Test 9: Verifying service account reference in Cloud Run service..."
if grep -q 'service_account = google_service_account.cloud_run_prompt_mgmt.email' cloud_run.tf; then
    print_result 0 "Service account is properly referenced"
else
    print_result 1 "Service account reference is missing or incorrect"
fi

# Test 10: Check for public access configuration
echo ""
echo "Test 10: Checking for public access configuration..."
if grep -q 'prompt_mgmt_public' cloud_run.tf; then
    print_result 0 "Public access IAM member is configured"
else
    print_result 1 "Missing public access configuration"
fi

# Test 11: Verify secret labels
echo ""
echo "Test 11: Checking secret labels..."
if grep -A 10 'resource "google_secret_manager_secret" "supabase_url"' secret_manager.tf | grep -q 'prompt-management-app'; then
    print_result 0 "Secrets have proper labels"
else
    print_result 1 "Secrets are missing proper labels"
fi

# Test 12: Check documentation exists
echo ""
echo "Test 12: Checking for documentation..."
if [ -f "$SCRIPT_DIR/../../docs/SUPABASE_GOOGLE_OAUTH_SETUP.md" ]; then
    print_result 0 "OAuth setup documentation exists"
else
    print_result 1 "OAuth setup documentation is missing"
fi

if [ -f "$SCRIPT_DIR/../../docs/PROMPT_MANAGEMENT_APP_DEPLOYMENT.md" ]; then
    print_result 0 "Deployment documentation exists"
else
    print_result 1 "Deployment documentation is missing"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
