# Feature Request #001: Podman-Based Local Development Environment

**Feature Status:** ?? Ideation & Planning  
**Priority:** High  
**Timeline:** 1 Week  
**Assigned To:** TBD

---

## Is your feature request related to a problem? Please describe.

Currently, developers working on **Agentic Navigator** face significant friction when setting up a local development environment. The project requires:

- **Frontend:** React + TypeScript application with bun runtime
- **Backend:** FastAPI application with Python dependencies managed by uv
- **External Services:** Firestore emulator, Secret Manager (for Gemini API keys), and potentially other GCP services
- **Dependencies:** Multiple environment variables, service account configurations, and API keys

**The Problem:**
- Developers spend 2-4 hours manually configuring their local environment
- Inconsistent setups lead to "works on my machine" issues
- New team members struggle to onboard and contribute quickly
- Testing locally requires manual setup of Firestore emulator and mock services
- No standardized way to demo the application locally with all services running

**I'm always frustrated when** I need to:
- Manually install bun, uv, Python, Node.js, and configure all dependencies
- Set up Firestore emulator separately and configure authentication
- Manually manage environment variables and secrets
- Coordinate multiple terminal windows to run frontend, backend, and emulators
- Debug issues that only appear in production because local setup differs

---

## Describe the solution you'd like

**Create a Podman-based local development environment** with the following components:

### 1. **Dockerfile for Frontend (Development)**
- Multi-stage build for optimal development experience
- Includes bun runtime and development dependencies
- Hot-reload support for Vite development server
- Exposes port 5173 for local development
- Compatible with Podman (uses standard Dockerfile format)

### 2. **Dockerfile for Backend (Development)**
- Python 3.11+ base image with uv pre-installed
- FastAPI development server with hot-reload
- Includes ADK dependencies and agent configurations
- Exposes port 8080 for API access
- Includes Firestore emulator client libraries
- Compatible with Podman (uses standard Dockerfile format)

### 3. **podman-compose.yml for Complete Local Stack**
A comprehensive `podman-compose.yml` file that orchestrates:

**Services:**
- `agentnav-frontend` - React development server with hot-reload
- `agentnav-backend` - FastAPI backend with auto-reload
- `firestore-emulator` - Google Firestore emulator for local data persistence
- `redis` (optional) - For caching and session management if needed
- `nginx` (optional) - Reverse proxy for unified local domain access

**Features:**
- Volume mounts for live code reloading (no rebuild needed for code changes)
- Environment variable management via `.env` file
- Network isolation between services
- Health checks for service dependencies
- Port mapping for easy local access

### 4. **podman-compose.test.yml**
- Lightweight configuration for running test suites
- Includes test databases and mock services
- Configurable via environment variables
- Supports parallel test execution

### 5. **podman-compose.demo.yml**
- Production-like configuration for demo purposes
- Includes all services configured with demo data
- Optimized for presentation and stability
- Includes sample data seeds

### 6. **Supporting Files**
- `.env.example` - Template for environment variables
- `.dockerignore` - Optimize build context (Podman-compatible)
- `Makefile` - Simplified commands for common operations (recommended)
- `scripts/podman-setup.sh` - One-command setup script (handles Podman machine startup)
- `scripts/podman-teardown.sh` - Cleanup script
- `docs/local-development.md` - Developer guide

**Expected Developer Experience:**

**Option 1: Using Makefile (Recommended)**
```bash
# Clone repository
git clone <repo-url>
cd agentnav

# One command setup (handles Podman machine, .env, build & start)
make setup

# View logs
make logs

# Run tests
make test

# Stop everything
make down

# See all commands
make help
```

**Option 2: Using podman-compose directly**
```bash
# Clone repository
git clone <repo-url>
cd agentnav

# Copy environment template
cp .env.example .env
# Edit .env with your Gemini API key

# Start Podman machine (macOS only)
podman machine start

# Start all services
podman-compose up -d

# View logs
podman-compose logs -f

# Run tests
podman-compose -f docker-compose.test.yml run --rm agentnav-backend pytest

# Stop everything
podman-compose down
```

**Note:** podman-compose uses Docker Compose V2 syntax and is compatible with docker-compose.yml format. Developers can use either 'podman-compose' or 'docker-compose' commands. The Makefile automatically detects which is available.

**Access Points:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080`
- API Docs: `http://localhost:8080/docs`
- Firestore Emulator: `http://localhost:8081`

---

## Describe alternatives you've considered

### Alternative 1: **Manual Setup Scripts**
- **Pros:** Simple bash scripts, no Docker dependency
- **Cons:** Platform-specific issues (macOS vs Linux vs Windows), doesn't solve dependency conflicts, still requires manual configuration

### Alternative 2: **Vagrant with Virtual Machines**
- **Pros:** Full OS isolation, consistent environment
- **Cons:** Heavy resource usage, slower startup, complex configuration, overkill for this use case

### Alternative 3: **Cloud-Based Development (Cloud Shell / Codespaces)**
- **Pros:** Always consistent, no local setup
- **Cons:** Internet dependency, latency, potential costs, less control over environment

### Alternative 4: **Kubernetes Local (minikube / kind)**
- **Pros:** Matches production environment closely
- **Cons:** Overkill for local development, complex setup, slower than Podman Compose

