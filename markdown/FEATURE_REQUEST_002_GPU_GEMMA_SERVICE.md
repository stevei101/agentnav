# Feature Request #002: GPU-Enabled Gemma Service on Cloud Run

**Feature Status:** ?? Ideation & Planning  
**Priority:** High (Required for GPU Category)  
**Timeline:** 1 Week  
**Assigned To:** TBD

---

## Is your feature request related to a problem? Please describe.

To compete in the **GPU Category** of the Cloud Run Hackathon, we need to deploy and run an open-source AI model (Gemma) on Cloud Run with NVIDIA L4 GPU acceleration. Currently, our project uses Gemini API for agent reasoning, but we lack GPU-powered model inference capabilities.

**The Problem:**
- We cannot compete in the GPU category without a GPU-enabled service
- Complex visualization and embedding tasks could benefit from GPU acceleration
- No open-source model deployment in our current architecture
- Missing demonstration of GPU utilization for hackathon judges
- Cannot show performance improvements from GPU acceleration

**I'm always frustrated when** I need to:
- Run complex AI tasks on CPU (slow inference times)
- Wait for embeddings or graph generation without GPU acceleration
- Cannot demonstrate GPU capabilities to hackathon judges
- Missing a key differentiator that could win the GPU category prize ($8,000)

---

## Describe the solution you'd like

**Create a GPU-enabled Cloud Run service** that deploys and runs the Gemma open-source model using NVIDIA L4 GPUs.

### Core Requirements

1. **Gemma Model Deployment**
   - Deploy Gemma model (7B or 2B variant) on Cloud Run
   - Use NVIDIA L4 GPU in europe-west1 region
   - Containerized model serving with proper GPU configuration
   - FastAPI service for model inference

2. **Cloud Run Service Configuration**
   - **Resource Type:** Cloud Run Service (for HTTP requests)
   - **Region:** europe-west1 (as required by hackathon)
   - **GPU:** NVIDIA L4 (1 GPU)
   - **Memory:** 16Gi (sufficient for Gemma 7B)
   - **CPU:** GPU-enabled
   - **Port:** 8080 (Cloud Run compatible)
   - **Health Check:** `/healthz` endpoint

3. **Model Integration**
   - Use Gemma for specific agent tasks:
     - **Visualizer Agent:** Complex graph generation
     - **Embedding Generation:** Semantic embeddings for knowledge graph
     - **Code Analysis:** Deep code understanding
   - Maintain Gemini API for orchestration and reasoning

4. **Performance Optimization**
   - Model quantization (if needed for memory)
   - Batch processing support
   - Caching mechanisms
   - Connection pooling

### Implementation Components

**Service Architecture:**
```
Backend API (FastAPI)
    ?
    ??? Gemini API (Agent Reasoning)
    ?
    ??? Gemma GPU Service (Cloud Run)
            ?
            ??? NVIDIA L4 GPU (europe-west1)
```

**Service Features:**
- REST API endpoints for model inference
- Support for text generation, embeddings, and analysis
- Health check endpoint for Cloud Run
- Error handling and retry logic
- Request/response logging

---

## Describe alternatives you've considered

### Alternative 1: **Deploy Gemma as Cloud Run Job**
- **Pros:** Better for batch processing, one-time tasks
- **Cons:** Not suitable for real-time HTTP requests, harder to integrate with agents
- **Decision:** Use Cloud Run Service for HTTP integration

### Alternative 2: **Use Vertex AI Model Garden**
- **Pros:** Managed service, easier deployment
- **Cons:** Not "open-source model on Cloud Run" - doesn't meet hackathon requirement
- **Decision:** Must deploy model directly on Cloud Run

### Alternative 3: **Use Smaller Model (Gemma 2B)**
- **Pros:** Lower memory requirements, faster startup
- **Cons:** Less capable, may not demonstrate GPU benefits as clearly
- **Decision:** Use Gemma 7B for better demonstration, optimize if needed

### Alternative 4: **CPU-Only Deployment**
- **Pros:** Lower cost, simpler deployment
- **Cons:** Doesn't meet GPU category requirement, slower performance
- **Decision:** Must use GPU for hackathon category

### **Why GPU-Enabled Cloud Run Service is Best:**
- ? Meets hackathon requirement (open-source model on Cloud Run with GPU)
- ? Integrates seamlessly with existing backend architecture
- ? Allows real-time HTTP requests from agents
- ? Demonstrates GPU acceleration benefits
- ? Scalable and production-ready
- ? europe-west1 region supports NVIDIA L4 GPUs

---

## Additional context

### Hackathon Requirements

**GPU Category Requirements:**
- ? Utilize NVIDIA L4 GPUs on Cloud Run
- ? Use europe-west1 or europe-west4 region
- ? Deploy open-source model (Gemma qualifies)
- ? Run on Cloud Run Service, Job, or Worker Pool
- ? Demonstrate performant AI/ML model inference

