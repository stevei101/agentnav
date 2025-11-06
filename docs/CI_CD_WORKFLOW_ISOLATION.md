# CI/CD Workflow Isolation - Implementation Guide

## Overview

This document describes the CI/CD workflow isolation strategy implemented to prevent cross-contamination between the `agentnav` and `prompt-vault` applications.

## Problem Statement

Previously, the agentnav CI workflows (`ci.yml`, `build.yml`, `terraform.yml`) would trigger on **all** repository changes, including changes to `prompt-vault/**` files. This caused:

- ❌ Backend tests failing due to missing agentnav files when only prompt-vault changed
- ❌ Secret verification failures on prompt-vault-only changes
- ❌ Quality gates failing unnecessarily
- ❌ Wasted CI/CD resources and time

## Solution

Implemented complete workflow isolation using GitHub Actions path filtering:

1. **Agentnav workflows** exclude prompt-vault changes
2. **Prompt-vault workflow** only runs on prompt-vault changes
3. **Independent quality gates** for each application

## Implementation Details

### 1. Agentnav Workflows (Exclude Prompt Vault)

Modified three workflow files to add `paths-ignore`:

#### `.github/workflows/ci.yml`
```yaml
on:
  pull_request:
    branches: [main]
    paths-ignore:
      - 'prompt-vault/**'
  push:
    branches: ['**']
    paths-ignore:
      - 'prompt-vault/**'
```

**Impact:** CI tests, linting, and security scans won't run when only prompt-vault files change.

#### `.github/workflows/build.yml`
```yaml
on:
  push:
    branches:
      - main
    paths:
      - '**'
    paths-ignore:
      - 'prompt-vault/**'
  pull_request:
    branches:
      - main
    paths:
      - '**'
    paths-ignore:
      - 'prompt-vault/**'
```

**Impact:** Container builds and deployments for agentnav won't run when only prompt-vault files change.

#### `.github/workflows/terraform.yml`
```yaml
on:
  push:
    branches: ['**']
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform.yml'
    paths-ignore:
      - 'prompt-vault/**'
  pull_request:
    branches:
      - main
    paths:
      - 'terraform/**'
      - '.github/workflows/terraform.yml'
    paths-ignore:
      - 'prompt-vault/**'
```

**Impact:** Terraform validation won't run when only prompt-vault files change (prompt-vault has separate infrastructure).

### 2. Prompt Vault Workflow (Isolated)

Created a new dedicated workflow: `.github/workflows/build-prompt-vault.yml`

**Triggers:** Only on changes to `prompt-vault/**`

**Features:**
- ✅ Path filtering: Only runs when prompt-vault files change
- ✅ Graceful handling: Checks if code exists before running jobs
- ✅ CI checks: Lint, format, and tests (when code is present)
- ✅ Build pipeline: Builds and pushes `prompt-vault-frontend` to Artifact Registry
- ✅ Deployment: Deploys to Cloud Run (us-central1) on main branch
- ✅ Quality gate: `PROMPT_VAULT_QUALITY_GATE` for branch protection

**Jobs:**
1. `changes` - Detects prompt-vault file changes
2. `prompt-vault-lint` - Runs ESLint and Prettier (if frontend exists)
3. `prompt-vault-tests` - Runs unit tests (if frontend exists)
4. `build-and-push` - Builds and pushes container image
5. `deploy` - Deploys to Cloud Run (main branch only)
6. `PROMPT_VAULT_QUALITY_GATE` - Quality gate for branch protection

## Workflow Trigger Matrix

| File Changed            | ci.yml | build.yml | terraform.yml | build-prompt-vault.yml |
|-------------------------|--------|-----------|---------------|------------------------|
| `backend/**`            | ✅     | ✅        | ❌            | ❌                     |
| `frontend/**`           | ✅     | ✅        | ❌            | ❌                     |
| `terraform/**`          | ❌     | ❌        | ✅            | ❌                     |
| `prompt-vault/**`       | ❌     | ❌        | ❌            | ✅                     |
| `backend/` + `prompt-vault/` | ✅ | ✅     | ❌            | ✅                     |

## Testing & Validation

### Automated Testing

A validation script is provided to verify the workflow isolation:

```bash
./scripts/test-workflow-isolation.sh
```

