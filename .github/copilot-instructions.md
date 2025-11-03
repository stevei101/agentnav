# **agentnav - GitHub Copilot Instructions**

## **Project Overview**

agentnav is a multi-agent knowledge exploration system using Google Agent Development Kit (ADK) with Agent2Agent (A2A) Protocol. The system features a TypeScript/React frontend and Python/FastAPI backend with specialized AI agents, deployed serverlessly on Google Cloud Run with GPU acceleration support.

**Tech Stack:** TypeScript, React, Vite, Tailwind CSS, Python, FastAPI, Google ADK, A2A Protocol, Gemini/Gemma models, Firestore, Podman, Terraform, GitHub Actions

**Project Type:** Full-stack web application with AI agent orchestration

**Repository Size:** Medium (\~10-20K lines of code)

**Target Runtimes:**

* Frontend: Node.js 20+ (via bun), deploys to Cloud Run  
* Backend: Python 3.11+, deploys to Cloud Run with optional GPU support  
* Infrastructure: Terraform 1.5+, managed via Terraform Cloud

---

## **Architecture Components**

### **Frontend (TypeScript/React)**

* **Location:** `frontend/` directory  
* **Package Manager:** bun (fast JS runtime and package manager)  
* **Build Tool:** Vite with TypeScript  
* **Styling:** Tailwind CSS utility classes only  
* **Deployment:** Static assets served via Nginx on Cloud Run (us-central1)

### **Backend (Python/FastAPI)**

* **Location:** `backend/` directory  
* **Package Manager:** uv (fast Python package resolver)  
* **Framework:** FastAPI with async/await  
* **AI Orchestration:** Google ADK with A2A Protocol  
* **Deployment:** Cloud Run serverless (europe-west1)

### **Agent Architecture**

Four specialized agents coordinate via A2A Protocol:

1. **Orchestrator Agent** \- Receives input, determines content type, delegates tasks  
2. **Summarizer Agent** \- Generates comprehensive content summaries  
3. **Linker Agent** \- Identifies entities and their relationships  
4. **Visualizer Agent** \- Creates graph structures (Mind Maps/Dependency Graphs)

All agents communicate asynchronously via A2A Protocol and persist state in Firestore.

### **Gemma GPU Service**

* **Location:** `backend/gemma_service/`  
* **Purpose:** GPU-accelerated model inference using Gemma open-source models  
* **Hardware:** NVIDIA L4 GPU on Cloud Run (europe-west1)  
* **Models:** Gemma 7B or 2B with optional 8-bit quantization

### **Infrastructure**

* **Database:** Firestore (NoSQL) for session memory and knowledge caching  
* **Secrets:** Google Secret Manager (never embed credentials)  
* **Container Registry:** Google Artifact Registry (GAR)  
* **CI/CD:** GitHub Actions → Terraform Cloud → Cloud Run  
* **DNS/TLS:** Cloud DNS + Cloud Run managed TLS for agentnav.lornu.com

---

## **Directory Structure**

agentnav/  
├── .github/  
│   ├── workflows/           \# GitHub Actions CI/CD  
│   └── copilot-instructions.md  
├── frontend/  
│   ├── src/  
│   │   ├── components/      \# React components  
│   │   ├── services/        \# API clients  
│   │   └── types/           \# TypeScript interfaces  
│   ├── package.json  
│   └── Containerfile        \# Podman build config  
├── backend/  
│   ├── agents/              \# ADK agent definitions  
│   │   ├── orchestrator.py  
│   │   ├── summarizer.py  
│   │   ├── linker.py  
│   │   └── visualizer.py  
│   ├── services/            \# External service clients  
│   ├── gemma_service/       \# GPU-accelerated model service  
│   ├── main.py              \# FastAPI app entry point  
│   ├── requirements.txt     \# Python dependencies  
│   └── Containerfile        \# Podman build config  
├── terraform/               \# Infrastructure as Code  
│   ├── main.tf  
│   ├── variables.tf  
│   └── modules/  
├── scripts/                 \# Build and deployment scripts  
└── docs/                    \# Additional documentation

---

## **Build & Development**

### **Frontend Development**

cd frontend  
bun install                  \# Install dependencies  
bun run dev                  \# Start dev server (port 5173\)  
bun run build                \# Production build  
bun run test                 \# Run tests  
bun run lint                 \# Lint code

**Important:** Always use bun, not npm/yarn. Bun is significantly faster for this codebase.

