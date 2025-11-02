# Gemma GPU Service Integration Guide

## Overview

This guide describes the implementation and integration of the **Gemma GPU Service** with the Agentic Navigator multi-agent system. The service provides GPU-accelerated text generation and semantic embeddings for enhanced knowledge exploration.

## Architecture

### Service Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend Service                          │
│                   (FastAPI + ADK)                           │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ Orchestrator │──────│  Summarizer  │                   │
│  │    Agent     │      │    Agent     │                   │
│  └──────────────┘      └──────────────┘                   │
│         │                                                   │
│         │              ┌──────────────┐                   │
│         └──────────────│   Linker     │                   │
│                        │    Agent     │                   │
│                        └──────┬───────┘                   │
│                               │                             │
│                               │ HTTP                        │
│                               │ (gemma_client.py)          │
└───────────────────────────────┼─────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Gemma GPU Service    │
                    │  (Cloud Run + L4 GPU) │
                    │                       │
                    │  Endpoints:           │
                    │  • /embed             │
                    │  • /reason            │
                    │  • /healthz           │
                    └───────────────────────┘
```

## API Specification

### 1. POST /embed - Batch Embedding Generation

Generates semantic embeddings for a batch of text strings.

**Request:**
```json
{
  "texts": [
    "Machine learning is a subset of AI",
    "Deep learning uses neural networks",
    "Natural language processing"
  ]
}
```

**Response:**
```json
{
  "embeddings": [
    [0.123, -0.456, ..., 0.789],  // 4096 dimensions
    [0.234, -0.567, ..., 0.890],
    [0.345, -0.678, ..., 0.901]
  ],
  "dimension": 4096,
  "model": "google/gemma-7b-it"
}
```

**Features:**
- Batch processing for efficiency
- 4096-dimensional embeddings (Gemma 7B)
- GPU-accelerated computation
- Automatic mean pooling of hidden states

### 2. POST /reason - Context-Aware Text Generation

Generates text with optional context for enhanced reasoning.

**Request:**
```json
{
  "prompt": "Explain the relationship between these concepts",
  "context": "Machine learning, deep learning, neural networks",
  "max_tokens": 500,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 50
}
```

**Response:**
```json
{
  "text": "Deep learning is a specialized form of machine learning...",
  "tokens_generated": 150,
  "model": "google/gemma-7b-it",
  "device": "cuda"
}
```

**Features:**
- Context-aware generation
- Configurable sampling parameters
- GPU-accelerated inference
- Automatic prompt formatting

### 3. GET /healthz - Health Check

Returns service health and GPU status.

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

## Linker Agent Integration

### Semantic Relationship Mapping

The Linker Agent uses Gemma embeddings to perform semantic relationship analysis:

```python
from services.gemma_client import embed_with_gemma, reason_with_gemma

async def identify_relationships(entities):
    # 1. Generate embeddings for all entities
    entity_labels = [e["label"] for e in entities]
    embeddings = await embed_with_gemma(entity_labels)
    
    # 2. Calculate cosine similarity
    for i, entity1 in enumerate(entities):
        for j, entity2 in enumerate(entities):
            similarity = cosine_similarity(
                embeddings[i], 
                embeddings[j]
            )
            
            # 3. Create relationship if similar (threshold: 0.7)
            if similarity >= 0.7:
                relationships.append({
                    "from": entity1["id"],
                    "to": entity2["id"],
                    "similarity": similarity,
                    "type": "semantically_related"
                })
    
    # 4. Enhance with reasoning
    reasoning = await reason_with_gemma(
        prompt="Analyze relationships between entities",
        context=document_context
    )
    
    return relationships
```

### Key Features

1. **Semantic Similarity Analysis**
   - Cosine similarity between entity embeddings
   - Configurable threshold (default: 0.7)
   - High-confidence relationships (>0.85) marked as "strongly_related"

2. **Reasoning Enhancement**
   - Uses Gemma to analyze relationship types
   - Adds contextual insights to relationships
   - Identifies causal, hierarchical, and contradictory relationships

3. **Fallback Mechanism**
   - Falls back to co-occurrence analysis if embeddings fail
   - Ensures robustness in degraded conditions
   - Logs warnings for debugging

## Client Usage

### Basic Usage

```python
from services.gemma_client import GemmaServiceClient

client = GemmaServiceClient(base_url="https://gemma-service-xxx.run.app")

# Generate embeddings
embeddings = await client.embed([
    "Text 1",
    "Text 2",
    "Text 3"
])

# Generate reasoning
response = await client.reason(
    prompt="Explain quantum computing",
    context="For a beginner audience",
    max_tokens=300
)
```

### Convenience Functions

```python
from services.gemma_client import embed_with_gemma, reason_with_gemma

# Simple embedding generation
embeddings = await embed_with_gemma(["Text 1", "Text 2"])

# Simple reasoning
text = await reason_with_gemma(
    prompt="What is AI?",
    context="Focus on practical applications"
)
```

### Legacy Compatibility

The client maintains backward compatibility:

```python
# Legacy methods still work
text = await client.generate(prompt="Hello")
embedding = await client.generate_embeddings("Text")
```

## Deployment

### Docker Build

```bash
cd backend
podman build -f gemma_service/Dockerfile -t gemma-service:latest .
```

### Cloud Run Deployment

```bash
gcloud run deploy gemma-service \
  --image europe-docker.pkg.dev/PROJECT_ID/agentnav/gemma-service:latest \
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
  --set-env-vars MODEL_NAME=google/gemma-7b-it
