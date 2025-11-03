# Manual Workflow Triggers

This document describes workflows that can be triggered manually via the GitHub Actions UI.

## Build Gemma Debug

**Workflow File:** `.github/workflows/build-gemma-debug.yml`

**Purpose:** Build a debug version of the Gemma GPU service for troubleshooting and development purposes. This workflow is designed for diagnostic use and is NOT required for standard Pull Request validation.

### When to Use

- Troubleshooting Gemma service build issues
- Testing changes to `backend/Dockerfile.gemma.ci` or `backend/Dockerfile.gemma`
- Validating Gemma service configuration changes
- Debugging deployment problems specific to the Gemma GPU service

### How to Trigger Manually

1. Navigate to the repository on GitHub
2. Go to **Actions** tab
3. Select **Build Gemma Debug** workflow from the left sidebar
4. Click **Run workflow** button
5. Select the branch you want to run the workflow against
6. (Optional) Enter a reason for the debug build in the "Reason for running this debug build" field
7. Click **Run workflow**

### Automatic Triggers

The workflow also runs automatically when:

- Changes are pushed to the `main` branch that affect:
  - `backend/Dockerfile.gemma*` files
  - `backend/gemma_service/**` directory

### History

- **FR#150** (2024): Removed from Pull Request triggers to optimize CI/CD runtime and reduce status check clutter
- The workflow was originally triggered on all PRs but caused unnecessary compute overhead for a diagnostic tool

### Related Documentation

- [GPU Setup Guide](./GPU_SETUP_GUIDE.md) - Full Gemma GPU service deployment guide
- [Gemma Integration Guide](./GEMMA_INTEGRATION_GUIDE.md) - Gemma service integration details
- [Contribution Quality Gates](./CONTRIBUTION_QUALITY_GATES.md) - Required CI/CD checks for PRs
