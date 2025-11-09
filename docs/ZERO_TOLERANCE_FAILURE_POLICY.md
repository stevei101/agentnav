# Zero-Tolerance Failure Policy & Automated FR Creation

**Status:** Active Policy  
**Priority:** Highest (CI/CD Stability & Governance)  
**Timeline:** Immediate (Effective on Approval)  
**Applicable To:** All Contributors and CI/CD Failures  
**Last Updated:** 2024-11-02  
**Related Issue:** #140

---

## Table of Contents

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [Policy Statement](#policy-statement)
4. [Mandatory FR Creation Process](#mandatory-fr-creation-process)
5. [Coverage of All CI Checks](#coverage-of-all-ci-checks)
6. [FR Creation Template](#fr-creation-template)
7. [Assignment and Priority](#assignment-and-priority)
8. [Exemptions and Exceptions](#exemptions-and-exceptions)
9. [Enforcement and Accountability](#enforcement-and-accountability)
10. [Success Metrics](#success-metrics)
11. [Related Documentation](#related-documentation)

---

## Overview

The **Zero-Tolerance Failure Policy** establishes a formal governance framework for responding to GitHub Actions CI/CD failures. This policy ensures that every non-passing status check is immediately converted into a tracked, assigned Feature Request (FR) or Issue, eliminating the risk of lingering bugs, security vulnerabilities, or infrastructure errors.

### Core Principle

> **Any failed GitHub Actions status check that is not already tracked by an open, assigned issue MUST result in a new Feature Request being created immediately.**

This policy is designed to:

- **Eliminate Lingering Failures:** Prevent untracked bugs from accumulating
- **Ensure Accountability:** Assign an owner to every failure
- **Maintain CI/CD Trust:** Keep the pipeline reliable and trustworthy
- **Reduce Risk:** Address security vulnerabilities and infrastructure issues immediately

---

## The Problem

Without a formal policy for CI failure response, several critical issues arise:

### 1. Lingering Failures

- Errors are not immediately assigned, leading to stagnation in bug resolution
- Developers lose faith in CI status when failures are ignored
- Critical warnings may be bypassed or dismissed

### 2. Workflow Inconsistency

- Developers must manually decide whether to log a bug, create an issue, or notify a colleague
- No standard process for failure response
- Inconsistent documentation of failure root causes

### 3. Lost Accountability

- Without a formal issue, bugs are not assigned to an owner
- Accountability becomes impossible to track
- No deadlines or priority assignments for fixes

### 4. Risk Accumulation

- Critical checks like `Terraform Security Scan` (tfsec) and `OSV Dependency Vulnerability Scan` failures introduce genuine security or IaC risk
- Security vulnerabilities may be overlooked when not immediately tracked
- Technical debt accumulates over time

---

## Policy Statement

### Formal Mandate

**The official policy is:**

> Any failed GitHub Actions status check that is not a pre-existing, open, assigned issue **MUST** result in a new Feature Request being created **immediately** by the developer or team member who observes the failure.

### Policy Scope

This policy applies to:

- All GitHub Actions workflows in `.github/workflows/`
- All CI/CD status checks that appear on Pull Requests
- All logical job failures within workflows
- All security scans, linting, testing, and deployment checks

### Policy Lifecycle

1. **Failure Detection:** Developer observes a failed CI check
2. **Issue Search:** Developer confirms no open, assigned issue exists for this failure
3. **FR Creation:** Developer creates a new Feature Request immediately
4. **Assignment:** FR is assigned to a team member with appropriate priority
5. **Resolution:** Team member resolves the issue and closes the FR
6. **Verification:** CI check passes on subsequent runs

---

## Mandatory FR Creation Process

### Step 1: Detect Failure

When a GitHub Actions workflow fails:

1. Review the workflow run details in the **Actions** tab
2. Identify the specific job(s) that failed
3. Review the job logs to understand the failure reason

### Step 2: Search for Existing Issue

Before creating a new FR:

1. Search the repository issues for keywords related to the failure
2. Confirm that no open, assigned issue already tracks this failure
3. If an open issue exists, add a comment with the new failure details and skip FR creation

### Step 3: Create Feature Request

If no existing issue is found, create a new Feature Request:

1. Use the standard Feature Request template (`.github/feature_request_template.md`)
2. Follow the **FR Creation Template** (see below)
3. Include all required information:
   - **Title:** Specific, descriptive title (e.g., "Fix: Backend Tests (pytest) Module Resolution Error")
   - **Description:** Full failing log output, error code, and preliminary root cause analysis
   - **Priority:** Assign appropriate priority (see Priority Guidelines below)
   - **Labels:** Add relevant labels (`bug`, `ci/cd`, `security`, `critical`, etc.)

### Step 4: Assign Owner and Deadline

1. Assign the FR to a team member or yourself
2. Set a priority level (Critical, High, Medium, Low)
3. Add relevant project board if applicable
4. Set a target resolution deadline based on priority

### Step 5: Track Progress

1. Update the FR with progress as work is performed
2. Link any related PRs or commits
3. Close the FR once the CI check passes consistently
4. Document the resolution for future reference

---

## Coverage of All CI Checks

This policy applies to **ALL** GitHub Actions status checks, including but not limited to:

| Status Check / Logical Job                      | Workflow File                             | Mandatory New FR if Failing       |
| :---------------------------------------------- | :---------------------------------------- | :-------------------------------- |
| **Code Quality (Linting & Formatting)**         | `.github/workflows/ci.yml`                | ✅ Yes                            |
| **Frontend Unit Tests**                         | `.github/workflows/ci.yml`                | ✅ Yes                            |
| **Backend Tests (pytest + Firestore emulator)** | `.github/workflows/ci.yml`                | ✅ Yes                            |
| **Terraform Security Scan (tfsec)**             | `.github/workflows/ci.yml`                | ✅ Yes                            |
| **OSV Dependency Vulnerability Scan**           | `.github/workflows/ci.yml`                | ✅ Yes                            |
| **Deploy Agentnav to Cloud Run**                | `.github/workflows/deploy-cloudrun.yaml`  | ✅ Yes                            |
| **Build Gemma Debug**                           | `.github/workflows/build-gemma-debug.yml` | ✅ Yes                            |
| **Terraform Infrastructure**                    | `.github/workflows/terraform.yml`         | ✅ Yes (for syntax/plan failures) |

### Special Cases

- **Terraform Apply Failures:** If `terraform apply` fails in production, this is a **Critical** priority FR
- **Security Scan Failures:** `tfsec` and `OSV Scanner` failures must be treated as **High** or **Critical** priority
- **Build Failures:** Container build failures block deployment and must be **High** priority

---

## FR Creation Template

When creating a Feature Request for a CI failure, use the following template:

```markdown
---
name: Fix CI Failure
about: Track and resolve a GitHub Actions CI failure
title: 'Fix: [Job Name] - [Brief Description]'
labels: bug, ci/cd, critical
assignees: ''
---

## CI Failure Summary

**Failed Workflow:** [Workflow Name]
**Failed Job:** [Job Name]
**Failure Date/Time:** [YYYY-MM-DD HH:MM UTC]
**PR/Commit:** [Link to PR or commit]

## Error Description

[Paste the relevant error message or log output]
```

[Full log output or link to workflow run]

```

## Root Cause Analysis (Preliminary)

[Your initial analysis of what caused the failure]

Possible causes:
- [ ] Dependency version conflict
- [ ] Configuration error
- [ ] Code regression
- [ ] Infrastructure issue
- [ ] Security vulnerability
- [ ] Other (describe)

## Impact Assessment

**Severity:** [Critical/High/Medium/Low]

**Impact:**
- [ ] Blocks deployment
- [ ] Blocks PRs from merging
- [ ] Security risk
- [ ] Infrastructure risk
- [ ] Developer productivity impact

## Proposed Solution

[Describe your proposed fix]

## Acceptance Criteria

- [ ] CI check passes consistently
- [ ] Root cause is identified and documented
- [ ] Fix is merged to main branch
- [ ] Similar failures are prevented (if applicable)

## Related Issues/PRs

- Related to: [Link to related issues]
- Fixed by: [Link to fix PR - add after creating PR]
```

---

## Assignment and Priority

### Priority Guidelines

Assign priority based on the failure's impact:

| Priority     | Criteria                                                                                                           | Response Time             |
| :----------- | :----------------------------------------------------------------------------------------------------------------- | :------------------------ |
| **Critical** | • Blocks all deployments<br>• Security vulnerability (High/Critical)<br>• Production outage<br>• Data loss risk    | Immediate (within 1 hour) |
| **High**     | • Blocks PRs from merging<br>• Security vulnerability (Medium)<br>• Build failures<br>• Test infrastructure broken | Within 4 hours            |
| **Medium**   | • Intermittent test failures<br>• Linting/formatting issues<br>• Non-blocking warnings                             | Within 1 day              |
| **Low**      | • Documentation issues<br>• Non-critical warnings<br>• Optimization opportunities                                  | Within 1 week             |

### Assignment Guidelines

1. **Self-Assignment:** If you caused the failure or are best positioned to fix it, assign to yourself
2. **Team Assignment:** If unsure, assign to the team lead or maintainer
3. **Escalation:** If no owner is available, escalate in team chat/Slack

---

## Exemptions and Exceptions

### When NOT to Create an FR

1. **Existing Open Issue:** If an open, assigned issue already tracks this failure, add a comment instead
2. **Known Transient Failure:** If the failure is a known, documented transient issue (e.g., network timeout), add a comment to the existing tracking issue
3. **Duplicate Failure:** If the same failure is already tracked in another FR, link to it instead

### Temporary Bypass (Emergency Only)

In rare emergency situations (e.g., production outage requiring immediate hotfix):

1. A temporary bypass of failing checks may be granted by a maintainer
2. An FR **MUST** still be created to track the failure
3. The FR must be labeled `urgent` and `bypass-granted`
4. The failure must be resolved within 24 hours

---

## Enforcement and Accountability

### Developer Responsibility

Every developer is responsible for:

1. Monitoring CI checks on their PRs
2. Creating FRs for any failures they encounter
3. Assigning appropriate priority and owner
4. Following up on FRs assigned to them

### Reviewer Responsibility

Code reviewers must:

1. Verify that all CI checks pass before approving PRs
2. Ensure any failing checks have associated FRs
3. Confirm that FRs are properly assigned and prioritized

### Maintainer Responsibility

Maintainers must:

1. Audit the issue tracker regularly for untracked failures
2. Enforce this policy during PR reviews
3. Update this policy as CI checks evolve

---

## Success Metrics

### Policy Success Criteria

- [ ] **Zero Untracked Failures:** All failing CI checks have corresponding, assigned FRs
- [ ] **Fast Response Time:** 100% of Critical failures have FRs created within 1 hour
- [ ] **High Resolution Rate:** 90% of High priority failures resolved within 24 hours
- [ ] **CI Trust Maintained:** Developers trust CI status and do not bypass checks

### Monitoring

Track the following metrics monthly:

- Number of CI failures
- Number of FRs created for CI failures
- Average time from failure to FR creation
- Average time from FR creation to resolution
- Number of untracked failures (target: 0)

---

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [docs/CONTRIBUTION_GUIDE_PR_DISCIPLINE.md](CONTRIBUTION_GUIDE_PR_DISCIPLINE.md) - PR best practices
- [docs/SYSTEM_INSTRUCTION.md](SYSTEM_INSTRUCTION.md) - System architecture and guidelines
- [.github/workflows/](../.github/workflows/) - GitHub Actions workflows
- [.github/feature_request_template.md](../.github/feature_request_template.md) - Feature Request template

---

## Revision History

| Date       | Version | Description                          |
| :--------- | :------ | :----------------------------------- |
| 2024-11-02 | 1.0     | Initial policy creation (Issue #140) |

---

## FAQ

### Q: What if I don't know who should fix the failure?

**A:** Create the FR and assign it to the team lead or maintainer. They will reassign to the appropriate owner.

### Q: What if the failure is intermittent and I can't reproduce it?

**A:** Create the FR anyway and document that it's intermittent. Include:

- Frequency of failure
- Steps to reproduce (if known)
- Any patterns observed

### Q: What if the failure is in a third-party dependency?

**A:** Create the FR and document:

- The third-party dependency
- The version causing the issue
- Any known workarounds
- Link to upstream issue (if available)

### Q: Can I create one FR for multiple related failures?

**A:** Only if the failures have the same root cause and can be fixed together. If unsure, create separate FRs.

### Q: What if the CI check is flaky and passes on retry?

**A:** Create an FR labeled `flaky-test` to track the instability. Flaky tests erode CI trust and must be fixed.

---

**This policy is mandatory for all contributors and maintainers. Compliance ensures the reliability, security, and trustworthiness of the Agentic Navigator CI/CD pipeline.**
