# FR#165 Cloud Run Startup Bug - Investigation Report

**Issue:** #132 - FR#165  
**Branch:** fix/fr165-cloud-run-startup  
**Date:** November 3, 2025

---

## 🔍 Root Cause Analysis

### Issue Identified: ✅ FOUND

The problem is in **both Dockerfiles** using an inefficient and error-prone startup method:

```dockerfile
# ❌ CURRENT (PROBLEMATIC)
CMD python -c "import os; port = int(os.getenv('PORT', 8080)); import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=port, log_level='info')"
```

**Problems with this approach:**
1. **Complex shell command** - Hard to parse, shell interpretation issues
2. **Error handling issues** - If PORT env var is missing or malformed, silently defaults
3. **Logging issues** - Output from this command may not be captured correctly by Cloud Run
4. **Signal handling** - SIGTERM not handled properly for graceful shutdown
5. **Debugging difficulty** - Hard to troubleshoot startup failures

### Root Cause: 

The indirect startup method combined with Cloud Run's timeout may cause:
- Connection refused errors (not binding to 0.0.0.0)
- Startup timeout (Cloud Run kills container before uvicorn starts)
- Logging issues (error messages not reaching Cloud Run logs)

### Solution: 

Replace `python -c` with direct entry point script that:
1. Explicitly binds to `0.0.0.0`
2. Reads `PORT` environment variable with proper error handling
3. Handles SIGTERM for graceful shutdown
4. Has clear logging
5. Is testable and debuggable

---

## 📋 Files Affected

### 1. backend/Dockerfile
- **Current:** Uses `python -c` with inline uvicorn command
- **Fix:** Create `backend/entrypoint.sh` script
- **Impact:** Backend service startup reliability

### 2. backend/Dockerfile.gemma
- **Current:** Uses `python -c` with inline uvicorn command
- **Fix:** Create `backend/gemma_service/entrypoint.sh` script
- **Impact:** Gemma GPU service startup reliability + model loading

### 3. terraform/cloud_run.tf (Optional)
- **Current:** Timeout is 300s (sufficient)
- **Review:** Add startup probe configuration if needed

---

## 🔧 Fix Strategy

### Fix 1: Create Backend Entrypoint Script

**File:** `backend/entrypoint.sh`

```bash
#!/bin/bash
set -e

# Get PORT from environment, default to 8080
PORT=${PORT:-8080}

# Validate PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT must be a valid number, got: $PORT"
    exit 1
fi

echo "Starting Agentic Navigator Backend..."
echo "  Host: 0.0.0.0"
echo "  Port: $PORT"

# Run uvicorn with proper signal handling
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --access-log
```

### Fix 2: Update Backend Dockerfile

**File:** `backend/Dockerfile`

```dockerfile
# Change FROM:
CMD python -c "import os; port = int(os.getenv('PORT', 8080)); import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=port, log_level='info')"

# TO:
# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
```

### Fix 3: Create Gemma Entrypoint Script

**File:** `backend/gemma_service/entrypoint.sh`

```bash
#!/bin/bash
set -e

# Get PORT from environment, default to 8080
PORT=${PORT:-8080}

# Validate PORT is a number
if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: PORT must be a valid number, got: $PORT"
    exit 1
fi

echo "Starting Gemma GPU Service..."
echo "  Host: 0.0.0.0"
echo "  Port: $PORT"
echo "  Model: ${MODEL_NAME:-google/gemma-7b-it}"

# Run uvicorn with proper signal handling
exec uvicorn gemma_service.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --access-log
```

### Fix 4: Update Gemma Dockerfile

**File:** `backend/Dockerfile.gemma`

```dockerfile
# Change FROM:
CMD python -c "import os; port = int(os.getenv('PORT', 8080)); import uvicorn; uvicorn.run('gemma_service.main:app', host='0.0.0.0', port=port)"

# TO:
# Copy entrypoint script
COPY gemma_service/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Use entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
```

---

## ✅ Verification Checklist

- [ ] Created `backend/entrypoint.sh`
- [ ] Updated `backend/Dockerfile` to use entrypoint
- [ ] Created `backend/gemma_service/entrypoint.sh`
- [ ] Updated `backend/Dockerfile.gemma` to use entrypoint
- [ ] Test locally: `PORT=8080 bash backend/entrypoint.sh`
- [ ] Verify scripts are executable: `ls -la backend/entrypoint.sh`
- [ ] Run CI checks: `make ci`
- [ ] Create PR with fixes
- [ ] Monitor Cloud Run deployment after merge

---

## 🧪 Local Testing

```bash
# Test backend entrypoint
cd /workspaces/agentnav/backend
PORT=8080 bash entrypoint.sh

# In another terminal, verify it's listening
netstat -an | grep 8080
# Should show: 0.0.0.0:8080

# Test with different port
PORT=9000 bash entrypoint.sh

# Test invalid port (should fail gracefully)
PORT=abc bash entrypoint.sh
# Should output: ERROR: PORT must be a valid number, got: abc
```

---

## 📚 References

- **SYSTEM_INSTRUCTION.md:** Cloud Run configuration requirements
- **GPU_SETUP_GUIDE.md:** Gemma service startup requirements
- **Docker Best Practices:** Entrypoint scripts for signal handling

---

**Status:** Investigation Complete → Ready for Implementation