### **Why Podman Compose is Best:**
- ? Fast startup and teardown
- ? Cross-platform compatibility (macOS, Linux, Windows via WSL2)
- ? Lightweight resource usage (rootless containers)
- ? Native volume mounting for live code reload
- ? Easy to extend with additional services
- ? Industry standard Docker Compose syntax compatibility
- ? Matches containerization strategy already in use (Podman for production builds)
- ? Rootless security model (no daemon required)
- ? Compatible with docker-compose.yml format (can use either tool)

---

## Additional context

### Current State
- Project uses **Podman** for production container builds (as per SYSTEM_INSTRUCTION.md)
- Cloud Build workflow exists for CI/CD (`cloudbuild.yaml`)
- Frontend is a React + TypeScript + Vite application
- Backend architecture is planned but not yet fully implemented (FastAPI + ADK)
- **Podman-compose** uses Docker Compose V2 syntax and is compatible with `docker-compose.yml` format

### Technical Requirements

**Frontend Dockerfile:**
- Base: `node:20-alpine` or `oven/bun:latest`
- Development dependencies: Vite, TypeScript, React
- Hot-reload via volume mounts
- Port: 5173

**Backend Dockerfile:**
- Base: `python:3.11-slim` or `uvicornorg/uvicorn-gunicorn:python3.11`
- Python dependencies: FastAPI, uvicorn, Google ADK, Firestore client
- Development dependencies: pytest, black, mypy
- Hot-reload via uvicorn `--reload` flag
- Port: 8080

**Firestore Emulator:**
- Use `gcr.io/google.com/cloudsdktool/cloud-sdk:emulators` image
- Configure via environment variables
- Persistent data via volume mount
- Port: 8080 (or custom port)

### Environment Variables Needed

```bash
# Gemini API
GEMINI_API_KEY=your-api-key-here

# Firestore
FIRESTORE_EMULATOR_HOST=firestore-emulator:8080
FIRESTORE_PROJECT_ID=agentnav-dev
FIRESTORE_DATABASE_ID=(default)

# Backend
BACKEND_URL=http://agentnav-backend:8080
ENVIRONMENT=development

# Frontend
VITE_API_URL=http://localhost:8080
VITE_GEMINI_API_KEY=your-api-key-here
```

### Success Criteria

? **Development Setup:**
- New developer can go from `git clone` to running application in < 10 minutes
- Single command (`make setup`) handles Podman machine, environment setup, build, and start
- Alternative: `podman-compose up` (preferred) or `docker-compose up` starts all services
- Code changes reflect immediately without container rebuild

? **Testing Setup:**
- Tests can run in isolated containers
- Test database is automatically provisioned and cleaned
- CI/CD can use same Podman Compose configuration

? **Demo Setup:**
- Demo environment runs with realistic sample data
- All services are stable and properly configured
- Can be used for stakeholder presentations

### Timeline Breakdown (1 Week)

- **Day 1-2:** Design podman-compose architecture, create Dockerfiles for frontend and backend
- **Day 3-4:** Implement podman-compose.yml with all services, configure Firestore emulator
- **Day 5:** Create test and demo configurations, write setup scripts
- **Day 6:** Documentation and developer guide
- **Day 7:** Testing, refinement, and team review

### Dependencies

- **Podman** installed on developer machines (or Docker Desktop as fallback)
- **podman-compose** installed (or docker-compose as compatible alternative)
- `.env.example` file with all required environment variables documented
- Access to Google Cloud SDK for Firestore emulator (or use containerized version)

**Note:** The compose files will use standard Docker Compose V2 syntax, making them compatible with both `podman-compose` and `docker-compose` commands for maximum developer flexibility.

### Future Enhancements (Post-MVP)

- [ ] Add PostgreSQL container for future database needs
- [ ] Include Redis for caching
- [ ] Add monitoring stack (Prometheus + Grafana)
- [ ] Include mock Gemini API server for offline development
- [ ] Add pre-commit hooks via Docker
- [ ] Include database migration tools
- [ ] Add performance profiling tools

### Related Issues

- Need to align with production deployment strategy (Cloud Run)
- Should match Podman build process where possible
- May need to update CI/CD to use Podman Compose for integration tests
- Compose files use standard Docker Compose syntax for compatibility with both Podman and Docker

---

## Acceptance Criteria

- [ ] `podman-compose.yml` starts all required services with single command
- [ ] Frontend Dockerfile supports hot-reload development (Podman-compatible)
- [ ] Backend Dockerfile supports hot-reload development (Podman-compatible)
- [ ] Firestore emulator is configured and accessible
- [ ] `.env.example` file documents all required variables
- [ ] `podman-compose.test.yml` supports running test suites
- [ ] `podman-compose.demo.yml` provides stable demo environment
- [ ] Documentation exists for local development workflow
- [ ] Setup script automates initial configuration (`scripts/podman-setup.sh`)
- [ ] All services have health checks
- [ ] Code changes reflect immediately without container rebuild
- [ ] Works on macOS, Linux, and Windows (via WSL2)
- [ ] Compatible with both `podman-compose` and `docker-compose` commands (standard Docker Compose syntax)

---

**Feature Request Created:** [Date]  
**Last Updated:** [Date]  
**Estimated Effort:** 1 Week (40 hours)
