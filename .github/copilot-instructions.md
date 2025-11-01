## Agentic Navigator — Copilot / AI Agent Instructions

This file provides focused, actionable knowledge for AI coding agents to be productive in this repository.
Keep guidance short and concrete: commands, file locations, patterns, and gotchas.

---

## 1. Quick Context (Big Picture)

### Architecture Overview
- **Frontend**: React 19 + TypeScript SPA using Vite (monorepo structure in root directory)
  - Entry point: `index.tsx` → `App.tsx`
  - Components: `components/` (AgentCard, InteractiveGraph, ResultsDisplay, icons)
  - Services: `services/geminiService.ts` (API client with Gemini integration)
  - Types: `types.ts` (shared TypeScript interfaces)
  
- **Backend**: FastAPI service in `backend/` directory
  - Entry: `backend/main.py`
  - Agents: `backend/agents/` (visualizer_agent.py)
  - Services: `backend/services/` (gemma_service.py, firestore_client.py, prompt_loader.py)
  - Gemma GPU Service: `backend/gemma_service/` (separate FastAPI app for GPU inference)
  
- **Infrastructure**: Podman-based containers for local development
  - Orchestration: `Makefile` (primary) and `docker-compose.yml`
  - Firestore emulator for local persistence
  - Cloud deployment: Google Cloud Run with GPU support (europe-west1)

### Tech Stack
- **Frontend**: React 19.2, TypeScript 5.8, Vite 6.2, Recharts 3.3, @google/genai 1.28
- **Backend**: FastAPI, Python 3.11+, httpx, pydantic, google-cloud-firestore
- **AI Models**: Google Gemini 2.5 Pro (reasoning), Gemma 7B (GPU-accelerated inference)
- **Dev Tools**: Vitest (frontend tests), pytest (backend tests), ESLint, Prettier
- **Deployment**: Cloud Run, Artifact Registry, Secret Manager, Terraform Cloud

---

## 2. How to Run (Developer Workflows)

### Quick Start
```bash
# Setup everything (recommended for first run)
make setup

# View logs
make logs

# Stop services
make down

# See all commands
make help
```

### Running Services Individually
**Frontend** (port 3000, internally 5173):
```bash
npm run dev           # Start dev server with hot-reload
npm run build         # Production build
npm run test          # Run Vitest tests
npm run lint          # Run ESLint
npm run format        # Run Prettier
```

**Backend** (port 8080):
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# Or using Makefile from root:
make logs-backend     # View backend logs
make shell-backend    # Open shell in backend container
```

**Backend Tests**:
```bash
cd backend
pytest                # Run all tests
pytest -v             # Verbose output
pytest tests/test_firestore_client.py  # Specific test file
```

### Environment Setup
1. Copy `.env.example` to `.env`
2. Add your `GEMINI_API_KEY` (required)
3. Configure optional vars:
   - `FIRESTORE_PROJECT_ID` (default: agentnav-dev)
   - `GEMMA_SERVICE_URL` (for GPU service integration)
   - `ENVIRONMENT` (development/staging/production)

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080
- API Documentation: http://localhost:8080/docs
- Firestore Emulator: http://localhost:8081

---

## 3. Integration / Runtime Conventions

### Security Pattern (CRITICAL)
**DO NOT expose API keys in frontend code.**
- ❌ Bad: `window.GEMINI_API_KEY` or `VITE_GEMINI_API_KEY` in browser
- ✅ Good: Frontend → Backend API → Backend calls external services
- Legacy code in `services/geminiService.ts` has frontend API calls—migrate to backend endpoints
- `vite.config.ts` intentionally omits API key exposure for security

### Backend Endpoints
**Main API** (`backend/main.py`):
- `GET /healthz` — Cloud Run health check (recommended)
- `GET /health` — Deprecated health check (use /healthz)
- `GET /api/docs` — API documentation
- `POST /api/generate` — Text generation via Gemma GPU service
  - Requires: `GEMMA_SERVICE_URL` environment variable
  - Request: `{"prompt": str, "max_tokens": int, "temperature": float}`
  - Response: `{"generated_text": str, "service_used": "gemma-gpu-service"}`
- `POST /api/visualize` — Graph generation via Visualizer Agent
  - Request: `{"document": str, "content_type": "document"|"codebase"}`
  - Returns: `{type, title, nodes, edges, generated_by}`

**Gemma GPU Service** (`backend/gemma_service/main.py`):
- Separate FastAPI app deployed on Cloud Run with NVIDIA L4 GPU
- Serves Gemma 7B model for text generation
- Endpoints: `/generate`, `/embeddings`, `/healthz`

### CORS Configuration
Backend allows local dev origins (see `backend/main.py`):
- `http://localhost:3000`
- `http://localhost:5173`

---

## 4. Agent & Response Contract (CRITICAL)

### Frontend-Backend Contract
**Function**: `runAgenticNavigator(documentText)` in `services/geminiService.ts`

**Request**: Plain text document or code

