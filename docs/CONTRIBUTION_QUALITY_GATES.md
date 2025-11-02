# Contribution Quality Gates Guide

**Status:** Active Policy  
**Feature Request:** #100  
**Priority:** High (Code Quality / Development Efficiency)  
**Last Updated:** 2025-11-02

---

## Table of Contents

1. [Overview](#overview)
2. [Mandatory Status Checks](#mandatory-status-checks)
3. [Running Checks Locally](#running-checks-locally)
4. [Troubleshooting](#troubleshooting)
5. [Coverage Requirements](#coverage-requirements)
6. [Integration with Branch Protection](#integration-with-branch-protection)

---

## Overview

Every Pull Request to the `main` branch must pass a comprehensive set of quality gates before merge. These checks ensure code quality, security, and reliability across the entire codebase.

**Why This Matters:**
- **Early Feedback:** Immediate feedback on every commit prevents last-minute fix-up work
- **Consistent Quality:** Enforces quality standards across all development branches
- **Faster Reviews:** Reviewers see clear PASS/FAIL status on each PR
- **Reduced Technical Debt:** Prevents accumulation of style violations and test failures

---

## Mandatory Status Checks

All Pull Requests must pass the following status checks before merging to `main`:

### 1. `quality / lint-and-style`

**What it validates:**
- TypeScript/JavaScript code follows ESLint rules
- Code formatting matches Prettier standards
- Python code follows Black formatting standards
- Python imports are sorted correctly (isort)
- Python code passes Ruff linting
- Python code passes mypy type checking

**Pass criteria:**
- No ESLint errors
- Code is formatted according to Prettier
- Python code is formatted with Black
- Imports sorted with isort (Black profile)
- No Ruff linting errors
- No mypy type errors

**How to run locally:**

```bash
# Frontend linting
bun run lint
bun run format:check

# Or use the Makefile
make lint

# Backend linting
cd backend
black --check .
isort --check-only --profile black .
ruff check .
mypy . --ignore-missing-imports
```

**How to fix issues:**

```bash
# Auto-fix frontend formatting
bun run format

# Auto-fix backend formatting
cd backend
black .
isort --profile black .
ruff check --fix .
```

---

### 2. `test / frontend-unit`

**What it validates:**
- All frontend unit tests pass
- Code coverage meets 70% minimum threshold
- Coverage includes lines, functions, branches, and statements

**Pass criteria:**
- All Vitest tests pass
- Line coverage ≥ 70%
- Function coverage ≥ 70%
- Branch coverage ≥ 70%
- Statement coverage ≥ 70%

**How to run locally:**

```bash
# Run tests with coverage
bun run test -- --run --coverage

# Run tests in watch mode (development)
bun run test

# Or use the Makefile
make test-frontend
```

**Coverage report location:**
- Terminal: Summary displayed after test run
- HTML: `coverage/index.html` (open in browser)
- JSON: `coverage/coverage.json`

**Example output:**
```
 % Coverage report from v8
----------------|---------|----------|---------|---------|-------------------
File            | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
----------------|---------|----------|---------|---------|-------------------
All files       |   72.5  |   68.2   |   75.0  |   72.5  |
 components/    |   80.1  |   72.3   |   85.2  |   80.1  |
  AgentCard.tsx |   90.5  |   85.0   |   95.0  |   90.5  | 45-48
----------------|---------|----------|---------|---------|-------------------
```

---

### 3. `test / backend-unit`

**What it validates:**
- All backend unit tests pass
- Code coverage meets 70% minimum threshold
- Tests run successfully with Firestore emulator

**Pass criteria:**
- All pytest tests pass
- Code coverage ≥ 70% (combined line/statement coverage)
- Tests complete within timeout limits

**How to run locally:**

```bash
# Option 1: Using Makefile (recommended - handles Firestore emulator)
make test-backend

# Option 2: Manual with local Firestore emulator
# Start Firestore emulator first
docker run -d --name firestore-emulator -p 8081:8080 \
  gcr.io/google.com/cloudsdktool/cloud-sdk:emulators \
  gcloud beta emulators firestore start --host-port=0.0.0.0:8080 --project=agentnav-dev

# Set environment variables
export FIRESTORE_EMULATOR_HOST='localhost:8081'
export FIRESTORE_PROJECT_ID='agentnav-dev'

# Run tests with coverage
cd backend
pytest tests --cov=backend --cov-report=term-missing --cov-fail-under=70

# Cleanup
docker rm -f firestore-emulator
```

**Coverage report location:**
- Terminal: Detailed report with missing line numbers
- XML: `coverage.xml` (for CI/CD tools)

**Example output:**
```
---------- coverage: platform linux, python 3.11.0 -----------
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
backend/__init__.py                     0      0   100%
backend/main.py                        42     10    76%   45-54
backend/services/session_service.py    85     18    79%   102-110, 145-150
-----------------------------------------------------------------
TOTAL                                 127     28    78%

Required test coverage of 70% reached. Total coverage: 78.00%
```

---

### 4. `security / tfsec-iac`

**What it validates:**
- Terraform infrastructure code follows security best practices
- No critical security vulnerabilities in IaC
- Sensitive data is not hardcoded
- IAM policies follow least-privilege principles

**Pass criteria:**
- No critical or high severity findings
- All security recommendations addressed or explicitly waived

**How to run locally:**

```bash
# Install tfsec (if not already installed)
brew install tfsec  # macOS
# or
curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash

# Run tfsec scan
cd terraform
tfsec .

# Or scan with specific output format
tfsec . --format json
```

**Common issues and fixes:**
- **Hardcoded secrets:** Use Secret Manager or environment variables
- **Overly permissive IAM:** Restrict to minimum required permissions
- **Unencrypted storage:** Enable encryption at rest
- **Public access:** Restrict access to authenticated users only

---

### 5. `security / secret-scan`

**What it validates:**
- No secrets, API keys, or credentials in code
- Dependencies are free from known vulnerabilities
- OSV Scanner detects vulnerable packages

**Pass criteria:**
- No secrets detected in committed code
- No critical or high severity vulnerabilities in dependencies
- All vulnerable dependencies updated or explicitly accepted

**How to run locally:**

```bash
# Install OSV Scanner
go install github.com/google/osv-scanner/cmd/osv-scanner@latest

# Run vulnerability scan
osv-scanner --recursive .

# Or use Docker (no installation required)
docker run -v $(pwd):/app ghcr.io/google/osv-scanner --recursive /app
```

**How to fix issues:**
- **Secrets detected:** Remove from code, use Secret Manager or environment variables
- **Vulnerable dependencies:** Update to patched versions
  - Frontend: `bun update <package>`
  - Backend: Update version in `requirements.txt` or `pyproject.toml`

---

## Running Checks Locally

### Quick Check: Run All Quality Gates

Use the Makefile to run all checks before submitting a PR:

```bash
# Run full CI check locally
make ci

# This runs:
# 1. Linting (frontend + backend)
# 2. Frontend tests with coverage
# 3. Backend tests with coverage
```

### Individual Checks

```bash
# Linting only
make lint

# Frontend tests only
make test-frontend

# Backend tests only
make test-backend

# Format code (auto-fix)
make format
```

---

## Troubleshooting

### Test / Frontend-Unit Failures

**Coverage below 70%:**
```
Error: Coverage for lines (68%) does not meet threshold (70%)
```

**Solution:**
1. Add tests for uncovered code paths
2. Review coverage report: `open coverage/index.html`
3. Focus on files with low coverage (shown in red)
4. Add unit tests for untested components/functions

**Example: Adding a test**
```typescript
// components/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import { MyComponent } from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });
});
```

---

### Test / Backend-Unit Failures

**Coverage below 70%:**
```
FAILED: Required test coverage of 70% not reached. Total coverage: 65.23%
```

**Solution:**
1. Check coverage report for missing lines
2. Add tests for uncovered code paths
3. Focus on business logic and edge cases

**Example: Adding a test**
```python
# backend/tests/test_my_service.py
import pytest
from backend.services.my_service import MyService

@pytest.mark.asyncio
async def test_my_service_handles_edge_case():
    service = MyService()
    result = await service.process_data(None)
    assert result is not None
```

**Firestore emulator issues:**
```
Error: Connection refused to localhost:8081
```

**Solution:**
1. Ensure Firestore emulator is running: `docker ps | grep firestore`
2. Start emulator: `make start-firestore`
3. Verify port 8081 is not in use: `lsof -i :8081`

---

### Quality / Lint-and-Style Failures

**Frontend linting errors:**
```
Error: 'variable' is never used (no-unused-vars)
```

**Solution:**
1. Auto-fix most issues: `bun run lint --fix`
2. Format code: `bun run format`
3. Review and fix remaining issues manually

**Backend formatting issues:**
```
Error: Black formatting check failed
```

**Solution:**
```bash
cd backend
# Auto-fix formatting
black .
isort --profile black .

# Verify
black --check .
isort --check-only --profile black .
```

---

### Security Scan Failures

**TFSec critical finding:**
```
HIGH: Unencrypted Cloud Storage bucket detected
```

**Solution:**
1. Review the finding in the CI output
2. Update Terraform code to address the issue
3. Add explicit encryption configuration
4. Re-run: `tfsec terraform/`

**OSV Scanner vulnerability:**
```
Vulnerability found in package 'requests' version 2.28.0
```

**Solution:**
```bash
# Update the vulnerable package
# Backend
pip install --upgrade requests
pip freeze | grep requests >> backend/requirements.txt

# Frontend
bun update <package-name>
```

---

## Coverage Requirements

### Why 70% Coverage?

The 70% code coverage threshold is a **mandatory policy** established in the project system instructions. This requirement ensures:

1. **Quality Assurance:** Core business logic is tested
2. **Regression Prevention:** Changes don't break existing functionality
3. **Confidence in Refactoring:** Safe to modify code with test safety net
4. **Documentation:** Tests serve as executable documentation

### What Counts Toward Coverage?

**Frontend (Vitest):**
- Lines: Individual code statements
- Functions: Function definitions
- Branches: Conditional paths (if/else, switch, ternary)
- Statements: Complete expressions

**Backend (pytest-cov):**
- Line coverage: Lines executed during tests
- Branch coverage: Conditional paths taken

### Coverage Exclusions

**Frontend (configured in `vitest.config.ts`):**
- `node_modules/**`
- `dist/**`
- Test files (`**/*.test.{ts,tsx}`)
- Config files (`**/*.config.{ts,js}`)
- Setup files (`**/*.setup.{ts,js}`)
- Type definitions (`types.ts`)

**Backend:**
- Test files in `backend/tests/`
- Configuration files
- `__init__.py` files (usually empty)

---

## Integration with Branch Protection

### Main Branch Protection Rules

The `main` branch is protected with the following rules:

**Required Status Checks:**
- `quality / lint-and-style`
- `test / frontend-unit`
- `test / backend-unit`
- `security / tfsec-iac`
- `security / secret-scan`

**Additional Rules:**
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Require conversation resolution before merging
- Do not allow force pushes
- Do not allow deletions

### Pull Request Workflow

1. **Create Feature Branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes and Commit:**
   ```bash
   git add .
   git commit -m "Add new feature"
   ```

3. **Run Local Checks:**
   ```bash
   make ci
   ```

4. **Push to GitHub:**
   ```bash
   git push origin feature/my-feature
   ```

5. **Open Pull Request:**
   - Navigate to GitHub
   - Open Pull Request from feature branch to `main`
   - Status checks automatically run

6. **Monitor Status Checks:**
   - View check results in PR UI
   - Fix any failing checks
   - Push updates trigger re-run

7. **Merge:**
   - All checks must pass (green checkmarks)
   - PR can be merged

---

## Best Practices

### During Development

1. **Run checks frequently:**
   - Before committing: `make lint`
   - Before pushing: `make test`
   - Before PR: `make ci`

2. **Write tests alongside code:**
   - Add tests for new features
   - Update tests for modified features
   - Ensure tests are meaningful, not just coverage padding

3. **Monitor coverage locally:**
   - Check coverage reports after tests
   - Focus on uncovered critical paths
   - Add tests incrementally

### Before Pull Request

1. **Self-review checklist:**
   - [ ] All status checks pass locally (`make ci`)
   - [ ] Code is formatted (`make format`)
   - [ ] Tests added/updated for changes
   - [ ] Coverage meets 70% threshold
   - [ ] No security vulnerabilities
   - [ ] Documentation updated if needed

2. **Clean commit history:**
   - Meaningful commit messages
   - Atomic commits (one logical change per commit)
   - No temporary/debug commits

3. **PR description:**
   - Clear description of changes
   - Link to related issues
   - Screenshots for UI changes
   - Testing performed

---

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [CONTRIBUTION_GUIDE_PR_DISCIPLINE.md](CONTRIBUTION_GUIDE_PR_DISCIPLINE.md) - PR discipline and MVC principles
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing best practices
- [local-development.md](local-development.md) - Local development setup

---

## FAQ

### Q: What if I can't reach 70% coverage?

**A:** Focus on testing:
1. Core business logic (highest priority)
2. Public API endpoints
3. Critical user flows
4. Error handling paths

If you genuinely cannot reach 70% due to untestable code (e.g., external API mocks), discuss with reviewers in the PR.

### Q: Can I skip a status check?

**A:** No. All status checks are mandatory and enforced by branch protection. If a check is failing incorrectly (false positive), discuss with maintainers.

### Q: How long do status checks take?

**A:** Typical run times:
- `quality / lint-and-style`: ~2-3 minutes
- `test / frontend-unit`: ~2-4 minutes
- `test / backend-unit`: ~3-5 minutes
- `security / tfsec-iac`: ~1-2 minutes
- `security / secret-scan`: ~2-3 minutes

**Total: ~10-15 minutes** for all checks to complete.

### Q: What if checks fail on `main` branch?

**A:** This should not happen due to branch protection. If it does:
1. Open an issue immediately
2. Do not merge additional PRs until resolved
3. Fix in a hotfix PR with expedited review

### Q: How do I run checks without pushing?

**A:** Use the Makefile:
```bash
make ci
```

This runs all quality gates locally before you push.

---

## Summary

**Before every Pull Request:**
1. ✅ Run `make ci` locally
2. ✅ Fix any failing checks
3. ✅ Verify coverage ≥ 70%
4. ✅ Push and open PR
5. ✅ Monitor GitHub status checks
6. ✅ Merge when all checks pass

**Remember:** Status checks are not obstacles—they're quality gates that help deliver reliable, maintainable software. Embrace them! 🚀