### **Backend Development**

cd backend  
uv venv                      \# Create virtual environment  
source .venv/bin/activate    \# Activate venv  
uv pip install \-r requirements.txt  
PORT=8080 uvicorn main:app \--host 0.0.0.0 \--port 8080 \--reload

**Important:** Backend MUST read PORT environment variable for Cloud Run compatibility.

### **Local Testing with Firestore Emulator**

gcloud emulators firestore start \--host-port=localhost:8080  
export FIRESTORE\_EMULATOR\_HOST=localhost:8080

### **Container Builds (Podman)**

\# Frontend  
podman build \-t agentnav-frontend:latest \-f frontend/Containerfile frontend/

\# Backend  
podman build \-t agentnav-backend:latest \-f backend/Containerfile backend/

\# Gemma GPU Service  
podman build \-t gemma-service:latest \-f backend/gemma\_service/Containerfile backend/gemma\_service/

### **Running Tests**

\# Frontend tests  
cd frontend && bun test

\# Backend tests  
cd backend && pytest tests/ \--cov=. \--cov-report=term-missing

\# Check coverage requirement (must be ≥70%)  
pytest tests/ \--cov=. \--cov-report=term \--cov-fail-under=70

**MANDATORY:** All new code must achieve minimum 70% test coverage before merge.

---

## **Deployment Pipeline**

### **CI/CD Flow**

1. Push code to GitHub  
2. GitHub Actions workflow triggers  
3. Authenticate via Workload Identity Federation (WIF)  
4. Terraform Cloud provisions/updates GCP infrastructure  
5. Podman builds container images, pushes to GAR

Deploy to Cloud Run:  
 \# Frontend (us-central1)gcloud run deploy agentnav-frontend \\  \--image gcr.io/$PROJECT\_ID/agentnav-frontend:$GITHUB\_SHA \\  \--region us-central1 \--platform managed \--port 80 \--timeout 300s\# Backend (europe-west1)gcloud run deploy agentnav-backend \\  \--image gcr.io/$PROJECT\_ID/agentnav-backend:$GITHUB\_SHA \\  \--region europe-west1 \--platform managed \--port 8080 \--timeout 300s \\  \--set-env-vars PORT=8080,GEMINI\_API\_KEY=$$GEMINI\_API\_KEY \\  \--set-secrets GEMINI\_API\_KEY=GEMINI\_API\_KEY:latest\# Gemma GPU Service (europe-west1)gcloud run deploy gemma-service \\  \--image $REGION-docker.pkg.dev/$PROJECT\_ID/$GAR\_REPO/gemma-service:$GITHUB\_SHA \\  \--region europe-west1 \--platform managed \\  \--cpu gpu \--memory 16Gi \--gpu-type nvidia-l4 \--gpu-count 1 \\  \--port 8080 \--timeout 300s

6. 

### **Cloud Run Requirements**

**CRITICAL:** All services must:

* Read `PORT` environment variable (Cloud Run sets this automatically)  
* Bind to `0.0.0.0` (not `127.0.0.1`)  
* Implement `/healthz` health check endpoint  
* Log to stdout/stderr (Cloud Run captures automatically)  
* Handle SIGTERM for graceful shutdown

### **Environment Variables**

Backend service requires:

* `PORT` \- Set by Cloud Run  
* `GEMINI_API_KEY` \- From Secret Manager  
* `GEMMA_SERVICE_URL` \- URL of Gemma GPU service  
* `FIRESTORE_PROJECT_ID`  
* `FIRESTORE_DATABASE_ID`  
* `ADK_AGENT_CONFIG_PATH`  
* `A2A_PROTOCOL_ENABLED=true`

---

## **Identity & Authentication**

### **Two Identity Mechanisms**

**1\. Workload Identity Federation (WIF)** \- For CI/CD

* GitHub Actions authenticates to GCP without static keys  
* Service Account: Deployment SA with `roles/run.admin`, `roles/artifactregistry.writer`  
* Configured in Terraform

**2\. Workload Identity (WI)** \- For Cloud Run Services

* Running containers use built-in Service Accounts to access GCP services  
* Backend SA needs: `roles/datastore.user`, `roles/secretmanager.secretAccessor`  
* No credentials in container images

**NEVER embed service account keys or credentials in code or containers.**

---

## **Firestore Schema**

### **Collections**

