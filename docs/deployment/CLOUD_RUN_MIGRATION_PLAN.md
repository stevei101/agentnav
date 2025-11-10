## Cloud Run Deployment Adoption Plan

Issue tracking reference: [#262](https://github.com/stevei101/agentnav/issues/262)

### Status: COMPLETED ✅

As of Issue [#445](https://github.com/stevei101/agentnav/issues/445), the deployment workflow has been **internalized** and no longer relies on the external `podman-cloudrun-deploy-gha` pattern. The deployment logic is now self-contained within `.github/workflows/deploy-cloudrun.yaml`.

### Objectives (COMPLETED)
- ✅ Align `agentnav` deployments with Cloud Run best practices
- ✅ Standardize Terraform modules and Workload Identity Federation
- ✅ Ensure service integrations (Supabase SSO, Prompt Vault, Cursor IDE) remain functional
- ✅ Eliminate external workflow dependencies for better maintainability and control

### Workstream Breakdown

1. **Workflow Alignment** ✅
   - Self-contained `Docker → Artifact Registry → Cloud Run` workflow steps
   - Direct container build logic without external dependencies
   - Comprehensive error handling and deployment validation

2. **Infrastructure Sync** ✅
   - Terraform state maintained for frontend, backend, and Gemma services
   - Shared modules for Cloud Run, Artifact Registry, and WIF bindings
   - Service account permissions validated for Supabase, Prompt Vault, and logging

3. **Integration Validation** ✅
   - Supabase SSO verified end-to-end in staging
   - Backend configuration calls external `prompt-vault` API correctly
   - Cursor IDE integration touchpoints documented and tested

4. **Security & Observability** ✅
   - Secret scans (`detect-secrets`, `gitleaks`) passing
   - Cloud Logging/Monitoring alerts operational
   - Rollback procedures documented

### Final Implementation Details

The deployment workflow now includes:
- **Frontend Deployment**: Bun-based build with linting, type-checking, and tests
- **Backend Deployment**: Python/FastAPI with Firestore access and Secret Manager integration
- **WIF Authentication**: Direct authentication without external workflow calls
- **Docker Build/Push**: Native Docker commands to Google Artifact Registry
- **Cloud Run Deployment**: Direct `gcloud run deploy` with all configurations inline

### References
- Implementation PR: Issue [#445](https://github.com/stevei101/agentnav/issues/445)
- Workflow File: `.github/workflows/deploy-cloudrun.yaml`
- Build Workflow: `.github/workflows/build.yml` (reference implementation)
### Historical Note

This section documented the original migration plan from Issue [#262](https://github.com/stevei101/agentnav/issues/262). The external workflow pattern reference has been superseded by the self-contained implementation documented above (Issue #445).

