# Prompt Vault Isolation Plan

**Feature Request:** Issue #193, #191, #195  
**Status:** Planning  
**Created:** November 2025

---

## Overview

This document outlines the strategy for integrating the new **"Prompt Vault"** (GenAI Prompt Management App) alongside the existing **agentnav** application without breaking existing functionality. The prompt-vault app uses **Supabase** for authentication and persistence, while agentnav uses **Firestore** and **GCP services**.

---

## Key Isolation Requirements

### 1. Container Image Isolation

**Current agentnav Images:**
- `agentnav-frontend`
- `agentnav-backend`
- `gemma-service`

**New prompt-vault Images:**
- `prompt-vault-frontend` (or `promptvault-frontend`)
- `prompt-vault-backend` (or `promptvault-backend`)

**GAR Repository Strategy:**
- **Option A (Recommended):** Use the same GAR repository (`agentnav-containers`) with different image names
  - **Pros:** Single repository, simpler IAM management, shared infrastructure
  - **Cons:** Images mixed in same repo (but clearly named)
  - **Location:** `europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/prompt-vault-frontend:${TAG}`
  
- **Option B:** Create separate GAR repository (`prompt-vault-containers`)
  - **Pros:** Complete isolation, clearer separation
  - **Cons:** Additional Terraform resource, separate IAM policies needed
  - **Location:** `europe-west1-docker.pkg.dev/${PROJECT_ID}/prompt-vault-containers/prompt-vault-frontend:${TAG}`

**Recommendation:** **Option A** - Use same repository with prefixed image names. This maintains simplicity while ensuring clear separation through naming.

---

### 2. Cloud Run Service Isolation

**Current agentnav Services:**
- `agentnav-frontend` (us-central1)
- `agentnav-backend` (europe-west1)
- `gemma-service` (europe-west1)

**New prompt-vault Services:**
- `prompt-vault-frontend` (us-central1)
- `prompt-vault-backend` (us-central1 or europe-west1)

**Service Naming Convention:**
- All prompt-vault services must use `prompt-vault-` prefix (or `promptvault-` for shorter names)
- This ensures no naming conflicts with existing agentnav services

**Cloud Run Configuration:**
- **Region:** Can share regions with agentnav (different service names prevent conflicts)
- **Service Accounts:** Create dedicated service accounts:
  - `prompt-vault-frontend@${PROJECT_ID}.iam.gserviceaccount.com`
  - `prompt-vault-backend@${PROJECT_ID}.iam.gserviceaccount.com`
- **IAM Roles:** Separate IAM roles for prompt-vault services (access to Supabase, not Firestore)

---

### 3. CI/CD Workflow Isolation

**Current Workflow:** `.github/workflows/build.yml`

**Strategy Options:**

#### Option A: Separate Workflow File (Recommended)
- Create `.github/workflows/build-prompt-vault.yml`
- Completely independent workflow
- Same tagging strategy (pr-{number}, {sha}, latest)
- Uses same GAR repository with different image names

#### Option B: Matrix Expansion in Existing Workflow
- Add `prompt-vault-frontend` and `prompt-vault-backend` to matrix
- Use conditional logic to build different Dockerfiles based on service name
- **Pros:** Single workflow, shared tagging logic
- **Cons:** More complex matrix, risk of breaking existing builds

