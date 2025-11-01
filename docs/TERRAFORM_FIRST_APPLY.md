# Terraform First Apply Setup Guide

## 🐔 Chicken-and-Egg Problem

**The Issue:**
- GitHub Actions needs WIF (Workload Identity Federation) to authenticate
- WIF resources need Terraform to create them
- Terraform workflow needs GitHub Actions to run
- **Circular dependency!** ❌

**Current State:**
- ✅ GitHub Secrets configured correctly
- ✅ Terraform config validated
- ❌ WIF resources don't exist in GCP yet
- ❌ Can't run GitHub Actions workflow to create them

## 🔧 Solution: Manual First Apply

You have **three options** to bootstrap the infrastructure:

---

## Option 1: Terraform Cloud UI (Recommended - Easiest)

### Prerequisites
1. Set `project_id` variable in Terraform Cloud workspace

### Steps
1. **Go to workspace:** https://app.terraform.io/app/disposable-org/workspaces/agentnav
2. Click **"Run workflow"** button (top right)
3. Select **"Plan and apply"**
4. Add any plan message (optional)
5. Click **"Start run"**
6. Wait for plan to complete
7. Review the plan
8. Click **"Confirm & Apply"** or **"Apply"**
9. Wait for apply to complete (~5-10 minutes)

**Result:** All WIF resources created, GitHub Actions can now authenticate!

---

## Option 2: Manual Local Terraform Apply

### Prerequisites
1. Have `gcloud` authenticated locally
2. Have Terraform Cloud credentials

### Steps
```bash
cd terraform

# Login to Terraform Cloud
terraform login

# Initialize with remote backend
terraform init \
  -backend-config="organization=disposable-org" \
  -backend-config="workspaces.name=agentnav"

# Set the required variable
export TF_VAR_project_id=linear-archway-476722-v0

# Or use terraform.tfvars
cat > terraform.tfvars << EOF
project_id = "linear-archway-476722-v0"
EOF

# Plan first
terraform plan

# If plan looks good, apply
terraform apply

# Confirm with 'yes' when prompted
```

**Result:** All WIF resources created in GCP.

---

## Option 3: Temporary Service Account Key (Fallback)

**⚠️ NOT RECOMMENDED** - Use only if Options 1 & 2 don't work.

### Steps
1. Create a temporary service account with necessary permissions
2. Download JSON key
3. Add to GitHub secret: `GCP_SA_KEY`
4. Update workflow to use SA key for initial run
5. Remove SA key after WIF is created
6. Revert workflow to WIF

This violates security best practices, use as last resort only.

---

## ✅ After First Apply

Once WIF resources are created:

1. **Verify WIF exists in GCP:**
   ```bash
   gcloud iam workload-identity-pools list --location=global
   gcloud iam workload-identity-pools providers list \
     --workload-identity-pool=github-actions-pool \
     --location=global
   ```

2. **Verify service account exists:**
   ```bash
   gcloud iam service-accounts list | grep github-actions
   ```

3. **Push to main to trigger GitHub Actions:**
   ```bash
   git push origin main
   ```

4. **GitHub Actions workflow should now succeed!**

---

## 📊 Expected Resources Created

After apply, you should have:

- ✅ `google_iam_workload_identity_pool.github_actions`
- ✅ `google_iam_workload_identity_pool_provider.github_actions`
- ✅ `google_service_account.github_actions`
- ✅ `google_service_account_iam_member.github_actions_workload_identity`
- ✅ All Cloud Run service accounts
- ✅ Artifact Registry
- ✅ Firestore database
- ✅ Secret Manager secrets (placeholders)
- ✅ Cloud Build triggers (if enabled)

---

## 🔗 Quick Links

- **Terraform Cloud Workspace:** https://app.terraform.io/app/disposable-org/workspaces/agentnav
- **Terraform Cloud Variables:** https://app.terraform.io/app/disposable-org/workspaces/agentnav/settings/variables
- **Terraform Cloud Runs:** https://app.terraform.io/app/disposable-org/workspaces/agentnav/runs
- **WIF Setup Guide:** [docs/WIF_GITHUB_SECRETS_SETUP.md](docs/WIF_GITHUB_SECRETS_SETUP.md)

---

## 🆘 Troubleshooting

### "invalid_target" error persists after apply
- Check Terraform Cloud workspace outputs for correct `wif_provider` value
- Verify GitHub secret matches exactly
- Wait 1-2 minutes for IAM propagation

### Terraform Cloud shows "waiting for configuration"
- Add `project_id` variable in workspace settings
- Check variable name is exactly `project_id` (not `TF_VAR_project_id`)

### Local apply fails with backend errors
- Make sure you're authenticated: `terraform login`
- Check backend config matches Terraform Cloud workspace

---

**Most likely next step:** Use **Option 1** (Terraform Cloud UI) - it's the simplest!

