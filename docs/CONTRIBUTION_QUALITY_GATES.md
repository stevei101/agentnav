# Contribution Quality Gates

This document describes the consolidated CI status checks and how they map to the underlying granular jobs.

Goal: reduce status-check noise while preserving the existing quality gates and execution steps.

## New primary status checks

We consolidated the CI checks into three primary, high-level checks. Each of these will appear as a single GitHub status check for pull requests targeting `main`.

1. CODE_QUALITY
   - Underlying jobs: `Code Quality (Linting & Formatting)`, `Frontend Unit Tests`, `Backend Tests (pytest + Firestore emulator)`
   - Purpose: Verifies code integrity, style, type checking, and unit tests / minimal coverage enforcement.

2. SECURITY_AUDIT
   - Underlying jobs: `Terraform Security Scan (tfsec)`, `OSV Dependency Vulnerability Scan`
   - Purpose: Verifies IaC security findings and dependency vulnerability scanning.

3. INFRA_VERIFICATION
   - Underlying job: `Terraform` (run as `terraform plan` on PRs)
   - Purpose: Verifies that proposed IaC changes produce a valid `terraform plan` and surface the plan in a PR comment. This workflow will not run `terraform apply` on PRs.
   - **Important**: This workflow runs conditionally based on path filters (only when `terraform/**` files change). GitHub will automatically skip this check for PRs without Terraform changes, and the check will show as "successful" in branch protection rules. This is expected behavior.

## How the consolidation works

- The repository keeps the granular jobs for useful logs and debugging. These jobs continue to run in their current workflows.
- The new composite jobs (named `CODE_QUALITY`, `SECURITY_AUDIT`, and `INFRA_VERIFICATION`) depend on their underlying granular jobs using the `needs:` relationship in GitHub Actions. The composite job will only succeed if all required upstream jobs succeed, producing a single high-level status.
- Operational workflows such as `Build and Deploy Containers` remain as non-mandatory operational workflows and should not be set as required checks for merging to `main`.
- **Note**: As of FR#150, the `Build Gemma Debug` workflow no longer runs on pull requests. It can be manually triggered via `workflow_dispatch` or runs automatically on pushes to `main` when Gemma-related files change.

## Branch protection: recommended configuration

Update the Branch Protection rules for `main` to require the following checks (names must match the workflow job names exactly):

- `CODE_QUALITY`
- `SECURITY_AUDIT`
- `INFRA_VERIFICATION`

Do NOT set the operational jobs as required (for example `Build and Push Containers`). The `Build Gemma (debug)` workflow no longer runs on pull requests as of FR#150.

### UI steps

1. Go to the repository on GitHub > Settings > Branches > Branch protection rules.
2. Edit the rule for `main` (or create a new one).
3. Under "Require status checks to pass before merging" select the three checks above and save.

### API snippet (optional)

You can programmatically set required status checks using the GitHub REST API. Replace placeholders as appropriate.

```bash
# list available status checks for a branch
curl -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/branches/main/protection/required_status_checks/contexts

# update required status checks (example body)
curl -X PUT -H "Authorization: token ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/branches/main/protection/required_status_checks \
  -d '{ "strict": true, "contexts": ["CODE_QUALITY", "SECURITY_AUDIT", "INFRA_VERIFICATION"] }'
```

## Understanding INFRA_VERIFICATION status

**Path Filtering Behavior:**

- `INFRA_VERIFICATION` only runs when `terraform/**` files are modified
- For PRs without Terraform changes, GitHub automatically skips the check
- **The check shows as "successful" in branch protection**, even though it was skipped
- This is the **correct and expected behavior** per GitHub's path filtering design

**Why This Design?**

- Prevents unnecessary Terraform validation runs for non-infrastructure PRs
- Reduces CI/CD costs and execution time
- Aligns with GitHub's recommendation for path-filtered required checks
- No waiting for checks that will never run

## Running checks locally

