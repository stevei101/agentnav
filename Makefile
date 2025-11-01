# Makefile for Agentic Navigator Local Development
# Uses Podman commands directly (no docker-compose dependency)
# Aligned with Cloud Run best practices

.PHONY: help setup up down logs logs-frontend logs-backend logs-firestore build clean test test-frontend test-backend demo teardown restart ps podman-start validate health check-env install-dev lint format shell-frontend shell-backend

# Detect Podman
PODMAN := $(shell command -v podman 2> /dev/null)
PODMAN_COMPOSE := $(shell command -v podman-compose 2> /dev/null)

# Load environment variables from .env file
ifneq (,$(wildcard .env))
include .env
export
endif

# Container names
FRONTEND_CONTAINER := agentnav-frontend
BACKEND_CONTAINER := agentnav-backend
FIRESTORE_CONTAINER := firestore-emulator

# Network name
NETWORK := agentnav-network

# Default target
help:
	@echo "🚀 Agentic Navigator - Local Development Commands (Podman)"
	@echo ""
	@echo "📦 Quick Start:"
	@echo "  make setup          Initial setup (.env, podman machine, build & start)"
	@echo "  make up             Start all services"
	@echo "  make down           Stop all services"
	@echo "  make logs           Follow all logs"
	@echo ""
	@echo "🛠️  Service Management:"
	@echo "  make restart        Restart all services"
	@echo "  make ps             Show running containers"
	@echo "  make build          Rebuild all containers"
	@echo "  make clean          Stop and remove containers, volumes, networks"
	@echo ""
	@echo "📋 Logs:"
	@echo "  make logs-frontend   Follow frontend logs"
	@echo "  make logs-backend    Follow backend logs"
	@echo "  make logs-firestore  Follow Firestore emulator logs"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-frontend  Run frontend tests"
	@echo "  make test-backend   Run backend tests"
	@echo ""
	@echo "🎬 Demo & Validation:"
	@echo "  make demo           Start demo environment"
	@echo "  make validate       Validate environment and services"
	@echo "  make health         Check health of all services"
	@echo ""
	@echo "🐳 Podman:"
	@echo "  make podman-start   Start Podman machine (macOS)"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make install-dev    Install development dependencies"
	@echo "  make lint           Lint code"
	@echo "  make format         Format code"
	@echo "  make shell-frontend Open shell in frontend container"
	@echo "  make shell-backend  Open shell in backend container"
	@echo ""
	@echo "📍 Using: $(if $(PODMAN),$(PODMAN),⚠️  Podman not found!)"
	@echo ""

# Ensure Podman is available
check-podman:
	@if [ -z "$(PODMAN)" ]; then \
		echo "❌ Podman not found."; \
		echo "   Install Podman: https://podman.io/getting-started/installation"; \
		exit 1; \
	fi

# Start Podman machine (macOS only)
podman-start: check-podman
	@if [[ "$$OSTYPE" == "darwin"* ]]; then \
		echo "🍎 Starting Podman machine..."; \
		if podman machine list 2>/dev/null | grep -q "running"; then \
			echo "✅ Podman machine is already running"; \
		else \
			if podman machine list 2>/dev/null | grep -q "podman-machine"; then \
				podman machine start; \
			else \
				echo "⚠️  No Podman machine found. Creating default machine..."; \
				podman machine init || echo "⚠️  Machine might already exist"; \
				podman machine start; \
			fi; \
			echo "⏳ Waiting for Podman machine to be ready..."; \
			sleep 5; \
		fi; \
	else \
		echo "ℹ️  Podman machine not needed on this platform"; \
	fi

# Create network
network-create: check-podman
	@if ! podman network exists $(NETWORK) 2>/dev/null; then \
		echo "🌐 Creating network: $(NETWORK)"; \
		podman network create $(NETWORK); \
	else \
		echo "✅ Network $(NETWORK) already exists"; \
	fi

# Create .env file from template if it doesn't exist
setup-env:
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp .env.example .env 2>/dev/null || echo "⚠️  .env.example not found, creating empty .env"; \
		touch .env; \
		echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# Validate environment variables
check-env: setup-env
	@echo "🔍 Validating environment configuration..."
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found"; \
		exit 1; \
	fi
	@if ! grep -q "GEMINI_API_KEY" .env || grep -q "GEMINI_API_KEY=your-api-key-here" .env || grep -q "^GEMINI_API_KEY=$$" .env; then \
		echo "⚠️  Warning: GEMINI_API_KEY not set in .env"; \
	fi
	@echo "✅ Environment file validated"

# Build containers using Podman
build: check-podman podman-start
	@echo "🔨 Building containers with Podman..."
	@echo "Building frontend..."
	@podman build -f Dockerfile.frontend -t agentnav-frontend:dev --target development .
	@echo "Building backend..."
	@podman build -f backend/Dockerfile -t agentnav-backend:dev --target development ./backend
	@echo "✅ All containers built successfully"

