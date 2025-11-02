# Terraform Cloud Setup Guide

## 📋 Required Variables

Based on [terraform/variables.tf](terraform/variables.tf), only **ONE** variable is truly required:

### Required Variable (No Default)

| Variable     | Type     | Description             | Value                      |
| ------------ | -------- | ----------------------- | -------------------------- |
| `project_id` | `string` | Google Cloud Project ID | `linear-archway-476722-v0` |

### Optional Variables (Have Defaults - Can Override)

All other variables have sensible defaults and can be left as-is or customized:

**Region Configuration:**

- `default_region`: `"us-central1"`
- `frontend_region`: `"us-central1"`
- `backend_region`: `"europe-west1"`
- `gemma_region`: `"europe-west1"`

**Repository Configuration:**

- `github_repository`: `"stevei101/agentnav"`
- `github_branch`: `"main"`
- `enable_connect_repo`: `true`

**Identity & Security:**

- `workload_identity_pool_id`: `"github-actions-pool"`
- `workload_identity_provider_id`: `"github-provider"`

**Services Configuration:**

- `artifact_registry_location`: `"europe-west1"`
- `artifact_registry_repository_id`: `"agentnav-containers"`
- `firestore_database_id`: `"agentnav-db"`

**Container Ports (NEW - Just Added):**

- `frontend_container_port`: `80`
- `backend_container_port`: `8080`
- `gemma_container_port`: `8080`

**Other:**

- `environment`: `"prod"`
- `domain_name`: `""` (empty - optional)

---

## 🔧 How to Set Variables in Terraform Cloud

### Method 1: Web UI (Recommended)

1. Go to: https://app.terraform.io/app/disposable-org/workspaces/agentnav
2. Click **"Variables"** in the left sidebar
3. Click **"Add variable"**
4. Fill in:
   - **Key:** `project_id`
   - **Value:** `linear-archway-476722-v0`
   - **Type:** `string`
   - **Description:** `Google Cloud Project ID`
   - ✅ Check **"HCL"** if you want to use HCL syntax (not needed for strings)
   - ✅ Check **"Sensitive"** if you want to hide the value
5. Click **"Save variable"**
6. (Optional) Add any overrides for default values

### Method 2: CLI (Advanced)

```bash
# Login to Terraform Cloud
terraform login

# Set workspace variables
terraform cloud workspace select agentnav

# Set the required variable
cat > terraform.tfvars << EOF
project_id = "linear-archway-476722-v0"
EOF

# The terraform.tfvars can be used locally, but for Cloud:
# You need to use the UI or API to set workspace variables
```

### Method 3: Environment Variables

In Terraform Cloud UI → Variables → Add variable:

- **Key:** `TF_VAR_project_id` (or use HCL mode and add as regular `project_id`)
- **Value:** `linear-archway-476722-v0`

---

## ✅ Verification

After setting the variable:

1. Go to workspace: https://app.terraform.io/app/disposable-org/workspaces/agentnav
2. Status should change from **"waiting for configuration"** to **"ready to queue"**
3. You should see the workspace is ready to run

---

## 🔗 Important URLs

- **Workspace:** https://app.terraform.io/app/disposable-org/workspaces/agentnav
- **Variables:** https://app.terraform.io/app/disposable-org/workspaces/agentnav/settings/variables
- **Runs:** https://app.terraform.io/app/disposable-org/workspaces/agentnav/runs

---

## 📝 Summary

**Minimum Required Setup:**

```hcl
project_id = "linear-archway-476722-v0"
```

That's it! All other variables have sensible defaults.

**Recommended Setup (for clarity):**

```hcl
project_id = "linear-archway-476722-v0"
github_repository = "stevei101/agentnav"
environment = "prod"
```

All other defaults are fine for standard deployment.