Before pushing your changes, you can run the equivalent checks locally using Makefile commands.

### CODE_QUALITY checks

Run all code quality checks locally:

```bash
# Lint frontend code
make lint

# Or run individual checks:
bun run lint              # Frontend ESLint
bun run format:check      # Frontend Prettier formatting
ruff check backend/       # Backend linting
black --check backend/    # Backend formatting
mypy backend/             # Backend type checking

# Run tests
make test                 # All tests (frontend + backend)
make test-frontend        # Frontend tests only
make test-backend         # Backend tests only

# Run full CI locally
make ci                   # Lint + test (same as CI pipeline)
```

### SECURITY_AUDIT checks

Run security scans locally:

```bash
# Terraform security scan
cd terraform
tfsec .

# OSV dependency scan (requires Docker)
docker run --rm -v "$(pwd)":/app ossf/osv-scanner --recursive /app
```

### INFRA_VERIFICATION checks

Validate Terraform changes:

```bash
cd terraform
terraform fmt -check -recursive     # Format check
terraform init                      # Initialize
terraform validate                  # Validate syntax
terraform plan                      # Preview changes (on PR, this posts as comment)
```

## Troubleshooting

### Check fails but works locally

1. **Different Python/Node versions**: Ensure local versions match CI:
   - Python: 3.11
   - Bun: latest

2. **Missing dependencies**: Run `make install-dev` to install all dev dependencies

3. **Environment variables**: Check `.env` file has required variables (see `.env.example`)

### Understanding failure messages

If a composite check fails, click on the failed check to see details:

- **CODE_QUALITY failed**: Look for "Code Quality", "Frontend Unit Tests", or "Backend Tests" job failures
- **SECURITY_AUDIT failed**: Check "Terraform Security Scan" or "OSV Dependency Vulnerability Scan" logs
- **INFRA_VERIFICATION failed**: Review "Terraform" job logs for plan errors

## Notes and rationale

- This approach preserves detailed logs for debugging while providing a simpler PR status surface area for reviewers.
- The `INFRA_VERIFICATION` check runs `terraform plan` on pull requests and posts the plan as a comment. It will not apply changes.
- If a composite check fails, open the failed job's logs to find the specific failing underlying step (lint, tests, or a scanner).
- All checks run automatically on every push to any branch, providing immediate feedback during development.

## Implementation details

### Status check execution

Status checks execute on:

- **All pushes** to any branch (immediate feedback during development)
- **Pull requests** targeting `main` (required for merge)
- **Direct pushes** to `main` (would be blocked if protection enabled)

### Required status checks

The following checks are **mandatory** for merging to `main`:

- `CODE_QUALITY` - Ensures code quality, style, and tests pass
- `SECURITY_AUDIT` - Ensures no security vulnerabilities introduced
- `INFRA_VERIFICATION` - Ensures Terraform changes are valid

### Operational checks (optional)

These checks run but are **not required** for merge:

- `Build and Push Containers` - Container build verification
- `Build Gemma Debug` - Gemma service debug builds

## Development Assistance

### agentnav-copilot-agent

The project includes a custom GitHub Copilot agent (`@agentnav-gh-copilot-agent`) that is context-aware of the complete system architecture, quality policies, and conventions. Use it to:

- Generate code following project patterns
- Review code for policy compliance (70% coverage, Cloud Run compatibility)
- Understand architectural decisions
- Get instant answers about tooling (e.g., "use uv for Python deps")

**Quick Start:**

```
@agentnav-gh-copilot-agent [your question]
```

For detailed usage instructions, see [COPILOT_AGENT_GUIDE.md](COPILOT_AGENT_GUIDE.md).

## Next steps

- ✅ GitHub Actions workflows configured with composite jobs
- ✅ Status checks appear automatically on all pushes
- ✅ Custom Copilot agent available for development assistance
- ⏳ Update branch protection rules in GitHub to require these checks (see setup script)
- ⏳ Optional: Add automated job to validate status check existence
