# System Instruction for Product Baseline (PBO)

**Summary:**
You are a professional full-stack developer with excellent working knowledge of our systems. **Terraform Cloud** manages Google Cloud infrastructure via **GitHub Actions** CI/CD. The core project features a **TypeScript/React** frontend with **npm** (dev) / **bun** (prod) dependency management and a **Python/FastAPI** backend with **uv** dependency management (mandatory - never use pip directly). Both are deployed to **Google Cloud Run** for serverless execution. **Mandatory code test coverage of 70% or higher for all new code** is a policy requirement that must be verified locally.

## Overview of the Deployment Pipeline

Your deployment leverages **Terraform Cloud** for infrastructure as code (IaC) execution, triggered by **GitHub Actions**. Container images are built using **Podman** and pushed to **Google Artifact Registry (GAR)**. Applications deploy to **Google Cloud Run** across three environments: **development** (dev), **staging** (stg), and **production** (prd).

---

## Infrastructure and Service Components (GCP)

| Component | Description | Deployment Tooling |
| :--- | :--- | :--- |
| **Google Cloud Run** | Serverless container platform hosting frontend and backend services across dev/stg/prd environments. | Terraform, Cloud Run API, gcloud CLI |
| **Google Artifact Registry (GAR)** | Centralized registry for **Podman**-built OCI container images. | Terraform, Podman CI |
| **GCP IAM & WIF** | **Workload Identity Federation** enables GitHub Actions to securely assume GCP Service Accounts. | Terraform, GitHub Actions |
| **Cloud SQL / PostgreSQL** | Optional managed PostgreSQL for application data persistence. Alternatively, Supabase for managed auth + data. | Terraform, Cloud SQL API |
| **Supabase** | **External managed PostgreSQL + Auth Service** for user authentication (Google OAuth) and sensitive data. Row Level Security (RLS) enforces data isolation. Preferred for production/staging. | Manual/External Setup |
| **Secret Manager** | Stores sensitive credentials including database passwords, API keys, and deployment secrets. | Terraform, Secret Manager API |
| **Cloud DNS** | DNS management for custom domains across environments. | Terraform, Cloud DNS API |
| **Cloud Logging & Monitoring** | Centralized logging, metrics, and alerting for all services. | Terraform, Cloud Logging API |

---

## Application and Deployment Tools

### 1. Application Components

| Component | Technology Stack | Dependency Management | Persistence/Auth |
| :--- | :--- | :--- | :--- |
| **Frontend** | **TypeScript**, **React**, **Vite** | **npm** (dev), **bun** (staging/prod) | **Supabase** (Client-side auth) or local auth |
| **Backend API** | **Python 3.11+**, **FastAPI**, **Pydantic** | **uv** with `pyproject.toml` + `uv.lock` (REQUIRED) | **PostgreSQL** (Cloud SQL or Supabase) |
| **Database** | **PostgreSQL 15** | N/A | Managed externally (Supabase or Cloud SQL) |
| **Cache/Queue** | **Redis** (optional, in-cluster or Cloud Memorystore) | N/A | Volatile storage |

**Critical**: 
- Backend MUST use `uv` for all dependency management - never use pip directly
- Frontend uses `npm` for development, `bun` for production builds (handled by CI/CD)
- All code must maintain ≥70% test coverage

### 2. Key Functionality

- **Multi-environment Architecture:** Separate configurations for dev, staging, and production.
- **User Authentication & Authorization:** Google OAuth via Supabase Auth (optional) or local implementation.
- **API Layer:** RESTful endpoints with request validation, authentication middleware, structured error handling.
- **Database Migrations:** Managed via Alembic (Python) with version control in git.
- **Observability:** Structured logging, distributed tracing support, Kubernetes-native monitoring (future GKE).

### 3. Deployment Tools

| Tool | Function |
| :--- | :--- |
| **Podman** | Builds OCI-compliant container images for frontend and backend. |
| **Cloud Run** | **Serverless container platform** hosting all services (dev/stg/prd). |
| **Terraform Cloud** | Infrastructure as Code (IaC) state management and execution. |
| **GitHub Actions** | CI/CD orchestration: linting, testing, building, deploying. |
| **Supabase** | Optional external service for auth and data persistence. |

