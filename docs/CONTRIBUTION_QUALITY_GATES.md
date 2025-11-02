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
- Operational workflows such as `Build and Deploy Containers` and `Build Gemma Debug` remain as non-mandatory operational workflows and should not be set as required checks for merging to `main`.

## Branch protection: recommended configuration

Update the Branch Protection rules for `main` to require the following checks (names must match the workflow job names exactly):

- `CODE_QUALITY`
- `SECURITY_AUDIT`
- `INFRA_VERIFICATION`

Do NOT set the operational jobs as required (for example `Build and Push Containers`, `Build Gemma (debug)`).

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

## Notes and rationale

- This approach preserves detailed logs for debugging while providing a simpler PR status surface area for reviewers.
- The `INFRA_VERIFICATION` check runs `terraform plan` on pull requests and posts the plan as a comment. It will not apply changes.
- If a composite check fails, open the failed job's logs to find the specific failing underlying step (lint, tests, or a scanner).

## Next steps

- Update branch protection rules in GitHub to require only these checks.
- Optionally, add an automated job to validate that the three contexts exist for new repositories or generate a periodic report of status checks.

