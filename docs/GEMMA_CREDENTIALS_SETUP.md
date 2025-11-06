# Gemma Credentials Setup Guide

**For:** Google Gemma 7B-IT Model on HuggingFace  
**Date:** November 2, 2025  
**Region:** europe-west1 (GPU-enabled)

---

## 📋 Credentials Required

For `google/gemma-7b-it` on HuggingFace, you need **one** credential:

| Credential            | Purpose                               | Required                  | How to Get                                                                |
| --------------------- | ------------------------------------- | ------------------------- | ------------------------------------------------------------------------- |
| **HUGGINGFACE_TOKEN** | Download Gemma model from HuggingFace | ⚠️ **Optional**           | [HuggingFace Tokens Page](https://huggingface.co/settings/tokens)         |
| GEMINI_API_KEY        | For Gemini cloud reasoning            | ✅ **Already Configured** | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |

---

## 🤔 Do You Actually Need the HuggingFace Token?

### ✅ You DON'T Need It If:

- Model is **public** (✓ `google/gemma-7b-it` is public)
- You accept the **HuggingFace Terms** (one-time)
- No special rate limiting concerns

### ⚠️ You SHOULD Get It If:

- You want **higher rate limits** (especially in production)
- You're accessing **private models** (future use case)
- You want **usage tracking** in HuggingFace dashboard
- Deployment in **highly concurrent environments**

---

## 🔧 Quick Setup (Recommended for Production)

Even though optional, having a token is best practice for production. Here's how:

### Step 1: Create HuggingFace Account (if needed)

1. Go to [HuggingFace.co](https://huggingface.co)
2. Click **Sign Up** (or Sign In if you have account)
3. Complete email verification

### Step 2: Accept Gemma Model License

1. Visit [google/gemma-7b-it Model Card](https://huggingface.co/google/gemma-7b-it)
2. Click **"Agree and access repository"**
3. Accept Google's license agreement
4. You now have access!

### Step 3: Create HuggingFace API Token

1. Go to [HuggingFace Tokens Settings](https://huggingface.co/settings/tokens)
2. Click **"New token"**
3. Configure:
   - **Token type:** Read (sufficient for downloading models)
   - **Name:** "agentnav-gemma" (or similar)
   - **Expiration:** 30 days (adjustable)
4. Click **Create Token**
5. **Copy the token** (looks like `hf_xxxxxxxxxxxxxxxxxxxxx`)
6. **Store it safely** (you won't see it again!)

---

## 🌐 Adding Credentials to agentnav Deployment

### Option 1: Local Development (Easiest)

```bash
# Create .env file in backend directory
echo 'HUGGINGFACE_TOKEN=hf_YOUR_TOKEN_HERE' >> backend/.env

# Now run the Gemma service locally
cd backend
python -m gemma_service.main
```

### Option 2: GitHub Secrets (for CI/CD)

For GitHub Actions CI/CD pipeline:

```bash
# 1. Add secret to GitHub
gh secret set HUGGINGFACE_TOKEN --body "hf_YOUR_TOKEN_HERE"

# 2. Verify it's set
gh secret list | grep HUGGINGFACE
```

Then in `.github/workflows/ci.yml`:

```yaml
env:
  HUGGINGFACE_TOKEN: ${{ secrets.HUGGINGFACE_TOKEN }}
```

### Option 3: GCP Secret Manager (for Cloud Run) - **RECOMMENDED**

#### 3a. Create Secret in GCP Console (Easy)

```bash
# Via Google Cloud Console:
# 1. Go to Secret Manager: https://console.cloud.google.com/security/secret-manager
# 2. Click "Create Secret"
# 3. Fill in:
#    - Name: "HUGGINGFACE_TOKEN"
#    - Secret Value: "hf_YOUR_TOKEN_HERE"
# 4. Click Create
```

#### 3b. Create Secret via gcloud CLI (Scriptable)

```bash
# Create the secret
echo -n "hf_YOUR_TOKEN_HERE" | gcloud secrets create HUGGINGFACE_TOKEN --data-file=-

# Verify creation
gcloud secrets describe HUGGINGFACE_TOKEN
```

#### 3c. Grant Cloud Run Service Account Access

```bash
# Grant Gemma service access to the secret
gcloud secrets add-iam-policy-binding HUGGINGFACE_TOKEN \
  --member="serviceAccount:gemma-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Verify permissions
gcloud secrets get-iam-policy HUGGINGFACE_TOKEN
```

#### 3d. Deploy to Cloud Run with Secret

```bash
# Option A: Via gcloud CLI
gcloud run services update gemma-service \
  --region europe-west1 \
  --set-secrets "HUGGINGFACE_TOKEN=HUGGINGFACE_TOKEN:latest"

# Option B: Via Terraform (already configured!)
# The secret is already in terraform/cloud_run.tf:
#
#   env {
#     name = "HUGGINGFACE_TOKEN"
#     value_source {
#       secret_key_ref {
#         secret  = google_secret_manager_secret.huggingface_token.secret_id
#         version = "latest"
#       }
#     }
#   }
#
# Just add the secret value and deploy:
terraform apply
```

---

## 📊 Current Credentials Status in agentnav

### Already Configured ✅

| Secret              | Status         | Location       | Used By                      |
| ------------------- | -------------- | -------------- | ---------------------------- |
| `GEMINI_API_KEY`    | ✅ Configured  | Secret Manager | Backend Agent Reasoning      |
| `HUGGINGFACE_TOKEN` | ⏳ Placeholder | Secret Manager | Gemma GPU Service (optional) |

### Terraform Configuration

All secrets are already **defined** in Terraform:

```hcl
# File: terraform/secret_manager.tf

resource "google_secret_manager_secret" "huggingface_token" {
  secret_id = "HUGGINGFACE_TOKEN"
  project   = var.project_id
  # ... replication config ...
}

resource "google_secret_manager_secret_iam_member" "gemma_huggingface_token" {
  secret_id = google_secret_manager_secret.huggingface_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_gemma.email}"
}
```

### Cloud Run Configuration

Gemma service is already **configured** to use the secret:

```hcl
# File: terraform/cloud_run.tf (gemma service)

env {
  name = "HUGGINGFACE_TOKEN"
  value_source {
    secret_key_ref {
      secret  = google_secret_manager_secret.huggingface_token.secret_id
      version = "latest"
    }
  }
}
```

**What you need to do:** Just add the actual token value to the secret!

---

## 🚀 Complete Deployment Checklist

```bash
# Step 1: Accept Gemma License on HuggingFace
# Visit: https://huggingface.co/google/gemma-7b-it
# Click "Agree and access repository"

# Step 2: Create HuggingFace Token
# Visit: https://huggingface.co/settings/tokens
# Create Read token, copy it

# Step 3: Add Token to GCP Secret Manager
export HF_TOKEN="hf_YOUR_TOKEN_HERE"
export PROJECT_ID="your-gcp-project-id"

# Create secret
echo -n "$HF_TOKEN" | gcloud secrets create HUGGINGFACE_TOKEN --data-file=-

# Step 4: Grant Service Account Access
gcloud secrets add-iam-policy-binding HUGGINGFACE_TOKEN \
  --member="serviceAccount:gemma-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Step 5: Deploy with Terraform
cd terraform
terraform apply

# Step 6: Verify Deployment
GEMMA_URL=$(gcloud run services describe gemma-service \
  --region europe-west1 \
  --format='value(status.url)')

curl ${GEMMA_URL}/healthz
```

---

## 🔒 Security Best Practices

### ✅ DO:

- ✅ Use **Secret Manager** (not environment variables in code)
- ✅ Grant **minimal permissions** (only Gemma service needs HF token access)
- ✅ **Rotate tokens** periodically (HuggingFace > Settings > Tokens)
- ✅ Use **Read tokens** (not Write/Full-access)
- ✅ Enable **token expiration** (30-90 days)
- ✅ Monitor **token usage** in HuggingFace dashboard

### ❌ DON'T:

- ❌ Commit tokens to Git (even in `.env` files!)
- ❌ Use **Write tokens** for deployment (only download needed)
- ❌ Set infinite token expiration
- ❌ Share tokens across teams (create separate tokens)
- ❌ Hardcode secrets in Docker images
- ❌ Log secrets in application output

---

## 🧪 Testing Credentials

### Local Test (Before Deployment)

```bash
# Set token in environment
export HUGGINGFACE_TOKEN="hf_YOUR_TOKEN_HERE"

# Test model download
cd backend
python -c "
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained('google/gemma-7b-it')
print('✅ Token valid! Model downloaded successfully')
"
```

### Cloud Run Test (After Deployment)

```bash
# Get Gemma service URL
GEMMA_URL=$(gcloud run services describe gemma-service \
  --region europe-west1 \
  --format='value(status.url)')

# Test health endpoint
curl -v ${GEMMA_URL}/healthz

# Expected response:
# {
#   "status": "healthy",
#   "model": "google/gemma-7b-it",
#   "device": "cuda",
#   "gpu_available": true,
#   "model_loaded": true
# }
```

---

## 🐛 Troubleshooting

### Error: "Token is invalid"

**Cause:** HuggingFace token not accepted or incorrect format

**Fix:**

```bash
# 1. Verify token format (should start with hf_)
echo $HUGGINGFACE_TOKEN | head -c 10

# 2. Create new token at: https://huggingface.co/settings/tokens
# 3. Accept Gemma license again at: https://huggingface.co/google/gemma-7b-it

# 4. Update secret
echo -n "hf_NEW_TOKEN" | gcloud secrets versions add HUGGINGFACE_TOKEN --data-file=-
```

### Error: "Model not found" or "Unauthorized"

**Cause:** Token lacks access to Gemma model or license not accepted

**Fix:**

```bash
# 1. Go to https://huggingface.co/google/gemma-7b-it
# 2. Ensure you're logged in
# 3. Click "Agree and access repository"
# 4. Create new token

# 5. Test locally
export HUGGINGFACE_TOKEN="hf_NEW_TOKEN"
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('google/gemma-7b-it', 'config.json', token=os.getenv('HUGGINGFACE_TOKEN'))
print('✅ License accepted!')
"
```

### Error: "AccessDenied" from Secret Manager

**Cause:** Service account doesn't have permission to read secret

**Fix:**

```bash
# Verify service account has permission
gcloud secrets get-iam-policy HUGGINGFACE_TOKEN

# Should show:
# - roles/secretmanager.secretAccessor for gemma-service@PROJECT_ID.iam.gserviceaccount.com

# If not, grant it:
gcloud secrets add-iam-policy-binding HUGGINGFACE_TOKEN \
  --member="serviceAccount:gemma-service@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Error: "Model download timeout"

**Cause:** Network issue or slow region

**Fix:**

```bash
# 1. Increase timeout in gemma_service/main.py
# 2. Pre-download model to custom location
# 3. Use quantized version for faster startup

# Check Gemma service logs
gcloud run services logs read gemma-service --region europe-west1 --limit 50
```

---

## 📚 Related Documentation

- [GPU Setup Guide](./GPU_SETUP_GUIDE.md) - Deployment instructions
- [Gemma Integration Guide](./GEMMA_INTEGRATION_GUIDE.md) - API reference
- [Terraform README](../terraform/README.md) - Infrastructure as code
- [HuggingFace Gemma Model Card](https://huggingface.co/google/gemma-7b-it)
- [GCP Secret Manager Docs](https://cloud.google.com/secret-manager/docs)

---

## 💡 Quick Reference

### HuggingFace Token Format

```
hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  │   └─ 37 alphanumeric characters
  └─ Always starts with "hf_"
```

### Environment Variable

```bash
export HUGGINGFACE_TOKEN="hf_YOUR_TOKEN_HERE"
```

### Secret Manager Query

```bash
gcloud secrets versions access latest --secret="HUGGINGFACE_TOKEN"
```

### Verify Gemma Service Has Access

```bash
gcloud run services describe gemma-service \
  --region europe-west1 \
  --format='get(spec.template.spec.containers[0].env[?name==`HUGGINGFACE_TOKEN`])'
```

---

**✅ Setup Complete!** Your Gemma service is now configured to use `google/gemma-7b-it` with proper credential management. 🚀
