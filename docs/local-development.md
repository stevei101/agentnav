# Local Development Guide

## ADK Quickstart Process

This local development environment follows the **Google ADK Quickstart** philosophy:
> **"No heavy cloud setups. No complex DevOps. Just clone, code, run—and see your agent live in minutes"**

The containerized setup enables you to:
- ✅ **Focus on agent logic** - not environment configuration
- ✅ **Iterate quickly** - changes reflect immediately with hot-reload
- ✅ **Match production** - local environment mirrors Cloud Run deployment
- ✅ **Get started fast** - single command setup (`make setup`)

## Prerequisites

- **Podman** (or Docker Desktop as fallback)
  - macOS: `brew install podman`
  - Linux: See [Podman Installation](https://podman.io/getting-started/installation)
  - Windows: Use WSL2 with Podman

- **podman-compose** (optional - Makefile uses Podman commands directly)
  ```bash
  pip install podman-compose
  ```

## Quick Start

### Option 1: Using Makefile (Recommended)

```bash
git clone <repo-url>
cd agentnav

# One command to set everything up!
make setup
```

The `make setup` command will:
- Check/start Podman machine (macOS)
- Create `.env` file from template
- Build and start all services

Then simply:
```bash
make logs    # View logs
make down    # Stop services
make help    # See all available commands
```

### Option 2: Using Setup Script

```bash
git clone <repo-url>
cd agentnav
./scripts/podman-setup.sh
```

### Option 3: Manual Setup

```bash
git clone <repo-url>
cd agentnav
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
podman-compose up -d --build
```

## Access Services

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8080
- **API Documentation:** http://localhost:8080/docs
- **Firestore Emulator API:** http://localhost:8081 (API-only, no built-in UI)

## Development Workflow

### Making Code Changes

Both frontend and backend support **hot-reload**:

- **Frontend:** Edit files in root directory, changes appear immediately
- **Backend:** Edit files in `backend/` directory, FastAPI auto-reloads

### Common Makefile Commands

```bash
make help           # Show all available commands
make up             # Start all services
make down           # Stop all services
make restart        # Restart all services
make logs           # Follow all logs
make logs-frontend  # Follow frontend logs only
make logs-backend   # Follow backend logs only
make ps             # Show running containers
make build          # Rebuild containers
make test           # Run backend tests
make demo           # Start demo environment
make clean          # Stop and remove everything
```

### Using Compose Directly

If you prefer using compose commands directly:

```bash
# View logs
podman-compose logs -f
podman-compose logs -f agentnav-frontend

# Run tests
podman-compose -f docker-compose.test.yml run --rm agentnav-backend pytest

# Demo environment
podman-compose -f docker-compose.demo.yml up -d
```

## Troubleshooting

### Port Already in Use

If ports 3000, 8080, or 8081 are already in use:

1. Edit `docker-compose.yml` and change port mappings
2. Update `.env` with new URLs

### Container Build Fails

```bash
# Clean build
podman-compose down -v
podman-compose build --no-cache
podman-compose up -d
```

### Firestore Emulator Issues

```bash
# Reset Firestore data
podman-compose down -v firestore-emulator
podman-compose up -d firestore-emulator
```

## Cleanup

```bash
# Using Makefile (recommended)
make clean
# or
make teardown

# Using script
./scripts/podman-teardown.sh

# Or manually
podman-compose down -v
```

## Architecture

```
┌─────────────────┐
│  Frontend (3000)│
│  React + Vite   │
└────────┬────────┘
         │
         │ HTTP
         │
┌────────▼────────┐
│ Backend (8080)  │
│  FastAPI + ADK  │
└────────┬────────┘
         │
         │ gRPC
         │
┌────────▼────────┐
│Firestore (8081) │
│    Emulator     │
└─────────────────┘
```

## Environment Variables

See `.env.example` for all available environment variables.

**Required:**
- `GEMINI_API_KEY` - Your Google Gemini API key

**Optional:**
- `FIRESTORE_PROJECT_ID` - Firestore project ID (default: `agentnav-dev`)
- `ENVIRONMENT` - Environment name (default: `development`)

