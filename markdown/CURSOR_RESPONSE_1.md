# Cursor Response #1: Podman Local Development Setup

## Summary

Based on the feature request and system instructions, I've analyzed the project structure and prepared a complete implementation plan for the Podman-based local development environment.

## Current State Analysis

- **Frontend:** React + TypeScript in root directory, using bun (per SYSTEM_INSTRUCTION.md)
- **Backend:** Not yet implemented (planned FastAPI + ADK structure)
- **Port Configuration:** Vite currently configured for port 3000 (feature request mentions 5173)
- **Project Structure:** Monorepo with frontend in root, backend planned for `backend/` directory

## Complete File List to Create

1. `Dockerfile.frontend` - Development Dockerfile for frontend
2. `backend/Dockerfile` - Development Dockerfile for backend
3. `docker-compose.yml` - Main development stack (Podman-compatible)
4. `docker-compose.test.yml` - Test environment
5. `docker-compose.demo.yml` - Demo environment
6. `.env.example` - Environment variable template
7. `.dockerignore` - Build context optimization
8. `scripts/podman-setup.sh` - One-command setup script
9. `scripts/podman-teardown.sh` - Cleanup script
10. `backend/main.py` - Minimal FastAPI application
11. `backend/pyproject.toml` - Python dependencies (using uv)
12. `docs/local-development.md` - Developer guide

## Implementation Details

### Frontend Dockerfile

- Uses `oven/bun:latest` base image
- Supports hot-reload via volume mounts
- Exposes port 5173 (or 3000 based on vite.config)

### Backend Dockerfile

- Python 3.11-slim with uv for dependency management
- FastAPI with uvicorn hot-reload
- Includes Firestore client libraries
- Exposes port 8080

### Docker Compose Configuration

- Uses Docker Compose V2 syntax (compatible with both podman-compose and docker-compose)
- Three services: frontend, backend, firestore-emulator
- Volume mounts for live code reloading
- Health checks for all services
- Network isolation

### Backend Structure

- Minimal FastAPI application to get started
- Health check endpoints
- CORS middleware for local development
- Ready for ADK integration

## Questions to Address

1. **Backend Structure:** Should I create a more complete FastAPI structure now, or is the minimal skeleton sufficient for the MVP?
2. **Bun Lockfile:** Should I create an empty `bun.lockb` file, or let bun generate it on first container build?
3. **Python Dependencies:** The Dockerfile tries to use `uv.lock` first, then falls back to installing packages directly. Should I create a `requirements.txt` instead for simplicity?
4. **Port Configuration:** I noticed vite.config.ts uses port 3000, but the feature request mentions 5173. Should I align them, or keep port 3000?

## Next Steps

After files are created:

1. Make setup scripts executable: `chmod +x scripts/podman-setup.sh scripts/podman-teardown.sh`
2. Test the setup: `./scripts/podman-setup.sh`
3. Verify all services start correctly
4. Document any issues encountered
