# Documentation Directory

This directory contains **published documentation** for developers, reviewers, and hackathon judges.

## Purpose

These documents are:

- ? Polished and ready for external consumption
- ? Helpful for understanding and using the project
- ? Included in hackathon submissions
- ? Suitable for sharing with reviewers

## Contents

### Active Guides

- `local-development.md` - Local development environment setup
- `SYSTEM_INSTRUCTION.md` - Complete system architecture and deployment guide
- `TESTING_STRATEGY.md` - Quality gates, coverage, and verification strategy
- `CONTRIBUTION_GUIDE_PR_DISCIPLINE.md` / `CONTRIBUTION_QUALITY_GATES.md` - PR flow and CI expectations
- `WORKFLOW_PR_RECOVERY.md` / `ZERO_TOLERANCE_FAILURE_POLICY.md` - CI incident response

### Deployment Playbooks (`deployment/`)

- `GCP_SETUP_GUIDE.md` / `TERRAFORM_FIRST_APPLY.md` - Platform bootstrap and Terraform flow
- `CUSTOM_DOMAIN_SETUP.md` / `STAGING_PRODUCTION_WORKFLOW.md` - Environment promotion & routing
- `WIF_GITHUB_SECRETS_SETUP.md` / `GITHUB_SECRETS_TO_GCP_GUIDE.md` - Workload Identity and secret sync
- `GPU_SETUP_GUIDE.md` / `GEMMA_*` docs - GPU and Gemma service operations
- `MANUAL_WORKFLOWS.md` - Manual GitHub Actions triggers (kept for disaster recovery)
- `CLOUD_RUN_MIGRATION_PLAN.md` - Readiness plan for Issue #262 (`podman-cloudrun-deploy-gha`)

### Integrations (`integrations/`)

- Supabase SSO (`SUPABASE_AUTH_GUIDE.md`, `SUPABASE_GOOGLE_OAUTH_SETUP.md`, `README_SUPABASE.md`)
- Prompt Vault integration overview (`PROMPT_MANAGEMENT_GUIDE.md`)
- ADK / A2A notes (`ADK_CONSIDERATION_PLAN.md`, `A2A_PROTOCOL_INTEGRATION.md`, `A2A_SECURITY_AUDIT.md`)
- Gemma client/service integration (`GEMMA_INTEGRATION_GUIDE.md`)

### Archives (`archive/`)

- `archive/hackathon/` – Hackathon submissions, checklists, and strategy decks
- `archive/strategy/` – Historical feature retros, gap analyses, and planning docs
- These references remain for historical context but are excluded from the active deployment playbooks

## For Developers

If you're a developer looking to:

- **Set up the project locally** ? Start with `local-development.md`
- **Deploy to Google Cloud** ? Use the `deployment/` playbooks (begin with `GCP_SETUP_GUIDE.md`)
- **Understand the architecture** ? Read `SYSTEM_INSTRUCTION.md`
- **Add GPU support** ? Follow `deployment/GPU_SETUP_GUIDE.md`
- **Get development assistance** ? Use the custom Copilot agent (see `COPILOT_AGENT_GUIDE.md`)
- **Understand CI/CD failure response** ? Review `ZERO_TOLERANCE_FAILURE_POLICY.md` (**mandatory reading**)
- **Follow PR best practices** ? See `CONTRIBUTION_GUIDE_PR_DISCIPLINE.md`

## For Reviewers

If you're reviewing this project:

- **System Architecture** ? `SYSTEM_INSTRUCTION.md`
- **Cloud Run migration progress** ? `deployment/CLOUD_RUN_MIGRATION_PLAN.md`
- **Legacy hackathon package** ? See `archive/hackathon/`