**Why Gemma?**
- Open-source model (meets requirement)
- Developed by Google (aligns with hackathon ecosystem)
- Good performance on Cloud Run GPUs
- Supports text generation and embeddings
- Well-documented and supported

### Technical Requirements

**Dockerfile Requirements:**
- Base image with CUDA support
- PyTorch with CUDA enabled
- Transformers library for Gemma
- FastAPI for HTTP service
- Model loading on container startup
- GPU memory management

**Model Configuration:**
- Model: `google/gemma-7b-it` or `google/gemma-2b-it`
- Quantization: Consider 8-bit or 4-bit for memory efficiency
- Device: CUDA (GPU)
- Batch size: Configurable
- Max tokens: Configurable per request

**Cloud Run Configuration:**
- Service name: `gemma-service`
- Region: `europe-west1`
- GPU type: `nvidia-l4`
- GPU count: `1`
- Memory: `16Gi` (or `8Gi` for 2B model)
- CPU: `gpu` (enables GPU)
- Port: `8080`
- Timeout: `300s` (for model loading)
- Min instances: `0` (scale to zero)
- Max instances: `2` (cost control)

### Integration Points

**Backend Integration:**
```python
# backend/services/gemma_service.py
async def generate_with_gemma(prompt: str) -> str:
    """Call Gemma GPU service"""
    response = await httpx.post(
        f"{GEMMA_SERVICE_URL}/generate",
        json={"prompt": prompt, "max_tokens": 1000}
    )
    return response.json()["text"]
```

**Agent Integration:**
```python
# backend/agents/visualizer_agent.py
class VisualizerAgent(Agent):
    async def process(self, context: dict) -> dict:
        # Use Gemma for complex graph generation
        graph_prompt = f"Generate knowledge graph: {context['document']}"
        graph_data = await generate_with_gemma(graph_prompt)
        return self.parse_graph(graph_data)
```

### Environment Variables

```bash
# Gemma Service Configuration
GEMMA_SERVICE_URL=https://gemma-service-XXXXX.run.app
MODEL_NAME=google/gemma-7b-it
DEVICE=cuda
MAX_MEMORY=16Gi

# Cloud Run Deployment
REGION=europe-west1
GPU_TYPE=nvidia-l4
GPU_COUNT=1
```

### Success Criteria

? **GPU Deployment:**
- Gemma model deployed on Cloud Run with NVIDIA L4 GPU
- Service accessible via HTTP endpoint
- Health check endpoint working
- GPU utilization visible in Cloud Console

? **Integration:**
- Backend can call Gemma service
- Visualizer Agent uses Gemma for complex tasks
- Error handling and fallback mechanisms in place

? **Performance:**
- GPU inference faster than CPU (demonstrable)
- Model startup time acceptable (< 5 minutes)
- Request latency reasonable (< 10 seconds for generation)

? **Hackathon Requirements:**
- Meets all GPU category requirements
- Can demonstrate GPU usage in demo video
- Architecture diagram shows GPU service
- Performance improvements documented

### Timeline Breakdown (1 Week)

- **Day 1:** Research Gemma model, create Dockerfile with CUDA support
- **Day 2:** Build Gemma service code, implement FastAPI endpoints
- **Day 3:** Test locally with GPU (if available) or CPU first
- **Day 4:** Deploy to Cloud Run with GPU, configure region and resources
- **Day 5:** Integrate with backend, update Visualizer Agent
- **Day 6:** Performance testing, optimization, error handling
- **Day 7:** Documentation, demo preparation, final testing

### Dependencies

- **GPU Quota:** NVIDIA L4 GPU quota in europe-west1 (may need to request)
- **Model Access:** Hugging Face account/token for Gemma model download
- **Container Registry:** Google Artifact Registry for storing images
- **Service Account:** Cloud Run service account with GPU permissions

### Implementation Steps

1. **Request GPU Quota**
   ```bash
   # Check quota
   gcloud compute project-info describe --project=PROJECT_ID
   # Request via Cloud Console if needed
   ```

2. **Create Gemma Dockerfile**
   - Base: `python:3.11-slim` or CUDA-enabled image
   - Install: PyTorch with CUDA, Transformers, FastAPI
   - Copy: Gemma service code
   - Configure: Model loading, GPU detection

3. **Implement Gemma Service**
   - FastAPI application
   - Model loading on startup
   - `/generate` endpoint
   - `/healthz` endpoint
   - Error handling

4. **Build and Push Image**
   ```bash
   podman build -f backend/Dockerfile.gemma -t gemma-service .
   podman push gcr.io/PROJECT_ID/gemma-service:latest
   ```

5. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy gemma-service \
     --image=gcr.io/PROJECT_ID/gemma-service:latest \
     --region=europe-west1 \
     --platform=managed \
     --cpu=gpu \
     --memory=16Gi \
     --gpu-type=nvidia-l4 \
     --gpu-count=1 \
     --port=8080 \
     --allow-unauthenticated
   ```

6. **Integrate with Backend**
   - Update backend to call Gemma service
   - Modify Visualizer Agent
   - Add error handling and fallbacks

7. **Test and Optimize**
   - Test inference performance
   - Monitor GPU utilization
   - Optimize model loading
   - Test error scenarios

### Cost Considerations

**GPU Costs (Approximate):**
- NVIDIA L4 GPU: ~$0.75/hour per GPU
- Memory: Included in GPU instance
- With scale-to-zero: Only pay when processing requests

**Cost Optimization:**
- Set `min-instances=0` (scale to zero)
- Limit `max-instances=2` (control costs)
- Use caching to reduce GPU calls
- Consider smaller model (2B) if cost is concern

### Future Enhancements (Post-MVP)

- [ ] Support for batch inference
- [ ] Model quantization (8-bit, 4-bit)
- [ ] Streaming responses
- [ ] Multiple model variants
- [ ] Performance benchmarking dashboard
- [ ] A/B testing CPU vs GPU
- [ ] Model versioning
- [ ] Warm-up requests to keep instance ready

### Related Issues

- Need to request GPU quota before deployment
- Model download time on first startup (can be slow)
- Memory requirements for Gemma 7B (~13GB)
- Integration with existing agent architecture
- Cost management for GPU instances

### Reference Implementation

**Example Gemma Service Structure:**
```
backend/
??? gemma_service/
?   ??? __init__.py
?   ??? main.py          # FastAPI app
?   ??? model_loader.py # Model loading logic
?   ??? inference.py    # Inference functions
??? Dockerfile.gemma     # GPU-enabled container
??? requirements-gemma.txt
```

**Example FastAPI Endpoints:**
```python
POST /generate
{
  "prompt": "string",
  "max_tokens": 500,
  "temperature": 0.7
}

GET /healthz
{
  "status": "healthy",
  "device": "cuda",
  "model": "google/gemma-7b-it",
  "gpu_available": true
}
```

---

## Acceptance Criteria

- [ ] Gemma model deployed on Cloud Run Service with NVIDIA L4 GPU
- [ ] Service deployed in europe-west1 region
- [ ] Service accessible via HTTP endpoint
- [ ] `/healthz` endpoint returns GPU status
- [ ] Backend can successfully call Gemma service
- [ ] Visualizer Agent uses Gemma for complex tasks
- [ ] GPU utilization visible in Cloud Console metrics
- [ ] Performance improvements demonstrable (CPU vs GPU comparison)
- [ ] Error handling and fallback mechanisms implemented
- [ ] Cost optimization (scale to zero) configured
- [ ] Documentation updated with GPU service details
- [ ] Architecture diagram updated to show GPU service
- [ ] Demo video includes GPU usage demonstration

---

## Judging Criteria Alignment

### Technical Implementation (40%)
- ? Clean, efficient code for model serving
- ? Proper Cloud Run GPU configuration
- ? Error handling and resilience
- ? Production-ready service design

### Demo & Presentation (40%)
- ? Clear demonstration of GPU usage
- ? Performance comparison (CPU vs GPU)
- ? Architecture diagram shows GPU service
- ? Explains GPU integration clearly

### Innovation & Creativity (20%)
- ? Hybrid approach (Gemini + Gemma)
- ? GPU used for appropriate tasks
- ? Efficient resource utilization
- ? Innovative use of Cloud Run GPU capabilities

---

## Documentation Updates Needed

- [ ] Update `docs/SYSTEM_INSTRUCTION.md` with GPU service details
- [ ] Update `docs/GPU_SETUP_GUIDE.md` with deployment steps
- [ ] Update `docs/DUAL_CATEGORY_STRATEGY.md` with implementation status
- [ ] Update architecture diagram to show GPU service
- [ ] Add GPU service to `docs/local-development.md` (if local GPU available)

---

## Risk Assessment

**High Risk:**
- GPU quota not approved in time
- Model too large for available memory
- Slow model startup affecting UX

**Medium Risk:**
- Integration complexity with existing agents
- Cost overruns if not properly configured
- Performance not meeting expectations

**Low Risk:**
- Model download delays
- API compatibility issues
- Documentation gaps

**Mitigation Strategies:**
- Request GPU quota early
- Test with smaller model first (2B)
- Implement proper error handling
- Set up cost alerts
- Create fallback to CPU/Gemini if GPU unavailable

---

**Feature Request Created:** [Date]  
**Last Updated:** [Date]  
**Estimated Effort:** 1 Week (40 hours)  
**Category:** GPU Category Requirement
