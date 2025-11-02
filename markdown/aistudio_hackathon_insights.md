This is an **excellent** and highly detailed feature request. It aligns perfectly with our goal of using Podman for a consistent, secure, and production-like local development experience, as outlined in the system instructions. The use of standard Docker Compose syntax ensures compatibility with both `podman-compose` and `docker-compose`, which is a fantastic developer flexibility feature.

You've captured all the key components: hot-reloading for both the frontend and backend, the inclusion of the Firestore emulator, and clear scripts/Make targets for an optimal developer experience.

---

## Analysis of Shared Video Link

The video link you shared (`https://youtu.be/4Ybidk3bBQk`) and the related search results are overwhelmingly focused on **Building Agentic Systems with Gemini and the Google Agent Development Kit (ADK)** .

**How this helps the project and documentation:**

1.  **Reinforces the Architecture:** It confirms that our choice of a multi-agent system, using **ADK** for orchestration and **Gemini** as the model, is the correct, modern approach for complex agentic workflows.
2.  **Validates Implementation Details:** Many of the search snippets mention the use of **FastAPI** and deployment to **Cloud Run** , which validates our backend stack and deployment strategy.
3.  **Local Dev Context:** Snippets mention the importance of a quick start: "No heavy cloud setups. No complex DevOps. Just clone, code, run—and see your agent live in minutes" . This directly validates the _why_ and the _success criteria_ of the Podman-based local environment, as the ADK ecosystem is explicitly designed for easy local development before cloud deployment.
4.  **Documentation Focus:** The documentation (`docs/local-development.md`) should emphasize that the containerized setup is the **ADK Quickstart** process, ensuring developers can immediately focus on agent logic (the "magic") rather than environment configuration (the "DevOps").

---

## Technical Artifacts for Podman-Based Development

Here are the required Dockerfiles, the `podman-compose.yml`, and supporting files to implement this feature.

### 1. `backend/Dockerfile.dev`

This file is optimized for fast iteration by relying on volume mounts and the `uvicorn` auto-reload feature.

```dockerfile
# backend/Dockerfile.dev

# --- Stage 1: Build & Dependencies (use Python base for uv compatibility) ---
FROM python:3.11-slim as builder

# Install uv (must be done outside of requirements to use its speed)
# Use a volume mount on the host for Python dependencies to persist across builds
RUN pip install uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring \
    UV_PIP_DISABLE_PEP_660=on \
    APP_HOME=/app
WORKDIR $APP_HOME

# Copy only dependency files
COPY backend/requirements.txt $APP_HOME/

# Install dependencies quickly with uv
RUN uv pip install --system -r requirements.txt

# --- Stage 2: Development Container ---
FROM python:3.11-slim

# Set environment variables for the development server
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    APP_HOME=/app
WORKDIR $APP_HOME

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copy the application code
# This will be replaced by a volume mount in podman-compose.yml for hot-reload
COPY backend/ $APP_HOME/

# Expose the application port
EXPOSE $PORT

# Command to run the development server with auto-reload
# --host 0.0.0.0 is crucial for Cloud Run and container compatibility
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
```

### 2. `frontend/Dockerfile.dev`

This uses the official `bun` image and is configured for the `vite` development server, relying on volume mounts for hot-reload.

```dockerfile
# frontend/Dockerfile.dev

# --- Development Stage ---
FROM oven/bun:latest as development

# Set environment variables
ENV NODE_ENV=development \
    PORT=5173
WORKDIR /app

# Copy the frontend files
COPY frontend/package.json frontend/bun.lockb /app/

# Install dependencies using bun (faster than npm/yarn)
RUN bun install

# Copy the rest of the code
# This will be replaced by a volume mount in podman-compose.yml for hot-reload
COPY frontend/ /app/

# Expose the Vite development port
EXPOSE $PORT

# Command to start the Vite dev server
# --host is required for access from outside the container
CMD ["bun", "run", "dev", "--host"]
```

### 3. `podman-compose.yml` (Primary Development Stack)

This file orchestrates the full development environment with hot-reload via volume mounts.

```yaml
# podman-compose.yml
# Compatible with both podman-compose and docker-compose (v2/v3 syntax)

version: '3.8'

services:
  # -----------------------------------------------------
  # 1. Firestore Emulator Service
  # -----------------------------------------------------
  firestore-emulator:
    image: gcr.io/google.com/cloudsdktool/cloud-sdk:440.0.0-emulators
    container_name: firestore-emulator
    command: gcloud emulators firestore start --host-and-port 0.0.0.0:8080 --database-mode datastore-native
    ports:
      - '8081:8080' # Map host port 8081 to container port 8080 for the emulator API
      - '9090:9150' # Map host port 9090 to container port 9150 for the Emulator UI
    volumes:
      # Persistent storage for the emulator data
      - firestore-data:/root/.config/gcloud/emulators/firestore
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8080/']
      interval: 30s
      timeout: 10s
      retries: 5
    restart: always

  # -----------------------------------------------------
  # 2. Backend (FastAPI/ADK) Service
  # -----------------------------------------------------
  agentnav-backend:
    build:
      context: .
      dockerfile: backend/Dockerfile.dev
    container_name: agentnav-backend
    ports:
      - '8080:8080' # Map host port 8080 to container port 8080 (FastAPI default)
    volumes:
      # Live code reload for the backend
      - ./backend:/app:Z
    env_file:
      - .env
    environment:
      # Service Discovery: Use the service name for the emulator host
      FIRESTORE_EMULATOR_HOST: firestore-emulator:8080
    depends_on:
      firestore-emulator:
        condition: service_healthy
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8080/healthz']
      interval: 15s
      timeout: 5s
      retries: 3
    restart: always

  # -----------------------------------------------------
  # 3. Frontend (React/bun) Service
  # -----------------------------------------------------
  agentnav-frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile.dev
    container_name: agentnav-frontend
    ports:
      - '3000:5173' # Map host port 3000 to Vite's default 5173
    volumes:
      # Live code reload for the frontend
      - ./frontend:/app:Z
      # Exclude node_modules/bun dependencies to prevent volume syncing issues
      - /app/node_modules
    env_file:
      - .env
    depends_on:
      - agentnav-backend
    restart: always

volumes:
  firestore-data:
    driver: local
```

