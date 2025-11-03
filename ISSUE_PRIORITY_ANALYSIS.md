# Open Issues Priority Analysis - November 3, 2025

## Current Context
- ✅ FR#090 (Model Selection) - COMPLETE - PR #136 ready for review
- ✅ Issue #132 (FR#165) - COMPLETE - PR #146 created  
- ✅ PR #145 (FR#095) - Security fixes applied
- ✅ PRs #146, #147, #148 created for Issue #132 (multiple approaches)

## Analysis of Top 5 Open Issues

### 1. Issue #142 - FR#190: Custom Domain Connectivity & TLS Setup
**Priority:** Crisis Level (Blocking Production Domain)
**Blocker:** Custom domain `agentnav.lornu.com` is not resolving
**Impact:** Production endpoint completely inaccessible
**Effort:** 3 days
**Status:** BLOCKING - Highest priority
**Recommended Action:** Start immediately after PRs #146, #145 are merged

### 2. Issue #131 - FR#160: Resolve Skipped CI Checks  
**Priority:** HIGH (Operational Risk)
**Problem:** CI quality checks not running properly
**Checks Affected:** CODE_QUALITY, SECURITY_AUDIT, INFRA_VERIFICATION
**Impact:** Deployment safety issues
**Effort:** 1-2 days
**Recommended Action:** Start after #142 or parallel with it

### 3. Issue #137 - FR#175: Cloud Run Deployment Optimization
**Priority:** HIGH (Operational Efficiency)
**Problem:** Deployment strategy not aligned with Google best practices
**Tasks:**
  - Refactor Backend Dockerfile (multi-stage builds)
  - Optimize Uvicorn startup
  - Review CI/CD gcloud commands
  - Add security headers
**Effort:** 1 week
**Recommended Action:** Start after Issue #132 is stable

### 4. Issue #117 - FR#145: Intelligent Conditional CI Execution
**Priority:** MEDIUM-HIGH (Developer Velocity)
**Problem:** Full CI runs on every PR (even doc changes)
**Solution:** Use path filtering to skip irrelevant tests
**Benefits:** 30-40% CI time reduction
**Effort:** 2-3 days
**Can Parallelize:** YES - independent of other issues
**Recommended Action:** Good mid-priority task

### 5. Issue #139 - FR#130: Custom Copilot Agent Integration
**Priority:** MEDIUM-HIGH (Developer Experience)
**Problem:** No context-aware AI assistant for project conventions
**Solution:** Create agentnav-copilot-agent with System Instruction
**Benefits:** Better DX, faster onboarding, enforces standards
**Effort:** 3 days
**Can Parallelize:** YES - independent of other issues
**Recommended Action:** Good medium-priority task

---

## Recommended Workflow

**Immediate (Now):**
1. ✅ Ensure PR #146, #145 are merged
2. ✅ Check if PR #147, #148 need review/merge

**This Session (Highest Value):**
1. **Issue #131 (FR#160)** - Quick win, resolves operational risk
   - Time: 1-2 days
   - Impact: HIGH (fixes CI checks)
   - Can start: Immediately

**Next Session:**
2. **Issue #142 (FR#190)** - Crisis level but needs GCP domain access
   - Time: 3 days
   - Impact: CRITICAL (unblocks production)
   - Prerequisite: May need access to domain registrar, GCP DNS

3. **Issue #137 (FR#175)** - Deployment optimization
   - Time: 1 week  
   - Impact: HIGH (stability + efficiency)
   - Prerequisite: Issue #132 must be stable

**Parallel Work (Can start anytime):**
- Issue #117 (CI path filtering) - Good for CI improvements
- Issue #139 (Copilot agent) - Good for DX improvements

---

## Recommendation: Start with Issue #131 (FR#160)

**Why Issue #131?**
1. ✅ **Quick win** (1-2 days vs 3-7 days for others)
2. ✅ **No external dependencies** (GCP domain access, production verification)
3. ✅ **High impact** (fixes critical CI checks)
4. ✅ **Self-contained** (GitHub Actions workflow only)
5. ✅ **Reduces risk** (ensures deployment safety)

**Next Priority: Issue #142 (FR#190)**
- Custom domain not resolving (production blocker)
- Requires verification in GCP console + Terraform changes
- Should be done after Issue #131 CI is stable

