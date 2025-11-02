#!/bin/bash
# Cleanup script for Podman local development environment

set -e

# Detect compose command
COMPOSE_CMD="podman-compose"
if ! command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

echo "🧹 Tearing down Agentic Navigator local development environment..."

# Stop and remove containers
$COMPOSE_CMD down -v

echo "✅ Teardown complete!"
echo "   All containers and volumes have been removed."