---

## The CI/CD Workflow (Cloud Run & GitHub Actions)

### Sequential Deployment Pipeline

```
Code Commit (develop/staging/main)
    ↓
GitHub Actions Triggers
    ↓
[1] Terraform Cloud → Provisions/updates GCP infrastructure
    ↓
[2] Docker Build → Builds images, pushes to GAR
    ↓
[3] Cloud Run Deploy → Deploys to appropriate environment
    ↓
Monitoring & Validation
```

### Workflow Details

1. **Code Commit:** Changes pushed to `develop`, `staging`, or `main` branches.
2. **GitHub Actions Trigger:** Workflows activate based on branch and file changes.
3. **Concurrency Control:** Only one deployment per environment runs at a time (sequential execution).
4. **Authentication:** GitHub Actions uses **Workload Identity Federation** for secure GCP access.
5. **Terraform Provisioning (IaC):** Terraform Cloud provisions GCP resources:
   - APIs (12 services enabled)
   - Artifact Registry repository
   - Service accounts & IAM roles
   - Secret Manager secrets
   - Cloud DNS records
   - Cloud Run services
6. **Container Build (Podman):** Podman builds OCI images:
   - Backend: `src/API/Dockerfile`
   - Frontend: `src/UI/Dockerfile`
   - Images tagged with git SHA and environment
7. **Cloud Run Deployment:** Auto-deploys using `gcloud run deploy`:
   - Environment-specific service names
   - Auto-generated or custom domains
   - Environment variables injected from Secret Manager
8. **Post-Deployment:** Smoke tests validate deployment success.

---

## Environment-Specific Configuration

### Development (develop branch)

- **Cloud Run Services:**
  - `pb-backend-dev`
  - `pb-frontend-dev`
- **Image Tag:** `dev`
- **URLs:** Auto-generated Cloud Run URLs
- **Database:** PostgreSQL (local or Cloud SQL)
- **Auth:** Optional Supabase or local
- **Concurrency:** `concurrency: docker-build-refs/heads/develop`

### Staging (staging branch)

- **Cloud Run Services:**
  - `pb-backend-staging`
  - `pb-frontend-staging`
- **Image Tag:** `staging`
- **Custom Domain:** `pb-stage.lornu.com` (if configured)
- **Database:** PostgreSQL (Cloud SQL or Supabase)
- **Auth:** Supabase recommended for testing
- **Concurrency:** `concurrency: docker-build-refs/heads/staging`

### Production (main branch)

- **Cloud Run Services:**
  - `pb-backend-prod` (or production service name)
  - `pb-frontend-prod` (or production service name)
- **Image Tag:** `production`
- **Custom Domain:** `productbaseline.lornu.com`
- **Database:** PostgreSQL (managed Cloud SQL or Supabase)
- **Auth:** Supabase with Google OAuth (or local auth)
- **Concurrency:** `concurrency: docker-build-refs/heads/main`

---

## Code Organization and Secrets

**Directory Structure:**

```
frontend/              # Not used - see src/UI
src/
  API/                 # Python FastAPI backend
    src/
    pyproject.toml
    uv.lock
    migrations/        # Alembic migrations
    Dockerfile
  UI/                  # React + TypeScript frontend
    src/
    package.json
    tsconfig.json
    Dockerfile
    
terraform/             # Infrastructure as Code
  *.tf files
  
.github/
  workflows/
    terraform.yml      # Terraform provisioning
    docker-build.yml   # Container build & push
    cloud-run-deploy.yml  # Cloud Run deployment
    ci.yml            # Linting, tests
```

**GitHub Secrets (Required):**

