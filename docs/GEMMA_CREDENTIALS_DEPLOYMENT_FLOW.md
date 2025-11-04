# Gemma Deployment Credentials Flow

## 📊 Complete Architecture View

```
                        HUGGINGFACE.CO
                              │
                              │ 1. Accept License
                              ↓
                   google/gemma-7b-it Model
                              │
                              │ 2. Create Read Token
                              │    (hf_xxxxxxx)
                              ↓
        ┌─────────────────────────────────────────┐
        │     HUGGINGFACE_TOKEN Secret            │
        │   (your HuggingFace API token)          │
        └─────────────┬───────────────────────────┘
                      │
                      │ 3. Store in GCP
                      ↓
        ┌─────────────────────────────────────────┐
        │   GCP SECRET MANAGER                    │
        │   ├─ HUGGINGFACE_TOKEN                  │
        │   │  (encrypted at rest)                │
        │   ├─ GEMINI_API_KEY ✅                  │
        │   ├─ FIRESTORE_CREDENTIALS              │
        │   └─ ...                                │
        └─────────────┬───────────────────────────┘
                      │
                      │ 4. Grant IAM Access
                      │    (Service Account)
                      ↓
        ┌─────────────────────────────────────────┐
        │   IAM POLICY BINDING                    │
        │   Gemma Service Account:                │
        │   roles/secretmanager.secretAccessor    │
        └─────────────┬───────────────────────────┘
                      │
                      │ 5. Deployed in Cloud Run
                      ↓
        ┌─────────────────────────────────────────────────────┐
        │   CLOUD RUN SERVICE: gemma-service                  │
        │   ├─ Region: europe-west1                           │
        │   ├─ GPU: NVIDIA L4 (1x)                           │
        │   ├─ Memory: 16Gi                                   │
        │   ├─ Container: Gemma 7B Model                      │
        │   └─ Env: HUGGINGFACE_TOKEN (from Secret Manager)  │
        └─────────────┬───────────────────────────────────────┘
                      │
                      │ 6. Startup
                      │    - Download model from HuggingFace
                      │    - Load on GPU
                      │    - Verify with HUGGINGFACE_TOKEN
                      ↓
        ┌─────────────────────────────────────────┐
        │   /healthz Endpoint                     │
        │   ├─ Status: healthy ✅                │
        │   ├─ Model: google/gemma-7b-it         │
        │   ├─ Device: cuda                      │
        │   ├─ GPU Available: true               │
        │   └─ Model Loaded: true                │
        └─────────────┬───────────────────────────┘
                      │
                      │ 7. Ready for Requests
                      ↓
        ┌─────────────────────────────────────────┐
        │   BACKEND SERVICE                       │
        │   (agentnav-backend)                    │
        │                                         │
        │   ├─ Linker Agent                      │
        │   ├─ Orchestrator Agent                │
        │   ├─ Summarizer Agent                  │
        │   └─ reason_with_gemma()               │
        │       └─ CALLS → Gemma Service ✨     │
        └─────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                               │
│                    (via Frontend React App)                       │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────────┐
        │   BACKEND SERVICE (Cloud Run)      │
        │   - Orchestrator Agent             │
        │   - Linker Agent                   │
        │   - Summarizer Agent               │
        └────────┬───────────────────────────┘
                 │
                 │ Check: AGENTNAV_MODEL_TYPE env var
                 │
        ┌────────┴──────────────────────────────────────┐
        │                                               │
        │ gemini ❓                              gemma ❓│
        ↓                                               ↓
    ┌───────────────┐                        ┌──────────────────┐
    │ GEMINI        │                        │ GEMMA SERVICE    │
    │ (Cloud-based) │◄──────────────────────►│ (GPU-based)      │
    │               │    reason_with_gemini()│                  │
    │ Google Cloud  │                        │ Cloud Run        │
    │ GenAI SDK     │                        │ europe-west1     │
    │               │                        │ NVIDIA L4 GPU    │
    └───────────────┘                        └────────┬─────────┘
                                                      │
                                                      │ Uses: HUGGINGFACE_TOKEN
                                                      ↓
                                             ┌─────────────────────┐
                                             │ HuggingFace Hub API │
                                             │                     │
                                             │ google/gemma-7b-it  │
                                             └─────────────────────┘
```

---

## 📝 Credentials Deployment Checklist

### Pre-Deployment

- [ ] Create HuggingFace account (if needed)
- [ ] Accept Gemma 7B-IT license agreement
- [ ] Create HuggingFace Read token
- [ ] Copy token value

### GCP Setup

- [ ] Verify Terraform is up-to-date
- [ ] Create HUGGINGFACE_TOKEN secret in Secret Manager
- [ ] Grant IAM permissions to gemma-service Service Account
- [ ] Verify secret creation: `gcloud secrets describe HUGGINGFACE_TOKEN`
- [ ] Verify IAM binding: `gcloud secrets get-iam-policy HUGGINGFACE_TOKEN`

