# Secret Sync Guide: GitHub Secrets → GCP Secret Manager

This guide explains how to sync secrets from GitHub Secrets to Google Cloud Secret Manager.

## Overview

Terraform creates the Secret Manager secrets and IAM permissions, but **does not automatically sync values** from GitHub Secrets. This workflow provides automated and manual methods to sync secrets.

## Prerequisites

1. **GitHub Secrets configured:**
   - `HUGGINGFACE_TOKEN` - Added to GitHub repository secrets
   - `GEMINI_API_KEY` - Added to GitHub repository secrets (optional)
   - `GCP_PROJECT_ID` - Your GCP project ID
   - `WIF_PROVIDER` - Workload Identity Federation provider name
   - `WIF_SERVICE_ACCOUNT` - Service account email for WIF

2. **Terraform applied:**
   - Secret Manager secrets created via `terraform apply`
   - Workload Identity Federation configured

## Method 1: GitHub Actions Workflow (Recommended)

### Step 1: Access the Workflow

1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Find **"Sync Secrets from GitHub to GCP Secret Manager"** workflow

### Step 2: Trigger the Workflow

**Option A: Manual Trigger (One-time sync)**

1. Click on the workflow name
2. Click **"Run workflow"** button (top right)
3. Select the secret to sync:
   - `HUGGINGFACE_TOKEN` - Sync only this secret
   - `GEMINI_API_KEY` - Sync only this secret
   - `all` - Sync all configured secrets
4. Click **"Run workflow"**

**Option B: Automatic Trigger (On Push)**

The workflow automatically runs when:
- Changes are pushed to `main` branch
- The workflow file itself is modified

**Option C: Repository Dispatch (API Trigger)**

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/stevei101/agentnav/dispatches \
  -d '{"event_type":"sync-secrets"}'
```

### Step 3: Monitor Execution

1. Click on the running workflow
2. View logs in real-time
3. Look for success messages:
   - `✅ HUGGINGFACE_TOKEN synced successfully`
   - `✅ GEMINI_API_KEY synced successfully`

### Step 4: Verify in GCP

```bash
# Check secret exists
gcloud secrets describe HUGGINGFACE_TOKEN \
  --project=YOUR_PROJECT_ID

# Check latest version
gcloud secrets versions list HUGGINGFACE_TOKEN \
  --project=YOUR_PROJECT_ID

# View secret value (requires proper IAM permissions)
gcloud secrets versions access latest \
  --secret=HUGGINGFACE_TOKEN \
  --project=YOUR_PROJECT_ID
```

## Method 2: Manual Script (Local)

### Quick Sync

```bash
# Set your project ID
export GCP_PROJECT_ID=your-project-id

# Sync HUGGINGFACE_TOKEN (copy value from GitHub Secrets first)
./scripts/sync-github-secret-to-gcp.sh HUGGINGFACE_TOKEN "your-token-value"

# Sync GEMINI_API_KEY
./scripts/sync-github-secret-to-gcp.sh GEMINI_API_KEY "your-api-key"
```

### Using gcloud Directly

```bash
# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Create secret if it doesn't exist (usually created by Terraform)
gcloud secrets create HUGGINGFACE_TOKEN \
  --replication-policy="automatic"

# Add secret version
echo -n "your-token-value" | gcloud secrets versions add HUGGINGFACE_TOKEN \
  --data-file=-
```

## Method 3: Using Cloud Build Secret Sync

If you're triggering Cloud Build, you can pass secrets directly:

```bash
gcloud builds submit \
  --config=cloudbuild-gemma.yaml \
  --substitutions=... \
  --secret=HUGGINGFACE_TOKEN:HUGGINGFACE_TOKEN:latest
```

## Verification

### 1. Check Secret Exists

```bash
gcloud secrets list --project=YOUR_PROJECT_ID | grep HUGGINGFACE_TOKEN
```

### 2. Check Secret Versions

```bash
gcloud secrets versions list HUGGINGFACE_TOKEN \
  --project=YOUR_PROJECT_ID
```

### 3. Verify Cloud Run Can Access

```bash
# Check IAM permissions
gcloud secrets get-iam-policy HUGGINGFACE_TOKEN \
  --project=YOUR_PROJECT_ID

# Should see your Cloud Run service account listed with:
# roles/secretmanager.secretAccessor
```

### 4. Test from Cloud Run Service

```bash
# If your Gemma service is deployed, check logs
gcloud run services logs read gemma-service \
  --region europe-west1 \
  --limit 50

# Look for errors about missing HUGGINGFACE_TOKEN
```

## Troubleshooting

### Error: Secret not found in GitHub Secrets

**Solution:** Ensure the secret is added to GitHub repository secrets:
1. Go to repository → Settings → Secrets and variables → Actions
2. Add repository secret with exact name: `HUGGINGFACE_TOKEN`

### Error: Permission denied in GCP

**Solution:** Ensure Workload Identity Federation is configured:
1. Verify `WIF_PROVIDER` and `WIF_SERVICE_ACCOUNT` are set in GitHub Secrets
2. Check IAM bindings in GCP Console

### Error: Secret already exists in Secret Manager

**Solution:** This is normal. The workflow will add a new version:
```bash
# Check all versions
gcloud secrets versions list HUGGINGFACE_TOKEN
```

### Error: Workflow authentication failed

**Solution:** Verify WIF setup:
```bash
# Check WIF provider exists
gcloud iam workload-identity-pools providers describe \
  --workload-identity-pool=github-actions-pool \
  --location=global \
  github-provider

# Check service account exists
gcloud iam service-accounts describe \
  wif-github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Security Best Practices

1. **Never commit secrets to code** - Always use GitHub Secrets
2. **Use Workload Identity Federation** - No static credentials
3. **Rotate secrets regularly** - Update GitHub Secrets and re-sync
4. **Limit access** - Only grant `secretmanager.secretAccessor` to necessary services
5. **Audit secret access** - Monitor who/what accesses secrets

## Automated Sync Options

### Trigger on Secret Update

Currently, GitHub doesn't provide webhooks for secret changes. Options:

1. **Manual trigger** when you update GitHub Secrets
2. **Scheduled sync** (add to workflow):
   ```yaml
   on:
     schedule:
       - cron: '0 0 * * *'  # Daily at midnight
   ```
3. **Repository dispatch** from external automation

## Related Documentation

- [Terraform Secret Manager Setup](../terraform/README.md#secret-values)
- [Workload Identity Federation Setup](./WIF_GITHUB_SECRETS_SETUP.md)
- [GCP Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)

## Quick Reference

```bash
# Sync one secret via script
./scripts/sync-github-secret-to-gcp.sh SECRET_NAME "secret-value"

# Check secret in GCP
gcloud secrets describe SECRET_NAME --project=PROJECT_ID

# List all secrets
gcloud secrets list --project=PROJECT_ID

# View secret value (requires permissions)
gcloud secrets versions access latest --secret=SECRET_NAME --project=PROJECT_ID
```

