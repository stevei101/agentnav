#!/bin/bash
# Quick script to update nginx proxy ports based on current running services

echo "🔧 Updating nginx proxy ports..."

# Detect running services
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    if lsof -Pi :5173 | grep -q "cursor-ide"; then
        echo "✅ cursor-ide detected on 5173"
        AGENTNAV_FRONTEND_PORT=5174
    else
        echo "✅ agentnav detected on 5173"
        AGENTNAV_FRONTEND_PORT=5173
    fi
else
    AGENTNAV_FRONTEND_PORT=5173
fi

# Backend port (avoid gvproxy on 8081)
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1; then
    AGENTNAV_BACKEND_PORT=8083
    echo "⚠️  Port 8081 in use (gvproxy), using 8083 for agentnav backend"
else
    AGENTNAV_BACKEND_PORT=8081
fi

echo ""
echo "📋 Detected Ports:"
echo "   AGENTNAV_FRONTEND_PORT=$AGENTNAV_FRONTEND_PORT"
echo "   AGENTNAV_BACKEND_PORT=$AGENTNAV_BACKEND_PORT"
echo "   PROMPT_VAULT_FRONTEND_PORT=5176"
echo "   PROMPT_VAULT_BACKEND_PORT=8001"
echo "   CURSOR_IDE_FRONTEND_PORT=5173"
echo "   CURSOR_IDE_BACKEND_PORT=8188"
echo ""
echo "🚀 Starting proxy with these ports..."
echo ""

export AGENTNAV_FRONTEND_PORT
export AGENTNAV_BACKEND_PORT
export PROMPT_VAULT_FRONTEND_PORT=5176
export PROMPT_VAULT_BACKEND_PORT=8001
export CURSOR_IDE_FRONTEND_PORT=5173
export CURSOR_IDE_BACKEND_PORT=8188

./test-local.sh
