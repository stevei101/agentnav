# GPU Setup Guide for Gemma Service

This guide covers deploying the Gemma GPU service on Cloud Run with NVIDIA L4 GPU acceleration.

## Prerequisites

1. **GCP Project** with billing enabled
2. **GPU Quota** in `europe-west1` region
   - Request NVIDIA L4 GPU quota via Cloud Console if needed
   - Default quota is often 0 GPUs, requires approval
3. **Google Artifact Registry (GAR)** repository for container images
4. **gcloud CLI** installed and authenticated
5. **Podman** installed for building containers

## GPU Quota Request

1. Go to [GCP Console > IAM & Admin > Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter by:
   - **Service:** Cloud Run API
   - **Location:** europe-west1
   - **Metric:** NVIDIA L4 GPUs
3. Click "Edit Quotas" and request 1-2 GPUs
4. Wait for approval (usually 1-2 business days)

## Quick Deployment

### Option 1: Using Deployment Script

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project-id
export GAR_REPO=docker-repo
export IMAGE_TAG=latest

# Run deployment script
./scripts/deploy-gemma.sh
```

### Option 2: Manual Deployment

#### Step 1: Build Container Image

```bash
cd backend
podman build -f Dockerfile.gemma -t gemma-service:latest .
```

#### Step 2: Tag for Google Artifact Registry

```bash
export PROJECT_ID=your-project-id
export REGION=europe-west1
export GAR_REPO=docker-repo

podman tag gemma-service:latest \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPO}/gemma-service:latest
```

#### Step 3: Authenticate to GAR

```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

#### Step 4: Push Image to GAR

```bash
podman push \
  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPO}/gemma-service:latest
```

#### Step 5: Deploy to Cloud Run

```bash
gcloud run deploy gemma-service \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${GAR_REPO}/gemma-service:latest \
  --region europe-west1 \
  --platform managed \
  --cpu gpu \
  --memory 16Gi \
  --gpu-type nvidia-l4 \
  --gpu-count 1 \
  --port 8080 \
  --timeout 300s \
  --min-instances 0 \
  --max-instances 2 \
  --allow-unauthenticated \
  --set-env-vars "MODEL_NAME=google/gemma-7b-it,USE_8BIT_QUANTIZATION=true"
```

**Note:** 8-bit quantization is now enabled by default to reduce memory usage and prevent OOM errors.

## Service Configuration

### Resource Requirements

- **Memory:** 16Gi (for Gemma 7B) or 8Gi (for Gemma 2B)
- **GPU:** NVIDIA L4 (1 GPU)
- **CPU:** GPU-enabled (automatically set with `--cpu gpu`)
- **Port:** 8080 (Cloud Run standard)

### Environment Variables

| Variable                | Description                     | Default              | Notes                            |
| ----------------------- | ------------------------------- | -------------------- | -------------------------------- |
| `MODEL_NAME`            | Hugging Face model name         | `google/gemma-7b-it` | -                                |
| `HUGGINGFACE_TOKEN`     | Optional: For private models    | -                    | Stored in Secret Manager         |
| `USE_8BIT_QUANTIZATION` | Enable 8-bit quantization       | `true`               | Enabled by default to reduce OOM |
| `REQUIRE_AUTH`          | Enable Workload Identity auth   | `false`              | Set to `true` for production     |
| `PORT`                  | Service port (set by Cloud Run) | `8080`               | Automatically set by Cloud Run   |

### Scaling Configuration

- **Min Instances:** 0 (scale to zero to save costs)
- **Max Instances:** 2 (control costs with GPU)
- **Concurrency:** 1 request per instance (GPU workloads)

## Verifying Deployment

### 1. Check Service Status

```bash
gcloud run services describe gemma-service --region europe-west1
```

### 2. Test Health Endpoint

```bash
SERVICE_URL=$(gcloud run services describe gemma-service \
  --region europe-west1 \
  --format='value(status.url)')

curl ${SERVICE_URL}/healthz
```

Expected response:

```json
{
  "status": "healthy",
  "model": "google/gemma-7b-it",
  "device": "cuda",
  "gpu_available": true,
  "model_loaded": true,
  "gpu_name": "NVIDIA L4",
  "gpu_memory_gb": 24.0
}
```

### 3. Test Generation Endpoint

```bash
curl -X POST ${SERVICE_URL}/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms:",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## Integration with Backend

### 1. Set Environment Variable

Add to your backend service:

```bash
gcloud run services update agentnav-backend \
  --set-env-vars "GEMMA_SERVICE_URL=https://gemma-service-XXXXX.run.app"
```

### 2. Use in Code

```python
from services.gemma_service import generate_with_gemma

