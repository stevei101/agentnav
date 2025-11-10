# GitHub Secrets → GCP Secret Manager Integration

**Question:** Does Terraform support getting a GitHub Secret and syncing it to GCP Secret Manager?

**Answer:** ❌ **No, not directly.** Terraform cannot directly read from GitHub Secrets and sync them to GCP Secret Manager.

However, you have **three options** to handle this:

---

## 🔴 Option 1: Manual Setup (Current Approach - RECOMMENDED)

**What you need to do:**

1. **GitHub Secrets** (you just did this ✅)

   ```
   HUGGINGFACE_TOKEN = hf_xxxxx...
   ```

2. **Manual create in GCP Secret Manager** (next step)
   ```bash
   echo -n "hf_xxxxx..." | gcloud secrets create HUGGINGFACE_TOKEN --data-file=-
   ```

**Pros:**

- ✅ Simple and straightforward
- ✅ Decoupled (GitHub and GCP manage their own secrets)
- ✅ No cross-platform dependencies
- ✅ Industry standard practice

**Cons:**

- ❌ Manual step required
- ❌ Must keep tokens in sync manually

**Current State in agentnav:**

```
Terraform creates the Secret Manager resource
     ↓
You add the value manually with gcloud
     ↓
Terraform doesn't touch the value (safe!)
```

---

## 🟢 Option 2: GitHub Actions Workflow (Recommended for Automation)

**If you want to automate GitHub→GCP sync**, use GitHub Actions:

```yaml
name: Sync GitHub Secrets to GCP

on:
  workflow_dispatch: # Manual trigger
  # Or schedule:
  # schedule:
  #   - cron: '0 0 * * 0'  # Weekly

jobs:
  sync-secrets:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Sync HUGGINGFACE_TOKEN to GCP Secret Manager
        run: |
          echo -n "${{ secrets.HUGGINGFACE_TOKEN }}" | \
            gcloud secrets versions add HUGGINGFACE_TOKEN --data-file=-

      - name: Sync GEMINI_API_KEY to GCP Secret Manager
        run: |
          echo -n "${{ secrets.GEMINI_API_KEY }}" | \
            gcloud secrets versions add GEMINI_API_KEY --data-file=-
```

**Pros:**

- ✅ Automated sync
- ✅ Can run on schedule
- ✅ Uses Workload Identity Federation (secure)
- ✅ No hardcoded credentials

**Cons:**

- ❌ Extra workflow file
- ❌ Additional GitHub Actions run time

---

## 🟡 Option 3: Terraform with Local Execution (Not Recommended)

If you absolutely need Terraform to do it, you'd use `local-exec`:

```hcl
# ⚠️  NOT RECOMMENDED - shown for completeness

# This requires GitHub CLI to be available during terraform apply
resource "google_secret_manager_secret_version" "huggingface_token" {
  secret      = google_secret_manager_secret.huggingface_token.id
  secret_data = var.huggingface_token  # Passed via tfvars or env var

  depends_on = [google_secret_manager_secret.huggingface_token]
}

# Alternative with local-exec (requires gh CLI):
resource "null_resource" "sync_github_secret" {
  provisioner "local-exec" {
    command = <<-EOT
      TOKEN=$(gh secret get HUGGINGFACE_TOKEN)
      echo -n "$TOKEN" | gcloud secrets versions add HUGGINGFACE_TOKEN --data-file=-
    EOT
  }
}
```

**Pros:**

- ✅ Everything in Terraform
- ✅ Infrastructure as code

**Cons:**

- ❌ Requires CLI tools (gh, gcloud) on runner
- ❌ Less secure (processes tokens in shell)
- ❌ Harder to debug
- ❌ Not idempotent
- ❌ GitHub token exposed in local exec

---

## 📊 Comparison Table

| Aspect          | Option 1 (Manual) | Option 2 (GH Actions) | Option 3 (Terraform) |
| --------------- | ----------------- | --------------------- | -------------------- |
| Automation      | ❌ No             | ✅ Yes                | ✅ Yes               |
| Security        | ✅ Best           | ✅ Good               | ⚠️ Medium            |
| Complexity      | ✅ Simple         | ⚠️ Medium             | ❌ Complex           |
| Error Prone     | ⚠️ Manual         | ✅ Automated          | ❌ Shell exec        |
| Industry Std    | ✅ Yes            | ✅ Yes                | ❌ No                |
| **Recommended** | ✅ NOW            | ✅ FOR FUTURE         | ❌ AVOID             |

---

## 🎯 WHAT YOU SHOULD DO RIGHT NOW

### For Your Immediate Deployment (Recommended)

**Use Option 1 (Manual):**

1. You added `HUGGINGFACE_TOKEN` to GitHub Secrets ✅
2. Manually add it to GCP Secret Manager:
   ```bash
   # Assuming you have the token value from GitHub
   echo -n "hf_YOUR_TOKEN_HERE" | gcloud secrets create HUGGINGFACE_TOKEN --data-file=-
   ```
3. Grant IAM permissions:
   ```bash
   gcloud secrets add-iam-policy-binding HUGGINGFACE_TOKEN \
     --member="serviceAccount:gemma-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```
4. Run `terraform apply`

**Time:** < 5 minutes  
**Effort:** Minimal  
**Reliability:** ✅ Guaranteed

---

## 🔮 FOR FUTURE AUTOMATION (Optional)

If you want automatic syncing later, add GitHub Actions workflow (Option 2):

```bash
# Create the workflow file
cat > .github/workflows/sync-secrets-gcp.yml << 'EOF'
name: Sync GitHub Secrets to GCP

on:
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Sync HUGGINGFACE_TOKEN
        run: |
          echo -n "${{ secrets.HUGGINGFACE_TOKEN }}" | \
            gcloud secrets versions add HUGGINGFACE_TOKEN --data-file=-
EOF
```

Then trigger it manually when GitHub secret changes:

```bash
gh workflow run sync-secrets-gcp.yml
```

---

## 📋 Current agentnav Setup

Your Terraform is set up correctly for **manual secret injection**:

```hcl
# terraform/secret_manager.tf
resource "google_secret_manager_secret" "huggingface_token" {
  secret_id = "HUGGINGFACE_TOKEN"
  project   = var.project_id

  replication {
    auto {}
  }

  # Note: Secret values should be added after creation via:
  # echo -n "YOUR_SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-
}
```

This is the **correct approach** because:

- ✅ Terraform creates the infrastructure (secret container)
- ✅ Manual secret injection (keeps credentials out of IaC)
- ✅ Follows Google Cloud best practices
- ✅ Secure and auditable

---

## 🚀 NEXT STEPS

### Now (< 5 minutes)

1. Get your `HUGGINGFACE_TOKEN` from GitHub Secrets
2. Add it to GCP Secret Manager manually
3. Run `terraform apply`

### Later (Optional)

- Set up GitHub Actions workflow for automatic syncing
- Add scheduled sync job for key rotation

---

## 📚 References

- [GCP Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [GitHub Actions with GCP](https://github.com/google-github-actions)
- [Terraform Secret Management](https://developer.hashicorp.com/terraform/cloud-docs/secret-management)

---

## ✅ Bottom Line

**Your current setup is perfect:**

- GitHub Secrets: ✅ Already have `HUGGINGFACE_TOKEN`
- GCP Terraform: ✅ Ready to create Secret Manager resource
- Next: Manually add secret value → `terraform apply` → Deploy! 🚀

No changes needed to Terraform. Just follow the 2-command sequence for GCP and you're done!