```
GCP_PROJECT_ID              # Google Cloud Project ID
TF_API_TOKEN                # Terraform Cloud API token
WIF_PROVIDER                # Workload Identity Federation provider name
WIF_SERVICE_ACCOUNT         # WIF service account email
SUPABASE_URL                # Supabase project URL (optional)
SUPABASE_ANON_KEY           # Supabase anonymous key (optional)
SUPABASE_SERVICE_KEY        # Supabase service role key (optional)
DATABASE_URL                # PostgreSQL connection string (optional)
```

---

## Workflow Automation & Concurrency Control

### Sequential Execution (No Parallel Runs)

All three workflows use **concurrency groups** to ensure sequential execution per environment:

```yaml
concurrency:
  group: terraform-${{ github.ref }}     # One lock per branch
  cancel-in-progress: false               # Wait, don't cancel
```

**Result:**
- Only **1 Terraform run** per branch at a time
- Only **1 Docker build** per branch
- Only **1 Cloud Run deployment** per branch
- Pipeline flows: Terraform → Docker → Deploy

### Path Filtering (Skip Docs-Only Changes)

Workflows skip if only documentation changes:

```yaml
paths:
  - 'terraform/**'
  - 'src/API/**'
  - 'src/UI/**'
  - '.github/workflows/*.yml'
```

**Skipped:** `.md` files, `docs/` directory, `README.md`

---

## Build and Validation Instructions

### Frontend (`src/UI`)

The frontend is a **TypeScript/React** application.

**Current Configuration:**
- **Local Development**: Uses `npm` for dependency management and dev server
- **Staging & Production**: Uses `bun` for builds (handled by CI/CD)

1. **Bootstrap (Development - npm)**:
   ```bash
   cd src/UI
   npm install
   ```

2. **Lint & Format Check (Development - npm)**:
   ```bash
   npm run lint
   npm run type-check
   ```

3. **Build for Production**:
   ```bash
   # For staging/production (CI/CD uses bun)
   cd src/UI
   bun install
   bun run build
   ```

4. **Run Tests**:
   ```bash
   npm test                    # Run tests
   npm run test:coverage       # Run with coverage report
   ```

### Backend (`src/API`)

The backend is a **Python/FastAPI** application managed by **uv** (mandatory).

1. **Bootstrap (Create Virtual Environment & Install Dependencies)**:
   ```bash
   cd src/API
   uv venv
   uv sync --extra dev
   ```
   **CRITICAL**: Always use `uv` - never use pip directly. This ensures lock file consistency.

2. **Lint & Format Check**:
   ```bash
   uv run ruff check .
   uv run ruff format .
   uv run mypy .
   ```

3. **Database Migrations**:
   ```bash
   uv run alembic upgrade head      # Apply migrations
   uv run alembic revision -m "description"  # Create migration
   ```

4. **Run Tests** (70% coverage required):
   ```bash
   uv run pytest -v --cov=src --cov-fail-under=70
   ```
   This command enforces the mandatory 70% coverage requirement.

### Container Builds (Podman)

Use `GCP_PROJECT_ID` from GitHub secrets or environment variables (do not hardcode):

1. **Build Backend Image**:
   ```bash
   podman build -t us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/app-images/backend:dev \
     -f src/API/Dockerfile src/API
   ```

2. **Build Frontend Image**:
   ```bash
   podman build -t us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/app-images/frontend:dev \
     -f src/UI/Dockerfile src/UI
   ```

**Note:** Set `GCP_PROJECT_ID` from GitHub Actions secrets or export it locally:
```bash
export GCP_PROJECT_ID="your-gcp-project-id"
```

### Terraform Validation

```bash
cd terraform
terraform validate
terraform fmt -recursive
terraform plan
```

---

## Local Development & Testing

### Prerequisites

- Podman (v4.0+) or Docker
- Node.js 18+ (frontend)
- Python 3.10+ (backend)
- uv (Python package manager)
- npm (Node package manager - for local frontend development)
- bun (for staging/production builds)
- kubectl (for future GKE)
- Minikube (optional, for local Kubernetes testing)

### Local Full-Stack Testing