# Generate text
text = await generate_with_gemma(
    prompt="Analyze this code: ...",
    max_tokens=500,
    temperature=0.7
)
```

## Cost Management

### Estimated Costs

- **NVIDIA L4 GPU:** ~$0.75/hour per GPU
- **Memory:** Included with GPU instance
- **With scale-to-zero:** Only pay when processing requests

### Cost Optimization Tips

1. **Set min-instances=0** to scale to zero when idle
2. **Limit max-instances** to control peak costs
3. **Use caching** to reduce GPU calls
4. **Consider smaller model** (Gemma 2B) if cost is concern
5. **Monitor usage** via Cloud Console metrics

### Setting Up Cost Alerts

1. Go to [Cloud Console > Billing > Budgets & Alerts](https://console.cloud.google.com/billing/budgets)
2. Create budget alert for Cloud Run GPU usage
3. Set threshold (e.g., $50/month)

## Troubleshooting

### Model Not Loading

- **Check logs:** `gcloud run services logs read gemma-service --region europe-west1`
- **Verify memory:** May need to increase to 16Gi for Gemma 7B
- **Check model name:** Ensure Hugging Face model name is correct

### GPU Not Detected

- **Verify GPU quota:** Check quotas in europe-west1
- **Check Cloud Run configuration:** Ensure `--cpu gpu --gpu-type nvidia-l4` is set
- **Check logs:** Look for CUDA/GPU initialization messages
- **Verify startup probe:** Ensure startup probe is configured with sufficient timeout (300s)

**Enhanced GPU Detection:** The service now performs a validation test to ensure the GPU is functional before accepting requests. Check logs for GPU detection status.

### Slow Startup

- **Model download:** First startup downloads model (~13GB for Gemma 7B)
- **Timeout:** Increase `--timeout` to 300s (already configured)
- **Startup probe:** The service uses a startup probe with 300s timeout to accommodate model loading
- **Warm instances:** Consider setting `--min-instances 1` for faster response

**Model Loading Time:** With 8-bit quantization enabled, initial model loading takes approximately 2-3 minutes. The health check endpoint will return 503 until the model is fully loaded.

### Out of Memory (OOM)

- **Use 8-bit quantization:** Enabled by default (`USE_8BIT_QUANTIZATION=true`)
- **Use smaller model:** Switch to `google/gemma-2b-it` if still experiencing OOM
- **Increase memory:** Maximum is 16Gi on Cloud Run with GPU
- **Check quantization:** Verify 8-bit quantization is working by checking logs for "Using 8-bit quantization" message

**OOM Prevention:** The default configuration now uses 8-bit quantization, which reduces memory usage by approximately 50% compared to float16, significantly reducing OOM errors.

## Monitoring

### View Metrics

1. Go to [Cloud Console > Cloud Run > gemma-service](https://console.cloud.google.com/run)
2. View metrics:
   - Request count
   - Latency
   - GPU utilization (if available)
   - Memory usage
   - Error rate

### View Logs

```bash
gcloud run services logs read gemma-service --region europe-west1 --limit 50
```

## Security

### Workload Identity Authentication (Recommended)

The Gemma service now supports **Workload Identity (WI)** authentication for secure service-to-service communication between the Backend and Gemma service on Cloud Run.

**How It Works:**
1. Backend service fetches an ID token from the metadata server
2. ID token is automatically added to requests as `Authorization: Bearer <token>`
3. Gemma service verifies the token (when `REQUIRE_AUTH=true`)
4. Only authenticated requests from the Backend Service Account are allowed

**Enable Authentication:**

```bash
# Deploy with authentication enabled
gcloud run deploy gemma-service \
  --set-env-vars "REQUIRE_AUTH=true" \
  --no-allow-unauthenticated \
  --service-account gemma-service@PROJECT_ID.iam.gserviceaccount.com
```

**Grant Backend Service Account Access:**

```bash
gcloud run services add-iam-policy-binding gemma-service \
  --region=europe-west1 \
  --member="serviceAccount:backend-service@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

**Local Development:** Authentication is automatically disabled when running locally (no `K_SERVICE` environment variable).

### Authentication (Legacy/Public Access)

For production, remove `--allow-unauthenticated` and set up authentication:

```bash
gcloud run deploy gemma-service \
  --no-allow-unauthenticated \
  --service-account gemma-service@PROJECT_ID.iam.gserviceaccount.com
```

### Secret Management

Store Hugging Face token in Secret Manager:

```bash
# Create secret
echo -n "your-token" | gcloud secrets create HUGGINGFACE_TOKEN --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding HUGGINGFACE_TOKEN \
  --member="serviceAccount:gemma-service@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Use in deployment
gcloud run services update gemma-service \
  --set-secrets "HUGGINGFACE_TOKEN=HUGGINGFACE_TOKEN:latest"
```

## Next Steps

1. **Integrate with Visualizer Agent** - Use Gemma for complex graph generation
2. **Add caching** - Cache frequent queries to reduce GPU calls
3. **Performance testing** - Benchmark GPU vs CPU performance
4. **Update architecture diagram** - Include Gemma service
5. **Documentation** - Update SYSTEM_INSTRUCTION.md with GPU service details

## References

- [Cloud Run GPU Documentation](https://cloud.google.com/run/docs/using/gpus)
- [Gemma Model Card](https://huggingface.co/google/gemma-7b-it)
- [NVIDIA L4 GPU Specs](https://www.nvidia.com/en-us/data-center/l4/)