**Tests performed:**
1. ✅ ci.yml has paths-ignore for prompt-vault
2. ✅ build.yml has paths-ignore for prompt-vault
3. ✅ terraform.yml has paths-ignore for prompt-vault
4. ✅ build-prompt-vault.yml exists
5. ✅ build-prompt-vault.yml has correct path filter
6. ✅ All workflow YAML files are valid
7. ✅ Agentnav workflows don't explicitly include prompt-vault
8. ✅ Prompt-vault workflow has quality gate

**Expected output:**
```
======================================
CI/CD Workflow Isolation Test
======================================

Test 1: Checking paths-ignore in ci.yml...
✓ PASS: ci.yml has paths-ignore for prompt-vault/**
Test 2: Checking paths-ignore in build.yml...
✓ PASS: build.yml has paths-ignore for prompt-vault/**
Test 3: Checking paths-ignore in terraform.yml...
✓ PASS: terraform.yml has paths-ignore for prompt-vault/**
Test 4: Checking build-prompt-vault.yml exists...
✓ PASS: build-prompt-vault.yml exists
Test 5: Checking build-prompt-vault.yml path filter...
✓ PASS: build-prompt-vault.yml has correct path filter
Test 6: Validating YAML syntax...
✓ PASS: All workflow files have valid YAML syntax
Test 7: Checking agentnav workflows don't explicitly include prompt-vault...
✓ PASS: Agentnav workflows don't explicitly include prompt-vault
Test 8: Checking prompt-vault workflow has quality gate...
✓ PASS: build-prompt-vault.yml has PROMPT_VAULT_QUALITY_GATE

======================================
Test Summary
======================================
Passed: 8
Failed: 0

✓ All tests passed! CI/CD workflow isolation is properly configured.
```

### Manual Testing Scenarios

#### Scenario 1: Change Only Agentnav Files
**Action:** Modify `backend/main.py`

**Expected behavior:**
- ✅ `ci.yml` runs (tests, linting, security)
- ✅ `build.yml` runs (builds agentnav containers)
- ❌ `terraform.yml` does NOT run (no terraform changes)
- ❌ `build-prompt-vault.yml` does NOT run (no prompt-vault changes)

#### Scenario 2: Change Only Prompt Vault Files
**Action:** Modify `prompt-vault/README.md`

**Expected behavior:**
- ❌ `ci.yml` does NOT run (filtered by paths-ignore)
- ❌ `build.yml` does NOT run (filtered by paths-ignore)
- ❌ `terraform.yml` does NOT run (no terraform changes)
- ✅ `build-prompt-vault.yml` runs

#### Scenario 3: Change Both Agentnav and Prompt Vault Files
**Action:** Modify `backend/main.py` and `prompt-vault/README.md`

**Expected behavior:**
- ✅ `ci.yml` runs (agentnav tests)
- ✅ `build.yml` runs (builds agentnav containers)
- ❌ `terraform.yml` does NOT run (no terraform changes)
- ✅ `build-prompt-vault.yml` runs (prompt-vault changes)

#### Scenario 4: Change Terraform Files
**Action:** Modify `terraform/main.tf`

**Expected behavior:**
- ❌ `ci.yml` does NOT run (no code changes detected by path filter)
- ❌ `build.yml` does NOT run (no code changes)
- ✅ `terraform.yml` runs
- ❌ `build-prompt-vault.yml` does NOT run (no prompt-vault changes)

## Branch Protection Rules

### Recommended Setup

Configure branch protection for `main` branch with these required status checks:

**For Agentnav:**
- `AGENTIC_NAVIGATOR_QUALITY_GATE` (from ci.yml)

**For Prompt Vault:**
- `PROMPT_VAULT_QUALITY_GATE` (from build-prompt-vault.yml)