**Response**: Must be a single JSON object matching `analysisSchema`:
```typescript
{
  summary: string,           // Comprehensive summary
  visualization: {
    type: 'MIND_MAP' | 'DEPENDENCY_GRAPH',  // Mind map for docs, dependency graph for code
    title: string,
    nodes: Array<{
      id: string,            // Unique identifier (e.g., "concept_1", "function_A")
      label: string,         // Display name
      group?: string         // Optional styling group
    }>,
    edges: Array<{
      from: string,          // Source node ID (must match a node.id)
      to: string,            // Target node ID (must match a node.id)
      label?: string         // Optional relationship label
    }>
  }
}
```

**Example Valid Nodes/Edges**:
```json
{
  "nodes": [
    {"id": "concept_1", "label": "Core Concept", "group": "Core"},
    {"id": "concept_2", "label": "Related Idea", "group": "Supporting"}
  ],
  "edges": [
    {"from": "concept_1", "to": "concept_2", "label": "relates_to"}
  ]
}
```

**Important**:
- All `from` and `to` in edges MUST reference valid node `id` values
- Return raw JSON (no markdown code fences like ```json)
- Frontend strips code fences as fallback, but avoid them
- Model used: `gemini-2.5-pro` with `responseMimeType: "application/json"`

### TypeScript Types (`types.ts`)
- `AgentName`: ORCHESTRATOR | SUMMARIZER | LINKER | VISUALIZER
- `AgentStatusValue`: IDLE | PROCESSING | DONE | ERROR
- `VisualizationType`: MIND_MAP | DEPENDENCY_GRAPH
- `GraphNode`: {id, label, group?}
- `GraphEdge`: {from, to, label?}
- `AnalysisResult`: {summary, visualization}

---

## 5. Common Patterns & Gotchas

### Security
- Never commit API keys to git
- Use `.env` file (gitignored) for local development
- In production, use Secret Manager (see `.env.example` comments)
- Frontend should call `/api/visualize` backend endpoint, not Gemini API directly

### Agent Simulation
- `App.tsx` has `initialAgents` state for UI visualization
- Agent progress is simulated visually (`simulateAgentActivity()`)
- Real work happens in the Gemini API prompt and backend agents
- Agents: Orchestrator → Summarizer → Linker → Visualizer (shown in UI)

### Gemma GPU Service Integration
- Backend expects `GEMMA_SERVICE_URL` env var to call GPU service
- If missing, `/api/generate` and `/api/visualize` return 503 errors
- Gemma service runs separately (on Cloud Run with GPU in production)
- Local development: typically mocked or GPU service disabled

### Prompt Management
- Visualizer agent loads prompts from Firestore (`backend/services/prompt_loader.py`)
- Fallback prompt available for development (`visualizer_agent.py`)
- Production/staging: Firestore prompts are required (no fallback)

### Schema Changes
When modifying the analysis schema:
1. Update `services/geminiService.ts` (frontend expectations)
2. Update `types.ts` (TypeScript types)
3. Update backend validation in `backend/agents/visualizer_agent.py`
4. Keep changes backward compatible (add optional fields, don't rename required ones)
5. Update tests: `components/__tests__/` and `backend/tests/`

---

## 6. Files to Inspect First (High ROI)

### Essential Documentation
- `README.md` — Project overview, features, deployment info
- `docs/local-development.md` — Detailed setup, troubleshooting, workflow guide
- `docs/SYSTEM_INSTRUCTION.md` — Full system architecture and deployment

### Frontend Core Files
- `App.tsx` — Main app component, agent state management, UI flow
- `services/geminiService.ts` — API client, prompt engineering, schema definition
- `types.ts` — TypeScript type definitions
- `components/AgentCard.tsx` — Agent status UI
- `components/InteractiveGraph.tsx` — Graph visualization (Recharts)
- `components/ResultsDisplay.tsx` — Summary and graph display

### Backend Core Files
- `backend/main.py` — FastAPI app, endpoint definitions, CORS
- `backend/agents/visualizer_agent.py` — Graph generation agent
- `backend/services/gemma_service.py` — HTTP client for Gemma GPU service
- `backend/services/firestore_client.py` — Firestore integration
- `backend/services/prompt_loader.py` — Dynamic prompt loading
- `backend/pyproject.toml` — Python dependencies

### Gemma GPU Service
- `backend/gemma_service/main.py` — FastAPI app for GPU inference
- `backend/gemma_service/model_loader.py` — Gemma model loading
- `backend/gemma_service/inference.py` — Text generation logic

### Configuration Files
- `.env.example` — Environment variables template
- `package.json` — Frontend dependencies and scripts
- `vite.config.ts` — Vite configuration (note: no API key exposure)
- `docker-compose.yml` — Local development stack
- `Makefile` — Development commands (Podman-based)

---

## 7. Development Practices

### Testing
**Frontend (Vitest)**:
```bash
npm run test                                    # Run all tests
npm run test -- --watch                         # Watch mode
npm run test -- components/__tests__/AgentCard.test.tsx  # Specific test
```
- Test files: `components/__tests__/*.test.tsx`
- Setup: `vitest.config.ts`, `vitest.setup.ts`
- Uses: @testing-library/react, @testing-library/jest-dom

**Backend (pytest)**:
```bash
cd backend
pytest                                          # Run all tests
pytest -v                                       # Verbose
pytest --cov                                    # Coverage report
```
- Test files: `backend/tests/test_*.py`
- Dependencies in `pyproject.toml` under `[project.optional-dependencies.dev]`

### Linting & Formatting
**Frontend**:
```bash
npm run lint          # ESLint (config: .eslintrc.json)
npm run format        # Prettier (config: .prettierrc.json)
npm run format:check  # Check formatting without fixing
```
- ESLint rules: TypeScript, React, React Hooks
- Prettier: 2 spaces, semicolons, single quotes

**Backend**:
```bash
cd backend
black .               # Format Python code (if installed)
mypy .                # Type checking (if installed)
```

### Pre-commit Hooks
- Configured in `.pre-commit-config.yaml`
- Runs linters and formatters before git commits

### Making Changes
1. Create feature branch from main
2. Make minimal, focused changes
3. Test locally (`make test`)
4. Lint and format code
5. Commit and push
6. Open pull request

---

## 8. When in Doubt — Useful Checks

### Service Health Checks
```bash
# Start all services
make setup

# Check health endpoints
curl http://localhost:8080/healthz              # Backend health
curl http://localhost:8080/docs                 # API docs
curl http://localhost:3000                      # Frontend (HTML)

# View logs
make logs                                       # All services
make logs-frontend                              # Frontend only
make logs-backend                               # Backend only
make logs-firestore                             # Firestore emulator

# Check running containers
make ps
```

### Testing Full Stack
1. Start services: `make setup`
2. Open browser: http://localhost:3000
3. Paste a sample document or code
4. Click "Run Navigator"
5. Verify:
   - Agents show progress (IDLE → PROCESSING → DONE)
   - Summary appears
   - Graph renders with nodes and edges
6. Check logs: `make logs` for errors

### Debugging Backend Issues
```bash
# Enter backend container
make shell-backend

# Check Python environment
python --version
pip list

# Test imports
python -c "from services.gemma_service import generate_with_gemma"

# Check environment variables
echo $GEMINI_API_KEY
echo $GEMMA_SERVICE_URL
echo $FIRESTORE_EMULATOR_HOST
```

### Common Issues

**Port conflicts**:
```bash
# Check what's using port 3000 or 8080
lsof -i :3000
lsof -i :8080

# Kill process
kill -9 <PID>
```

**Podman machine not running (macOS)**:
```bash
podman machine start
make podman-start  # Or use Makefile
```

**Container build fails**:
```bash
make clean         # Remove all containers/volumes
make build         # Rebuild
```

**Environment variables not loading**:
```bash
# Verify .env file exists
cat .env

# Restart services to pick up changes
make restart
```

**Firestore connection issues**:
- Check `FIRESTORE_EMULATOR_HOST=firestore-emulator:8080` in backend env
- Verify Firestore container is healthy: `make ps`
- Check emulator logs: `make logs-firestore`

---

## 9. Deployment (Production)

### Cloud Run Services
1. **Frontend**: Static SPA served on us-central1
2. **Backend**: FastAPI app on europe-west1 (near GPU service)
3. **Gemma GPU Service**: Gemma 7B on europe-west1 with NVIDIA L4 GPU

### Infrastructure as Code
- **Terraform**: `terraform/` directory
- **Cloud Build**: `cloudbuild.yaml`, `cloudbuild-frontend.yaml`, `cloudbuild-backend.yaml`
- **GitHub Actions**: Automated deployment via Workload Identity Federation

### Key Environment Variables (Production)
- `GEMINI_API_KEY` — From Secret Manager
- `GEMMA_SERVICE_URL` — Gemma GPU service URL
- `FIRESTORE_PROJECT_ID` — Production project ID
- `ENVIRONMENT=production` — Enforces strict settings

### Deployment Docs
- `docs/SYSTEM_INSTRUCTION.md` — Full deployment guide
- `docs/GCP_SETUP_GUIDE.md` — GCP project setup
- `docs/GPU_SETUP_GUIDE.md` — Gemma GPU service setup
- `docs/WIF_GITHUB_SECRETS_SETUP.md` — GitHub Actions authentication

---

## 10. Additional Resources

### Project Documentation
- `docs/HACKATHON_SUBMISSION_GUIDE.md` — Hackathon requirements
- `docs/ARCHITECTURE_DIAGRAM_GUIDE.md` — Architecture diagrams
- `docs/PROMPT_MANAGEMENT_GUIDE.md` — Firestore prompt management
- `docs/TESTING_STRATEGY.md` — Testing approach

### External Links
- Google Gemini API: https://ai.google.dev/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Vite Docs: https://vitejs.dev/
- Podman Docs: https://podman.io/

---

**If anything is unclear or you need more examples (e.g., sample JSON outputs, specific command sequences), ask for clarification and I'll provide detailed guidance.**
