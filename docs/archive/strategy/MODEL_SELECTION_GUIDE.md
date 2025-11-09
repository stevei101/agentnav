# Model Selection Guide (FR#090 Enhancement)

## Overview

The **Agentnav** backend now supports flexible model selection for reasoning tasks. Agents can choose between:

- **Gemini** (cloud-based): Google's latest generative model, hosted on Google Cloud
- **Gemma** (local GPU): Open-source model running on a dedicated GPU service for low-latency or offline inference

This guide explains how to configure and use model selection across your agents.

---

## Quick Start

### Environment Variable

Set the default model type globally:

```bash
export AGENTNAV_MODEL_TYPE=gemini  # or "gemma"
```

Supported values:

- `gemini` (default): Cloud-based Gemini model
- `gemma`: Local GPU-based Gemma model

### Per-Call Override

Pass `model_type` to any reasoning helper:

```python
from services.gemini_client import reason_with_gemini

response = await reason_with_gemini(
    prompt="Analyze this content...",
    max_tokens=256,
    temperature=0.5,
    model_type="gemma"  # Use local Gemma instead
)
```

---

## Agent Configuration

### Linker Agent

Initialize the Linker agent with a preferred model:

```python
from agents.linker_agent import LinkerAgent

# Use Gemini for reasoning
linker = LinkerAgent(model_type="gemini")

# Or use Gemma for local inference
linker = LinkerAgent(model_type="gemma")
```

The agent will use the specified model type for all reasoning tasks:

- Entity extraction from documents
- Relationship analysis
- Semantic similarity reasoning

### Custom Agents

If you create new agents that use `reason_with_gemini`, follow this pattern:

```python
class MyAgent(Agent):
    def __init__(self, a2a_protocol=None, model_type: str = "gemini"):
        super().__init__("my_agent", a2a_protocol)
        self.model_type = model_type

    async def process(self, context):
        # Use model_type when calling reasoning
        result = await reason_with_gemini(
            prompt=my_prompt,
            model_type=self.model_type
        )
        return result
```

---

## Model Comparison

| Aspect           | Gemini                             | Gemma                              |
| ---------------- | ---------------------------------- | ---------------------------------- |
| **Location**     | Cloud (Google Cloud)               | Local GPU (Cloud Run with L4)      |
| **Latency**      | ~500ms–2s                          | ~200–500ms (no network)            |
| **Cost**         | Per-API-call pricing               | Compute cost (GPU hours)           |
| **Availability** | Always available                   | Requires GPU service running       |
| **Model Size**   | Latest (1.5, 2.0, etc.)            | 2B or 7B (configurable)            |
| **Best For**     | Complex reasoning, latest features | Real-time, cost-sensitive, offline |

---

## Fallback Behavior

If `model_type="gemma"` is requested but the Gemma service is unavailable:

1. A warning is logged
2. The system automatically falls back to Gemini
3. The request completes successfully

This ensures resilience:

```python
# Will use Gemma if available, fall back to Gemini if not
result = await reason_with_gemini(
    prompt="...",
    model_type="gemma"
)
```

---

## Deployment Configuration

### Cloud Run Environment Variables

Set in your Terraform or deployment manifest:

```terraform
# terraform/cloud_run.tf
env {
  name  = "AGENTNAV_MODEL_TYPE"
  value = "gemini"  # or "gemma" for GPU-enabled deployments
}
```

Or via `gcloud`:

```bash
gcloud run deploy agentnav-backend \
  --set-env-vars AGENTNAV_MODEL_TYPE=gemini \
  ...
```

### GitHub Actions CI/CD

Control model selection in workflows:

```yaml
env:
  AGENTNAV_MODEL_TYPE: gemini # For cloud reasoning in tests
```

---

## Implementation Details

### `services/gemini_client.py`

The `reason_with_gemini` helper:

```python
async def reason_with_gemini(
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.0,
    model: Optional[str] = None,
    model_type: str = "gemini"  # ← NEW: "gemini" or "gemma"
) -> str:
```

- Checks `AGENTNAV_MODEL_TYPE` environment variable (overrides parameter)
- Routes to Gemma service if `model_type="gemma"`
- Falls back to Gemini if Gemma unavailable
- Normalizes response formats across SDK versions

### Gemma Service Discovery

The `reason_with_gemini` function imports `services.gemma_service` at runtime:

```python
if model_type == "gemma":
    from services.gemma_service import reason_with_gemma
    # Use local Gemma service
```

If the import fails or service is unavailable, it falls back to Gemini.

---

## Best Practices

1. **Default to Gemini** for new agents (cloud-based, always available)
2. **Use Gemma** for:
   - High-volume reasoning tasks (cost optimization)
   - Ultra-low-latency requirements
   - Offline/air-gapped deployments
3. **Test both** during development to understand latency/cost tradeoffs
4. **Monitor logs** for fallback events (Gemma → Gemini)
5. **Pin model names** in `backend/requirements.txt` for reproducibility

---

## Troubleshooting

### "Unsupported model_type" Error

```
ValueError: Unsupported model_type: invalid. Must be 'gemini' or 'gemma'.
```

**Fix:** Ensure `model_type` is either `"gemini"` or `"gemma"` (case-insensitive).

### Gemma Service Unavailable

```
⚠️ Gemma service unavailable: Connection refused. Falling back to Gemini.
```

**Check:**

- Is the Gemma GPU service deployed and running?
- Does the backend have network access to the Gemma service?
- Check service URL in `GEMMA_SERVICE_URL` environment variable

### Slow Reasoning with Gemini

Latency spikes may indicate:

- Cold start (first request after scale-down)
- API rate limiting
- Network latency

**Mitigation:**

- Use Gemma for latency-sensitive workloads
- Increase Cloud Run min-instances if Gemini is your primary model

---

## See Also

- [FR#090: Standardize AI Model Interaction with Google GenAI Python SDK](../docs/FR090_IMPLEMENTATION_SUMMARY.md)
- [Gemma Integration Guide](./GEMMA_INTEGRATION_GUIDE.md)
- [GPU Setup Guide](./GPU_SETUP_GUIDE.md)
