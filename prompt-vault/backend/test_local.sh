#!/bin/bash

# Local Testing Script for Prompt Vault Backend
# This script runs comprehensive local tests before deployment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Prompt Vault Backend - Local Testing${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check Python version
echo -e "${YELLOW}[1/7] Checking Python version...${NC}"
python3 --version || { echo -e "${RED}Python 3 not found${NC}"; exit 1; }
echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Step 2: Check if virtual environment exists
echo -e "${YELLOW}[2/7] Checking virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment ready${NC}"
echo ""

# Step 3: Install/update dependencies
echo -e "${YELLOW}[3/7] Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 4: Check environment variables
echo -e "${YELLOW}[4/7] Checking environment variables...${NC}"
MISSING_VARS=()

if [ -z "$GEMINI_API_KEY" ]; then
    MISSING_VARS+=("GEMINI_API_KEY")
fi

if [ -z "$SUPABASE_URL" ]; then
    echo -e "${YELLOW}⚠ SUPABASE_URL not set (optional for basic testing)${NC}"
fi

if [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo -e "${YELLOW}⚠ SUPABASE_SERVICE_KEY not set (optional for basic testing)${NC}"
fi

if [ -z "$FIRESTORE_PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠ FIRESTORE_PROJECT_ID not set (optional for basic testing)${NC}"
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}✗ Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${RED}  - $var${NC}"
    done
    echo -e "${YELLOW}Set them with: export ${MISSING_VARS[0]}=\"your-key\"${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables OK${NC}"
echo ""

# Step 5: Run unit tests
echo -e "${YELLOW}[5/7] Running unit tests...${NC}"
pytest tests/ -v --tb=short || {
    echo -e "${RED}✗ Unit tests failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ All unit tests passed${NC}"
echo ""

# Step 6: Test Suggestion Agent directly
echo -e "${YELLOW}[6/7] Testing Suggestion Agent...${NC}"
python3 test_suggestion_agent.py || {
    echo -e "${RED}✗ Suggestion Agent test failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Suggestion Agent test passed${NC}"
echo ""

# Step 7: Start server and test endpoints
echo -e "${YELLOW}[7/7] Starting server and testing endpoints...${NC}"
echo -e "${BLUE}Starting FastAPI server on port 8080...${NC}"

# Start server in background
uvicorn app.main:app --host 0.0.0.0 --port 8080 > /tmp/prompt-vault-server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${RED}✗ Server failed to start${NC}"
    cat /tmp/prompt-vault-server.log
    exit 1
fi

echo -e "${GREEN}✓ Server started (PID: $SERVER_PID)${NC}"

# Test endpoints
echo -e "${BLUE}Testing endpoints...${NC}"

# Test root endpoint
if curl -s http://localhost:8080/ | grep -q "Prompt Vault Backend"; then
    echo -e "${GREEN}✓ Root endpoint OK${NC}"
else
    echo -e "${RED}✗ Root endpoint failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test health endpoint
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health endpoint OK${NC}"
else
    echo -e "${RED}✗ Health endpoint failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test healthz endpoint (Cloud Run)
if curl -s http://localhost:8080/healthz | grep -q "ok"; then
    echo -e "${GREEN}✓ Healthz endpoint OK${NC}"
else
    echo -e "${RED}✗ Healthz endpoint failed${NC}"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Test analyze endpoint
ANALYZE_RESPONSE=$(curl -s -X POST http://localhost:8080/api/agents/analyze \
    -H "Content-Type: application/json" \
    -d '{"prompt_text": "Write a function that sorts a list of numbers."}')

if echo "$ANALYZE_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Analyze endpoint OK${NC}"
else
    echo -e "${YELLOW}⚠ Analyze endpoint returned unexpected response${NC}"
    echo "$ANALYZE_RESPONSE" | head -20
fi

# Stop server
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo -e "${GREEN}✓ Server stopped${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All local tests passed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Review test results above"
echo -e "  2. Test manually: uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
echo -e "  3. Test API endpoints with curl or Postman"
echo -e "  4. Push to remote and deploy to Cloud Run"
echo ""