**Recommendation:** **Option A** - Separate workflow file. This provides:
- Complete isolation (prompt-vault changes won't affect agentnav builds)
- Clear separation of concerns
- Easier debugging and maintenance
- Independent deployment schedules

---

### 4. Image Tagging Strategy

**Maintain Same Tagging Strategy:**
- **Pull Requests:** `pr-{PR_NUMBER}` (e.g., `pr-195`)
- **Main Branch:** Full SHA + `latest` tag
- **Other Branches:** Short SHA (7 chars)

**Example Tags:**
```
europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/prompt-vault-frontend:pr-195
europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/prompt-vault-frontend:abc123def456...
europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/prompt-vault-frontend:latest
```

**Key Point:** Tagging logic is identical, but applied to different image names. This ensures consistency and traceability.

---

### 5. Terraform Infrastructure Isolation

**Current Terraform Resources:**
- Cloud Run services: `agentnav-frontend`, `agentnav-backend`, `gemma-service`
- Service accounts: `agentnav-frontend`, `agentnav-backend`, `agentnav-gemma`
- Artifact Registry: `agentnav-containers` (shared)

**New Terraform Resources:**
- Cloud Run services: `prompt-vault-frontend`, `prompt-vault-backend`
- Service accounts: `prompt-vault-frontend`, `prompt-vault-backend`
- **Artifact Registry:** Use existing `agentnav-containers` (no new resource needed if using Option A)

**Terraform File Organization:**
- Option A: Add to existing `terraform/cloud_run.tf` with clear section comments
- Option B: Create `terraform/prompt_vault_cloud_run.tf` for separation

**Recommendation:** **Option B** - Separate Terraform file. This provides:
- Clear separation of infrastructure code
- Easier to review and maintain
- Can be conditionally applied via Terraform variables

---

### 6. Environment Variables and Secrets Isolation

**Current agentnav Secrets (GitHub Secrets):**
- `GCP_PROJECT_ID`
- `GEMINI_API_KEY`
- `FIRESTORE_CREDENTIALS` (if needed)
- `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT`
- `TF_API_TOKEN`, `TF_CLOUD_ORGANIZATION`, `TF_WORKSPACE`

**New prompt-vault Secrets (GitHub Secrets):**
- `SUPABASE_URL` (new)
- `SUPABASE_ANON_KEY` (new)
- `SUPABASE_SERVICE_KEY` (new, for backend only)
- `GOOGLE_OAUTH_CLIENT_ID` (new, for Supabase Google Sign-in)
- `GOOGLE_OAUTH_CLIENT_SECRET` (new, for Supabase Google Sign-in)

**Shared Secrets:**
- `GCP_PROJECT_ID` (shared)
- `WIF_PROVIDER`, `WIF_SERVICE_ACCOUNT` (shared)
- `TF_API_TOKEN`, `TF_CLOUD_ORGANIZATION`, `TF_WORKSPACE` (shared)

**Cloud Run Environment Variables:**
- prompt-vault services will have completely different environment variables
- No overlap with agentnav services (different service names)

---

### 7. Code Organization Isolation

**Current Structure:**
```
agentnav/
├── backend/          # agentnav FastAPI backend
├── components/       # agentnav React components
├── services/         # agentnav frontend services
├── Dockerfile        # agentnav frontend
└── ...
```

**New prompt-vault Structure:**
```
agentnav/
├── prompt-vault/     # NEW: Separate directory
│   ├── frontend/     # prompt-vault React app
│   ├── backend/      # prompt-vault backend (if needed, or use Supabase Edge Functions)
│   ├── Dockerfile    # prompt-vault frontend Dockerfile
│   └── ...
├── backend/          # agentnav (unchanged)
├── components/       # agentnav (unchanged)
└── ...
```

**Key Points:**
- All prompt-vault code in `prompt-vault/` directory
- Completely separate from agentnav code
- Can share root-level configs (package.json for dependencies, but separate workspaces)

---

### 8. Path Filtering in CI/CD

**Current Path Filters:**
```yaml
paths:
  - '**'  # Triggers on all changes
```

**New Workflow Path Filters:**
```yaml
# .github/workflows/build-prompt-vault.yml
on:
  push:
    paths:
      - 'prompt-vault/**'
      - '.github/workflows/build-prompt-vault.yml'
  pull_request:
    paths:
      - 'prompt-vault/**'
      - '.github/workflows/build-prompt-vault.yml'
```

**Benefits:**
- prompt-vault builds only trigger on prompt-vault changes
- agentnav builds only trigger on agentnav changes
- No cross-contamination

---

### 9. Domain and DNS Isolation

**Current Domain:**
- `agentnav.lornu.com` → `agentnav-frontend` Cloud Run service

**New Domain (if needed):**
- `prompt-vault.lornu.com` → `prompt-vault-frontend` Cloud Run service
- Or use subdomain: `prompt-vault.agentnav.lornu.com`

**Terraform DNS Configuration:**
- Add separate DNS records for prompt-vault domain
- Separate Cloud Run domain mapping resource

---

### 10. Testing and Validation

**Isolation Testing Checklist:**
- [ ] Build prompt-vault images without affecting agentnav images
- [ ] Deploy prompt-vault services without affecting agentnav services
- [ ] Verify prompt-vault uses Supabase (not Firestore)
- [ ] Verify agentnav still uses Firestore (not Supabase)
- [ ] Test path filtering triggers builds correctly
- [ ] Verify no shared environment variables between services
- [ ] Test rollback of prompt-vault without affecting agentnav
- [ ] Verify GAR image isolation (same repo, different names)

---

## Implementation Checklist

### Phase 1: Infrastructure Setup
- [ ] Create Terraform file for prompt-vault Cloud Run services
- [ ] Create service accounts: `prompt-vault-frontend`, `prompt-vault-backend`
- [ ] Configure IAM roles for prompt-vault services (Supabase access)
- [ ] Add DNS configuration for prompt-vault domain (if needed)
- [ ] Add Supabase secrets to GitHub Secrets

### Phase 2: CI/CD Setup
- [ ] Create `.github/workflows/build-prompt-vault.yml`
- [ ] Configure path filtering for prompt-vault directory
- [ ] Implement image tagging strategy (same as agentnav)
- [ ] Test build workflow with dummy Dockerfile
- [ ] Verify images pushed to GAR with correct names

### Phase 3: Application Code
- [ ] Create `prompt-vault/` directory structure
- [ ] Set up prompt-vault frontend (React/Next.js)
- [ ] Configure Supabase client
- [ ] Implement Google Sign-in via Supabase
- [ ] Create Dockerfile for prompt-vault frontend

### Phase 4: Deployment
- [ ] Deploy prompt-vault-frontend to Cloud Run
- [ ] Configure domain mapping (if needed)
- [ ] Test Google Sign-in flow
- [ ] Verify Supabase connectivity
- [ ] Monitor logs for any agentnav interference

### Phase 5: Documentation
- [ ] Update SYSTEM_INSTRUCTION.md with prompt-vault details
- [ ] Document new GitHub Secrets
- [ ] Update deployment checklist
- [ ] Create prompt-vault README

---

## Risk Mitigation

### Risk 1: Accidental Overwrite of agentnav Images
**Mitigation:**
- Use different image names (`prompt-vault-frontend` vs `agentnav-frontend`)
- Separate workflow files
- Path filtering prevents cross-builds

### Risk 2: Shared GAR Repository Conflicts
**Mitigation:**
- Image names are unique (different prefixes)
- Tags follow same strategy but applied separately
- No risk of tag collision (same SHA used for both apps, but different image names)

### Risk 3: Terraform State Conflicts
**Mitigation:**
- Separate Terraform resources with unique names
- Use `terraform/prompt_vault_cloud_run.tf` for clear separation
- Test Terraform plan before apply

### Risk 4: CI/CD Workflow Breaking Existing Builds
**Mitigation:**
- Separate workflow file (no changes to existing workflow)
- Path filtering ensures prompt-vault changes don't trigger agentnav builds

### Risk 5: Environment Variable Leakage
**Mitigation:**
- Separate service accounts
- Separate Cloud Run services
- Explicit environment variable configuration per service

---

## Example Workflow Configuration

### `.github/workflows/build-prompt-vault.yml`

```yaml
name: Build and Deploy Prompt Vault

on:
  push:
    branches:
      - main
    paths:
      - 'prompt-vault/**'
      - '.github/workflows/build-prompt-vault.yml'
  pull_request:
    branches:
      - main
    paths:
      - 'prompt-vault/**'
      - '.github/workflows/build-prompt-vault.yml'

env:
  GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  ARTIFACT_REGISTRY_LOCATION: europe-west1
  ARTIFACT_REGISTRY_REPOSITORY: agentnav-containers  # Shared repo

jobs:
  build-and-push:
    name: Build and Push Prompt Vault Containers
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    strategy:
      matrix:
        service: [frontend, backend]  # Only prompt-vault services
      fail-fast: false

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
          project_id: ${{ env.GCP_PROJECT_ID }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker for Artifact Registry
        run: |
          gcloud auth configure-docker ${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev

      - name: Determine Image Tags based on Event
        id: image
        shell: bash
        run: |
          set -euo pipefail
          
          LATEST_TAG=""
          
          if [[ "${{ github.event_name }}" == "pull_request" ]]; then
            PR_NUMBER="${{ github.event.pull_request.number }}"
            IMAGE_TAG="pr-${PR_NUMBER}"
          elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            IMAGE_TAG="${{ github.sha }}"
            LATEST_TAG="latest"
          else
            IMAGE_TAG="$(echo '${{ github.sha }}' | cut -c1-7)"
          fi
          
          echo "image_tag=${IMAGE_TAG}" >> $GITHUB_OUTPUT
          if [[ -n "${LATEST_TAG}" ]]; then
            echo "latest_tag=${LATEST_TAG}" >> $GITHUB_OUTPUT
          fi

      - name: Build and push prompt-vault-frontend
        if: matrix.service == 'frontend'
        run: |
          set -euo pipefail
          
          IMAGE_NAME="${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPOSITORY}/prompt-vault-frontend"
          IMAGE_TAG="${{ steps.image.outputs.image_tag }}"
          
          docker build \
            -t ${IMAGE_NAME}:${IMAGE_TAG} \
            -f prompt-vault/Dockerfile \
            ./prompt-vault
          
          if [[ -n "${{ steps.image.outputs.latest_tag }}" ]]; then
            docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:${{ steps.image.outputs.latest_tag }}
          fi
          
          docker push ${IMAGE_NAME}:${IMAGE_TAG}
          if [[ -n "${{ steps.image.outputs.latest_tag }}" ]]; then
            docker push ${IMAGE_NAME}:${{ steps.image.outputs.latest_tag }}
          fi

      # Similar for backend...

  deploy:
    name: Deploy Prompt Vault to Cloud Run
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      contents: read
      id-token: write

    strategy:
      matrix:
        service: [frontend, backend]
      fail-fast: false

    steps:
      # Deploy steps similar to agentnav workflow
      # But using prompt-vault-frontend and prompt-vault-backend service names
```

---

## Summary

**Key Isolation Mechanisms:**
1. ✅ **Separate container image names** (`prompt-vault-*` vs `agentnav-*`)
2. ✅ **Separate Cloud Run service names** (`prompt-vault-frontend` vs `agentnav-frontend`)
3. ✅ **Separate CI/CD workflow file** (no changes to existing workflow)
4. ✅ **Path filtering** (prompt-vault changes don't trigger agentnav builds)
5. ✅ **Separate Terraform resources** (clear separation in infrastructure code)
6. ✅ **Separate service accounts** (isolated IAM permissions)
7. ✅ **Separate environment variables** (no shared state)
8. ✅ **Code organization** (separate `prompt-vault/` directory)

**Shared Resources (Safe to Share):**
- GAR Repository (`agentnav-containers`) - images are named differently
- GitHub Secrets (WIF, Terraform tokens) - read-only, no conflicts
- GCP Project - different services, no conflicts

**Result:** Complete isolation while maintaining infrastructure efficiency.

---

## Next Steps

1. Review this plan with the team
2. Create GitHub issue for implementation tracking
3. Start with Phase 1 (Infrastructure Setup)
4. Test each phase before moving to the next
5. Document any deviations from this plan

---

**Related Issues:**
- #193: Supabase Authentication (Google Sign-in)
- #191: System Instruction Update
- #195: [Review issue #195 for specific requirements]

**Related Documentation:**
- [IMAGE_TAGGING_STRATEGY.md](./IMAGE_TAGGING_STRATEGY.md)
- [SYSTEM_INSTRUCTION.md](./SYSTEM_INSTRUCTION.md)
- [GCP_SETUP_GUIDE.md](./GCP_SETUP_GUIDE.md)