# Start Firestore emulator
start-firestore: check-podman network-create
	@if ! podman ps -a --format "{{.Names}}" | grep -q "^$(FIRESTORE_CONTAINER)$$"; then \
		echo "🔥 Starting Firestore emulator..."; \
		podman run -d \
			--name $(FIRESTORE_CONTAINER) \
			--network $(NETWORK) \
			-p 8081:8080 \
			-p 4000:4000 \
			-v firestore-data:/firestore \
			-e FIRESTORE_PROJECT_ID=$${FIRESTORE_PROJECT_ID:-agentnav-dev} \
			gcr.io/google.com/cloudsdktool/cloud-sdk:emulators \
			gcloud beta emulators firestore start \
			--host-port=0.0.0.0:8080 \
			--project=$${FIRESTORE_PROJECT_ID:-agentnav-dev}; \
	else \
		if ! podman ps --format "{{.Names}}" | grep -q "^$(FIRESTORE_CONTAINER)$$"; then \
			echo "🔄 Starting existing Firestore container..."; \
			podman start $(FIRESTORE_CONTAINER); \
		else \
			echo "✅ Firestore emulator already running"; \
		fi; \
	fi

# Start backend
start-backend: check-podman network-create start-firestore
	@if ! podman ps -a --format "{{.Names}}" | grep -q "^$(BACKEND_CONTAINER)$$"; then \
		echo "🚀 Starting backend..."; \
		podman run -d \
			--name $(BACKEND_CONTAINER) \
			--network $(NETWORK) \
			-p 8080:8080 \
			-v $$(pwd)/backend:/app \
			-e PORT=8080 \
			-e ENVIRONMENT=development \
			-e GEMINI_API_KEY=$${GEMINI_API_KEY} \
			-e FIRESTORE_EMULATOR_HOST=$(FIRESTORE_CONTAINER):8080 \
			-e FIRESTORE_PROJECT_ID=$${FIRESTORE_PROJECT_ID:-agentnav-dev} \
			-e FIRESTORE_DATABASE_ID=$${FIRESTORE_DATABASE_ID:-default} \
			agentnav-backend:dev; \
	else \
		if ! podman ps --format "{{.Names}}" | grep -q "^$(BACKEND_CONTAINER)$$"; then \
			echo "🔄 Starting existing backend container..."; \
			podman start $(BACKEND_CONTAINER); \
		else \
			echo "✅ Backend already running"; \
		fi; \
	fi

# Start frontend
start-frontend: check-podman network-create start-backend
	@if ! podman ps -a --format "{{.Names}}" | grep -q "^$(FRONTEND_CONTAINER)$$"; then \
		echo "🚀 Starting frontend..."; \
		podman run -d \
			--name $(FRONTEND_CONTAINER) \
			--network $(NETWORK) \
			-p 3000:3000 \
			-v $$(pwd):/app:Z \
			-e VITE_API_URL=http://localhost:8080 \
			-e VITE_GEMINI_API_KEY=$${GEMINI_API_KEY} \
			agentnav-frontend:dev; \
	else \
		if ! podman ps --format "{{.Names}}" | grep -q "^$(FRONTEND_CONTAINER)$$"; then \
			echo "🔄 Starting existing frontend container..."; \
			podman start $(FRONTEND_CONTAINER); \
		else \
			echo "✅ Frontend already running"; \
		fi; \
	fi

# Start all services
up: start-frontend
	@echo "✅ All services started!"
	@echo ""
	@echo "📍 Access points:"
	@echo "   - Frontend:      http://localhost:3000"
	@echo "   - Backend API:   http://localhost:8080"
	@echo "   - API Docs:      http://localhost:8080/docs"
	@echo "   - Health Check:  http://localhost:8080/healthz"
	@echo "   - Firestore UI:  http://localhost:4000"
	@echo ""
	@echo "📊 View logs: make logs"

# Stop all services
down: check-podman
	@echo "🛑 Stopping services..."
	@podman stop $(FRONTEND_CONTAINER) $(BACKEND_CONTAINER) $(FIRESTORE_CONTAINER) 2>/dev/null || true
	@echo "✅ Services stopped."

# Restart all services
restart: down up

# Initial setup
setup: check-podman podman-start setup-env check-env network-create
	@echo "🚀 Setting up Agentic Navigator local development environment..."
	@$(MAKE) build
	@$(MAKE) up
	@echo ""
	@echo "✅ Setup complete!"

# Show running containers
ps: check-podman
	@podman ps --filter "name=$(FRONTEND_CONTAINER)|$(BACKEND_CONTAINER)|$(FIRESTORE_CONTAINER)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Follow all logs
logs: check-podman
	@echo "📊 Following logs from all running containers (Ctrl+C to exit)..."
	@running_containers=""; \
	for container in $(FRONTEND_CONTAINER) $(BACKEND_CONTAINER) $(FIRESTORE_CONTAINER); do \
		if podman ps --format "{{.Names}}" | grep -q "^$$container$$"; then \
			running_containers="$$running_containers $$container"; \
		fi; \
	done; \
	if [ -z "$$running_containers" ]; then \
		echo "⚠️  No containers are running. Use 'make up' to start them."; \
	else \
		podman logs -f $$running_containers; \
	fi

