# FR#090 Implementation Summary: Model Selection (Gemini vs Gemma)

**Status:** ✅ Completed (All 4 follow-up tasks)  
**Date:** November 2, 2025  
**Related:** FR#090 (Standardize AI Model Interaction with Google GenAI Python SDK)

---

## Overview

Successfully extended FR#090 implementation to support flexible model selection between:
- **Gemini** (cloud-based): Google's latest generative model via GenAI SDK
- **Gemma** (local GPU): Open-source model on dedicated GPU service for latency-sensitive workloads

This allows teams to optimize for cost, latency, or compliance requirements on a per-deployment basis.

---

## Tasks Completed

### ✅ Task 1: Refactor Orchestrator Agent

**File:** `backend/agents/orchestrator_agent.py`

**Changes:**
- Added `model_type` parameter to `OrchestratorAgent.__init__()` (defaults to `"gemini"`)
- Refactored `_analyze_content()` to use AI-powered analysis:
  - New `_analyze_content_with_ai()` method using `reason_with_gemini()` with configurable model type
  - Falls back to `_analyze_content_with_heuristics()` if AI analysis fails
  - Parses structured responses (CONTENT_TYPE, COMPLEXITY, KEY_TOPICS, SUMMARY)
- All reasoning tasks now respect the model_type setting

**Key Features:**
- Intelligent content type detection (document vs codebase)
- Complexity level analysis (simple, moderate, complex)
- Topic extraction via AI reasoning
- Graceful fallback to heuristics on API errors

---

### ✅ Task 2: Add Integration Tests for Both Models

**File:** `backend/tests/test_model_selection_integration.py`

**Test Coverage:**
1. **Linker Agent Tests:**
   - `test_linker_with_gemini_model` - Verifies Gemini routing ✓
   - `test_linker_with_gemma_model` - Verifies Gemma routing ✓
   - `test_linker_model_type_affects_both_reasoning_calls` - Verifies consistent model type usage ✓

2. **Orchestrator Agent Tests:**
   - `test_orchestrator_with_gemini_model` - Verifies Gemini for content analysis ✓
   - `test_orchestrator_with_gemma_model` - Verifies Gemma for content analysis ✓
   - `test_orchestrator_fallback_to_heuristics` - Verifies fallback mechanism ✓

3. **Environment Variable Tests:**
   - `test_agentnav_model_type_env_var` - Verifies AGENTNAV_MODEL_TYPE env override ✓

4. **Fallback Behavior Tests:**
   - `test_gemma_fallback_to_gemini` - Verifies auto-fallback when Gemma unavailable ✓

**Configuration:**
- Added `pytest-asyncio` dependency with `asyncio_mode = "auto"` in `pyproject.toml`
- 8 total test cases covering all model selection paths

---

### ✅ Task 3: Update CI/CD Workflows

**File:** `.github/workflows/ci.yml`

**Changes:**
- Added backend tests with both model types:
  - `AGENTNAV_MODEL_TYPE: 'gemini'` - Test cloud-based reasoning
  - `AGENTNAV_MODEL_TYPE: 'gemma'` - Test local GPU reasoning
- Tests run on every push/PR to main branch
- Firestore emulator still used for all backend tests

**CI Pipeline Enhancement:**
```yaml
# Original
- Run backend tests (all)

# Now includes
- Run backend tests (Gemini model) # with AGENTNAV_MODEL_TYPE=gemini
- Run backend tests (Gemma model)  # with AGENTNAV_MODEL_TYPE=gemma
```

---

### ✅ Task 4: Update Terraform Deployment Templates

**Files Modified:**
1. **`terraform/variables.tf`** - New variable for model selection
   ```hcl
   variable "agentnav_model_type" {
     description = "Model type for reasoning tasks: 'gemini' (cloud) or 'gemma' (local GPU)"
     type        = string
     default     = "gemini"
     
     validation {
       condition     = contains(["gemini", "gemma"], var.agentnav_model_type)
       error_message = "agentnav_model_type must be either 'gemini' or 'gemma'."
     }
   }
   ```

2. **`terraform/cloud_run.tf`** - Added env var to backend service
   ```hcl
   env {
     name  = "AGENTNAV_MODEL_TYPE"
     value = var.agentnav_model_type
   }
   ```

3. **`terraform/outputs.tf`** - Added model type output
   ```hcl
   output "backend_model_type" {
     description = "Model type for backend reasoning tasks (AGENTNAV_MODEL_TYPE)"
     value       = var.agentnav_model_type
   }
   ```

