# Open Issues Analysis & Prioritization

**Analysis Date:** November 3, 2025  
**Total Open Issues:** 18  
**Last Updated:** Real-time from GitHub

---

## 🎯 Issue Priority Matrix

### 🔥 CRITICAL (Blocking Deployment)

#### **Issue #132 - FR#165: Critical Bugfix: Cloud Run Container Startup Timeout**

**Status:** Not Started  
**Priority:** Crisis Level  
**Effort:** 3 Days  
**Impact:** Blocks all production/staging deployments

**Problem:**
Container fails to start on Cloud Run with error:
> "The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout"

**Root Causes (Pick One or Both):**
1. **Code Binding Issue:** FastAPI/Uvicorn not binding to `0.0.0.0` or reading `$PORT` environment variable (defaulting to `127.0.0.1`)
2. **Timeout Issue:** Gemma GPU Service takes too long to load model (>240s), exceeding startup timeout

**Action Items:**
- [ ] Audit Uvicorn CMD in Backend/Gemma Dockerfiles
- [ ] Verify: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}`
- [ ] Check Cloud Run startup timeout (extend to 300s if needed)
- [ ] Review Terraform deployment configuration
- [ ] Test successful deployment

**Why This Matters:** This single bug blocks deployment of critical components (Backend, Gemma Service). Everything stops here.

---

### 🟠 HIGH PRIORITY (Quality/Deployment)

#### **Issue #131 - FR#160: Critical Bugfix: Resolve Skipped Checks**

**Status:** Not Started  
**Priority:** High (Quality Gate)  
**Effort:** 1-2 Days  
**Impact:** Compromises code quality standards

**Problem:**
Some CI/CD quality checks are being skipped, allowing non-compliant code to merge.

**Likely Causes:**
- Workflow condition logic broken
- GitHub Actions syntax error
- Missing required checks in branch protection

**Action Items:**
- [ ] Review `.github/workflows/*.yml` for conditional skip logic
- [ ] Check branch protection settings for required checks
- [ ] Verify all 3 primary checks running: CODE_QUALITY, SECURITY_AUDIT, INFRA_VERIFICATION
- [ ] Add logging to confirm check execution

**Why This Matters:** Code quality gates are your first line of defense. If they're skipped, bad code gets through.

---

#### **Issue #137 - FR#175: Cloud Run Deployment Optimization & Best Practices**

**Status:** Not Started  
**Priority:** High (Operational)  
**Effort:** 1 Week  
**Impact:** Improves deployment efficiency & stability

**Problem:**
Current deployment strategy (Dockerfiles, Uvicorn config, CI/CD steps) may not follow latest Google Cloud Run best practices from official codelab.

**Tasks:**
1. **Backend Dockerfile Refactoring**
   - Review for multi-stage build optimization
   - Verify base image selection
   - Ensure `uv` dependency installation is optimal

2. **FastAPI/Uvicorn Optimization**
   - Review startup command
   - Validate host binding and port reading
   - Optimize worker count and concurrency

3. **CI/CD Workflow Review**
   - Check `gcloud run deploy` command syntax
   - Verify Google Artifact Registry (GAR) integration
   - Modernize Docker build steps

4. **Security Headers Audit**
   - Check CORS configuration
   - Review HSTS headers
   - Validate authentication headers

**Why This Matters:** Running on outdated patterns = slower deployments, worse stability, missed security/performance optimizations.

**Blocks:** Issue #137 should be done AFTER #132 is fixed (can't optimize before it works).

---

### 💡 MEDIUM PRIORITY (Developer Experience)

#### **Issue #139 - FR#130: DevEx - Custom Copilot Agent Integration**

**Status:** Not Started  
**Priority:** Medium (Developer Experience)  
**Effort:** 3 Days  
**Impact:** Accelerates development & ensures compliance

**Problem:**
Developers must constantly cross-reference System Instruction, Terraform, and CI/CD to follow conventions. No single source of truth for:
- 70% test coverage requirement
- Cloud Run conventions (`0.0.0.0` binding, PORT env var)
- ADK/A2A patterns
- Preferred tooling (uv, bun, WIF)

**Solution:**
Create `agentnav-copilot-agent` - a custom Copilot Agent loaded with the full System Instruction.

**Responsibilities:**
- Generate code adhering to project conventions
- Review PRs for Cloud Run readiness
- Provide architectural guidance
- Enforce tooling requirements (uv > pip, bun > npm)

**Success Criteria:**
- [ ] Agent created and functional
- [ ] Correctly identifies GEMMA_SERVICE_URL as env variable
- [ ] Quotes 70% test coverage when asked about testing

**Why This Matters:** This is a force multiplier for the entire team. Every developer gets instant access to project knowledge.

**Blocks:** None (nice-to-have after critical issues)

---

#### **Issue #117 - FR#145: Intelligent Conditional CI Execution**

**Status:** Not Started  
**Priority:** Medium (CI/CD Optimization)  
**Effort:** 2-3 Days  
**Impact:** Reduces CI/CD runtime, faster feedback

**Problem:**
CI/CD runs all tests regardless of what changed:
- If only backend files changed, frontend tests still run
- If only frontend changed, backend tests still run
- Wastes compute time and slows feedback loop

**Solution:**
Implement conditional test execution based on changed files:
- Frontend tests: only if `frontend/`, `package.json`, or `vitest.config.ts` changed
- Backend tests: only if `backend/`, `requirements.txt`, or `pyproject.toml` changed
- Terraform tests: only if `terraform/` changed

**GitHub Actions Approach:**
```yaml
- name: Determine Changed Files
  uses: dorny/paths-filter@v2
  id: changes
  with:
    filters: |
      frontend:
        - 'frontend/**'
        - 'package.json'
      backend:
        - 'backend/**'
        - 'requirements.txt'
      terraform:
        - 'terraform/**'

- name: Run Frontend Tests
  if: steps.changes.outputs.frontend == 'true'
  run: ...
```

**Why This Matters:** Faster CI/CD = faster developer feedback = faster development velocity.

---

### ✅ READY TO START

#### Summary Table

| Issue | Title | Status | Priority | Effort | Blocks | Why Pick It |
|-------|-------|--------|----------|--------|--------|------------|
| **#132** | **Cloud Run Startup Bug** | 🔴 Blocked | CRITICAL | 3 days | Everything | Must fix before ANY deployment |
| **#131** | **Skipped CI Checks** | 🟡 Ready | HIGH | 1-2 days | #132 | Fix quality gates, then proceed |
| **#137** | **Deployment Optimization** | 🟡 Ready | HIGH | 1 week | None | Only after #132 works |
| **#139** | **Copilot Agent** | ✅ Ready | MEDIUM | 3 days | None | Developer experience multiplier |
| **#117** | **Conditional CI** | ✅ Ready | MEDIUM | 2-3 days | None | Optimize feedback loop |

---

## 🎲 Recommended Starting Point

### **Recommendation: Start with Issue #132 (FR#165)**

**Why:**
1. **Blocking:** Nothing else matters if services won't deploy
2. **Clear:** Problem statement is specific and testable
3. **High Impact:** Unblocks all other issues
4. **Quick:** 3 days vs. weeks for other work

**Execution Path:**
```
1. Issue #132 (FR#165) - Fix Cloud Run startup
   ↓ (1-3 days)
   
2. Issue #131 (FR#160) - Verify CI checks are passing
   ↓ (1 day)
   
3. Issue #137 (FR#175) - Optimize deployment stack
   ↓ (1 week)
   
4. Issue #139 (FR#130) or #117 (FR#145) - Developer experience
   ↓ (parallel, 3 days)
```

---

## 📋 Other Open Issues (Status Only)

### Lower Priority / Blocked

| Issue | Title | Status | Notes |
|-------|-------|--------|-------|
| #115 | Test assignee visibility | Minor | Awaiting decision |
| #112 | FR#140 Zero-Tolerance Failure Policy | Ready | Low priority |
| #109 | FR#130 OSV-Scanner GitHub Action Bug | Bug | Low priority |
| #107 | FR#125 Backend Python Path | Bug | Low priority |
| #104 | FR#120 Frontend Test Dependency | Bug | Low priority |
| #79 | FR#130 Duplicate (older) | Duplicate | See #139 |
| #75 | FR#110 Advanced MLOps | Draft | Not ready |
| #73 | FR#105 Open-Source Sustainability | Planning | Lower priority |
| #70 | FR#090 Model Selection | **COMPLETED** | ✅ Handled by current PR #136 |
| #67 | FR#095 Purge .env from Git | Completed | Security fix applied |
| #64 | FR#085 ADK System Error | Resolved | Already fixed |
| #60 | FR#070 Branch Protection | Ready | Setup task |
| #41 | FR#035 YouTube Walkthrough | Ready | Content creation |

---

## 🚀 Action Plan

### Immediate Next Steps (Next 2 Hours)

1. **Pick Issue #132** ← Recommended
   - [ ] Read full issue details
   - [ ] Check current Cloud Run error logs
   - [ ] Inspect Backend and Gemma Dockerfiles
   - [ ] Verify Uvicorn command and host binding
   - [ ] Create fix branch: `fix/fr165-cloud-run-startup`

2. **Alternative:** Pick Issue #117 or #139
   - [ ] More straightforward implementation
   - [ ] Less critical but valuable
   - [ ] Good for learning the codebase

### First Week

- [ ] Fix critical issues (#132, #131)
- [ ] Optimize deployment (#137)
- [ ] Implement CI conditionals (#117)
- [ ] Start Copilot agent setup (#139)

---

## 📊 Issue Metrics

**By Priority:**
- 🔥 Critical: 1
- 🟠 High: 2
- 💡 Medium: 2
- ✅ Ready: 5
- 📌 Planning: 8

**By Type:**
- Bugs: 5
- Features: 12
- Documentation: 1

**Estimated Total Effort:** 3-4 weeks

---

**Ready to dive in? Which issue interests you?**
