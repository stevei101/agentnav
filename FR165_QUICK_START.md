# Quick Start: Issue #132 - FR#165 Cloud Run Startup Bug

**Issue:** https://github.com/stevei101/agentnav/issues/132  
**Status:** 🔥 CRITICAL - Blocks all deployments  
**Effort:** 3 Days  
**Created:** 2025-11-03

---

## 🔍 Problem Statement

Cloud Run deployment fails with:

```
The user-provided container failed to start and listen on the port
defined provided by the PORT=8080 environment variable within the
allocated timeout
```

**Two possible root causes:**

1. **Code Binding Issue:** FastAPI/Uvicorn not respecting `0.0.0.0` and `$PORT`
2. **Timeout Issue:** Gemma GPU service takes too long to load model

---

## 🎯 Investigation Plan

### Step 1: Check Backend Dockerfile (5 min)

```bash
# View the Backend Dockerfile
cat /workspaces/agentnav/backend/Dockerfile

# Look for the CMD instruction - should be:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
# OR similar Python code that reads the PORT env var
```

**What to check:**

- [ ] Is the host `0.0.0.0`? (NOT `127.0.0.1` or `localhost`)
- [ ] Is the port reading `$PORT` env var? (default 8080)
- [ ] Is the command using the correct syntax?

### Step 2: Check Gemma Dockerfile (5 min)

```bash
# View the Gemma Dockerfile
cat /workspaces/agentnav/backend/Dockerfile.gemma

# Look for similar CMD instruction
```

**What to check:**

- [ ] Same host/port requirements
- [ ] Model loading timeout configuration

### Step 3: Check backend/main.py (10 min)

```bash
# Check if main.py is reading PORT env var
grep -n "PORT\|0\.0\.0\.0\|host\|port" /workspaces/agentnav/backend/main.py | head -20
```

**What to check:**

- [ ] Is uvicorn configured with `host="0.0.0.0"`?
- [ ] Is it reading `os.getenv("PORT", "8080")`?
- [ ] Example from SYSTEM_INSTRUCTION.md:
  ```python
  PORT = int(os.getenv("PORT", 8080))
  uvicorn.run(app, host="0.0.0.0", port=PORT)
  ```

### Step 4: Check Terraform Configuration (10 min)

```bash
# Check terraform/cloud_run.tf for startup timeout
grep -n "startup_timeout\|timeout\|PORT" /workspaces/agentnav/terraform/cloud_run.tf | head -20

# Check for Gemma service configuration
grep -A 20 "gemma" /workspaces/agentnav/terraform/cloud_run.tf | head -30
```

**What to check:**

- [ ] Backend service: Normal timeout (240s default usually OK)
- [ ] Gemma service: Extended timeout (300s for model loading)?
- [ ] Both services expose PORT via environment variable?

### Step 5: Review System Instruction Requirements (10 min)

From `docs/SYSTEM_INSTRUCTION.md`:

```bash
grep -A 20 "Backend Service Configuration" /workspaces/agentnav/docs/SYSTEM_INSTRUCTION.md
grep -A 20 "Gemma GPU Service Configuration" /workspaces/agentnav/docs/SYSTEM_INSTRUCTION.md
```

**Key requirements:**

- Backend: `PORT` env var, `host="0.0.0.0"`, timeout 300s
- Gemma: `PORT` env var, `host="0.0.0.0"`, timeout 300s, startup timeout 300s

---

## 🔧 Fix Strategy

### If Code Binding is the Issue:

**Backend (backend/main.py):**

```python
# WRONG ❌
uvicorn.run(app, port=8080)  # Defaults to 127.0.0.1!

# RIGHT ✅
PORT = int(os.getenv("PORT", 8080))
uvicorn.run(app, host="0.0.0.0", port=PORT)
```

**Gemma Service (backend/gemma_service/main.py or similar):**

```python
# WRONG ❌
uvicorn.run(app, port=8080)

# RIGHT ✅
PORT = int(os.getenv("PORT", 8080))
uvicorn.run(app, host="0.0.0.0", port=PORT)
```

### If Timeout is the Issue:

**Dockerfile.gemma:**

