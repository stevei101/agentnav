# Terraform Secret Management Guide

## Overview

Terraform can manage both the secret container AND the secret values using `google_secret_manager_secret_version` resource.

**⚠️ IMPORTANT SECURITY WARNING:**
- Secret values stored in Terraform state are visible to anyone with state file access
- For production, prefer using gcloud CLI or GitHub Actions workflow
- If using Terraform, ensure state is stored securely and access is restricted

## Setup

### Step 1: Enable Secret Version Resources

The resources are commented out in `secret_manager.tf`. To enable:

1. Uncomment the `google_secret_manager_secret_version` resources in `terraform/secret_manager.tf`
2. The variables are already defined in `terraform/variables.tf`

### Step 2: Create terraform.tfvars (Local Only)

Create `terraform/terraform.tfvars` (already in .gitignore):

```hcl
# Secret values - NEVER COMMIT THIS FILE!
gemini_api_key    = "your-gemini-api-key-here"
huggingface_token = "your-huggingface-token-here"
```

### Step 3: Apply

```bash
cd terraform
terraform apply
```

## Current Setup (Recommended - Secure)

The current configuration:
- ✅ Creates secret containers via Terraform
- ✅ Sets up IAM permissions via Terraform
- ❌ Secret values added manually via gcloud CLI or GitHub Actions

This is the **recommended approach** because:
- Secrets never stored in Terraform state
- Can use GitHub Secrets as source of truth
- Automated sync via GitHub Actions workflow

## Using Terraform for Secret Values

If you want to use Terraform for secret values:

### Option 1: terraform.tfvars (Local)

```bash
# Create terraform/terraform.tfvars
cat > terraform/terraform.tfvars <<EOF
gemini_api_key    = "YOUR_KEY_HERE"
huggingface_token = "YOUR_TOKEN_HERE"
EOF

# Apply
terraform apply
```

### Option 2: Environment Variables

```bash
export TF_VAR_gemini_api_key="your-key"
export TF_VAR_huggingface_token="your-token"
terraform apply
```

### Option 3: Command Line

```bash
terraform apply \
  -var="gemini_api_key=your-key" \
  -var="huggingface_token=your-token"
```

## Security Best Practices

1. **Never commit `terraform.tfvars`** - Ensure it's in `.gitignore`
2. **Use remote state** - Store Terraform state in GCS with encryption
3. **Restrict state access** - Limit who can read Terraform state
4. **Use sensitive = true** - Already set in variable definitions
5. **Rotate secrets** - Update values regularly

## Comparison

| Method | Security | Automation | Complexity |
|--------|---------|-----------|------------|
| **Terraform** | ⚠️ Medium (state exposure) | ✅ High | Low |
| **gcloud CLI** | ✅ High | ⚠️ Medium | Low |
| **GitHub Actions** | ✅ High | ✅ High | Medium |

## Recommendation

For your use case:
1. Keep secret creation in Terraform (current setup)
2. Use GitHub Actions workflow to sync values
3. Store secrets only in GitHub Secrets (source of truth)

This gives you:
- Infrastructure as Code for secret containers
- Secure value management via GitHub Actions
- No secrets in Terraform state
- Automated sync on secret updates

## Quick Reference

```bash
# Check current secret status
cd terraform
terraform state list | grep secret

# View secret (not the value)
terraform state show google_secret_manager_secret.gemini_api_key

# Add secret value via gcloud (current method)
echo -n "value" | gcloud secrets versions add GEMINI_API_KEY --data-file=-

# Add secret value via Terraform (if enabled)
terraform apply -var="gemini_api_key=value"
```

