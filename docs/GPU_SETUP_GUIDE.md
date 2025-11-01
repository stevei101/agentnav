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
  --set-env-vars "MODEL_NAME=google/gemma-7b-it"
```

## Service Configuration

### Resource Requirements

- **Memory:** 16Gi (for Gemma 7B) or 8Gi (for Gemma 2B)
- **GPU:** NVIDIA L4 (1 GPU)
- **CPU:** GPU-enabled (automatically set with `--cpu gpu`)
- **Port:** 8080 (Cloud Run standard)

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_NAME` | Hugging Face model name | `google/gemma-7b-it` |
| `HUGGINGFACE_TOKEN` | Optional: For private models | - |
| `USE_8BIT_QUANTIZATION` | Enable 8-bit quantization | `false` |
| `PORT` | Service port (set by Cloud Run) | `8080` |

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

### Slow Startup

- **Model download:** First startup downloads model (~13GB for Gemma 7B)
- **Timeout:** Increase `--timeout` to 300s or higher
- **Warm instances:** Consider setting `--min-instances 1` for faster response

### Out of Memory

- **Use smaller model:** Switch to `google/gemma-2b-it`
- **Enable quantization:** Set `USE_8BIT_QUANTIZATION=true`
- **Increase memory:** Use 16Gi or higher

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

### Authentication (Production)

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
