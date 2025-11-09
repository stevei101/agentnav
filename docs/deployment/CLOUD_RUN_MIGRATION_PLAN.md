## Cloud Run Deployment Adoption Plan

Issue tracking reference: [#262](https://github.com/stevei101/agentnav/issues/262)

### Objectives
- Align `agentnav` deployments with the `podman-cloudrun-deploy-gha` GitHub Actions pattern.
- Standardize Terraform modules and Workload Identity Federation with the shared infrastructure stack.
- Ensure service integrations (Supabase SSO, Prompt Vault, Cursor IDE) remain functional after pipeline changes.

### Workstream Breakdown

1. **Workflow Alignment**
   - Mirror the `Podman → Terraform → Cloud Run` workflow steps.
   - Consolidate container build logic into reusable workflow calls.
   - Add shared caching, artifact naming, and risk controls from the pattern repository.

2. **Infrastructure Sync**
   - Baseline current Terraform state for frontend, backend, and Gemma services.
   - Import shared modules for Cloud Run, Artifact Registry, and WIF bindings.
   - Validate service account permissions required for Supabase, Prompt Vault, and logging sinks.

3. **Integration Validation**
   - Confirm Supabase SSO works end-to-end in staging after deployment updates.
   - Update backend configuration to call the external `prompt-vault` API (no intra-repo imports).
   - Capture Cursor IDE integration touchpoints and define smoke tests to verify context hand-offs.

4. **Security & Observability**
   - Re-run secret scans (`detect-secrets`, `gitleaks`) post-migration.
   - Ensure Cloud Logging/Monitoring alerts survive infrastructure refactors.
   - Document rollback steps in `deployment/GEMMA_ROLLBACK_TEST_PLAN.md`.

### Deliverables
- Updated GitHub Actions workflows referencing the shared deployment pattern.
- Terraform changes merged with accompanying migration notes.
- Verification checklist covering authentication, agent orchestration, and external integrations.
- Release notes summarizing the pipeline change and required environment updates.

### Next Steps
- Use this plan as the skeleton for PR checklists.
- Keep `docs/README.md` aligned with any new guides that spin out from the migration.
- Track progress directly in issue [#262](https://github.com/stevei101/agentnav/issues/262) to keep the backlog clean.
