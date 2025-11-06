#!/bin/bash
# Local Testing Script for Nginx Proxy
# Tests the nginx proxy with local services for all three apps:
# - agentnav
# - prompt-vault
# - cursor-ide

set -euo pipefail

echo "=== Nginx Proxy Local Test (Multi-App) ==="
echo ""

# Default ports
# Note: Proxy uses 8082 locally to avoid conflict with gvproxy (Podman) on 8080
PROXY_PORT=${PROXY_PORT:-8082}

# Agentnav ports
AGENTNAV_FRONTEND_PORT=${AGENTNAV_FRONTEND_PORT:-5173}
AGENTNAV_BACKEND_PORT=${AGENTNAV_BACKEND_PORT:-8081}

# Prompt-vault ports
PROMPT_VAULT_FRONTEND_PORT=${PROMPT_VAULT_FRONTEND_PORT:-5176}
PROMPT_VAULT_BACKEND_PORT=${PROMPT_VAULT_BACKEND_PORT:-8001}

# Cursor-ide ports
CURSOR_IDE_FRONTEND_PORT=${CURSOR_IDE_FRONTEND_PORT:-5173}
CURSOR_IDE_BACKEND_PORT=${CURSOR_IDE_BACKEND_PORT:-8188}

# Check if ports are available
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "✅ Port $port ($service) is in use"
        return 0
    else
        echo "⚠️  Port $port ($service) is NOT in use"
        return 1
    fi
}

echo "📋 Checking Port Availability:"
check_port $PROXY_PORT "Proxy" || echo "   (Proxy will use this port)"
echo ""
echo "   Agentnav:"
check_port $AGENTNAV_FRONTEND_PORT "Agentnav Frontend"
check_port $AGENTNAV_BACKEND_PORT "Agentnav Backend"
echo ""
echo "   Prompt-vault:"
check_port $PROMPT_VAULT_FRONTEND_PORT "Prompt-vault Frontend"
check_port $PROMPT_VAULT_BACKEND_PORT "Prompt-vault Backend"
echo ""
echo "   Cursor-ide:"
check_port $CURSOR_IDE_FRONTEND_PORT "Cursor-ide Frontend"
check_port $CURSOR_IDE_BACKEND_PORT "Cursor-ide Backend"

echo ""
echo "🔧 Environment Variables:"
echo "   PROXY_PORT=$PROXY_PORT"
echo "   AGENTNAV_FRONTEND_PORT=$AGENTNAV_FRONTEND_PORT"
echo "   AGENTNAV_BACKEND_PORT=$AGENTNAV_BACKEND_PORT"
echo "   PROMPT_VAULT_FRONTEND_PORT=$PROMPT_VAULT_FRONTEND_PORT"
echo "   PROMPT_VAULT_BACKEND_PORT=$PROMPT_VAULT_BACKEND_PORT"
echo "   CURSOR_IDE_FRONTEND_PORT=$CURSOR_IDE_FRONTEND_PORT"
echo "   CURSOR_IDE_BACKEND_PORT=$CURSOR_IDE_BACKEND_PORT"
echo ""

# Build the proxy image
echo "🔨 Building nginx proxy image..."
cd "$(dirname "$0")"
podman build -t agentnav-proxy:local . || docker build -t agentnav-proxy:local .

echo ""
echo "🚀 Starting nginx proxy container..."
echo "   Make sure services are running on their respective ports:"
echo "   - Agentnav frontend: $AGENTNAV_FRONTEND_PORT"
echo "   - Agentnav backend: $AGENTNAV_BACKEND_PORT"
echo "   - Prompt-vault frontend: $PROMPT_VAULT_FRONTEND_PORT"
echo "   - Prompt-vault backend: $PROMPT_VAULT_BACKEND_PORT"
echo "   - Cursor-ide frontend: $CURSOR_IDE_FRONTEND_PORT"
echo "   - Cursor-ide backend: $CURSOR_IDE_BACKEND_PORT"
echo ""

