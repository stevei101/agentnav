# Terraform Infrastructure as Code

This directory contains Terraform configuration for provisioning all Google Cloud infrastructure required for the Agentic Navigator project.

## Overview

This Terraform configuration provisions:

- **Workload Identity Federation (WIF)** for secure GitHub Actions → GCP authentication
- **Service Accounts** with least-privilege IAM roles
- **Artifact Registry** for container image storage
- **Firestore** database for session memory and knowledge caching
- **Secret Manager** secrets for API keys
- **Cloud Run** service blueprints (frontend, backend)
- **Staging Environment** Cloud Run services (frontend-staging, backend-staging)
- **Cloud Build Triggers** for automatic "Connect Repo" deployments from GitHub (frontend & backend)

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Terraform Cloud Account** (or local Terraform)
3. **Required APIs:** Automatically enabled by Terraform (see `apis.tf`)

## Setup

### 1. Enable Required APIs

**Note:** APIs are automatically enabled by Terraform via `apis.tf`. However, if you need to enable them manually first (for initial setup), you can run:

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com
```

### 2. Configure Terraform Cloud Backend

Edit `backend.tf` or use environment variables:

```bash
export TF_CLOUD_ORGANIZATION="your-org-name"
export TF_WORKSPACE="agentnav-production"
```

### 3. Create `terraform.tfvars`

```hcl
project_id = "your-gcp-project-id"
github_repository = "stevei101/agentnav"
environment = "prod"
enable_staging_environment = true  # Enable staging Cloud Run services
```

### 4. Initialize Terraform

```bash
cd terraform
terraform init
```

### 5. Plan and Apply

```bash
terraform plan
terraform apply
```

## Important Notes

````

This is because Terraform's `google` provider doesn't fully support GPU configuration in Cloud Run v2 yet.

### Secret Values

Terraform creates the Secret Manager secrets but **does not set their values**. You must add secret values manually:

```bash
# Add Gemini API key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add GEMINI_API_KEY --data-file=-

# Add Hugging Face token (optional)
echo -n "YOUR_HF_TOKEN" | gcloud secrets versions add HUGGINGFACE_TOKEN --data-file=-
````

### Workload Identity Federation Outputs

After `terraform apply`, you'll get WIF outputs that need to be added as GitHub Secrets:

- `wif_provider` → GitHub Secret: `WIF_PROVIDER`
- `wif_service_account_email` → GitHub Secret: `WIF_SERVICE_ACCOUNT`

## File Structure

- `versions.tf` - Terraform and provider version requirements
- `provider.tf` - Google Cloud provider configuration
- `backend.tf` - Terraform Cloud remote backend
- `variables.tf` - Input variables (includes `enable_staging_environment`)
- `data.tf` - Data sources (project info, etc.)
- `iam.tf` - IAM roles, service accounts, and WIF setup
- `artifact_registry.tf` - Artifact Registry repository
- `firestore.tf` - Firestore database
- `secret_manager.tf` - Secret Manager secrets
- `cloud_run.tf` - Cloud Run service definitions (production and staging)
- `cloud_build.tf` - Cloud Build triggers for "Connect Repo" automatic deployments
- `outputs.tf` - Output values (WIF info, service URLs, staging URLs, etc.)

## Outputs

After applying, Terraform outputs:

- WIF provider and service account (for GitHub Secrets)
- Service URLs for all Cloud Run services (production and staging)
- Artifact Registry repository info
- Firestore database ID

### Staging Environment

The staging environment is controlled by the `enable_staging_environment` variable (default: `true`):

```hcl
variable "enable_staging_environment" {
  description = "Enable staging environment Cloud Run services"
  type        = bool
  default     = true
}
```

When enabled, Terraform provisions:

- `agentnav-frontend-staging` (us-central1)
- `agentnav-backend-staging` (europe-west1)

These services are used by the CI/CD pipeline for deployment gates. See `docs/BRANCH_PROTECTION_SETUP.md` for details.

## CI/CD Integration

This infrastructure is designed to work with GitHub Actions workflows:

1. Terraform provisions infrastructure
2. GitHub Actions uses WIF to authenticate
3. CI/CD builds images and pushes to Artifact Registry
4. CI/CD deploys images to Cloud Run services

See `docs/SYSTEM_INSTRUCTION.md` for full CI/CD workflow.

## Troubleshooting

### GPU Quota Issues

Ensure NVIDIA L4 GPU quota is approved in `europe-west1` region:

```bash
gcloud compute project-info describe --project=PROJECT_ID
```

### WIF Not Working

Verify the GitHub repository in `variables.tf` matches your actual repository:

```hcl
github_repository = "stevei101/agentnav"
```

### Secret Access Denied

Ensure service accounts have `secretmanager.secretAccessor` role (configured in `iam.tf`).

## Security Best Practices

- ✅ All secrets stored in Secret Manager (not in code)
- ✅ Service accounts use least-privilege IAM roles
- ✅ WIF used for GitHub Actions (no static keys)
- ✅ Secrets only accessible to required services