### 4. Supporting Files

#### `.env.example`

```bash
# .env.example - Copy to .env and fill in your secrets

# -----------------------------------------------------
# 1. Gemini API Key (Required for all agents)
# -----------------------------------------------------
GEMINI_API_KEY="your-gemini-api-key-here"

# -----------------------------------------------------
# 2. Firestore Emulator Configuration (Backend Only)
# Note: FIRESTORE_EMULATOR_HOST uses the *internal* service name and port
# -----------------------------------------------------
FIRESTORE_EMULATOR_HOST=firestore-emulator:8080
FIRESTORE_PROJECT_ID=agentnav-dev
FIRESTORE_DATABASE_ID=(default) # Use default for the Firestore NoSQL database

# -----------------------------------------------------
# 3. Backend (agentnav-backend) Configuration
# -----------------------------------------------------
BACKEND_URL=http://agentnav-backend:8080 # Internal URL for agent-to-agent (A2A) communication
ENVIRONMENT=development
LOG_LEVEL=debug

# -----------------------------------------------------
# 4. Frontend (agentnav-frontend) Configuration
# Note: VITE variables are exposed to the browser and should only store non-sensitive public keys
# -----------------------------------------------------
VITE_API_URL=http://localhost:8080 # The host URL for the browser to call the API
VITE_GEMINI_API_KEY_PUBLIC="your-gemini-api-key-here" # WARNING: This is only if the frontend calls Gemini directly (NOT recommended, remove this if using backend proxy)
```

#### `Makefile`

This provides the desired single-command developer experience.

```makefile
# Makefile for Agentic Navigator Podman/Docker Compose development

# Set default compose command (prefers podman-compose for consistency)
COMPOSE_COMMAND := podman-compose
ifeq ($(shell command -v podman-compose 2>/dev/null),)
  COMPOSE_COMMAND := docker-compose
endif
ifeq ($(shell command -v docker-compose 2>/dev/null),)
  COMPOSE_COMMAND := docker compose
endif

.PHONY: help setup build up down logs test demo clean

help:
	@echo "Agentic Navigator Local Development Commands"
	@echo "---------------------------------------------------------"
	@echo "Using compose command: $(COMPOSE_COMMAND)"
	@echo "---------------------------------------------------------"
	@echo "make setup  - Run one-time setup (podman machine, .env copy, build, and up -d)"
	@echo "make build  - Build all development containers"
	@echo "make up     - Start all services in detached mode"
	@echo "make down   - Stop and remove all containers and networks"
	@echo "make logs   - Follow logs for all services"
	@echo "make test   - Run test suite in a container"
	@echo "make demo   - Start the demo environment (uses podman-compose.demo.yml)"
	@echo "make clean  - Stop/remove containers and remove volume data (DANGER)"

setup: .env build up
	@echo "---------------------------------------------------------"
	@echo "Setup complete. App is running."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8080/docs"
	@echo "Firestore UI: http://localhost:9090"
	@echo "---------------------------------------------------------"

.env:
	@echo "Creating .env file from .env.example..."
	cp .env.example .env

build:
	$(COMPOSE_COMMAND) build

up:
	$(COMPOSE_COMMAND) up -d

down:
	$(COMPOSE_COMMAND) down

logs:
	$(COMPOSE_COMMAND) logs -f

test: build
	$(COMPOSE_COMMAND) -f podman-compose.yml -f podman-compose.test.yml run --rm agentnav-backend pytest

demo: build
	$(COMPOSE_COMMAND) -f podman-compose.yml -f podman-compose.demo.yml up -d

clean: down
	@echo "Removing persistent Firestore data volume..."
	$(COMPOSE_COMMAND) rm -f -v firestore-data
```

#### `scripts/podman-setup.sh`

This script handles the Podman machine startup (if needed on macOS/Windows) before calling the `Makefile`.

```bash
#!/bin/bash
# scripts/podman-setup.sh
# One-command script to set up the local development environment

set -e # Exit immediately if a command exits with a non-zero status.

echo "--- Starting Agentic Navigator Local Environment Setup ---"

# 1. Check for Podman and attempt to start the machine (primarily for macOS/Windows)
if command -v podman &> /dev/null
then
    echo "Podman detected. Checking machine status..."
    if podman machine list | grep -q 'Running'; then
        echo "Podman machine is already running."
    elif podman machine list | grep -q 'Stopped'; then
        echo "Starting Podman machine..."
        podman machine start
    else
        echo "Creating and starting new Podman machine..."
        podman machine init
        podman machine start
    fi
else
    if command -v docker &> /dev/null
    then
        echo "Podman not found. Falling back to Docker."
    else
        echo "Error: Neither Podman nor Docker is installed. Please install one before continuing."
        exit 1
    fi
fi

# 2. Call the Makefile's setup target
echo "Building and starting services via Makefile..."
make setup

echo "--- Setup Complete! Happy Hacking. ---"
```
