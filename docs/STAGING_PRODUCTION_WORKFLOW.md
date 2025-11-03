# Staging and Production Deployment Workflow

This document describes the staging and production deployment workflow for Agentic Navigator, including Terraform infrastructure management and CI/CD automation.

## Overview

Agentic Navigator uses a **two-environment deployment strategy**:

1. **Staging Environment** - Automatic deployments for PR testing
2. **Production Environment** - Deployments from main branch after PR merge

## Architecture

### Staging Environment
- **Purpose**: Test PRs before merging to main
- **Services**:
  - `agentnav-frontend-staging` (us-central1)
  - `agentnav-backend-staging` (europe-west1)
- **Image Tags**: `pr-{number}` (e.g., `pr-105`)
- **Deployment Trigger**: Automatic on PR creation/update
- **Access**: Public (unauthenticated)

### Production Environment
- **Purpose**: Serve production traffic
- **Services**:
  - `agentnav-frontend` (us-central1)
  - `agentnav-backend` (europe-west1)
  - `gemma-service` (europe-west1, GPU-enabled)
- **Image Tags**: `latest` and commit SHA
- **Deployment Trigger**: Automatic on merge to main
- **Access**: Public (unauthenticated)

## Workflow

### 1. Development Phase

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to GitHub
git push origin feature/my-feature
```

### 2. Pull Request Phase

```bash
# Create PR targeting main branch
gh pr create --title "feat: add new feature" --body "Description"
```

**What Happens Automatically:**

1. **CI Tests Run** (`.github/workflows/ci.yml`)
   - Frontend tests (Vitest)
   - Backend tests (pytest)
   - Security scans (TFSec, OSV)
   - Linting (ESLint, Ruff)

2. **Container Images Built** (`.github/workflows/build.yml`)
   - Frontend image: `agentnav-frontend:pr-{number}`
   - Backend image: `agentnav-backend:pr-{number}`
   - Gemma image: `gemma-service:pr-{number}` (via Cloud Build)

3. **Staging Deployment** (`.github/workflows/build.yml`)
   - Deploys to `agentnav-frontend-staging`
   - Deploys to `agentnav-backend-staging`
   - Comments PR with staging URLs
   - Creates GitHub deployment record

**Testing Staging:**

```bash
# Get staging URLs from PR comment or:
gcloud run services describe agentnav-frontend-staging \
  --region us-central1 \
  --format="value(status.url)"

gcloud run services describe agentnav-backend-staging \
  --region europe-west1 \
  --format="value(status.url)"
```

### 3. Review and Merge

1. **Code Review**: Team reviews PR
2. **Staging Testing**: Test features on staging URLs
3. **Approval**: PR approved by reviewers
4. **Merge**: Merge PR to main

### 4. Production Deployment

**What Happens Automatically on Merge:**

1. **CI Tests Run Again** on main branch
2. **Container Images Built** with `latest` tag
3. **Production Deployment**:
   - Updates `agentnav-frontend` with latest image
   - Updates `agentnav-backend` with latest image
   - Updates `gemma-service` with latest image
   - Creates GitHub deployment record

**Verify Production:**

```bash
# Get production URLs
gcloud run services describe agentnav-frontend \
  --region us-central1 \
  --format="value(status.url)"

gcloud run services describe agentnav-backend \
  --region europe-west1 \
  --format="value(status.url)"

gcloud run services describe gemma-service \
  --region europe-west1 \
  --format="value(status.url)"
```

## Terraform Infrastructure

### Enable/Disable Staging

Staging environment is controlled by the `enable_staging_environment` variable in `terraform/variables.tf`:

```hcl
variable "enable_staging_environment" {
  description = "Enable staging environment Cloud Run services for PR testing and validation."
  type        = bool
  default     = true  # Enabled by default
}
```

### Apply Infrastructure Changes

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan changes
terraform plan

# Apply changes (creates/updates staging services)
terraform apply

# Verify staging services exist
terraform output frontend_staging_service_url
terraform output backend_staging_service_url
```

### Terraform Outputs

```bash
# Production URLs
terraform output frontend_service_url
terraform output backend_service_url
terraform output gemma_service_url

# Staging URLs (if enabled)
terraform output frontend_staging_service_url
terraform output backend_staging_service_url

# Artifact Registry
terraform output artifact_registry_url
```

## Environment Variables

### Backend Environment Variables

Both staging and production backends receive:

```bash
GEMINI_API_KEY          # From Secret Manager
GEMMA_SERVICE_URL       # Gemma GPU service URL
FIRESTORE_PROJECT_ID    # GCP project ID
FIRESTORE_DATABASE_ID   # Firestore database name
ENVIRONMENT             # "staging" or "prod"
A2A_PROTOCOL_ENABLED    # "true"
```