# Stop existing container if running
podman stop agentnav-proxy-local 2>/dev/null || docker stop agentnav-proxy-local 2>/dev/null || true
podman rm agentnav-proxy-local 2>/dev/null || docker rm agentnav-proxy-local 2>/dev/null || true

# Determine host address (for Docker/Podman to access host services)
# macOS/Windows use host.docker.internal, Linux may need different approach
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    HOST_ADDR="172.17.0.1"  # Default Docker bridge IP on Linux
else
    HOST_ADDR="host.docker.internal"
fi

# Run the proxy with all service URLs
podman run -d \
  --name agentnav-proxy-local \
  -p $PROXY_PORT:8080 \
  -e PORT=8080 \
  -e AGENTNAV_FRONTEND_URL=http://$HOST_ADDR:$AGENTNAV_FRONTEND_PORT \
  -e AGENTNAV_BACKEND_URL=http://$HOST_ADDR:$AGENTNAV_BACKEND_PORT \
  -e AGENTNAV_GEMMA_URL=http://$HOST_ADDR:8083 \
  -e PROMPT_VAULT_FRONTEND_URL=http://$HOST_ADDR:$PROMPT_VAULT_FRONTEND_PORT \
  -e PROMPT_VAULT_BACKEND_URL=http://$HOST_ADDR:$PROMPT_VAULT_BACKEND_PORT \
  -e CURSOR_IDE_FRONTEND_URL=http://$HOST_ADDR:$CURSOR_IDE_FRONTEND_PORT \
  -e CURSOR_IDE_BACKEND_URL=http://$HOST_ADDR:$CURSOR_IDE_BACKEND_PORT \
  agentnav-proxy:local || \
docker run -d \
  --name agentnav-proxy-local \
  -p $PROXY_PORT:8080 \
  -e PORT=8080 \
  -e AGENTNAV_FRONTEND_URL=http://$HOST_ADDR:$AGENTNAV_FRONTEND_PORT \
  -e AGENTNAV_BACKEND_URL=http://$HOST_ADDR:$AGENTNAV_BACKEND_PORT \
  -e AGENTNAV_GEMMA_URL=http://$HOST_ADDR:8083 \
  -e PROMPT_VAULT_FRONTEND_URL=http://$HOST_ADDR:$PROMPT_VAULT_FRONTEND_PORT \
  -e PROMPT_VAULT_BACKEND_URL=http://$HOST_ADDR:$PROMPT_VAULT_BACKEND_PORT \
  -e CURSOR_IDE_FRONTEND_URL=http://$HOST_ADDR:$CURSOR_IDE_FRONTEND_PORT \
  -e CURSOR_IDE_BACKEND_URL=http://$HOST_ADDR:$CURSOR_IDE_BACKEND_PORT \
  agentnav-proxy:local

echo ""
echo "✅ Proxy container started!"
echo ""
echo "📋 Test URLs:"
echo "   Health: http://localhost:$PROXY_PORT/healthz"
echo ""
echo "   Agentnav:"
echo "     Frontend: http://localhost:$PROXY_PORT/agentnav/"
echo "     API: http://localhost:$PROXY_PORT/agentnav/api/healthz"
echo "     Docs: http://localhost:$PROXY_PORT/agentnav/docs"
echo ""
echo "   Prompt-vault:"
echo "     Frontend: http://localhost:$PROXY_PORT/prompt-vault/"
echo "     API: http://localhost:$PROXY_PORT/prompt-vault/api/healthz"
echo "     Docs: http://localhost:$PROXY_PORT/prompt-vault/docs"
echo ""
echo "   Cursor-ide:"
echo "     Frontend: http://localhost:$PROXY_PORT/cursor-ide/"
echo "     API: http://localhost:$PROXY_PORT/cursor-ide/api/"
echo ""
echo "   Root (defaults to agentnav):"
echo "     http://localhost:$PROXY_PORT/"
echo ""
echo "📝 To view logs:"
echo "   podman logs -f agentnav-proxy-local"
echo "   (or: docker logs -f agentnav-proxy-local)"
echo ""
echo "🛑 To stop:"
echo "   podman stop agentnav-proxy-local"
echo "   (or: docker stop agentnav-proxy-local)"
echo ""
