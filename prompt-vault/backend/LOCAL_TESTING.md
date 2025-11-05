# Local Testing Guide for Prompt Vault Backend

This guide helps you test the Prompt Vault backend locally before deploying to Cloud Run.

## Prerequisites

1. **Python 3.11+** installed
2. **GEMINI_API_KEY** environment variable set (required)
3. **SUPABASE_URL** and **SUPABASE_SERVICE_KEY** (optional, for full Supabase integration)
4. **FIRESTORE_PROJECT_ID** (optional, for Firestore integration)

## Quick Start

### Option 1: Automated Testing Script

Run the comprehensive test script:

```bash
cd prompt-vault/backend
export GEMINI_API_KEY="your-gemini-api-key"
export SUPABASE_URL="your-supabase-url"  # Optional
export SUPABASE_SERVICE_KEY="your-service-key"  # Optional
export FIRESTORE_PROJECT_ID="your-gcp-project-id"  # Optional

./test_local.sh
```

This script will:
- ✅ Check Python version
- ✅ Create/activate virtual environment
- ✅ Install dependencies
- ✅ Validate environment variables
- ✅ Run all unit tests
- ✅ Test Suggestion Agent directly
- ✅ Start server and test endpoints
- ✅ Clean up and report results

### Option 2: Manual Testing

#### Step 1: Set Up Environment

```bash
cd prompt-vault/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-gemini-api-key"
export SUPABASE_URL="your-supabase-url"  # Optional
export SUPABASE_SERVICE_KEY="your-service-key"  # Optional
export FIRESTORE_PROJECT_ID="your-gcp-project-id"  # Optional
```

#### Step 2: Run Unit Tests

```bash
pytest tests/ -v
```

Expected output:
- ✅ All health endpoint tests pass
- ✅ All config tests pass
- ✅ All agent API tests pass

#### Step 3: Test Suggestion Agent

```bash
python3 test_suggestion_agent.py
```

This will test:
- ✅ Prompt analysis (optimization, structured output, function calling)
- ✅ Prompt generation from requirements

#### Step 4: Start the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

The server will start on `http://localhost:8080`

#### Step 5: Test API Endpoints

##### Health Checks

```bash
# Root endpoint
curl http://localhost:8080/

# Basic health
curl http://localhost:8080/health

# Cloud Run health check
curl http://localhost:8080/healthz

# Detailed health
curl http://localhost:8080/health/detailed
```

##### Analyze Endpoint (Issue #200)

```bash
# Analyze with prompt text
curl -X POST http://localhost:8080/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_text": "Write a function that sorts a list of numbers."
  }'
```

Expected response:
```json
{
  "success": true,
  "workflow_id": "uuid",
  "workflow_type": "analyze",
  "result": {
    "success": true,
    "suggestions": {
      "optimization_suggestions": [...],
      "structured_output": {...},
      "function_calling": {...},
      "assessment": {...}
    },
    "analysis": {...}
  }
}
```

##### Suggest Endpoint

```bash
curl -X POST http://localhost:8080/api/agents/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {
      "purpose": "Code review assistant",
      "target_model": "gemini-pro",
      "constraints": ["Must output JSON"],
      "examples": []
    },
    "options": {
      "num_suggestions": 3
    }
  }'
```

##### Other Endpoints (Phase 1 - Skeleton)

These endpoints are implemented but agents are not fully functional yet:

```bash
# Optimize (skeleton)
curl -X POST http://localhost:8080/api/agents/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "test-prompt-id",
    "options": {}
  }'

# Test (skeleton)
curl -X POST http://localhost:8080/api/agents/test \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "test-prompt-id",
    "scenarios": [],
    "options": {}
  }'

# Compare (skeleton)
curl -X POST http://localhost:8080/api/agents/compare \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "test-prompt-id",
    "version_ids": []
  }'
```

## Testing Checklist

Before deploying to Cloud Run, verify:

### Core Functionality
- [ ] Unit tests pass (100% pass rate)
- [ ] Suggestion Agent works with Gemini API
- [ ] Server starts without errors
- [ ] All health endpoints respond correctly
- [ ] Analyze endpoint returns valid suggestions
- [ ] Suggest endpoint generates prompts

### Error Handling
- [ ] Missing GEMINI_API_KEY shows appropriate warning
- [ ] Invalid API requests return proper error codes
- [ ] Server handles missing optional services gracefully (Supabase, Firestore)

### Configuration
- [ ] Environment variables are read correctly
- [ ] Default values are used when env vars are missing
- [ ] CORS is configured for frontend origins
- [ ] PORT is configurable (for Cloud Run)

### Logging
- [ ] Startup logs show configuration status
- [ ] Errors are logged with stack traces (in debug mode)
- [ ] Request timing headers are included

## Troubleshooting

### "GEMINI_API_KEY not set" warning

**Solution:** Export the API key:
```bash
export GEMINI_API_KEY="your-key"
```

### "Firestore not available" messages

**This is expected** if `FIRESTORE_PROJECT_ID` is not set. The app will work without Firestore for basic functionality.

### "Supabase operations will fail" warning

**This is expected** if Supabase credentials are not set. The app will work for endpoints that don't require Supabase.

### Port already in use

**Solution:** Use a different port:
```bash
export PORT=8081
uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload
```

### Import errors

**Solution:** Make sure you're in the virtual environment and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Gemini API errors

**Check:**
1. API key is valid and has quota remaining
2. Model name is correct (`gemini-2.0-flash` or `gemini-pro`)
3. Network connectivity to Google APIs

## Next Steps After Local Testing

Once all local tests pass:

1. **Commit and push changes:**
   ```bash
   git add .
   git commit -m "feat: Prompt Vault Backend Phase 1 - Ready for deployment"
   git push origin feat/prompt-vault-backend-phase1
   ```

2. **Create/update PR** targeting `main-promptvault`

3. **Verify CI/CD pipeline** passes:
   - Build succeeds
   - Tests pass
   - Docker image builds
   - Security scans pass

4. **Deploy to Cloud Run** (automated via GitHub Actions on merge)

5. **Verify deployment:**
   - Check Cloud Run service health
   - Test production endpoints
   - Verify environment variables and secrets are set

## Related Documentation

- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Detailed testing guide for Suggestion Agent
- [README.md](./README.md) - Backend overview and setup
- [PHASE1_COMPLETE.md](./PHASE1_COMPLETE.md) - Phase 1 implementation summary