**sessions/** \- User session data

* Document ID: `session_id`  
* Fields: `created_at`, `updated_at`, `user_input`, `agent_states` (map)

**knowledge\_cache/** \- Cached analysis results

* Document ID: `content_hash`  
* Fields: `summary`, `visualization_data`, `created_at`, `expires_at`

**agent\_context/** \- Shared agent context via A2A Protocol

* Document ID: `session_id`  
* Fields: `context_data` (map), `last_updated_by` (agent name)

**agent\_prompts/** \- Agent prompt configurations

* Document ID: `{agent}_{prompt_type}` (e.g., `visualizer_graph_generation`)  
* Fields: `prompt_text`, `version`, `created_at`, `updated_at`, `metadata` (map)

---

## **Code Conventions & Best Practices**

### **General**

1. **RORO Pattern:** Receive an Object, Return an Object for all functions, APIs, DTOs  
2. **Type Safety:** Use TypeScript for frontend, Pydantic models for backend  
3. **Error Handling:** Centralized error handlers with consistent error shape: `{code: string, message: string, details?: object}`  
4. **Validation:** Validate all inputs early (frontend before API call, backend with Pydantic)  
5. **70% Coverage Rule:** All new/modified code MUST have ≥70% test coverage before merge

### **Frontend (React/TypeScript)**

* Pure functional components with named exports  
* Use TypeScript for all type safety  
* Tailwind utility classes only (no custom CSS)  
* Error Boundaries for graceful error handling  
* Lazy load visualization components  
* Guard early: validate props/data at component entry

**Example Component:**

interface VisualizationProps {  
  data: GraphData;  
  onError?: (error: Error) \=\> void;  
}

export function Visualization({ data, onError }: VisualizationProps) {  
  if (\!data?.nodes) {  
    return \<div\>No data available\</div\>;  
  }  
  // Component logic...  
}

### **Backend (Python/FastAPI)**

* Use async/await for all I/O operations  
* Pydantic models for request/response validation  
* Type hints for all function signatures  
* ADK agents inherit from base `Agent` class  
* A2A Protocol for inter-agent communication

**Example FastAPI Route:**

from fastapi import APIRouter  
from pydantic import BaseModel

class AnalyzeRequest(BaseModel):  
    content: str  
    content\_type: str

class AnalyzeResponse(BaseModel):  
    summary: str  
    visualization: dict

@router.post("/analyze", response\_model=AnalyzeResponse)  
async def analyze\_content(request: AnalyzeRequest):  
    \# Handler logic...  
    return AnalyzeResponse(summary="...", visualization={})

**Example ADK Agent:**

from google.adk import Agent, A2AProtocol

class SummarizerAgent(Agent):  
    async def process(self, context: dict) \-\> dict:  
        result \= await self.summarize(context\['document'\])  
          
        \# Share via A2A Protocol  
        await self.a2a.send\_message({  
            'agent': 'visualizer',  
            'type': 'summary\_complete',  
            'data': result  
        })  
          
        return result

### **Terraform**

* Use modules for reusable components  
* Always use variables for configurable values  
* Document all resources with comments  
* Use data sources for existing resources

---

## **Common Pitfalls & Solutions**

### **Cloud Run Issues**

❌ **Mistake:** Hardcoding port 8080 instead of reading PORT env var ✅ **Solution:** `port = int(os.getenv('PORT', 8080))`

❌ **Mistake:** Binding to 127.0.0.1 instead of 0.0.0.0 ✅ **Solution:** `uvicorn.run(app, host='0.0.0.0', port=port)`

❌ **Mistake:** Missing /healthz endpoint ✅ **Solution:** Add `@app.get('/healthz')` that returns 200 OK

### **GPU Service Issues**

❌ **Mistake:** Using THREE.CapsuleGeometry (requires r142+, we use r128) ✅ **Solution:** Use CylinderGeometry, SphereGeometry, or custom geometry

❌ **Mistake:** Not handling model loading timeout ✅ **Solution:** Set startup timeout to 300s in Cloud Run config

### **Identity Issues**

❌ **Mistake:** Embedding service account JSON keys in containers ✅ **Solution:** Use Workload Identity (WI) with Cloud Run Service Accounts

❌ **Mistake:** Using static keys in GitHub Secrets for CI/CD ✅ **Solution:** Use Workload Identity Federation (WIF)

### **Browser Storage Issues**

❌ **Mistake:** Using localStorage in artifacts (not supported in Claude.ai) ✅ **Solution:** Use React state (useState, useReducer) for in-memory storage

---

## **Testing Requirements**

### **Coverage Mandate**

**MANDATORY:** All new or modified code must achieve ≥70% test coverage as verified by:

\# Backend  
pytest tests/ \--cov=. \--cov-report=term \--cov-fail-under=70

\# Frontend  
bun test \--coverage \--coverageThreshold='{"global":{"lines":70}}'

### **Test Organization**

* **Frontend:** `frontend/src/__tests__/` \- Jest \+ React Testing Library  
* **Backend:** `backend/tests/` \- pytest with fixtures  
* **Integration:** `tests/integration/` \- Full workflow tests  
* **E2E:** `tests/e2e/` \- End-to-end user flows

### **What to Test**

* All ADK agent logic and A2A Protocol handlers  
* FastAPI route handlers and Pydantic validation  
* React components with different prop combinations  
* Firestore operations with mocked clients  
* Error handling and edge cases

---

## **Performance Optimization**

### **Frontend**

* Code split with Vite automatic chunking  
* Lazy load visualization components  
* Leverage Cloud Run CDN caching for static assets  
* Minimize bundle size

### **Backend**

* Use async Firestore operations  
* Cache analysis results in Firestore (check before processing)  
* Connection pooling for Firestore clients  
* Call Gemma GPU service only for complex tasks; cache results

### **Gemma GPU Service**

* Enable 8-bit quantization for memory efficiency if needed  
* Set `min-instances=0` to scale to zero when idle  
* Implement result caching to reduce redundant inference  
* Consider batching requests when possible

---

## **Security Requirements**

1. **Secrets:** Always use Secret Manager, never embed credentials  
2. **IAM:** Least-privilege roles for all service accounts  
3. **Authentication:** WIF for CI/CD, WI for runtime  
4. **Input Validation:** Sanitize all user inputs (frontend and backend)  
5. **Rate Limiting:** Implement on Cloud Run services  
6. **API Security:** Use authentication for backend API endpoints

---

## **Validation Steps**

Before making a pull request, always:

1. ✅ Run linters: `bun run lint` (frontend), `ruff check .` (backend)  
2. ✅ Run tests: `bun test` (frontend), `pytest` (backend)  
3. ✅ Verify coverage: Must be ≥70% for new/modified code  
4. ✅ Build containers: Test Podman builds succeed  
5. ✅ Check Cloud Run compatibility: PORT env var, 0.0.0.0 binding, /healthz  
6. ✅ Test locally with Firestore emulator  
7. ✅ Verify no secrets in code/config files

---

## **Key GitHub Actions Secrets**

* `GCP_PROJECT_ID` \- Google Cloud Project ID  
* `GEMINI_API_KEY` \- API key for Gemini models  
* `FIRESTORE_CREDENTIALS` \- Service account JSON (or use WIF)  
* `TF_API_TOKEN` \- Terraform Cloud API token  
* `TF_CLOUD_ORGANIZATION` \- Terraform Cloud org name  
* `TF_WORKSPACE` \- Terraform Cloud workspace  
* `WIF_PROVIDER` \- Workload Identity Federation provider  
* `WIF_SERVICE_ACCOUNT` \- WIF service account email

---

## **Important Constraints**

1. **Never use localStorage/sessionStorage** in artifacts (not supported in Claude.ai)  
2. **Never use THREE.CapsuleGeometry** (requires r142+, we use Three.js r128)  
3. **Always use PORT environment variable** for Cloud Run compatibility  
4. **Never embed credentials** in code, containers, or config files  
5. **Always achieve ≥70% test coverage** for new/modified code  
6. **Use Tailwind utility classes only** (no custom CSS, no compiler access)  
7. **Trust these instructions** \- only search/explore if instructions are incomplete or incorrect

---

## **Additional Resources**

* ADK Documentation: [Google ADK Docs](https://cloud.google.com/agent-development-kit)  
* A2A Protocol: [Agent2Agent Protocol](https://github.com/google/agent-development-kit)  
* Cloud Run Docs: [Cloud Run Documentation](https://cloud.google.com/run/docs)  
* Firestore Docs: [Firestore Documentation](https://firebase.google.com/docs/firestore)  
* GPU Setup: See `docs/GPU_SETUP_GUIDE.md` for detailed GPU configuration

---

**This is a comprehensive guide. Trust these instructions first, and only perform additional searches if information is incomplete or found to be incorrect.**