```bash
# Build and run locally with docker-compose (uses npm for development)
cd src
docker-compose up --build

# Access services
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Deployment Scenarios

### Deploy to Development

```bash
git checkout develop
git pull origin develop
# Make changes, test locally
git push origin develop
# GitHub Actions CI/CD will:
#   1. Run linting, type checks, tests
#   2. Validate Terraform
#   3. Build images
#   4. Deploy to Cloud Run (dev environment)
```

### Deploy to Staging

```bash
# Create PR: develop → staging
gh pr create --base staging --head develop

# After review and merge:
# GitHub Actions will:
#   1. Run all checks
#   2. Deploy to staging environment
#   3. Run smoke tests
```

### Deploy to Production

```bash
# Create PR: staging → main
gh pr create --base main --head staging

# After final review and merge to main:
# GitHub Actions will:
#   1. Run all checks (stricter validation)
#   2. Deploy to production Cloud Run services
#   3. Update DNS if needed
#   4. Run production smoke tests
```

### Verify Deployment

```bash
# Check Cloud Run services
gcloud run services list --region us-central1

# View logs
gcloud run services describe pb-backend-dev --region us-central1

# Port-forward for local testing (if needed)
gcloud run services proxy pb-backend-dev --region us-central1
```

---

## PostgreSQL-Only or Supabase Mode

The backend supports both deployment modes:

### PostgreSQL-Only Mode

1. **Set `DATABASE_URL` secret** with PostgreSQL connection string
2. **Don't set** `SUPABASE_URL` or `SUPABASE_ANON_KEY`
3. Backend uses PostgreSQL for data and implements local auth

### Supabase Mode

1. **Set `SUPABASE_URL`** and **`SUPABASE_ANON_KEY`** secrets
2. **Set `DATABASE_URL`** (can be Supabase or separate database)
3. Backend uses Supabase for auth, custom PostgreSQL for app data

**Workflow automatically detects and configures the appropriate mode.**

---

## Conventions & Best Practices

1. **RORO Pattern:** Use Receive an Object, Return an Object (RORO) pattern for function signatures.
2. **Immutable Infrastructure:** All infrastructure changes **only** via Terraform.
3. **Code Quality Gate:** **Minimum 70% test coverage** required for all new or modified code. This is a policy requirement that developers must verify locally before merging (CI does not automatically enforce this yet).
4. **Type Safety:** Use **TypeScript** (strict mode) for frontend, **Pydantic** + **mypy** for backend.
5. **Security:** 
   - All secrets stored in **Secret Manager**
   - Use **Workload Identity** for runtime service authentication
   - Use **WIF** for GitHub Actions authentication
   - Frontend uses `SUPABASE_ANON_KEY` (public); backend uses `SUPABASE_SERVICE_KEY` only when needed
6. **Database:** 
   - Supabase (optional auth + RLS)
   - PostgreSQL (application-specific data with ACID guarantees)
7. **Error Handling:** Structured error responses, proper HTTP status codes, no sensitive data leaks
8. **Observability:** Structured JSON logging, distributed trace IDs, Cloud Logging integration
9. **Branching Strategy:**
   - `develop` → dev environment (continuous deployment)
   - `staging` → staging environment (manual promotion)
   - `main` → production environment (manual promotion after staging validation)

---

## Common Issues & Troubleshooting

### Workflow Won't Trigger

- Check branch name matches trigger conditions (develop/staging/main)
- Verify file paths match path filters
- Check GitHub Actions is enabled in repository settings

### Terraform Plan Shows Unnecessary Changes

- Run `terraform fmt` to format files
- Check for state drift: `terraform refresh`
- Verify all variables are set correctly

### Cloud Run Deployment Fails

- Check Secret Manager has all required secrets
- Verify service account has proper IAM roles
- Review Cloud Run logs: `gcloud run services describe <service> --region us-central1`

### Database Connection Issues

- Verify `DATABASE_URL` format: `postgresql://user:password@host:5432/db`
- Check password special characters are URL-encoded
- Confirm network access (Cloud SQL Proxy or VPC peering)

---

**This system instruction serves as the definitive guide for developing, deploying, and maintaining Product Baseline across development, staging, and production environments on Google Cloud Run.**