```

### Environment Variables

**Gemma Service:**
- `PORT`: Service port (default: 8080, set by Cloud Run)
- `MODEL_NAME`: Gemma model to use (default: google/gemma-7b-it)
- `HUGGINGFACE_TOKEN`: Optional token for private models
- `USE_8BIT_QUANTIZATION`: Enable 8-bit quantization (default: false)

**Backend Service:**
- `GEMMA_SERVICE_URL`: URL of Gemma service (e.g., https://gemma-service-xxx.run.app)
- `GEMMA_SERVICE_TIMEOUT`: Request timeout in seconds (default: 60.0)

## Performance

### Benchmarks

| Operation | Input Size | Time (GPU) | Time (CPU) |
|-----------|-----------|------------|------------|
| Embedding (single) | 1 text | ~100ms | ~2s |
| Embedding (batch) | 10 texts | ~500ms | ~20s |
| Reasoning | 500 tokens | ~2s | ~30s |

### Optimization

1. **Batch Processing**: Use batch embedding for multiple texts
   ```python
   # Good: Batch request
   embeddings = await embed_with_gemma(["Text 1", "Text 2", "Text 3"])
   
   # Avoid: Sequential requests
   for text in texts:
       embedding = await embed_with_gemma([text])
   ```

2. **Caching**: Cache embeddings in Firestore
   ```python
   # Check cache first
   cached = firestore.get_embeddings(text_hash)
   if not cached:
       embeddings = await embed_with_gemma([text])
       firestore.store_embeddings(text_hash, embeddings)
   ```

3. **Scale to Zero**: Set `min-instances=0` to save costs when idle

## Testing

### Run Tests

```bash
cd backend
pytest tests/test_gemma_service.py -v        # Client tests
pytest tests/test_linker_integration.py -v   # Integration tests
```

### Test Coverage

- ✅ Client tests (4 tests)
  - reason() method with context
  - embed() batch processing
  - Legacy compatibility
  - Health checks

- ✅ Integration tests (8 tests)
  - Semantic similarity calculation
  - Embedding-based relationship mapping
  - Fallback mechanisms
  - Code entity extraction
  - A2A protocol notifications

## Troubleshooting

### Common Issues

1. **Model Loading Timeout**
   - **Symptom**: Service times out during startup
   - **Solution**: Increase `start-period` in healthcheck to 600s for first startup
   - **Note**: First startup downloads ~13GB model, subsequent starts are faster

2. **GPU Not Available**
   - **Symptom**: Service falls back to CPU
   - **Solution**: Verify GPU quota in europe-west1 region
   - **Check**: Cloud Run config includes `--cpu gpu --gpu-type nvidia-l4`

3. **Embedding Dimension Mismatch**
   - **Symptom**: Cosine similarity calculation fails
   - **Solution**: Ensure all embeddings use the same model version
   - **Check**: Log the dimension returned by `/embed` endpoint

4. **Service Unavailable**
   - **Symptom**: Client receives 503 errors
   - **Solution**: Check if service is scaled to zero, first request may be slow
   - **Workaround**: Set `min-instances=1` for consistent availability

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check service logs:

```bash
gcloud run services logs read gemma-service --region europe-west1 --limit 100
```

## Security

### Workload Identity (WI)

The Backend Service authenticates to Gemma Service using Workload Identity:

1. Backend Cloud Run service has a Service Account
2. Grant `roles/run.invoker` to Backend's Service Account for Gemma service
3. Client automatically fetches ID token for authentication

### API Authentication

For production, consider adding API key authentication:

```python
# In gemma_service/main.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/embed", dependencies=[Depends(verify_api_key)])
async def embed(request: EmbedRequest):
    # ...
```

## Migration from Previous API

### Endpoint Changes

| Old Endpoint | New Endpoint | Changes |
|--------------|--------------|---------|
| `/embeddings` | `/embed` | Now accepts batch (`texts` array) |
| `/generate` | `/reason` | Added optional `context` parameter |
| `/healthz` | `/healthz` | No changes |

### Client Migration

```python
# Old code
embedding = await client.generate_embeddings("Text")

# New code (batch support)
embeddings = await client.embed(["Text"])
embedding = embeddings[0]

# Or use legacy method (still supported)
embedding = await client.generate_embeddings("Text")
```

## Cost Estimation

### GPU Pricing (NVIDIA L4)

- **Hourly Rate**: ~$0.75/hour
- **Scale to Zero**: Only pay when processing
- **Estimated Monthly Cost**: $10-50 (depends on usage)

### Optimization Tips

1. Use batch requests to reduce number of service invocations
2. Enable scale-to-zero for non-production environments
3. Consider using Gemma 2B model for lower memory requirements (8Gi vs 16Gi)
4. Implement caching for frequently requested embeddings

## Future Enhancements

1. **Batch Reasoning**: Support batch text generation
2. **Streaming**: Add streaming support for long text generation
3. **Custom Embeddings**: Support fine-tuned embedding models
4. **Model Selection**: Allow runtime model selection (7B vs 2B)
5. **Quantization**: Implement 4-bit quantization for memory efficiency

## References

- [Gemma Model Card](https://huggingface.co/google/gemma-7b-it)
- [Cloud Run GPU Documentation](https://cloud.google.com/run/docs/using/gpus)
- [ADK Multi-Agent Documentation](./FR005_README.md)
- [GPU Setup Guide](./GPU_SETUP_GUIDE.md)