### Deployment

- [ ] Run `terraform apply` to deploy Gemma service
- [ ] Verify service created: `gcloud run services list --region=europe-west1`
- [ ] Check service URL: `gcloud run services describe gemma-service --region europe-west1`

### Post-Deployment Verification

- [ ] Test health endpoint: `curl https://gemma-service-XXXXX.run.app/healthz`
- [ ] Verify GPU detected: Check response includes `"device": "cuda"`
- [ ] Verify model loaded: Check response includes `"model_loaded": true`
- [ ] Test generation endpoint
- [ ] Verify backend can reach Gemma service

---

## 🔑 Environment Variable Reference

### Local Development

```bash
export HUGGINGFACE_TOKEN=hf_YOUR_TOKEN_HERE
export AGENTNAV_MODEL_TYPE=gemma
export GEMMA_SERVICE_URL=http://localhost:8080
export PORT=8080
```

### Cloud Run (Gemma Service)

```
HUGGINGFACE_TOKEN   → Secret Manager (encrypted)
MODEL_NAME          → google/gemma-7b-it (Dockerfile default)
USE_8BIT_QUANTIZATION → false (optional, for memory)
PORT                → 8080 (set automatically by Cloud Run)
```

### Cloud Run (Backend Service)

```
AGENTNAV_MODEL_TYPE → gemini or gemma (via Terraform variable)
GEMMA_SERVICE_URL   → https://gemma-service-XXXXX.run.app
GEMINI_API_KEY      → Secret Manager (existing)
```

---

## 🐛 Credential Issues Troubleshooting

### Issue: "Token is invalid"

```bash
# Check token format
echo $HUGGINGFACE_TOKEN | head -c 10  # Should show: hf_
```

### Issue: "AccessDenied" from Secret Manager

```bash
# Verify IAM binding
gcloud secrets get-iam-policy HUGGINGFACE_TOKEN

# Should show roles/secretmanager.secretAccessor for gemma-service SA
# If not present, run:
gcloud secrets add-iam-policy-binding HUGGINGFACE_TOKEN \
  --member="serviceAccount:gemma-service@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Issue: "Model not found" on Cloud Run

```bash
# Check Gemma service logs
gcloud run services logs read gemma-service --region europe-west1 --limit 50

# Look for:
# - HF token being read
# - Model download progress
# - GPU initialization
```

### Issue: "Timeout downloading model"

```bash
# Increase memory in terraform/cloud_run.tf
# Change from 16Gi to 32Gi if needed

# Or pre-download model to container:
# Edit backend/Dockerfile.gemma to include model download step
```

---

## ✅ Success Indicators

### Credentials Properly Configured If:

1. ✅ Secret exists in GCP:

   ```bash
   gcloud secrets describe HUGGINGFACE_TOKEN
   # Shows: "Status: ENABLED"
   ```

2. ✅ Service account has permission:

   ```bash
   gcloud secrets get-iam-policy HUGGINGFACE_TOKEN
   # Shows: "roles/secretmanager.secretAccessor" for gemma-service@PROJECT_ID
   ```

3. ✅ Gemma service running:

   ```bash
   gcloud run services describe gemma-service --region europe-west1 | grep -i status
   # Shows: "status: active"
   ```

4. ✅ Service can download model:

   ```bash
   GEMMA_URL=$(gcloud run services describe gemma-service --region europe-west1 --format='value(status.url)')
   curl -v ${GEMMA_URL}/healthz
   # Response shows: "model_loaded": true
   ```

5. ✅ Backend can reach Gemma:
   ```bash
   BACKEND_URL=$(gcloud run services describe agentnav-backend --region europe-west1 --format='value(status.url)')
   curl -X POST ${BACKEND_URL}/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"content": "test", "content_type": "document"}'
   # Should use model_type from AGENTNAV_MODEL_TYPE env var
   ```

---

## 📚 Related Files in agentnav

```
docs/
├── GEMMA_CREDENTIALS_SETUP.md      ← Full setup guide
├── GPU_SETUP_GUIDE.md              ← GPU deployment details
├── GEMMA_INTEGRATION_GUIDE.md      ← API reference
└── SYSTEM_INSTRUCTION.md           ← Architecture overview

backend/
├── gemma_service/
│   ├── main.py                     ← FastAPI app
│   ├── model_loader.py             ← Uses HUGGINGFACE_TOKEN
│   └── Dockerfile                  ← Container definition
└── services/
    └── gemini_client.py            ← SDK wrapper with model routing

terraform/
├── secret_manager.tf               ← Secret definition
├── cloud_run.tf                    ← Service env configuration
├── iam.tf                          ← Permissions setup
└── variables.tf                    ← Model type variable
```

---

**Status: 🟢 Ready for Deployment**

All infrastructure is configured. You only need to:

1. Create HuggingFace token
2. Add it to Secret Manager
3. Run `terraform apply`

🚀 Let's deploy!
