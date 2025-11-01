# Cloud Run "Connect Repo" Setup Guide

This guide explains how to set up the Cloud Run "Connect Repo" feature for automatic deployments from GitHub.

## Overview

The Cloud Run "Connect Repo" feature enables automatic deployments directly from your GitHub repository to Cloud Run services. This eliminates the need for complex GitHub Actions workflows for standard deployments.

**What's Configured:**
- ✅ Cloud Build triggers for Frontend and Backend services
- ✅ Automatic build and deploy on push to `main` branch
- ✅ Build configurations (`cloudbuild-frontend.yaml`, `cloudbuild-backend.yaml`)
- ✅ IAM permissions for Cloud Build service account

**What's NOT Configured (by design):**
- ❌ Gemma GPU service (requires manual GPU configuration)
- ❌ Initial GitHub repository connection (first-time setup)

---

## Initial Setup

### Step 1: Connect GitHub Repository (First Time Only)

Before Terraform triggers work, you need to connect your GitHub repository to Cloud Build. This is a one-time setup:

**Option A: Via Cloud Console (Recommended)**

1. Go to [Cloud Build > Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **"Connect Repository"**
3. Select **GitHub** as your source
4. Authenticate with GitHub (authorize Google Cloud)
5. Select your repository: `stevei101/agentnav`
6. Click **"Connect"**

**Option B: Via gcloud CLI**

```bash
gcloud builds triggers connect github \
  --repo-name=agentnav \
  --repo-owner=stevei101 \
  --region=global
```

### Step 2: Terraform Creates Triggers

After connecting the repository, Terraform will create the Cloud Build triggers:

```bash
cd terraform
terraform apply
```

This will create:
- `agentnav-frontend-deploy` trigger
- `agentnav-backend-deploy` trigger

---

## How It Works

### Automatic Deployment Flow

1. **Developer pushes to `main` branch**
2. **Cloud Build detects push** (via trigger)
3. **Cloud Build executes** `cloudbuild-frontend.yaml` or `cloudbuild-backend.yaml`
4. **Builds container image** using Docker
5. **Pushes to Artifact Registry**
6. **Deploys to Cloud Run** automatically

### Build Configuration Files

**`cloudbuild-frontend.yaml`:**
- Builds frontend using `frontend.Dockerfile.dev`
- Pushes to Artifact Registry
- Deploys to `agentnav-frontend` service in `us-central1`

**`cloudbuild-backend.yaml`:**
- Builds backend using `backend/Dockerfile.dev`
- Pushes to Artifact Registry
- Deploys to `agentnav-backend` service in `europe-west1`
- Sets environment variables and secrets

---

## Variables

The triggers use Terraform substitutions:

| Variable | Description | Example |
|----------|-------------|---------|
| `_SERVICE_NAME` | Cloud Run service name | `agentnav-frontend` |
| `_REGION` | Deployment region | `us-central1` |
| `_PROJECT_ID` | GCP Project ID | `your-project-id` |
| `_ARTIFACT_REGION` | Artifact Registry location | `europe-west1` |
| `_GAR_REPO` | Artifact Registry repository | `agentnav-containers` |
| `_SERVICE_ACCOUNT` | Service account email | `agentnav-frontend@...` |
| `_GEMMA_URL` | Gemma service URL (backend only) | `https://gemma-service-...` |

---

## Configuration

### Enable/Disable Connect Repo

Edit `terraform/terraform.tfvars`:

```hcl
# Enable automatic deployments
enable_connect_repo = true

# Or disable if you prefer manual deployments
enable_connect_repo = false
```

### Change GitHub Branch

```hcl
github_branch = "production"  # Deploy from production branch
```

### Manual Trigger Execution

You can also manually trigger builds:

```bash
# Trigger frontend build
gcloud builds triggers run agentnav-frontend-deploy \
  --branch=main

# Trigger backend build
gcloud builds triggers run agentnav-backend-deploy \
  --branch=main
```

---

## Benefits

### ✅ Simplified CI/CD
- No need for complex GitHub Actions workflows
- Automatic deployments on every push
- Native Google Cloud integration

### ✅ Reduced Complexity
- No manual `gcloud` commands in CI/CD
- No Podman setup in GitHub Actions
- Automatic image tagging and deployment

### ✅ Cost Efficiency
- Uses Cloud Build (included in GCP free tier)
- No GitHub Actions minutes for standard deployments

### ✅ Security
- Uses Cloud Build service account (IAM-managed)
- Secrets accessed via Secret Manager
- No API keys in GitHub Actions

---

## Limitations

### Gemma GPU Service
The Gemma GPU service is **NOT** included in automatic deployments because:
1. GPU configuration requires post-apply script
2. Terraform doesn't fully support GPU in Cloud Run v2
3. Manual deployment ensures GPU is properly configured

**Workaround:** Use GitHub Actions or manual deployment for Gemma service.

---

## Troubleshooting

### Trigger Not Firing

**Check:**
1. Is repository connected? Go to Cloud Build > Triggers
2. Is trigger enabled? (should show as "Active")
3. Are you pushing to the correct branch? (default: `main`)
4. Check Cloud Build logs for errors

### Build Fails

**Common Issues:**
1. **Dockerfile not found:** Ensure `frontend.Dockerfile.dev` or `backend/Dockerfile.dev` exists
2. **Artifact Registry access:** Verify Cloud Build service account has `artifactregistry.writer` role
3. **Secret access:** Verify Cloud Build service account has `secretmanager.secretAccessor` role
4. **Image push fails:** Check Artifact Registry repository exists and is in correct region

### Deployment Fails

**Common Issues:**
1. **Service doesn't exist:** Run `terraform apply` first to create Cloud Run services
2. **Service account permissions:** Verify Cloud Build has `run.admin` role
3. **Region mismatch:** Ensure trigger uses correct region for service

---

## Verification

### Check Trigger Status

```bash
# List all triggers
gcloud builds triggers list

# Get trigger details
gcloud builds triggers describe agentnav-frontend-deploy
```

### View Build History

```bash
# List recent builds
gcloud builds list --limit=10

# View build logs
gcloud builds log BUILD_ID
```

### Test Deployment

1. Make a small change (e.g., update README)
2. Push to `main` branch
3. Check Cloud Build console for running build
4. Verify Cloud Run service is updated

---

## Integration with GitHub Actions

You can still use GitHub Actions for:
- **Gemma GPU service** deployment
- **Terraform apply** operations
- **Complex multi-step workflows**
- **Testing and validation**

The Cloud Build triggers handle **standard deployments**, while GitHub Actions can handle **special cases**.

---

## Next Steps

1. Connect GitHub repository (see Step 1 above)
2. Run `terraform apply` to create triggers
3. Push to `main` branch and verify automatic deployment
4. Monitor Cloud Build logs for any issues

---

**Ready to enable automatic deployments! 🚀**

