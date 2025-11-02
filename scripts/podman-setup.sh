#!/bin/bash
# One-command setup script for Podman local development environment

set -e

echo "🚀 Setting up Agentic Navigator local development environment..."

# Port configuration (override via environment variables if needed)
# Defaults align with system instruction and project config:
# - Frontend (Vite dev server): 5173
# - Backend (FastAPI): 8080
# - Firestore Emulator UI: 4000
FRONTEND_PORT=${FRONTEND_PORT:-5173}
BACKEND_PORT=${BACKEND_PORT:-8080}
FIRESTORE_UI_PORT=${FIRESTORE_UI_PORT:-4000}

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    echo "❌ Podman is not installed. Please install Podman first."
    echo "   macOS: brew install podman"
    echo "   Linux: See https://podman.io/getting-started/installation"
    exit 1
fi

# Check and start Podman machine (macOS only)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS - checking Podman machine..."
    if podman machine list | grep -q "running"; then
        echo "✅ Podman machine is already running"
    else
        echo "🚀 Starting Podman machine..."
        if podman machine list | grep -q "podman-machine"; then
            podman machine start
        else
            echo "⚠️  No Podman machine found. Creating default machine..."
            podman machine init || echo "⚠️  Machine might already exist"
            podman machine start
        fi
        echo "⏳ Waiting for Podman machine to be ready..."
        sleep 5
    fi
fi

# Check if podman-compose is available (or use docker-compose)
COMPOSE_CMD="podman-compose"
if ! command -v podman-compose &> /dev/null; then
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        echo "⚠️  podman-compose not found, using docker-compose instead"
    else
        echo "❌ Neither podman-compose nor docker-compose found."
        echo "   Install podman-compose: pip install podman-compose"
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ ! -f .env.example ]; then
        echo "❌ .env.example template file not found!"
        echo "   Please create .env.example or copy it from the repository before running this script."
        exit 1
    fi
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
    # Only prompt interactively if running in a terminal (not in CI/CD)
    if [ -t 0 ] && [ -z "$CI" ]; then
        read -p "Press Enter to continue after adding your API key..."
    else
        echo "ℹ️  Running in non-interactive mode. Please edit .env and add GEMINI_API_KEY manually."
    fi
fi

# Build and start services
echo "🔨 Building and starting services..."
$COMPOSE_CMD up -d --build

echo "✅ Setup complete!"
echo ""
echo "📍 Access points:"
echo "   - Frontend: http://localhost:${FRONTEND_PORT}"
echo "   - Backend API: http://localhost:${BACKEND_PORT}"
echo "   - API Docs: http://localhost:${BACKEND_PORT}/docs"
echo "   - Firestore Emulator UI: http://localhost:${FIRESTORE_UI_PORT}"
echo ""
echo "📊 View logs: $COMPOSE_CMD logs -f"
echo "🛑 Stop services: $COMPOSE_CMD down"