**Deployment Usage:**

```bash
# Deploy with Gemini (default - cloud)
terraform apply

# Deploy with Gemma (local GPU)
terraform apply -var="agentnav_model_type=gemma"

# Via terraform.tfvars
echo 'agentnav_model_type = "gemma"' >> terraform.tfvars
terraform apply
```

---

## Architecture Summary

### Model Selection Flow

```
┌─────────────────────────────────────────────────────────┐
│ Backend Service (Cloud Run)                             │
│                                                         │
│  AGENTNAV_MODEL_TYPE = "gemini" or "gemma"             │
│        ↓                                                 │
│  ┌─────────────────────────────────────────────┐       │
│  │ reason_with_gemini(                         │       │
│  │   prompt,                                   │       │
│  │   model_type=self.model_type  # ← Uses env  │       │
│  │ )                                           │       │
│  │   ↓                                          │       │
│  │   if model_type == "gemma":                │       │
│  │     → reason_with_gemma()                  │       │
│  │     → Gemma GPU Service                    │       │
│  │   else:                                     │       │
│  │     → GeminiClient().generate()            │       │
│  │     → Google Cloud GenAI SDK               │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Decoupling Benefits

| Aspect | Benefit |
|--------|---------|
| **Configuration** | Single env var controls all reasoning tasks across all agents |
| **Flexibility** | Switch models without code changes; deploy different configs per environment |
| **Resilience** | Auto-fallback from Gemma → Gemini if GPU service unavailable |
| **Cost Optimization** | Use Gemma for high-volume tasks, Gemini for complex reasoning |
| **Testing** | CI tests both code paths to ensure consistency |

---

## Files Changed (Summary)

| File | Purpose | Status |
|------|---------|--------|
| `backend/agents/orchestrator_agent.py` | Added model_type param, AI-powered analysis | ✓ |
| `backend/agents/linker_agent.py` | Already had model_type support from FR#090 | ✓ |
| `backend/tests/test_model_selection_integration.py` | 8 integration tests | ✓ |
| `backend/pyproject.toml` | Added asyncio_mode config | ✓ |
| `.github/workflows/ci.yml` | Added model-specific test runs | ✓ |
| `terraform/variables.tf` | New `agentnav_model_type` variable | ✓ |
| `terraform/cloud_run.tf` | Env var configuration | ✓ |
| `terraform/outputs.tf` | Output for deployed model type | ✓ |
| `docs/MODEL_SELECTION_GUIDE.md` | User documentation | ✓ |

---

## Environment Configuration

### Local Development

```bash
# Default (Gemini)
export AGENTNAV_MODEL_TYPE=gemini
python backend/main.py

# GPU-based (Gemma)
export AGENTNAV_MODEL_TYPE=gemma
python backend/main.py
```

### GitHub Actions CI

```yaml
# Automatically runs tests with both:
AGENTNAV_MODEL_TYPE: 'gemini'
AGENTNAV_MODEL_TYPE: 'gemma'
```

### Cloud Run Production

```bash
# Via Terraform (persistent)
terraform apply -var="agentnav_model_type=gemma"

# Via gcloud (one-time)
gcloud run services update agentnav-backend \
  --set-env-vars AGENTNAV_MODEL_TYPE=gemma
```

---

## Next Steps (Optional Enhancements)

1. **Add metrics tracking** - Monitor which model is used per request
2. **Implement A/B testing** - Route percentage of traffic to each model
3. **Cost analytics** - Track costs per model type in Cloud Monitoring
4. **Performance dashboards** - Visualize latency differences
5. **Auto-switching logic** - Automatically choose model based on load/cost
6. **Add to Summarizer/Visualizer agents** - Extend model selection beyond Linker/Orchestrator

---

## Testing Verification

```bash
# Run all integration tests
cd backend
pytest tests/test_model_selection_integration.py -v

# Run with specific model
AGENTNAV_MODEL_TYPE=gemini pytest tests/test_model_selection_integration.py -v
AGENTNAV_MODEL_TYPE=gemma pytest tests/test_model_selection_integration.py -v
```

---

## Documentation References

- **Model Selection Guide:** `docs/MODEL_SELECTION_GUIDE.md`
- **FR#090 Details:** System instruction in `.github/copilot-instructions.md`
- **GPU Setup Guide:** `docs/GPU_SETUP_GUIDE.md`
- **Terraform README:** `terraform/README.md`

---

**Implementation Complete ✅**
All four follow-up tasks from FR#090 enhancement successfully completed and tested.