```dockerfile
# Add or increase startup timeout in gcloud deploy command
# Or via Terraform:
# startup_probe {
#   timeout_seconds = 300
#   failure_threshold = 3
# }
```

**Terraform (terraform/cloud_run.tf):**

```hcl
# For Gemma service:
timeout_seconds = 300  # Max allowed for startup

# Add if missing:
startup_probe {
  timeout_seconds = 300
  failure_threshold = 3
}
```

---

## 📋 Implementation Checklist

### Phase 1: Diagnosis (1 day)

- [ ] Read Issue #132 completely
- [ ] Check all Dockerfiles for host binding
- [ ] Check main.py and entry points
- [ ] Review Terraform timeout config
- [ ] Examine Cloud Logging for actual error
  ```bash
  gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" \
    --limit 10 --format json | jq '.[] | .textPayload'
  ```

### Phase 2: Fix (1-2 days)

**Option A: If code binding issue**

- [ ] Update backend/main.py to bind to `0.0.0.0`
- [ ] Update backend/gemma_service/main.py (if exists)
- [ ] Test locally: `python backend/main.py`
- [ ] Rebuild Dockerfiles
- [ ] Test with local Podman if possible

**Option B: If timeout issue**

- [ ] Update Terraform startup probe timeout to 300s
- [ ] Add startup probe if missing
- [ ] Run `terraform plan` to verify
- [ ] Test in staging if possible

### Phase 3: Validation (1 day)

- [ ] Create fix branch: `git checkout -b fix/fr165-cloud-run-startup`
- [ ] Make changes
- [ ] Test locally if possible
- [ ] Run CI/CD checks: `make ci`
- [ ] Push and create PR: `git push origin fix/fr165-cloud-run-startup`
- [ ] Monitor deployment after merge

---

## 🧪 Local Testing

Before deploying, test locally:

```bash
# Test Backend
cd /workspaces/agentnav/backend

# Set PORT and run
PORT=8080 python main.py

# In another terminal, verify it listens on 0.0.0.0:8080
netstat -an | grep 8080

# Should show: 0.0.0.0:8080 (not 127.0.0.1:8080)
```

---

## 📚 Reference Files

**Key files to review:**

- `backend/main.py` - Check uvicorn configuration
- `backend/Dockerfile` - Check CMD instruction
- `backend/Dockerfile.gemma` - Check Gemma CMD
- `terraform/cloud_run.tf` - Check timeout and probe config
- `docs/SYSTEM_INSTRUCTION.md` - Cloud Run configuration section
- `docs/GPU_SETUP_GUIDE.md` - GPU startup requirements

---

## ✅ Success Criteria

- [ ] Backend service successfully starts on Cloud Run
- [ ] Gemma service successfully starts on Cloud Run
- [ ] Both services respond to health check endpoint: `/healthz`
- [ ] Cloud Logging shows service as "Ready" (not "Failed")
- [ ] Tests pass: `make ci`

---

## 🚀 Quick Commands

```bash
# Start investigation
cd /workspaces/agentnav
git checkout -b fix/fr165-cloud-run-startup

# Check current code
cat backend/main.py | grep -A 10 "if __name__"
cat backend/Dockerfile | grep CMD

# View issue details
gh issue view 132

# When ready to commit
git add .
git commit -m "fix: FR#165 - Cloud Run container startup (0.0.0.0 binding + timeout)"
git push origin fix/fr165-cloud-run-startup

# Create PR
gh pr create --title "Fix: FR#165 Cloud Run Startup Bug" \
  --body "Fixes #132\n\nResolves container startup timeout by...\n- Binding to 0.0.0.0\n- Reading PORT env var\n- Extending startup timeout to 300s"
```

---

## 📞 Need Help?

If stuck:

1. Check `docs/SYSTEM_INSTRUCTION.md` for requirements
2. Review `docs/GPU_SETUP_GUIDE.md` for Gemma timeouts
3. Look at Cloud Logging output for specific error
4. Compare with working services (if any)

---

**Ready to start? Run this:**

```bash
cd /workspaces/agentnav && git checkout -b fix/fr165-cloud-run-startup
```

Good luck! 🚀
