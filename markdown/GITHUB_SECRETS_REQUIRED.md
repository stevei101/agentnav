# GitHub Secrets Required for Feature #007 (Terraform IaC)

## Complete List of Required Secrets

Based on `docs/SYSTEM_INSTRUCTION.md`, here are **all GitHub secrets** needed for the infrastructure:

### 🔑 Core Google Cloud Configuration

1. **`GCP_PROJECT_ID`**
   - **Description:** Your Google Cloud Project ID
   - **Example:** `agentic-navigator-123456`
   - **How to get:** `gcloud config get-value project`
   - **Required for:** All GCP operations

2. **`GCP_SA_KEY`** *(Legacy/Fallback - Optional if using WIF)*
   - **Description:** Google Cloud Service Account Key (JSON format)
   - **Purpose:** Legacy authentication method (Workload Identity Federation is preferred)
   - **When to use:** Fallback if WIF setup fails
   - **How to create:** 
     ```bash
     gcloud iam service-accounts keys create sa-key.json \
       --iam-account=SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com
     ```
   - **Note:** Store entire JSON content as secret

### 🤖 AI/ML Services

3. **`GEMINI_API_KEY`**
   - **Description:** API key for Google Gemini models
   - **Format:** `AIza...` (starts with AIza)
   - **Where to get:** [Google AI Studio](https://aistudio.google.com/apikey)
   - **Required for:** Backend agent orchestration

### 🔐 Terraform Cloud Configuration

4. **`TF_API_TOKEN`**
   - **Description:** API token for Terraform Cloud
   - **Where to get:** Terraform Cloud → User Settings → Tokens → Create API Token
   - **Required for:** Remote state management and CI/CD automation

5. **`TF_CLOUD_ORGANIZATION`**
   - **Description:** Your Terraform Cloud organization name
   - **Example:** `your-org-name`
   - **Where to find:** Terraform Cloud dashboard URL: `https://app.terraform.io/app/[ORG_NAME]`
   - **Required for:** Workspace configuration

6. **`TF_WORKSPACE`**
   - **Description:** Workspace name in Terraform Cloud
   - **Example:** `agentnav-production` or `agentnav-dev`
   - **Where to create:** Terraform Cloud → Organizations → Workspaces
   - **Required for:** State management

### 🔒 Workload Identity Federation (WIF) - Set After Terraform

**⚠️ IMPORTANT:** These will be **output from Terraform** after Feature #007 is deployed. You'll need to set them after the first `terraform apply`.

7. **`WIF_PROVIDER`**
   - **Description:** Workload Identity Federation Provider name
   - **Example:** `projects/123456789/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`
   - **How to get:** Terraform output after applying infrastructure
   - **Required for:** Secure GitHub Actions → GCP authentication

8. **`WIF_SERVICE_ACCOUNT`**
   - **Description:** Service account email used by WIF
   - **Example:** `github-actions@agentic-navigator-123456.iam.gserviceaccount.com`
   - **How to get:** Terraform output after applying infrastructure
   - **Required for:** GitHub Actions deployment permissions

### 📦 Additional Secrets (Optional/Dependent)

9. **`FIRESTORE_CREDENTIALS`** *(Optional if using WIF)*
   - **Description:** Service account JSON for Firestore access
   - **When needed:** Only if not using WIF for Firestore access
   - **Note:** WIF is preferred method

10. **`HUGGINGFACE_TOKEN`** *(Optional)*
    - **Description:** Hugging Face API token (for private Gemma model access)
    - **Required for:** Only if using private Gemma models
    - **Where to get:** [Hugging Face Settings](https://huggingface.co/settings/tokens)

---

## 🚀 Setup Order

### Phase 1: Before Terraform (Set These First)
1. ✅ `GCP_PROJECT_ID` - Must have a GCP project
2. ✅ `TF_API_TOKEN` - Need Terraform Cloud account
3. ✅ `TF_CLOUD_ORGANIZATION` - Create organization in Terraform Cloud
4. ✅ `TF_WORKSPACE` - Create workspace in Terraform Cloud
5. ✅ `GEMINI_API_KEY` - Get from AI Studio
6. ✅ `GCP_SA_KEY` *(Optional)* - Only if not using WIF

### Phase 2: After Terraform Apply (Outputs)
7. ⏳ `WIF_PROVIDER` - From Terraform output
8. ⏳ `WIF_SERVICE_ACCOUNT` - From Terraform output

### Phase 3: Optional/As Needed
9. ⏳ `FIRESTORE_CREDENTIALS` - Only if not using WIF
10. ⏳ `HUGGINGFACE_TOKEN` - Only if using private models

---

## 📋 Quick Setup Checklist

- [ ] Create/verify GCP project and get `GCP_PROJECT_ID`
- [ ] Create Terraform Cloud account and organization
- [ ] Generate `TF_API_TOKEN` in Terraform Cloud
- [ ] Create `TF_WORKSPACE` in Terraform Cloud
- [ ] Get `GEMINI_API_KEY` from Google AI Studio
- [ ] *(Optional)* Create service account and get `GCP_SA_KEY` JSON
- [ ] Run `terraform apply` for Feature #007
- [ ] Copy `WIF_PROVIDER` and `WIF_SERVICE_ACCOUNT` from Terraform outputs
- [ ] Add all secrets to GitHub Repository Settings → Secrets and variables → Actions

---

## 🔗 How to Add Secrets to GitHub

1. Go to: `https://github.com/stevei101/agentnav/settings/secrets/actions`
2. Click **"New repository secret"**
3. Add each secret name and value
4. Click **"Add secret"**

---

## ✅ Verification

After setting secrets, verify they're accessible in GitHub Actions workflow:
```yaml
env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  TF_TOKEN: ${{ secrets.TF_API_TOKEN }}
  # etc.
```

---

**Next Step:** Once you've set the Phase 1 secrets, I'll proceed with implementing the Terraform infrastructure code!

