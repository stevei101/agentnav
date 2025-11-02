# GitHub Actions WIF Authentication Error - Analysis & Solution

## 🔍 Error Message

```
Error: google-github-actions/auth failed with: failed to generate Google Cloud federated token for //iam.googleapis.com/***:
{"error":"invalid_request","error_description":"Invalid value for \"audience\". This value should be the full resource name of the Identity Provider."}
```

## ✅ Root Cause Analysis

The Terraform configuration is **CORRECT**. The error indicates that the GitHub secret `WIF_PROVIDER` is incorrectly formatted.

**Current Terraform Setup:**

```terraform
# terraform/outputs.tf - This is correct ✅
output "wif_provider" {
  value = google_iam_workload_identity_pool_provider.github_actions.name
}

# terraform/iam.tf - Configuration is correct ✅
resource "google_iam_workload_identity_pool_provider" "github_actions" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_actions.workload_identity_pool_id
  workload_identity_pool_provider_id = var.workload_identity_provider_id
  # ...
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}
```

The `.name` attribute returns the **full resource name** in the correct format:

```
projects/{projectNumber}/locations/global/workloadIdentityPools/{poolId}/providers/{providerId}
```

## 🎯 Solution

### Step 1: Get the Correct Value

Since Terraform state is in Terraform Cloud, get the value from there:

**Option A: From Terraform Cloud UI**

1. Go to your Terraform Cloud workspace
2. Navigate to **"Outputs"** tab
3. Copy the value for `wif_provider`

**Option B: From Terraform Cloud CLI**

```bash
terraform cloud output wif_provider
```

**Option C: From GCP Console**

```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --workload-identity-pool=github-actions-pool \
  --location=global \
  --format="value(name)"
```

### Step 2: Set GitHub Secret

1. Go to: **Settings** → **Secrets and variables** → **Actions**
2. Edit or create secret: `WIF_PROVIDER`
3. Paste the **exact** value from Step 1
4. Save

### Step 3: Verify Format

The value should look like:

```
projects/123456789012/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
```

**Critical points:**

- ✅ Starts with `projects/`
- ✅ Uses **project NUMBER** (not project ID like `agentnav-dev`)
- ✅ Includes `/providers/` segment
- ✅ No trailing slashes

## ❌ Common Mistakes

### Wrong Format 1: Missing segments

```
❌ projects/123456789012/.../workloadIdentityPools/github-actions-pool
```

Missing `/providers/github-provider`

### Wrong Format 2: Using project ID instead of number

```
❌ projects/agentnav-dev/locations/global/...
```

Should use project number: `projects/123456789012/locations/global/...`

### Wrong Format 3: Just the provider ID

```
❌ github-provider
```

Needs the full resource name

### Wrong Format 4: Using gcloud resource path

```
❌ //iam.googleapis.com/projects/.../providers/github-provider
```

The `//iam.googleapis.com` prefix is not needed for `workload_identity_provider`

## 🔍 Verification Steps

After setting the correct secret:

1. **Trigger workflow:**

   ```bash
   # Make any change to terraform/ directory
   git commit --allow-empty -m "test WIF auth"
   git push origin main
   ```

2. **Check workflow logs:**
   - Go to **Actions** tab in GitHub
   - Find the "Authenticate to Google Cloud" step
   - Should pass without errors

3. **Verify in workflow:**
   ```yaml
   # .github/workflows/terraform.yml
   - name: Authenticate to Google Cloud
     uses: google-github-actions/auth@v2
     with:
       workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
       service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}
       project_id: ${{ env.GCP_PROJECT_ID }}
   ```

## 📋 Quick Checklist

- [ ] WIF_PROVIDER uses full resource name format
- [ ] WIF_PROVIDER uses project NUMBER (not ID)
- [ ] WIF_PROVIDER includes `/providers/{providerId}` segment
- [ ] WIF_SERVICE_ACCOUNT is correct email format
- [ ] Both secrets are set in GitHub repository settings
- [ ] Terraform apply has completed successfully
- [ ] Workload Identity Pool and Provider exist in GCP

## 🔗 Related Resources

- [Setup Guide](docs/WIF_GITHUB_SECRETS_SETUP.md)
- [Terraform Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/iam_workload_identity_pool_provider)
- [Google Auth Action Docs](https://github.com/google-github-actions/auth#workload-identity-federation)

## 💡 Key Insight

**The Terraform configuration is correct. The issue is with the GitHub secret value.**

The secret `WIF_PROVIDER` must exactly match the output of:

```bash
terraform output wif_provider
```

Any manual construction or copy-paste errors will cause this authentication failure.
