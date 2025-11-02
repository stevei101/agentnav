# Gemma GPU Service

GPU-accelerated Gemma model serving on Cloud Run with NVIDIA L4 GPU.

## Overview

This service provides a FastAPI application that serves the Gemma open-source model on Cloud Run with GPU acceleration. It's designed to meet the GPU category requirements for the Cloud Run Hackathon.

## Architecture

- **Framework:** FastAPI
- **Model:** Google Gemma 7B (or 2B variant)
- **GPU:** NVIDIA L4 (via Cloud Run)
- **Region:** europe-west1
- **Device:** CUDA (with CPU fallback)

## Features

- ✅ Text generation with configurable parameters
- ✅ Embedding generation
- ✅ GPU detection and automatic fallback to CPU
- ✅ Health check endpoint with GPU status
- ✅ Cloud Run compatible (PORT env var, /healthz endpoint)
- ✅ Optional 8-bit quantization for memory efficiency

## API Endpoints

### `GET /healthz`

Health check endpoint (Cloud Run requirement).

**Response:**

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

### `POST /generate`

Generate text from a prompt.

**Request:**

```json
{
  "prompt": "Explain quantum computing:",
  "max_tokens": 500,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 50
}
```

**Response:**

```json
{
  "text": "Quantum computing uses quantum mechanical phenomena...",
  "tokens_generated": 150,
  "model": "google/gemma-7b-it",
  "device": "cuda"
}
```

### `POST /embeddings`

Generate embeddings for text.

**Request:**

```json
{
  "text": "Text to embed"
}
```

**Response:**

```json
{
  "embeddings": [0.123, -0.456, ...],
  "dimension": 4096,
  "model": "google/gemma-7b-it"
}
```

## Local Development

### Prerequisites

- Python 3.11+
- CUDA-capable GPU (optional, falls back to CPU)
- PyTorch with CUDA support (if using GPU)

### Setup

```bash
cd backend/gemma_service

# Install dependencies
pip install -r ../requirements-gemma.txt

# Set environment variables
export MODEL_NAME=google/gemma-7b-it
export PORT=8080

# Run service
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Testing

```bash
# Health check
curl http://localhost:8080/healthz

# Generate text
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!", "max_tokens": 50}'
```

## Deployment

See [docs/GPU_SETUP_GUIDE.md](../../docs/GPU_SETUP_GUIDE.md) for detailed deployment instructions.

### Quick Deploy

```bash
# Using deployment script
./scripts/deploy-gemma.sh

# Or manually
cd backend
podman build -f Dockerfile.gemma -t gemma-service:latest .
# ... push to GAR and deploy to Cloud Run
```

## Integration

### From Backend Service

```python
from services.gemma_service import generate_with_gemma

# Generate text
text = await generate_with_gemma(
    prompt="Analyze this code: ...",
    max_tokens=500,
    temperature=0.7
)
```

### Environment Variables

Set in backend service:

```bash
GEMMA_SERVICE_URL=https://gemma-service-XXXXX.run.app
GEMMA_SERVICE_TIMEOUT=60.0
```

## Performance

- **Model Loading:** ~2-5 minutes (first time, downloads ~13GB)
- **Inference Time:** ~1-5 seconds per request (GPU)
- **Memory Usage:** ~13GB for Gemma 7B, ~5GB for Gemma 2B

## Cost Considerations

- NVIDIA L4 GPU: ~$0.75/hour
- With scale-to-zero: Only pay when processing
- Estimated cost: $10-50/month (depending on usage)

## Troubleshooting

### Model Not Loading

- Check memory: Need 16Gi for Gemma 7B
- Check logs: `gcloud run services logs read gemma-service --region europe-west1`

### GPU Not Detected

- Verify GPU quota in europe-west1
- Check Cloud Run config: `--cpu gpu --gpu-type nvidia-l4`

### Slow Startup

- First startup downloads model (~13GB)
- Subsequent starts are faster (~1-2 minutes)

## References

- [Gemma Model Card](https://huggingface.co/google/gemma-7b-it)
- [Cloud Run GPU Docs](https://cloud.google.com/run/docs/using/gpus)
- [PyTorch CUDA Setup](https://pytorch.org/get-started/locally/)