### Frontend Environment Variables

Frontend services are static (nginx) and don't require runtime env vars. API URLs are configured at build time.

## GitHub Environments

GitHub Environments provide deployment tracking and protection:

### Staging Environment
- **Name**: `staging`
- **Protection**: None (automatic deployments)
- **Reviewers**: Not required
- **Deployment URL**: Staging frontend URL

### Production Environment
- **Name**: `production`
- **Protection**: Optional (can require manual approval)
- **Reviewers**: Optional (can require team approval)
- **Deployment URL**: Production frontend URL

**Configure in GitHub:**
1. Go to repository Settings → Environments
2. Create `staging` and `production` environments
3. Set protection rules as needed

## Rollback Procedures

### Rollback Staging

Staging uses PR-specific tags, so rollback isn't typically needed. Close/reopen PR to redeploy.

### Rollback Production

```bash
# Option 1: Revert the merge commit
git revert <merge-commit-sha>
git push origin main
# CI/CD will automatically deploy the reverted state

# Option 2: Deploy specific image tag
gcloud run services update agentnav-backend \
  --image europe-west1-docker.pkg.dev/PROJECT_ID/agentnav-containers/agentnav-backend:PREVIOUS_SHA \
  --region europe-west1

# Option 3: Use Cloud Console
# Navigate to Cloud Run → Select service → Revisions → Route traffic to previous revision
```

## Monitoring and Logs

### View Logs

```bash
# Staging logs
gcloud run services logs read agentnav-backend-staging \
  --region europe-west1 \
  --limit 50

# Production logs
gcloud run services logs read agentnav-backend \
  --region europe-west1 \
  --limit 50
```

### Cloud Console

- **Cloud Run**: https://console.cloud.google.com/run
- **Cloud Build**: https://console.cloud.google.com/cloud-build
- **Artifact Registry**: https://console.cloud.google.com/artifacts
- **Logs Explorer**: https://console.cloud.google.com/logs

## Troubleshooting

### Staging Deployment Fails

1. Check GitHub Actions logs
2. Verify Terraform applied successfully
3. Ensure `enable_staging_environment = true`
4. Check service account permissions

### Production Deployment Fails

1. Check GitHub Actions logs
2. Verify images were built successfully
3. Check Cloud Run service health
4. Review service account IAM roles

### Image Not Found

```bash
# List available images
gcloud artifacts docker images list \
  europe-west1-docker.pkg.dev/PROJECT_ID/agentnav-containers

# Check specific image tags
gcloud artifacts docker tags list \
  europe-west1-docker.pkg.dev/PROJECT_ID/agentnav-containers/agentnav-backend
```

## Best Practices

1. **Always test on staging** before merging to main
2. **Use descriptive PR titles** for clear deployment history
3. **Monitor production** after deployments
4. **Keep staging enabled** for continuous testing
5. **Use semantic versioning** in commit messages
6. **Review Cloud Run metrics** regularly
7. **Set up alerts** for production errors
8. **Document breaking changes** in PR descriptions

## Cost Optimization

### Staging Environment

- **Min instances**: 0 (scales to zero when not in use)
- **Max instances**: 5 (lower than production)
- **Resources**: Same as production for accurate testing

### Production Environment

- **Min instances**: 0 (can be increased for lower latency)
- **Max instances**: 10
- **Resources**: Optimized for workload

### Gemma GPU Service

- **Min instances**: 0 (GPUs are expensive)
- **Max instances**: 2
- **GPU Type**: NVIDIA L4
- **Cost**: ~$0.70/hour per instance

## Security

### Service Accounts

- **Frontend**: `agentnav-frontend@PROJECT_ID.iam.gserviceaccount.com`
- **Backend**: `agentnav-backend@PROJECT_ID.iam.gserviceaccount.com`
- **Gemma**: `agentnav-gemma@PROJECT_ID.iam.gserviceaccount.com`

### Secrets

All secrets stored in Secret Manager:
- `gemini-api-key`
- `huggingface-token`
- `firestore-credentials`

### Workload Identity Federation

GitHub Actions authenticates to GCP using WIF (no service account keys):
- **Provider**: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`
- **Service Account**: `github-actions@PROJECT_ID.iam.gserviceaccount.com`

## Related Documentation

- [Terraform README](../terraform/README.md)
- [CI/CD Documentation](./CONTRIBUTION_QUALITY_GATES.md)
- [Branch Protection Setup](./BRANCH_PROTECTION_SETUP.md)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)