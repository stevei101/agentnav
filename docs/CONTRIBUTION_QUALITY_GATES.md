# Contribution Quality Gates (FR#135)

**Status:** Active Policy  
**Priority:** High (Developer Velocity / Code Quality)  
**Timeline:** Standard PR Review  
**Applicable To:** All Pull Requests to `main` branch  
**Last Updated:** 2025-11-02

---

## Table of Contents

1. [Overview](#overview)
2. [Consolidated Status Checks](#consolidated-status-checks)
3. [Underlying Checks](#underlying-checks)
4. [Branch Protection Requirements](#branch-protection-requirements)
5. [Operational Jobs](#operational-jobs)
6. [Troubleshooting Failed Checks](#troubleshooting-failed-checks)

---

## Overview

As part of **Feature Request #135 (CI/CD Status Check Optimization)**, we have consolidated our GitHub status checks into **three primary, high-level quality gates** that provide clear, actionable feedback for reviewers and contributors.

**The Goal:** Reduce status check fatigue while maintaining comprehensive quality enforcement through consolidated reporting.

---

## Consolidated Status Checks

All Pull Requests targeting the `main` branch must pass these three consolidated status checks before merging:

### 1. CODE_QUALITY

**Purpose:** Verifies code integrity, style, type safety, and the **70% code coverage** policy.

**Scope:** This check consolidates the results of:
- Code Quality (Linting & Formatting)
- Frontend Unit Tests
- Backend Tests (pytest + Firestore emulator)

**Success Criteria:**
- All linting and formatting checks pass for both frontend (ESLint, Prettier) and backend (Black, isort, ruff, mypy)
- All frontend unit tests pass (Vitest)
- All backend unit tests pass (pytest)
- Code coverage meets the 70% minimum threshold

**If this check fails:**
1. Review the job logs to identify which underlying check failed
2. Fix linting issues: `bun run lint:fix` (frontend) or `black backend/ && isort backend/` (backend)
3. Fix failing tests: `bun run test` (frontend) or `pytest backend/tests` (backend)
4. Ensure test coverage meets 70% minimum

---

### 2. SECURITY_AUDIT

**Purpose:** Verifies Infrastructure as Code (IaC) security and dependency vulnerabilities.

**Scope:** This check consolidates the results of:
- Terraform Security Scan (tfsec)
- OSV Dependency Vulnerability Scan

**Success Criteria:**
- No critical security issues found in Terraform configuration
- No known vulnerabilities in project dependencies (npm, pip, etc.)

**If this check fails:**
1. Review tfsec findings and address any security misconfigurations in `terraform/`
2. Review OSV-Scanner findings and update vulnerable dependencies
3. If a finding is a false positive, document the justification and request reviewer approval

---

### 3. INFRA_VERIFICATION

**Purpose:** Verifies that Infrastructure as Code (IaC) changes are syntactically correct and pass the `terraform plan` phase.

**Scope:** This check runs:
- Terraform format validation (`terraform fmt`)
- Terraform initialization (`terraform init`)
- Terraform validation (`terraform validate`)
- TFLint for Terraform best practices
- TFSec security scan (duplicate from SECURITY_AUDIT for completeness)
- Terraform plan (dry-run, no apply)

**Success Criteria:**
- Terraform configuration is properly formatted
- Terraform configuration is valid
- Terraform plan executes successfully without errors
- No critical TFLint or TFSec findings

**If this check fails:**
1. Fix Terraform formatting: `terraform fmt -recursive terraform/`
2. Review and fix any validation errors
3. Check the terraform plan output in the PR comment for issues
4. Address any TFLint or TFSec findings

**Note:** This check only runs `terraform plan` in PRs, not `terraform apply`. The actual infrastructure changes are applied only after merge to `main`.

---

## Underlying Checks

While the three consolidated checks are the **primary status checks** reported to GitHub, the following granular checks run as part of the CI/CD pipeline:

| Underlying Job Name | Primary Gate | Description |
|:-------------------|:-------------|:------------|
| `Code Quality (Linting & Formatting)` | CODE_QUALITY | ESLint, Prettier, Black, isort, ruff, mypy |
| `Frontend Unit Tests` | CODE_QUALITY | Vitest test suite for React frontend |
| `Backend Tests (pytest + Firestore emulator)` | CODE_QUALITY | pytest test suite with Firestore emulator |
| `Terraform Security Scan (tfsec)` | SECURITY_AUDIT | Security scanning for Terraform IaC |
| `OSV Dependency Vulnerability Scan` | SECURITY_AUDIT | Vulnerability scanning for all dependencies |

**Important:** These underlying jobs run independently but are **not** required as individual status checks. Only the three consolidated checks (CODE_QUALITY, SECURITY_AUDIT, INFRA_VERIFICATION) are mandatory for merge.

---

## Branch Protection Requirements

The `main` branch is protected with the following **required status checks**:

1. ✅ **CODE_QUALITY** (required)
2. ✅ **SECURITY_AUDIT** (required)
3. ✅ **INFRA_VERIFICATION** (required)

**Not Required for Merge (Operational Jobs):**
- ❌ Build and Deploy Containers
- ❌ Build Gemma Debug
- ❌ Any individual underlying checks

**Rationale:** Operational jobs (build, deploy) are execution steps, not quality gates. They run automatically but do not block merging if they fail. This allows for deployment issues to be addressed separately without blocking code quality improvements.

---

## Operational Jobs

The following jobs are **operational** and run as part of the CI/CD pipeline but are **not mandatory status checks**:

### Build and Deploy Containers (`build.yml`)
- **Purpose:** Build and push container images to Google Artifact Registry, then deploy to Cloud Run
- **Trigger:** All PRs and pushes to `main`
- **Status:** Optional (does not block merge)

### Build Gemma Debug (`build-gemma-debug.yml`)
- **Purpose:** Debug build job for Gemma GPU service
- **Trigger:** All PRs
- **Status:** Optional (does not block merge)

**Why are these optional?**
- Build and deployment issues should not block code quality improvements
- These jobs may fail due to infrastructure issues (GCP credentials, quota, etc.) that are outside the contributor's control
- Failed builds can be addressed separately after merge if needed

---

## Troubleshooting Failed Checks

### CODE_QUALITY Failed

**Step 1:** Identify which underlying check failed:
```bash
# Check the GitHub Actions run details to see which job failed:
# - Code Quality (Linting & Formatting)
# - Frontend Unit Tests
# - Backend Tests
```

**Step 2:** Run checks locally:
```bash
# Frontend linting
bun run lint
bun run format:check

# Backend linting
black --check backend/
isort --check-only --profile black backend/
ruff check backend/
mypy backend/ --ignore-missing-imports

# Frontend tests
bun run test

# Backend tests (requires Firestore emulator)
docker run -d --name firestore-emulator -p 8081:8080 \
  gcr.io/google.com/cloudsdktool/cloud-sdk:emulators \
  gcloud beta emulators firestore start --host-port=0.0.0.0:8080 --project=agentnav-dev
FIRESTORE_EMULATOR_HOST=localhost:8081 pytest backend/tests
docker rm -f firestore-emulator
```

**Step 3:** Fix issues and push changes

---

### SECURITY_AUDIT Failed

**Step 1:** Identify which security scan failed:
```bash
# Check the GitHub Actions run details to see which scan failed:
# - Terraform Security Scan (tfsec)
# - OSV Dependency Vulnerability Scan
```

**Step 2:** Run scans locally:
```bash
# TFSec scan
tfsec terraform/

# OSV-Scanner
osv-scanner --recursive .
```

**Step 3:** Address findings:
- **TFSec:** Fix security misconfigurations in Terraform files
- **OSV-Scanner:** Update vulnerable dependencies or document false positives

---

### INFRA_VERIFICATION Failed

**Step 1:** Check the PR comment for Terraform plan output

**Step 2:** Run Terraform checks locally:
```bash
cd terraform/

# Format check
terraform fmt -check -recursive

# Validation
terraform init
terraform validate

# TFLint
tflint --format=default --recursive

# TFSec
tfsec .

# Plan (requires proper GCP credentials)
terraform plan
```

**Step 3:** Fix issues and push changes

---

## Integration with Existing Workflow

This quality gate system integrates with:
- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [CONTRIBUTION_GUIDE_PR_DISCIPLINE.md](CONTRIBUTION_GUIDE_PR_DISCIPLINE.md) - PR discipline and minimum viable commit
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing best practices

**Workflow:**
1. Create feature branch
2. Make changes
3. Run checks locally (see troubleshooting section)
4. Open Pull Request
5. Wait for three consolidated status checks to pass
6. Address any failures using troubleshooting guide
7. Request review once all checks pass
8. Merge after approval

---

## FAQ

### Q: Why consolidate status checks?

**A:** The previous workflow had too many individual status checks (5+ checks), which created:
- **Status check fatigue** for reviewers
- **Confusing status matrix** in the PR interface
- **Wasted runtime** due to redundant job setups

The three consolidated checks provide:
- **Clarity:** Immediate, actionable feedback in three logical areas
- **Efficiency:** Streamlined check process
- **Focus:** Easier to understand what failed and why

### Q: Can I see the results of individual underlying checks?

**A:** Yes! All underlying checks still run and their results are visible in the GitHub Actions run details. The consolidation only affects the **required status checks** for merge.

### Q: What if an operational job (build/deploy) fails?

**A:** Operational job failures do **not** block merge. These issues can be addressed separately after merge if needed, as they are often related to infrastructure (GCP credentials, quota) rather than code quality.

### Q: How do I know which underlying check failed if CODE_QUALITY fails?

**A:** Click on the failed CODE_QUALITY check in the PR status section. The job logs will show the status of each underlying check (code-quality, frontend-tests, backend-tests).

### Q: Can I skip a check?

**A:** No. All three consolidated checks are **mandatory** for merge to `main`. However, if you believe a check failure is a false positive or infrastructure issue, discuss with reviewers in the PR.

---

## Related Documentation

- [FR#135: CI/CD Status Check Optimization](https://github.com/stevei101/agentnav/issues/135) - Original feature request
- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing best practices
- [CONTRIBUTION_GUIDE_PR_DISCIPLINE.md](CONTRIBUTION_GUIDE_PR_DISCIPLINE.md) - PR discipline

---

## Revision History

| Date | Version | Description |
|:-----|:--------|:------------|
| 2025-11-02 | 1.0 | Initial policy creation (FR#135) |

---

**This guide is a living document.** As the project evolves, this guide will be updated to reflect new best practices and lessons learned. If you have suggestions for improvement, please open an issue or submit a PR.
