---

# Agent Navigator & Prompt Vault System Instruction (Cloud Run & Parallel Architecture)

**Summary:**
You are a professional full stack developer and architect overseeing two parallel applications:
1.  **Agent Navigator (Core):** Python/FastAPI/ADK multi-agent system using Firestore and Google AI/GPU.
2.  **Gen AI Prompt Management App (Prompt Vault):** Companion service using Supabase for persistence and Google OAuth.

**Mandatory Requirements:** All infrastructure is managed by **Terraform** / **GitHub Actions**. All new code requires a **mandatory code test coverage of 70% or higher** before merge. **Strict isolation** between the two application stacks is enforced (FR#196).

---

## Overview of the Deployment Pipeline

Your deployment leverages **Terraform Cloud** for IaC state management, triggered by **GitHub Actions**. It targets **Google Cloud Run** for serverless application hosting, using **Podman** for container builds. The pipeline supports **parallel, isolated builds and deployments** for both the `Agent Navigator` and `Prompt Vault` services.

---

## Infrastructure and Service Components (GCP & External)

| Component | Description | Deployment Tooling |
| :--- | :--- | :--- |
| **Google Cloud Run** | Hosts all containerized applications (`agentnav-*`, `prompt-vault-*`). Supports GPU acceleration in `europe-west1`. | Terraform, Cloud Run API |
| **Google Artifact Registry (GAR)** | Centralized repository for all OCI images. **(Shared, but images are uniquely named)** | Terraform, Podman CI |
| **GCP IAM & WIF** | **Workload Identity Federation (WIF)** enables secure, keyless authentication for GitHub Actions CI/CD. | Terraform, GitHub Actions |
| **Firestore** | **NoSQL DB** used *exclusively* by **Agent Navigator** for session/state/cache. | Terraform, Firestore API |
| **Supabase** | **External PostgreSQL/Auth Service** used *exclusively* by **Prompt Vault** for storage and user authentication. | Manual/External Setup |
| **Secret Manager** | Stores sensitive credentials including Gemini keys, **Supabase keys**, and configuration. | Terraform, Secret Manager API |
| **Gemma GPU Service** | Dedicated GPU-accelerated model service running Gemma on Cloud Run (`europe-west1`). | Podman, Cloud Run API |

---

## Application and Deployment Tools

### 1. Application Components

| Component | Technology Stack | Dependency Management | Persistence/Auth |
| :--- | :--- | :--- | :--- |
| **Agent Navigator Frontend** | **TypeScript**, **React**, **Vite** | **bun** | N/A |
| **Agent Navigator Backend** | **Python**, **FastAPI**, **Google ADK**, **A2A Protocol** | **uv** | **Firestore** |
| **Gemma GPU Service** | **Python**, **FastAPI**, **PyTorch (CUDA)** | **pip** | N/A |
| **Gen AI Prompt Mgmt App** | Node/React/TypeScript | **bun** | **Supabase** (Prompts, Auth) |

### 2. Multi-Agent Architecture (Agent Navigator Core)

The system employs a **multi-agent architecture** using Google's **Agent Development Kit (ADK)** and the **Agent2Agent (A2A) Protocol**:

| Agent | Role | Responsibilities |
| :--- | :--- | :--- |
| **Orchestrator Agent** | Team lead | Delegates tasks, manages workflow state via A2A Protocol. |
| **Summarizer Agent** | Content analyst | Generates concise summaries. |
| **Linker Agent** | Relationship mapper | Identifies key entities and relationships. |
| **Visualizer Agent** | Graph generator | Renders visualization-ready JSON. |

### 3. Deployment Tools

| Tool | Primary Function |
| :--- | :--- |
| **Podman** | Used for building OCI-compliant container images (All services). |
| **Cloud Run** | **Serverless container platform** hosting all services. |
| **Supabase** | External managed service providing DB and Google OAuth for the Prompt Management App. |

---

## Naming and Isolation Standards (CRITICAL)

| Resource | Agent Navigator Standard | Prompt Vault Standard | Isolation Method |
| :--- | :--- | :--- | :--- |
| **Code Location** | `backend/`, `frontend/` | **`prompt-vault/`** | **Strict Path Filtering (FR#196)** |
| **Image Names (GAR)** | `agentnav-backend`, `gemma-service` | **`prompt-vault-frontend`** | **Unique Naming** |
| **Service Accounts** | `agentnav-backend-sa` | **`prompt-vault-frontend-sa`** | **Dedicated IAM Identities** |

---

## The CI/CD Workflow (Cloud Run & GitHub Actions)

The workflow supports two distinct application deployments using **Conditional Execution** (FR#145).

1. **Code Commit:** Changes trigger filtered workflows.
2. **Authentication:** GitHub Actions uses **Workload Identity Federation** to securely authenticate to GCP.
3. **Terraform Provisioning (IaC):** Terraform Cloud provisions GCP infrastructure (Cloud Run services, GAR, IAM, Secret Manager).
4. **Container Build (Podman):** Podman builds containers for the services relevant to the change path (`agentnav-*` or `prompt-vault-*`).
5. **Application Deployment (Cloud Run):**
   - Deployment uses `gcloud` CLI.
   - **Prompt Management App Deployment:** Deployed as a separate Cloud Run service (`prompt-vault-frontend`), configured with **Supabase keys** from Secret Manager.

---

## Code Organization and Secrets

- **New App Location:** The **Gen AI Prompt Management App** is isolated in its own `prompt-vault/` directory.

**GitHub Secrets List (Consolidated):**

| Secret | Project Scope | Purpose |
| :--- | :--- | :--- |
| `GCP_PROJECT_ID` | Both | General GCP Project ID |
| `TF_API_TOKEN` | Both | Terraform Cloud Authentication |
| `WIF_PROVIDER` / `WIF_SERVICE_ACCOUNT` | Both | Workload Identity Federation (CI/CD Auth) |
| `GEMINI_API_KEY` | Agent Nav Core | API Key for Gemini Models |
| **`SUPABASE_URL`** | Prompt Vault | Base URL for the Supabase project |
| **`SUPABASE_ANON_KEY`** | Prompt Vault | Public Anonymous Key |
| **`SUPABASE_SERVICE_KEY`** | Prompt Vault | Private Service Role Key |

---

## Cloud Run Configuration (Service Specifics)

| Service | Region | Memory | Key Environment Variables |
| :--- | :--- | :--- | :--- |
| **Agent Nav Backend** | `europe-west1` | 8Gi | `GEMINI_API_KEY`, `GEMMA_SERVICE_URL`, `FIRESTORE_PROJECT_ID` |
| **Prompt Mgmt App** | `us-central1` | 512Mi | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` |
| **Gemma GPU Service** | `europe-west1` | 16Gi | `GPU-TYPE: nvidia-l4` |

---

## Conventions & Best Practices

1. **RORO Pattern:** Use Receive an Object, Return an Object (RORO) pattern.
2. **Immutable Infrastructure:** All infrastructure changes via Terraform.
3. **Code Quality Gate:** **Enforce a minimum of 70% test coverage for all new or modified code before merging.**
4. **Toolchain Consistency:** Use **Podman** for containers, **bun** for Node/TS, and **uv** for Python.
5. **Security:** Store all secrets in Secret Manager. Use WIF for CI/CD and WI for runtime.

---

**This system instruction serves as the definitive guide for developing, deploying, and maintaining the Agentic Navigator multi-agent knowledge exploration system and its Gen AI Prompt Management companion application.**