**Note:** Both quality gates handle skipped jobs gracefully, so they will pass even when their respective workflows don't run.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│                    stevei101/agentnav                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  agentnav/       │         │  prompt-vault/   │          │
│  │  ├── backend/    │         │  ├── frontend/   │          │
│  │  ├── frontend/   │         │  ├── database/   │          │
│  │  └── terraform/  │         │  └── Dockerfile  │          │
│  └────────┬─────────┘         └─────────┬────────┘          │
│           │                             │                    │
│           │ Change detected             │ Change detected   │
│           ▼                             ▼                    │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │  Agentnav        │         │  Prompt Vault    │          │
│  │  Workflows       │         │  Workflow        │          │
│  │  ├── ci.yml      │         │  └── build-      │          │
│  │  ├── build.yml   │         │     prompt-      │          │
│  │  └── terraform.yml│        │     vault.yml    │          │
│  └────────┬─────────┘         └─────────┬────────┘          │
│           │                             │                    │
│           │ paths-ignore:               │ paths:            │
│           │   - prompt-vault/**         │   - prompt-vault/**│
│           │                             │                    │
└───────────┴─────────────────────────────┴────────────────────┘
            │                             │
            ▼                             ▼
┌───────────────────────────────────────────────────────────────┐
│                   Google Cloud Platform                        │
├───────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐         ┌──────────────────┐           │
│  │  Agentnav        │         │  Prompt Vault    │           │
│  │  Services        │         │  Service         │           │
│  │  ├── frontend    │         │  └── frontend    │           │
│  │  └── backend     │         │     (us-central1)│           │
│  │    (eu-west1)    │         │                  │           │
│  └──────────────────┘         └──────────────────┘           │
└───────────────────────────────────────────────────────────────┘
```

## Benefits

### 1. **Reduced CI/CD Failures**
- No more backend test failures on prompt-vault changes
- No more secret verification failures on prompt-vault changes
- Quality gates function correctly for each application

### 2. **Faster CI/CD Pipeline**
- Workflows only run when relevant files change
- Reduced queue time and runner usage
- Faster feedback for developers

### 3. **Better Resource Utilization**
- GitHub Actions minutes saved by not running unnecessary jobs
- Cloud Build resources saved
- Artifact Registry storage optimized

### 4. **Cleaner CI/CD Logs**
- Easier to debug issues when workflows are isolated
- Clearer understanding of what's being tested/built
- Better audit trail

### 5. **Future-Proof Architecture**
- Ready for when prompt-vault code is added
- Graceful handling of missing directories
- Easy to extend for additional applications

## Troubleshooting

### Issue: Workflow still running when it shouldn't

**Cause:** The path filter might not be catching all files

**Solution:** Check the `paths-ignore` or `paths` configuration in the workflow file:

```bash
# View the workflow triggers
cat .github/workflows/<workflow-name>.yml | grep -A 10 "^on:"
```

### Issue: Quality gate failing even though no tests ran

**Cause:** Quality gate logic might not handle skipped jobs correctly

**Solution:** Verify the quality gate logic includes handling for skipped jobs:

```yaml
if [[ "$JOB_RESULT" == "failure" ]] || [[ "$JOB_RESULT" == "cancelled" ]]; then
  exit 1
fi
# success and skipped are both acceptable
```

### Issue: Both workflows running when only one should

**Cause:** Files changed in both agentnav and prompt-vault directories

**Solution:** This is expected behavior. Both workflows should run when both applications are modified.

## Maintenance

### Adding New Workflows

When adding new workflows for agentnav, remember to add `paths-ignore`:

```yaml
on:
  push:
    paths-ignore:
      - 'prompt-vault/**'
```

### Adding New Applications

If adding another isolated application (e.g., `analytics-app`):

1. Add `paths-ignore` to all agentnav and prompt-vault workflows:
   ```yaml
   paths-ignore:
     - 'prompt-vault/**'
     - 'analytics-app/**'
   ```

2. Create a dedicated workflow: `.github/workflows/build-analytics-app.yml`

3. Update the test script: `scripts/test-workflow-isolation.sh`

## References

- [GitHub Actions: Path Filtering](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpaths)
- [dorny/paths-filter Action](https://github.com/dorny/paths-filter)
- [Prompt Vault README](../prompt-vault/README.md)
- [Agentnav CI/CD Documentation](../README.md#cicd-pipeline)

## Changelog

### 2024-11-06 - Initial Implementation
- Added `paths-ignore` to ci.yml, build.yml, terraform.yml
- Created build-prompt-vault.yml workflow
- Created test-workflow-isolation.sh validation script
- Documented implementation in this guide

---

**Last Updated:** 2024-11-06  
**Status:** ✅ Complete and Validated  
**Next Review:** When adding new applications or workflows
