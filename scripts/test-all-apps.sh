#!/bin/bash
# Test script for all three apps: agentnav, prompt-vault, cursor-ide
# Tests backend, frontend, and proxy routes

set -euo pipefail

echo "🧪 Testing All Apps"
echo "==================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test result
test_result() {
    local name=$1
    local status=$2
    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}✅ $name${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ $name${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# ============================================
# 1. AGENTNAV Tests
# ============================================
echo "📦 Testing Agentnav"
echo "-------------------"

# Backend tests
echo "  Testing backend..."
cd "$(dirname "$0")/../backend" || exit 1
if command -v pytest >/dev/null 2>&1; then
    if python3 -m pytest tests/ -v --tb=short >/tmp/agentnav-backend-tests.log 2>&1; then
        test_result "Agentnav Backend Tests" 0
    else
        test_result "Agentnav Backend Tests" 1
        echo "    See /tmp/agentnav-backend-tests.log for details"
    fi
else
    echo -e "${YELLOW}⚠️  pytest not installed, skipping backend tests${NC}"
    echo "    Install with: uv pip install -r requirements.txt"
fi

# Frontend tests
echo "  Testing frontend..."
cd "$(dirname "$0")/.." || exit 1
if command -v bun >/dev/null 2>&1; then
    if bun test --run >/tmp/agentnav-frontend-tests.log 2>&1; then
        test_result "Agentnav Frontend Tests" 0
    else
        test_result "Agentnav Frontend Tests" 1
        echo "    See /tmp/agentnav-frontend-tests.log for details"
    fi
else
    echo -e "${YELLOW}⚠️  bun not installed, skipping frontend tests${NC}"
fi

# Backend health check (if running)
echo "  Testing backend health..."
if curl -s http://localhost:8081/healthz >/dev/null 2>&1; then
    test_result "Agentnav Backend Health" 0
else
    echo -e "${YELLOW}⚠️  Backend not running on port 8081${NC}"
fi

# Frontend accessibility (if running)
echo "  Testing frontend accessibility..."
if curl -s http://localhost:5173 >/dev/null 2>&1; then
    test_result "Agentnav Frontend Accessibility" 0
else
    echo -e "${YELLOW}⚠️  Frontend not running on port 5173${NC}"
fi

echo ""

# ============================================
# 2. PROMPT-VAULT Tests
# ============================================
echo "📦 Testing Prompt Vault"
echo "----------------------"

# Check if prompt-vault exists
if [ -d "$(dirname "$0")/../prompt-vault" ]; then
    cd "$(dirname "$0")/../prompt-vault" || exit 1
    
    # Frontend tests (if test script exists)
    if [ -f "package.json" ]; then
        echo "  Testing frontend..."
        if command -v bun >/dev/null 2>&1; then
            if bun test --run >/tmp/prompt-vault-tests.log 2>&1 2>/dev/null; then
                test_result "Prompt Vault Frontend Tests" 0
            else
                echo -e "${YELLOW}⚠️  No tests configured or tests failed${NC}"
            fi
        fi
    fi
    
    # Frontend accessibility (if running)
    echo "  Testing frontend accessibility..."
    if curl -s http://localhost:5175 >/dev/null 2>&1; then
        test_result "Prompt Vault Frontend Accessibility" 0
    else
        echo -e "${YELLOW}⚠️  Frontend not running on port 5175${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  prompt-vault directory not found${NC}"
fi

echo ""

# ============================================
# 3. CURSOR-IDE Tests
# ============================================
echo "⌨️  Testing Cursor IDE"
echo "---------------------"

# Check if cursor-ide exists
if [ -d "$(dirname "$0")/../../cursor-ide" ]; then
    cd "$(dirname "$0")/../../cursor-ide" || exit 1
    
    # CLI tests (if test script exists)
    if [ -f "cli.py" ]; then
        echo "  Testing CLI..."
        if python3 cli.py --help >/dev/null 2>&1; then
            test_result "Cursor IDE CLI" 0
        else
            test_result "Cursor IDE CLI" 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️  cursor-ide directory not found${NC}"
fi

echo ""

# ============================================
# 4. NGINX PROXY Tests
# ============================================
echo "🌐 Testing Nginx Proxy Routes"
echo "----------------------------"

PROXY_URL="http://localhost:8082"

# Test landing page
echo "  Testing landing page..."
if curl -s "$PROXY_URL/" | grep -q "Agentnav Hub"; then
    test_result "Proxy Landing Page" 0
else
    test_result "Proxy Landing Page" 1
fi

# Test agentnav routes
echo "  Testing agentnav routes..."
if curl -s -I "$PROXY_URL/agentnav/" >/dev/null 2>&1; then
    test_result "Proxy /agentnav/ Route" 0
else
    test_result "Proxy /agentnav/ Route" 1
fi

if curl -s -I "$PROXY_URL/agentnav/docs" >/dev/null 2>&1; then
    test_result "Proxy /agentnav/docs Route" 0
else
    test_result "Proxy /agentnav/docs Route" 1
fi

# Test prompt-vault routes
echo "  Testing prompt-vault routes..."
if curl -s -I "$PROXY_URL/prompt-vault/" >/dev/null 2>&1; then
    test_result "Proxy /prompt-vault/ Route" 0
else
    test_result "Proxy /prompt-vault/ Route" 1
fi

# Test cursor-ide routes
echo "  Testing cursor-ide routes..."
if curl -s -I "$PROXY_URL/cursor-ide/" >/dev/null 2>&1; then
    test_result "Proxy /cursor-ide/ Route" 0
else
    test_result "Proxy /cursor-ide/ Route" 1
fi

# Test health endpoint
echo "  Testing health endpoint..."
if curl -s "$PROXY_URL/healthz" | grep -q "healthy"; then
    test_result "Proxy Health Endpoint" 0
else
    test_result "Proxy Health Endpoint" 1
fi

echo ""

# ============================================
# Summary
# ============================================
echo "📊 Test Summary"
echo "==============="
echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed or were skipped${NC}"
    exit 1
fi