# Follow frontend logs only
logs-frontend: check-podman
	@podman logs -f $(FRONTEND_CONTAINER)

# Follow backend logs only
logs-backend: check-podman
	@podman logs -f $(BACKEND_CONTAINER)

# Follow Firestore emulator logs only
logs-firestore: check-podman
	@podman logs -f $(FIRESTORE_CONTAINER)

# Run all tests
test: test-frontend test-backend

# Run backend tests
test-backend: check-podman podman-start network-create start-firestore
	@echo "🧪 Running backend tests..."
	@podman run --rm \
		--network $(NETWORK) \
		-v $$(pwd)/backend:/app \
		-e FIRESTORE_EMULATOR_HOST=$(FIRESTORE_CONTAINER):8080 \
		-e FIRESTORE_PROJECT_ID=$${FIRESTORE_PROJECT_ID:-agentnav-dev} \
		agentnav-backend:dev \
		pytest -v

# Run frontend tests
test-frontend: check-podman podman-start
	@echo "🧪 Running frontend tests..."
	@if command -v bun >/dev/null 2>&1; then \
		bun test; \
	else \
		echo "⚠️  bun not found, running tests in container..."; \
		podman run --rm \
			-v $$(pwd):/app \
			agentnav-frontend:dev \
			bun test; \
	fi

# Start demo environment (using podman-compose if available, otherwise same as up)
demo: check-podman podman-start
	@echo "🎬 Starting demo environment..."
	@if [ -n "$(PODMAN_COMPOSE)" ] && [ -f docker-compose.demo.yml ]; then \
		$(PODMAN_COMPOSE) -f docker-compose.demo.yml up -d; \
	else \
		echo "⚠️  podman-compose or docker-compose.demo.yml not found, starting regular environment..."; \
		$(MAKE) up; \
	fi
	@echo "✅ Demo environment started."
	@echo "📍 Access: http://localhost:5173"

# Validate environment and services
validate: check-env
	@echo "🔍 Validating services..."
	@$(MAKE) health

# Check health of all services
health: check-podman
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "Backend Health Check:"
	@curl -s http://localhost:8080/healthz >/dev/null 2>&1 && \
		echo "  ✅ Backend is healthy" || \
		echo "  ❌ Backend health check failed"
	@echo ""
	@echo "Frontend Health Check:"
	@curl -s http://localhost:5173 >/dev/null 2>&1 && \
		echo "  ✅ Frontend is healthy" || \
		echo "  ❌ Frontend health check failed"
	@echo ""
	@echo "Firestore Emulator:"
	@curl -s http://localhost:8081 >/dev/null 2>&1 && \
		echo "  ✅ Firestore emulator is running" || \
		echo "  ❌ Firestore emulator is not accessible"
	@echo ""

# Clean: Stop and remove everything (including volumes)
clean: check-podman
	@echo "🧹 Cleaning up containers, volumes, and networks..."
	@podman stop $(FRONTEND_CONTAINER) $(BACKEND_CONTAINER) $(FIRESTORE_CONTAINER) 2>/dev/null || true
	@podman rm $(FRONTEND_CONTAINER) $(BACKEND_CONTAINER) $(FIRESTORE_CONTAINER) 2>/dev/null || true
	@podman volume rm firestore-data 2>/dev/null || true
	@podman network rm $(NETWORK) 2>/dev/null || true
	@echo "✅ Cleanup complete."

# Teardown (alias for clean)
teardown: clean

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	@if command -v bun >/dev/null 2>&1; then \
		bun install; \
	else \
		echo "⚠️  bun not found, skipping frontend dependencies"; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		cd backend && uv pip install -r requirements.txt -r requirements-dev.txt 2>/dev/null || uv pip install -r requirements.txt; \
	else \
		echo "⚠️  uv not found, skipping backend dependencies"; \
	fi

# Lint code
lint:
	@echo "🔍 Linting code..."
	@if command -v bun >/dev/null 2>&1; then \
		bun run lint 2>/dev/null || echo "⚠️  No lint script found for frontend"; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		cd backend && uv run ruff check . 2>/dev/null || echo "⚠️  ruff not found, skipping backend lint"; \
	fi

# Format code
format:
	@echo "✨ Formatting code..."
	@if command -v bun >/dev/null 2>&1; then \
		bun run format 2>/dev/null || echo "⚠️  No format script found for frontend"; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		cd backend && uv run ruff format . 2>/dev/null || echo "⚠️  ruff not found, skipping backend format"; \
	fi

# Open shell in frontend container
shell-frontend: check-podman
	@podman exec -it $(FRONTEND_CONTAINER) /bin/sh || \
	podman exec -it $(FRONTEND_CONTAINER) /bin/bash || \
	echo "❌ Could not open shell in frontend container"

# Open shell in backend container
shell-backend: check-podman
	@podman exec -it $(BACKEND_CONTAINER) /bin/sh || \
	podman exec -it $(BACKEND_CONTAINER) /bin/bash || \
	echo "❌ Could not open shell in backend container"
