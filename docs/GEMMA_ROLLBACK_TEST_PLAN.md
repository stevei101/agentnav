# Gemma GPU Service Rollback - Test Plan

**Purpose:** Verify that the backend works correctly without Gemma GPU service  
**Related Issue:** #132 (Cloud Run Container Startup Timeout)  
**Date:** $(date)

## Changes Summary

### 1. Backend Code Changes

- ✅ Made `get_gemma_client()` return `None` when `GEMMA_SERVICE_URL` not set
- ✅ Added `RuntimeError` handling in convenience functions
- ✅ Updated all agents to gracefully fallback to Gemini:
  - `VisualizerAgent`: Falls back to Gemini for graph generation
  - `LinkerAgent`: Falls back to simple relationship extraction
  - `SummarizerAgent`: Falls back to Gemini for summaries
  - `main.py`: `/api/generate` endpoint falls back to Gemini

### 2. Infrastructure Changes

- ✅ Commented out Gemma service in `terraform/cloud_run.tf`
- ✅ Removed `GEMMA_SERVICE_URL` from backend environment variables
- ✅ Removed `gemma` from CI/CD build matrix

### 3. Import Updates

- ✅ Changed all `from services.gemma_service` to `from services.gemma_client`
- ✅ Updated error handling to catch `RuntimeError` when Gemma unavailable

## Test Cases

### Test 1: Gemma Client Without URL

```python
import os
os.environ.pop('GEMMA_SERVICE_URL', None)
from services.gemma_client import get_gemma_client

client = get_gemma_client()
assert client is None  # Should return None
```

### Test 2: Agents Import Successfully

```python
from agents.visualizer_agent import VisualizerAgent
from agents.linker_agent import LinkerAgent
from agents.summarizer_agent import SummarizerAgent
# All should import without errors
```

### Test 3: RuntimeError When Gemma Unavailable

```python
import os
os.environ.pop('GEMMA_SERVICE_URL', None)
from services.gemma_client import reason_with_gemma

try:
    await reason_with_gemma(prompt="test", max_tokens=10)
except RuntimeError as e:
    assert "not available" in str(e).lower()
```

### Test 4: Backend Starts Without Gemma

```bash
# Ensure GEMMA_SERVICE_URL is not set
unset GEMMA_SERVICE_URL

# Start backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8080

# Should start successfully without errors
```

### Test 5: Health Check Endpoint

```bash
curl http://localhost:8080/healthz
# Should return 200 OK even without Gemma service
```

### Test 6: API Endpoints Work

```bash
# Test /api/generate (should fallback to Gemini)
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_tokens": 10}'

# Should work (may need GEMINI_API_KEY set)
```

## Manual Testing Steps

1. **Set Up Environment:**

   ```bash
   cd backend
   # Ensure GEMMA_SERVICE_URL is NOT set
   unset GEMMA_SERVICE_URL
   ```

2. **Run Test Script:**

   ```bash
   python3 test_gemma_rollback.py
   ```

3. **Start Backend Locally:**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Verify Health Check:**

   ```bash
   curl http://localhost:8080/healthz
   ```

5. **Test Agent Functionality:**
   - Upload a document via the UI
   - Verify agents process without Gemma errors
   - Check logs for "Gemma service unavailable" messages (expected)

## Expected Behavior

### ✅ Should Work:

- Backend starts without `GEMMA_SERVICE_URL`
- All agents import successfully
- Health check endpoint returns 200 OK
- Agents fallback to Gemini when Gemma unavailable
- No startup timeout errors

### ⚠️ Expected Log Messages:

- "GEMMA_SERVICE_URL not configured, Gemma service unavailable"
- "Gemma service unavailable, using Gemini"
- "Falling back to simple relationship extraction"

### ❌ Should NOT Happen:

- Import errors
- Startup failures
- Timeout errors related to Gemma service
- 503 errors when Gemma unavailable (should fallback to Gemini)

## Verification Checklist

- [ ] `get_gemma_client()` returns `None` when `GEMMA_SERVICE_URL` not set
- [ ] All agents import successfully
- [ ] Backend starts without errors
- [ ] Health check endpoint works
- [ ] Agents gracefully handle missing Gemma service
- [ ] Fallback to Gemini works correctly
- [ ] No import errors in logs
- [ ] No startup timeout errors

## Next Steps

After successful local testing:

1. Create feature branch
2. Commit changes
3. Create PR with label `agentnav`
4. Verify CI/CD passes (should skip Gemma builds)
5. Deploy to staging to verify Cloud Run startup
