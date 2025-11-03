# Branch Protection Setup for Deployment Gate

This document describes how to configure GitHub branch protection rules to enforce deployment gates on the `main` branch.

## Overview

The deployment gate ensures that code is successfully deployed to the **staging environment** before it can be merged to the `main` branch. This is a critical safeguard to prevent broken code from reaching production.

## Architecture

The deployment pipeline consists of:

1. **Pull Request Trigger**: When a PR is opened targeting `main`, the CI/CD pipeline:
   - Builds and pushes container images with tag `pr-{number}`
   - Deploys images to **staging environment** (`agentnav-frontend-staging`, `agentnav-backend-staging`)
   - Reports deployment status to GitHub's `staging` environment

2. **Merge to Main Trigger**: When a PR is merged to `main`, the CI/CD pipeline:
   - Builds and pushes container images with tag `latest`
   - Deploys images to **production environment** (`agentnav-frontend`, `agentnav-backend`)
   - Reports deployment status to GitHub's `production` environment

3. **Branch Protection Rule**: The `main` branch protection rule requires:
   - Successful deployment to `staging` environment before merge is allowed
   - All CI checks to pass (tests, linting, security scans)

## Infrastructure Components

### Staging Environment (Cloud Run Services)

The staging environment consists of:

- **agentnav-frontend-staging** (us-central1)
  - Lower resource limits than production (max 5 instances vs 10)
  - Serves as pre-production validation environment
- **agentnav-backend-staging** (europe-west1)
  - Same configuration as production but with reduced limits
  - Environment variable: `ENVIRONMENT=staging`
  - Uses same Gemma GPU service as production (shared to reduce costs)

### GitHub Environments

Two GitHub Environments are configured:

1. **staging**: Tracks deployments to staging Cloud Run services
2. **production**: Tracks deployments to production Cloud Run services

These environments are created automatically by the CI/CD workflow when deployments occur.

## Configuration Steps

### Step 1: Enable Staging Environment in Terraform

The staging environment is controlled by the `enable_staging_environment` variable in Terraform:

```hcl
# terraform/variables.tf
variable "enable_staging_environment" {
  description = "Enable staging environment Cloud Run services"
  type        = bool
  default     = true
}
```

To provision the staging services:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This will create:

- `google_cloud_run_v2_service.frontend_staging`
- `google_cloud_run_v2_service.backend_staging`

### Step 2: Verify CI/CD Workflow

The `.github/workflows/build.yml` workflow handles deployments:

**On Pull Request:**

- Job: `deploy-staging`
- Deploys to staging environment
- Reports to GitHub `staging` environment
- Posts comment with staging URLs to PR

**On Merge to Main:**

- Job: `deploy` (production)
- Deploys to production environment
- Reports to GitHub `production` environment

### Step 3: Configure GitHub Branch Protection

**⚠️ IMPORTANT: This step must be done manually in GitHub repository settings.**

1. Navigate to: **Repository Settings** → **Branches** → **Branch protection rules**

2. Click **Add rule** (or edit existing rule for `main` branch)

3. Configure the following settings:

   **Branch name pattern:** `main`

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: 1 (recommended)

   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - **Status checks that are required:**
     - `code-quality` (from ci.yml)
     - `frontend-tests` (from ci.yml)
     - `backend-tests` (from ci.yml)
     - `build-and-push (frontend)` (from build.yml)
     - `build-and-push (backend)` (from build.yml)
     - `build-and-push (gemma)` (from build.yml)

   ✅ **Require deployments to succeed before merging**
   - **Required deployment environments:** `staging`

   ✅ **Require conversation resolution before merging** (recommended)

   ✅ **Do not allow bypassing the above settings** (recommended)

4. Click **Create** or **Save changes**

### Step 4: Test the Deployment Gate

1. Create a test branch and make a small change:

   ```bash
   git checkout -b test/branch-protection
   echo "# Test" >> README.md
   git add README.md
   git commit -m "Test: Branch protection"
   git push origin test/branch-protection
   ```

2. Open a Pull Request targeting `main`

3. Observe the CI/CD pipeline:
   - Build jobs should complete
   - `deploy-staging` job should run
   - GitHub should show deployment to `staging` environment

4. Check that the merge button is blocked until:
   - All status checks pass
   - Staging deployment succeeds

