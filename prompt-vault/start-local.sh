#!/bin/bash
# Start Prompt Vault locally (Frontend + Backend)
# Ports: Frontend 5176, Backend 8001

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Prompt Vault - Local Development${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check for port conflicts
echo -e "${YELLOW}Checking for port conflicts...${NC}"
if lsof -ti :5176 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port 5176 (frontend) is in use. Stopping...${NC}"
    lsof -ti :5176 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -ti :8001 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Port 8001 (backend) is in use. Stopping...${NC}"
    lsof -ti :8001 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo -e "${GREEN}✓ Ports available${NC}"
echo ""

# Start Backend
echo -e "${YELLOW}Starting Backend (port 8001)...${NC}"
cd backend

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/.deps_installed" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r requirements.txt
    touch .venv/.deps_installed
fi

# Start backend in background
PORT=8001 uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > /tmp/prompt-vault-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend started
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}✗ Backend failed to start${NC}"
    cat /tmp/prompt-vault-backend.log
    exit 1
fi

echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo ""

# Start Frontend
echo -e "${YELLOW}Starting Frontend (port 5176)...${NC}"
cd ../frontend

# Check for node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    bun install
fi

# Start frontend in background
bun run dev --port 5176 > /tmp/prompt-vault-frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend started
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}✗ Frontend failed to start${NC}"
    cat /tmp/prompt-vault-frontend.log
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Prompt Vault is running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:5176${NC}"
echo -e "  Backend:  ${GREEN}http://localhost:8001${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8001/docs${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  Backend:  ${YELLOW}tail -f /tmp/prompt-vault-backend.log${NC}"
echo -e "  Frontend: ${YELLOW}tail -f /tmp/prompt-vault-frontend.log${NC}"
echo ""
echo -e "${BLUE}To stop:${NC}"
echo -e "  ${YELLOW}kill $BACKEND_PID $FRONTEND_PID${NC}"
echo -e "  ${YELLOW}or: pkill -f 'uvicorn.*prompt-vault' && pkill -f 'bun.*prompt-vault'${NC}"
echo ""

# Keep script running
wait

