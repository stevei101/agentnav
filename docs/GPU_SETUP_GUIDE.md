# GPU Setup Guide for Cloud Run
## Adding Gemma Model with NVIDIA L4 GPU

This guide helps you add GPU support to target the **GPU Category** in addition to the AI Agents category.

---

## Prerequisites

1. Google Cloud Project with billing enabled
2. GPU quota requested (if needed)
3. gcloud SDK installed and configured
4. Docker/Podman installed

---

## Step 1: Request GPU Quota

### Check Current Quota

```bash
# List GPU quotas
gcloud compute project-info describe \
  --project=YOUR_PROJECT_ID \
  --format="value(quotas)"

# Or check in Cloud Console:
# https://console.cloud.google.com/iam-admin/quotas
# Filter: "NVIDIA L4 GPUs" in europe-west1
```

### Request Quota Increase

1. Go to [Cloud Console Quotas](https://console.cloud.google.com/iam-admin/quotas)
2. Filter: `NVIDIA L4 GPUs` in `europe-west1`
3. Select quota
4. Click "EDIT QUOTAS"
5. Request increase (start with 1-2 GPUs)
6. Wait for approval (usually minutes to hours)

---

## Step 2: Create Gemma Dockerfile

Create `backend/Dockerfile.gemma`:

```dockerfile
# Use Python base image with CUDA support
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install transformers and other dependencies
RUN pip install --no-cache-dir \
    transformers \
    accelerate \
    fastapi \
    uvicorn \
    httpx

# Copy Gemma service code
WORKDIR /app
COPY backend/gemma_service.py .
COPY backend/requirements-gemma.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-gemma.txt

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080
ENV MODEL_NAME=google/gemma-7b-it

# Run Gemma service
CMD ["python", "gemma_service.py"]
```

---

## Step 3: Create Gemma Service Code

Create `backend/gemma_service.py`:

```python
"""
Gemma Service - Runs Gemma model on GPU-enabled Cloud Run
"""
import os
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM

app = FastAPI()

# Load model on startup
MODEL_NAME = os.getenv("MODEL_NAME", "google/gemma-7b-it")
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model {MODEL_NAME} on {device}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto" if device == "cuda" else None
)
if device == "cpu":
    model = model.to(device)

print(f"Model loaded successfully on {device}")

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 500
    temperature: float = 0.7

class GenerateResponse(BaseModel):
    text: str
    device: str

@app.get("/healthz")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "device": device,
        "model": MODEL_NAME,
        "gpu_available": torch.cuda.is_available()
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text using Gemma model"""
    try:
        # Tokenize input
        inputs = tokenizer(request.prompt, return_tensors="pt").to(device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=True
            )
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return GenerateResponse(
            text=generated_text,
            device=device
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## Step 4: Create Requirements File

Create `backend/requirements-gemma.txt`:

```
torch>=2.0.0
transformers>=4.35.0
accelerate>=0.24.0
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0
```

---

## Step 5: Build and Push Image

```bash
# Set variables
PROJECT_ID=your-project-id
IMAGE_NAME=gemma-service
REGION=europe-west1

# Build image with Podman
podman build -f backend/Dockerfile.gemma \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/agentnav-repo/${IMAGE_NAME}:latest \
  .

# Authenticate with Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Push image
podman push ${REGION}-docker.pkg.dev/${PROJECT_ID}/agentnav-repo/${IMAGE_NAME}:latest
```

---

## Step 6: Deploy to Cloud Run with GPU

```bash
# Deploy Gemma service with GPU
gcloud run deploy gemma-service \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/agentnav-repo/${IMAGE_NAME}:latest \
  --region=${REGION} \
  --platform=managed \
  --cpu=gpu \
  --memory=16Gi \
  --gpu-type=nvidia-l4 \
  --gpu-count=1 \
  --port=8080 \
  --allow-unauthenticated \
  --set-env-vars="MODEL_NAME=google/gemma-7b-it" \
  --timeout=300s \
  --max-instances=2 \
  --min-instances=0

# Get service URL
gcloud run services describe gemma-service \
  --region=${REGION} \
  --format="value(status.url)"
```

---

## Step 7: Integrate with Backend

Update `backend/services/gemma_service.py`:

```python
import os
import httpx

GEMMA_SERVICE_URL = os.getenv(
    "GEMMA_SERVICE_URL",
    "https://gemma-service-XXXXX.run.app"  # Replace with your URL
)

async def generate_with_gemma(prompt: str, max_tokens: int = 500) -> str:
    """Call Gemma service running on GPU"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{GEMMA_SERVICE_URL}/generate",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            return response.json()["text"]
        except httpx.HTTPError as e:
            print(f"Error calling Gemma service: {e}")
            raise
```

---

## Step 8: Update Visualizer Agent

Update `backend/agents/visualizer_agent.py`:

```python
from google.adk import Agent
from services.gemma_service import generate_with_gemma

class VisualizerAgent(Agent):
    async def process(self, context: dict) -> dict:
        """Use Gemma on GPU for complex graph generation"""
        
        # Use Gemma for complex visualization tasks
        graph_prompt = f"""
        Analyze this document and create a knowledge graph:
        
        {context['document'][:2000]}
        
        Generate nodes and edges in JSON format.
        """
        
        # Call Gemma service (GPU-accelerated)
        graph_data = await generate_with_gemma(graph_prompt, max_tokens=1000)
        
        # Parse and structure
        return self.parse_graph_data(graph_data)
```

---

## Step 9: Update Environment Variables

Add to your `.env` file:

```bash
# Gemma GPU Service
GEMMA_SERVICE_URL=https://gemma-service-XXXXX.run.app
```

Update Cloud Run backend service:

```bash
gcloud run services update agentnav-backend \
  --region=us-central1 \
  --set-env-vars="GEMMA_SERVICE_URL=https://gemma-service-XXXXX.run.app"
```

---

## Step 10: Test GPU Service

```bash
# Test health endpoint
curl https://gemma-service-XXXXX.run.app/healthz

# Test generation
curl -X POST https://gemma-service-XXXXX.run.app/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in simple terms.",
    "max_tokens": 200
  }'
```

---

## Step 11: Monitor GPU Usage

### View GPU Metrics

```bash
# View service logs
gcloud run services logs read gemma-service --region=europe-west1

# View in Cloud Console
# https://console.cloud.google.com/run/detail/europe-west1/gemma-service/metrics
```

### Check GPU Utilization

The health endpoint returns GPU status:
```json
{
  "status": "healthy",
  "device": "cuda",
  "model": "google/gemma-7b-it",
  "gpu_available": true
}
```

---

## ?? Cost Considerations

### GPU Pricing (Approximate)
- **NVIDIA L4 GPU**: ~$0.75/hour per GPU
- **Memory**: 16Gi recommended
- **Min instances**: 0 (scale to zero when not in use)
- **Max instances**: 2 (limit costs)

### Cost Optimization Tips
1. **Scale to zero** - Set min-instances=0
2. **Use only when needed** - Call Gemma for complex tasks only
3. **Cache results** - Store in Firestore
4. **Batch requests** - Process multiple requests together

---

## ?? Troubleshooting

### Issue: "Quota exceeded"
```bash
# Request quota increase
gcloud compute project-info describe --project=YOUR_PROJECT_ID
# Then request via Cloud Console
```

### Issue: "GPU not available"
```bash
# Check region
gcloud run services describe gemma-service --region=europe-west1

# Verify GPU configuration
gcloud run services describe gemma-service --region=europe-west1 \
  --format="value(spec.template.spec.containers[0].resources)"
```

### Issue: "Model too large"
- Use smaller model: `google/gemma-2b-it`
- Reduce memory: `--memory=8Gi`
- Use quantization

### Issue: "Slow startup"
- Increase timeout: `--timeout=600s`
- Use pre-warmed instances: `--min-instances=1`
- Optimize Dockerfile (layer caching)

---

## ? Verification Checklist

- [ ] GPU quota approved
- [ ] Gemma Dockerfile created
- [ ] Service code written
- [ ] Image built and pushed
- [ ] Service deployed with GPU
- [ ] Health check working
- [ ] Backend integrated
- [ ] Visualizer Agent updated
- [ ] Environment variables set
- [ ] GPU usage visible in metrics

---

## ?? Architecture Update

Add to your architecture diagram:

```
???????????????????????????????????????????
?      Backend (Cloud Run)               ?
?      us-central1                       ?
?      ????????????????????????          ?
?      ?  Visualizer Agent    ?          ?
?      ????????????????????????          ?
??????????????????????????????????????????
                   ?
         ?????????????????????
         ?                    ?
???????????????????  ???????????????????
?  Gemini API     ?  ?  Gemma Service  ?
?  (Cloud API)    ?  ?  Cloud Run GPU  ?
?                 ?  ?  NVIDIA L4      ?
?                 ?  ?  europe-west1   ?
???????????????????  ???????????????????
```

---

## ?? Next Steps

1. ? Complete GPU setup
2. ? Update architecture diagram
3. ? Update demo video to show GPU
4. ? Update submission text
5. ? Test end-to-end
6. ? Monitor costs

---

**You're now targeting BOTH categories! ????**