5. Once all checks pass, the PR can be merged

6. After merge, observe the production deployment

## Verification

### Check Staging Services

```bash
# Check staging frontend
gcloud run services describe agentnav-frontend-staging \
  --region us-central1 \
  --project ${GCP_PROJECT_ID} \
  --format="value(status.url)"

# Check staging backend
gcloud run services describe agentnav-backend-staging \
  --region europe-west1 \
  --project ${GCP_PROJECT_ID} \
  --format="value(status.url)"
```

### Check GitHub Environments

1. Navigate to: **Repository** → **Environments**
2. Verify `staging` and `production` environments exist
3. Click into each environment to view deployment history

### Check Branch Protection Status

1. Navigate to: **Repository Settings** → **Branches**
2. Verify `main` branch rule shows:
   - ✅ Require deployments to succeed: `staging`
   - ✅ Require status checks to pass

## Troubleshooting

### Problem: Staging deployment fails

**Solution:**

1. Check Cloud Run service logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agentnav-frontend-staging" --limit 50 --format json
   ```
2. Verify staging services exist in GCP Console
3. Check Terraform apply completed successfully

### Problem: GitHub environment doesn't show deployment

**Solution:**

1. Verify workflow has `deployments: write` permission
2. Check that `chrnorm/deployment-action@v2` step completed successfully
3. Review GitHub Actions logs for errors

### Problem: Branch protection rule doesn't block merge

**Solution:**

1. Verify branch protection rule is saved correctly
2. Check that "Require deployments to succeed" is enabled with `staging` environment
3. Ensure "Do not allow bypassing" is enabled

### Problem: PR builds but doesn't deploy to staging

**Solution:**

1. Check that workflow trigger includes `pull_request` event
2. Verify `if: github.event_name == 'pull_request'` condition in `deploy-staging` job
3. Check Workload Identity Federation credentials are configured

## Cost Considerations

### Staging Environment Costs

- **Lower resource limits**: Staging services have `max_instance_count = 5` vs production's `10`
- **Scale to zero**: Both staging and production scale to 0 when idle
- **Shared Gemma service**: Staging backend uses the same Gemma GPU service to reduce costs

### Cost Optimization Tips

1. **Disable staging when not needed:**

   ```hcl
   # terraform/variables.tf
   variable "enable_staging_environment" {
     default = false  # Temporarily disable
   }
   ```

2. **Delete old PR images:**

   ```bash
   # List old PR images
   gcloud artifacts docker images list \
     ${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPOSITORY}/agentnav-frontend \
     --filter="tags:pr-*"

   # Delete specific PR image
   gcloud artifacts docker images delete \
     ${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev/${GCP_PROJECT_ID}/${ARTIFACT_REGISTRY_REPOSITORY}/agentnav-frontend:pr-123
   ```

3. **Monitor costs in GCP Console:**
   - Navigate to: **Billing** → **Cost breakdown**
   - Filter by: Cloud Run, Artifact Registry

## Security Considerations

1. **Service Account Permissions**: Staging services use the same service accounts as production
   - Consider creating separate service accounts for staging with more restrictive permissions

2. **Secrets**: Staging uses the same secrets as production (GEMINI_API_KEY, etc.)
   - Consider creating separate secrets for staging environment

3. **Public Access**: Both staging and production services allow unauthenticated access
   - Consider adding Cloud Armor or Identity-Aware Proxy for staging

## Maintenance

### Regular Tasks

1. **Review deployment history** (weekly):
   - Check GitHub Environments for failed deployments
   - Review Cloud Run logs for errors

2. **Clean up old PR images** (monthly):
   - Delete images older than 30 days with `pr-*` tags

3. **Verify branch protection** (monthly):
   - Ensure rules haven't been accidentally disabled
   - Check that new status checks are added to required list

### Updates

When adding new services:

1. Add staging variant in `terraform/cloud_run.tf`
2. Add deploy step in `.github/workflows/build.yml`
3. Update this documentation

## References

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Deployments API](https://docs.github.com/en/rest/deployments)
- [Cloud Run Deployment](https://cloud.google.com/run/docs/deploying)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)

## Related Feature Requests

- FR#002: CI/CD Pipeline (parent implementation)
- FR#007: Terraform Infrastructure (IaC foundation)
- FR#070: Deployment Gate (this document)
