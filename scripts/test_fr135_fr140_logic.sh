#!/bin/bash
# Test validation script for FR#135/FR#140 implementation
# This script simulates different job result scenarios to validate the aggregation logic

set -e

echo "=== FR#135/FR#140 Aggregation Logic Test ==="
echo ""

# Test function for CODE_QUALITY logic
test_code_quality() {
    local code_quality_result=$1
    local frontend_tests_result=$2
    local backend_tests_result=$3
    local expected=$4
    
    echo "Testing CODE_QUALITY: code-quality=$code_quality_result, frontend-tests=$frontend_tests_result, backend-tests=$backend_tests_result"
    
    # Simulate the aggregation logic
    local failed=false
    
    if [[ "$code_quality_result" == "failure" ]] || [[ "$code_quality_result" == "cancelled" ]]; then
        failed=true
    fi
    
    if [[ "$frontend_tests_result" == "failure" ]] || [[ "$frontend_tests_result" == "cancelled" ]]; then
        failed=true
    fi
    
    if [[ "$backend_tests_result" == "failure" ]] || [[ "$backend_tests_result" == "cancelled" ]]; then
        failed=true
    fi
    
    if [[ "$failed" == "true" ]]; then
        result="FAIL"
    else
        result="PASS"
    fi
    
    if [[ "$result" == "$expected" ]]; then
        echo "  ✅ Result: $result (Expected: $expected) - CORRECT"
    else
        echo "  ❌ Result: $result (Expected: $expected) - INCORRECT"
        exit 1
    fi
}

# Test function for SECURITY_AUDIT logic
test_security_audit() {
    local tfsec_result=$1
    local osv_result=$2
    local expected=$3
    
    echo "Testing SECURITY_AUDIT: tfsec-scan=$tfsec_result, osv-scanner=$osv_result"
    
    # Simulate the aggregation logic
    local failed=false
    
    if [[ "$tfsec_result" == "failure" ]] || [[ "$tfsec_result" == "cancelled" ]]; then
        failed=true
    fi
    
    if [[ "$osv_result" == "failure" ]] || [[ "$osv_result" == "cancelled" ]]; then
        failed=true
    fi
    
    if [[ "$failed" == "true" ]]; then
        result="FAIL"
    else
        result="PASS"
    fi
    
    if [[ "$result" == "$expected" ]]; then
        echo "  ✅ Result: $result (Expected: $expected) - CORRECT"
    else
        echo "  ❌ Result: $result (Expected: $expected) - INCORRECT"
        exit 1
    fi
}

echo "--- Scenario 1: All Jobs Succeed ---"
test_code_quality "success" "success" "success" "PASS"
test_security_audit "success" "success" "PASS"
echo ""

echo "--- Scenario 2: One Job Fails ---"
test_code_quality "success" "failure" "success" "FAIL"
test_security_audit "success" "success" "PASS"
echo ""

echo "--- Scenario 3: All Jobs Skipped (Path Filtering) ---"
test_code_quality "skipped" "skipped" "skipped" "PASS"
test_security_audit "skipped" "skipped" "PASS"
echo ""

echo "--- Scenario 4: Mixed Success and Skipped ---"
test_code_quality "success" "skipped" "skipped" "PASS"
test_security_audit "success" "skipped" "PASS"
echo ""

echo "--- Scenario 5: Job Cancelled ---"
test_code_quality "success" "success" "cancelled" "FAIL"
test_security_audit "cancelled" "success" "FAIL"
echo ""

echo "--- Scenario 6: Multiple Failures ---"
test_code_quality "failure" "failure" "success" "FAIL"
test_security_audit "failure" "failure" "FAIL"
echo ""

echo "--- Scenario 7: All Combinations ---"
test_code_quality "success" "skipped" "failure" "FAIL"
test_code_quality "skipped" "success" "success" "PASS"
test_code_quality "skipped" "skipped" "success" "PASS"
test_security_audit "skipped" "success" "PASS"
test_security_audit "success" "failure" "FAIL"
echo ""

echo "=== All Tests Passed ✅ ==="
echo ""
echo "The aggregation logic correctly handles:"
echo "  ✅ Success states (PASS)"
echo "  ✅ Skipped states (PASS - critical for path filtering)"
echo "  ✅ Failure states (FAIL)"
echo "  ✅ Cancelled states (FAIL)"
echo "  ✅ Mixed states (PASS only if no failures/cancellations)"
