# Issue #131 (FR#160) Investigation & Fix Plan

## Problem Summary

The CI workflow has a conflict:
1. **FR#145** (Conditional CI) causes jobs to be `skipped` when file paths don't match
2. **GitHub Branch Protection** requires status checks `CODE_QUALITY`, `SECURITY_AUDIT`, `INFRA_VERIFICATION` to **pass**
3. **Conflict:** A skipped check is neither pass nor fail → GitHub blocks the PR

## Root Cause

GitHub branch protection interprets a "skipped" status check as a failed requirement, not as a non-blocker.

## Solution Strategy

### Step 1: Create a Meta-Check Job
Create a final, unconditional job `CI_QUALITY_GATE` that:
- Runs `if: always()` (regardless of other job results)
- Checks the `conclusion` of the consolidated jobs
- Reports "success" only if all *triggered* jobs succeeded
- Reports "failure" if any *triggered* job failed

### Step 2: Update Branch Protection
- Make only `CI_QUALITY_GATE` a required check (not the individual consolidated jobs)
- This ensures a single, non-skippable gate governs PR merges

### Step 3: Handle Skipped Jobs
- When a job is skipped (due to path filtering), it won't affect the meta-check
- Only jobs that were *triggered* need to succeed

## Implementation Steps

1. Add `CI_QUALITY_GATE` job to CI workflow
2. Update GitHub branch protection ruleset
3. Test with a documentation-only PR to verify skipped jobs don't block merge

## Files to Modify

- `.github/workflows/ci.yml` - Add CI_QUALITY_GATE job
- GitHub Ruleset settings (via gh CLI or web UI)

## Success Criteria

- ✅ Documentation-only PR skips all test jobs
- ✅ PR still passes the single `CI_QUALITY_GATE` check
- ✅ PR can be merged successfully
- ✅ Code change PR still fails if tests fail

---

## Current CI Job Structure

```
├── code-quality (runs always)
├── frontend-tests (individual tests)
├── backend-tests (individual tests)
├── tfsec-scan (individual security scan)
├── osv-scanner (individual dependency scan)
├── secret-verification (individual security check)
│
├── CODE_QUALITY (depends: code-quality, frontend-tests, backend-tests)
├── SECURITY_AUDIT (depends: tfsec-scan, osv-scanner, secret-verification)
│
└── [NEW] CI_QUALITY_GATE (depends: always, checks CODE_QUALITY and SECURITY_AUDIT conclusions)
```

## Detailed Job Logic

### New `CI_QUALITY_GATE` Job

```yaml
CI_QUALITY_GATE:
  name: CI Quality Gate
  runs-on: ubuntu-latest
  if: always()
  needs: [CODE_QUALITY, SECURITY_AUDIT]
  steps:
    - name: Check consolidated job results
      run: |
        # Check if either consolidated job failed
        # If skipped, it's OK. If failed, fail this job.
```

This way:
- If a job is *skipped* (path filter), it doesn't fail the gate
- If a job is *triggered* and *failed*, the gate fails
- The gate always reports a status (never skipped)
- GitHub protection can require this single gate without conflicts
