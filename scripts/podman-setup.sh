#!/bin/bash
# One-command setup script for Podman local development environment

set -e

echo "🚀 Setting up Agentic Navigator local development environment..."

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
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
    read -p "Press Enter to continue after adding your API key..."
fi

# Build and start services
echo "🔨 Building and starting services..."
$COMPOSE_CMD up -d --build

echo "✅ Setup complete!"
echo ""
echo "📍 Access points:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8080"
echo "   - API Docs: http://localhost:8080/docs"
echo "   - Firestore Emulator: http://localhost:8081"
echo ""
echo "📊 View logs: $COMPOSE_CMD logs -f"
echo "🛑 Stop services: $COMPOSE_CMD down"

