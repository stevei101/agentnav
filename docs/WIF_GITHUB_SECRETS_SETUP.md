# Workload Identity Federation (WIF) - GitHub Secrets Setup Guide

## 🔐 Required GitHub Secrets

After running `terraform apply`, you need to set up the following GitHub Secrets for the CI/CD pipeline:

1. `WIF_PROVIDER` - Full resource name of Workload Identity Provider
2. `WIF_SERVICE_ACCOUNT` - Service account email

## 📋 How to Get the Values

### Option 1: From Terraform Outputs (Recommended)

After applying Terraform:

```bash
cd terraform
terraform output wif_provider
terraform output wif_service_account_email
```

### Option 2: From Terraform Cloud

1. Go to your Terraform Cloud workspace
2. Navigate to "Outputs" tab
3. Copy the values for:
   - `wif_provider`
   - `wif_service_account_email`

### Option 3: Manual Construction

If you know your configuration values, construct manually:

**WIF_PROVIDER** (Full Resource Name):
```
projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
```

Where:
- `PROJECT_NUMBER` = Your GCP project number (found in console or via `gcloud projects describe PROJECT_ID`)
- `POOL_ID` = `github-actions-pool` (default) or value in `terraform/variables.tf`
- `PROVIDER_ID` = `github-provider` (default) or value in `terraform/variables.tf`

**WIF_SERVICE_ACCOUNT**:
```
github-actions@PROJECT_ID.iam.gserviceaccount.com
```

Where `PROJECT_ID` is your GCP project ID.

## 🚨 Common Error: Invalid Audience

If you see this error in GitHub Actions:

```
Error: failed to generate Google Cloud federated token for //iam.googleapis.com/***: 
{"error":"invalid_request","error_description":"Invalid value for \"audience\"..."}
```

This means `WIF_PROVIDER` is incorrectly formatted. 

### ✅ Correct Format

```yaml
# Example (with project number 123456789012)
WIF_PROVIDER: "projects/123456789012/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider"
```

### ❌ Wrong Formats

```yaml
# Missing "projects/" prefix
WIF_PROVIDER: "123456789012/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider"

# Using project ID instead of project NUMBER
WIF_PROVIDER: "projects/agentnav-dev/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider"

# Using just the provider ID
WIF_PROVIDER: "github-provider"

# Missing /providers/ segment
WIF_PROVIDER: "projects/123456789012/locations/global/workloadIdentityPools/github-actions-pool"
```

## 🔧 How to Get Your Project Number

```bash
# Method 1: Using gcloud
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"

# Method 2: From Terraform
cd terraform
terraform output project_number

# Method 3: From Terraform Cloud
# Look in the "Outputs" tab of your workspace
```

## 📝 How to Set GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add each secret:

   **Secret 1:**
   - Name: `WIF_PROVIDER`
   - Value: (full resource name from terraform output)

   **Secret 2:**
   - Name: `WIF_SERVICE_ACCOUNT`
   - Value: (service account email from terraform output)

5. Click **"Add secret"**

## ✅ Verification

After setting secrets, trigger the GitHub Actions workflow:

```bash
# Push a change to terraform/ directory
cd terraform
echo "# test" >> README.md
git commit -am "test WIF authentication"
git push origin main
```

Check the workflow logs - the "Authenticate to Google Cloud" step should pass without errors.

## 🔍 Troubleshooting

### Still Getting Errors?

1. **Verify the pool and provider exist:**
   ```bash
   gcloud iam workload-identity-pools list
   gcloud iam workload-identity-pools providers list \
     --workload-identity-pool=github-actions-pool \
     --location=global
   ```

2. **Check the provider name:**
   ```bash
   gcloud iam workload-identity-pools providers describe github-provider \
     --workload-identity-pool=github-actions-pool \
     --location=global \
     --format="value(name)"
   ```

3. **Verify the service account binding:**
   ```bash
   gcloud iam service-accounts get-iam-policy github-actions@PROJECT_ID.iam.gserviceaccount.com
   ```
   
   Should show:
   ```
   members:
   - principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/stevei101/agentnav
   ```

## 📚 Related Documentation

- [Google Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)
- [GitHub Actions: Authenticating to Google Cloud](https://github.com/google-github-actions/auth)
- [Terraform: google_iam_workload_identity_pool_provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/iam_workload_identity_pool_provider)

## 🔗 Quick Reference

| Secret Name | Expected Format | Example |
|------------|-----------------|---------|
| `WIF_PROVIDER` | `projects/{projectNumber}/locations/global/workloadIdentityPools/{poolId}/providers/{providerId}` | `projects/123456789012/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider` |
| `WIF_SERVICE_ACCOUNT` | `{saId}@{projectId}.iam.gserviceaccount.com` | `github-actions@agentnav-dev.iam.gserviceaccount.com` |

**Remember:** `WIF_PROVIDER` uses **project NUMBER**, not project ID!
