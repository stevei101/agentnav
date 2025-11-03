# Contribution Guide #050: PR Discipline and Minimum Viable Commit

**Status:** Active Policy  
**Priority:** Highest (Productivity / Hygiene)  
**Timeline:** Standard PR Review  
**Applicable To:** All Pull Requests  
**Last Updated:** 2024-11-02

---

## Table of Contents

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [Minimum Viable Commit (MVC) Principles](#minimum-viable-commit-mvc-principles)
4. [File Audit Guidelines](#file-audit-guidelines)
5. [Pre-Merge Checklist](#pre-merge-checklist)
6. [How to Conduct Self-Audit](#how-to-conduct-self-audit)
7. [Acceptance Criteria for Reviewers](#acceptance-criteria-for-reviewers)
8. [Examples](#examples)

---

## Overview

As the **Agentic Navigator** repository grows, maintaining a clean, efficient, and focused codebase is paramount for achieving high developer velocity and reducing cognitive load. This guide establishes a clear, repeatable process for all contributions to prevent the introduction of unused, outdated, or unnecessary files.

**The Goal:** Every Pull Request should achieve the **Minimum Viable Commit (MVC)** — a set of files containing the changes strictly necessary to deliver the feature without breakage or bloat.

---

## The Problem

Following the initial **Repository Hygiene (FR#045)** pass, we identified several issues that must be prevented in future contributions:

### Codebase Clutter
- Pull Requests often include temporary notes, redundant files, or local IDE configuration that bloat the commit history and confuse reviewers.
- Example: `notes.md`, `scratchpad.py`, `test_temp.ts`, `FR020_COMPLETION_SUMMARY.md`

### Build Context Degradation
- Unnecessary files increase the size of the Podman build context, slowing down the CI/CD pipeline and local build times.
- Every file not excluded by `.dockerignore` is sent to the container build context.

### Conflicting Documentation
- Ad-hoc notes or temporary markdown files, if merged, quickly become outdated and contradict the authoritative **System Instruction** or **Architecture Guide**.
- Temporary documentation should never be committed.

### Increased Review Burden
- Reviewers must manually audit every file to determine if it is essential to the feature.
- This slows down the review process and increases the chance of missing issues.

---

## Minimum Viable Commit (MVC) Principles

### 1. The Core Principle: Ask "Is it *Consumed*?"

Before committing or merging, audit every new file and ask:

> **"Is this file consumed by the running application, the CI/CD pipeline, or the Infrastructure as Code (IaC)?"**

| File Type | Criteria for Inclusion | Action for Exclusion |
|:----------|:----------------------|:---------------------|
| **Source Code** | Must be imported/called by the application (`frontend/`, `backend/`). | **Keep** only final, functional code. |
| **Configuration** | Must be used by `podman-compose.yml`, `uv`, `bun`, or `terraform/`. | **Keep** only `requirements.txt`, `package.json`, `podman-compose.yml`. |
| **Documentation** | Must be a *final* file in the `docs/` folder or the `README.md`. | **Drop** all temporary notes, scratchpad files, or internal markdown drafts. |
| **Build/Hygiene** | Must be an updated `.*ignore` file (`.gitignore`, `.dockerignore`). | **Keep** only if an addition is necessary. |

### 2. The Non-Breaking Guiding Question

To ensure no new features are broken, the final check is:

> **"If I delete this file, does `make ci` still pass, and does the final deployed feature work as expected?"**
>
> **If the answer is "Yes," the file should be deleted.**

---

## File Audit Guidelines

### Files to ALWAYS Exclude

With a focus on **efficiency and clean CI/CD**, the following files/types **MUST** be audited and dropped from the PR before final merge, unless a specific, production-critical reason is provided:

| File Pattern | Description & Action |
|:------------|:--------------------|
| `*.bak`, `*.tmp`, `*.old` | **Discard.** Backup and temporary files. |
| `notes.md`, `scratchpad.*` | **Discard.** Personal note files. |
| `*_SUMMARY.md` (in root) | **Discard.** Feature implementation summaries belong in docs/ or should be removed after merge. |
| `PR_*.md` (in root) | **Discard.** PR-specific notes should not be committed. |
| `test_temp.*`, `scratch_*` | **Discard.** Ad-hoc test files that do not belong in the final test suite. |
| **Local Dev Environment** | **Discard.** Do not commit local `.env`, `.vscode/settings.json`, `.idea/`, or other IDE configuration files. Ensure these are in `.gitignore`. |
| **Duplicate Documentation** | **Discard.** Any temporary documentation that has not been finalized and merged into an official `docs/` file or the `README.md`. |
| **Build Artifacts** | **Discard.** Ensure `dist/`, `build/`, `__pycache__/`, `node_modules/` are in `.gitignore`. |

### Files to CAREFULLY Review

| File Type | Review Question |
|:----------|:---------------|
| **New Dependencies** | Is this dependency absolutely necessary? Does it add value proportional to its size/complexity? |
| **Configuration Files** | Is this configuration file required for CI/CD or deployment? Or is it local-only? |
| **Test Files** | Is this test file part of the permanent test suite? Or was it created for ad-hoc debugging? |
| **Scripts** | Is this script used in CI/CD or deployment? Or is it a one-time utility? |

---

## Pre-Merge Checklist

Before requesting final review, complete this checklist:

### 1. Self-Audit
- [ ] Review your PR file list and ask the "Is it Consumed?" question for every file
- [ ] Verify all new files have a clear purpose in the application or CI/CD process
- [ ] Ensure no temporary notes, local configuration, or outdated drafts are present

### 2. File Cleanup
- [ ] Remove unnecessary files using `git rm <file>`
- [ ] Commit the deletion: `git commit -m "Remove temporary files"`
- [ ] Push the cleanup: `git push`

### 3. Build Context Validation
- [ ] Verify `.dockerignore` excludes all unnecessary files
- [ ] Check that build context size is reasonable (use `podman build --no-cache` to verify)

### 4. Final Testing
- [ ] Run `make ci` to ensure all linting, building, and testing passes
- [ ] Verify the deployed feature works as expected
- [ ] Check that no functionality was broken by file removals

### 5. Documentation
- [ ] Update documentation if adding user-facing features
- [ ] Ensure all documentation is in `docs/` folder
- [ ] Remove any temporary documentation files

---

## How to Conduct Self-Audit

### Step 1: List All Changed Files

```bash
git --no-pager diff --name-only main
```

### Step 2: Review Each File

For each file, ask:
1. **Is this file consumed?** (by application, CI/CD, or IaC)
2. **If I delete this file, does `make ci` still pass?**
3. **Is this file in the correct location?** (e.g., docs in `docs/`, not root)

### Step 3: Remove Unnecessary Files

```bash
# Remove individual file
git rm path/to/unnecessary/file.md

# Remove multiple files
git rm *.tmp notes.md scratchpad.py

# Commit the cleanup
git commit -m "Remove temporary and unnecessary files"
```

### Step 4: Verify Build and Tests

```bash
# Run full CI check
make ci

# If ci target doesn't exist yet, run individual checks:
make lint
make test
make build  # if applicable
```

---

## Acceptance Criteria for Reviewers

When reviewing a Pull Request, verify:

- [ ] All newly added files have a clear and justifiable purpose in the final application or CI/CD process
- [ ] No temporary notes, local configuration files, or outdated drafts are present in the Pull Request
- [ ] The full CI check (`make ci`) passes successfully
- [ ] The `.dockerignore` and `.gitignore` files are optimized to minimize build context size
- [ ] Documentation changes are in the correct location (`docs/` folder)
- [ ] No build artifacts or dependencies are committed (`dist/`, `node_modules/`, `__pycache__/`, etc.)

### Reviewer Action Items

If unnecessary files are found:
1. **Comment** on the PR with specific files to remove
2. **Request changes** and ask the contributor to follow the self-audit process
3. **Do not approve** until all unnecessary files are removed

---

## Examples

### ✅ Good PR: Minimum Viable Commit

**Feature:** Add Firestore session persistence

**Files Changed:**
```
backend/services/session_service.py          # New service implementation
backend/tests/test_session_service.py        # Tests for new service
backend/main.py                              # Import and use new service
docs/SESSION_PERSISTENCE_GUIDE.md            # User-facing documentation
.gitignore                                   # Add session cache to ignore
```

**Result:** All files are consumed by the application or documentation. Clean, focused PR.

---

### ❌ Bad PR: Includes Unnecessary Files

**Feature:** Add Firestore session persistence

**Files Changed:**
```
backend/services/session_service.py          # ✅ New service implementation
backend/tests/test_session_service.py        # ✅ Tests for new service
backend/main.py                              # ✅ Import and use new service
docs/SESSION_PERSISTENCE_GUIDE.md            # ✅ User-facing documentation
.gitignore                                   # ✅ Add session cache to ignore
notes.md                                     # ❌ Personal notes
FR028_IMPLEMENTATION_SUMMARY.md              # ❌ Temporary summary
backend/scratch_test.py                      # ❌ Ad-hoc test file
.vscode/settings.json                        # ❌ IDE configuration
```

**Action Required:** Remove `notes.md`, `FR028_IMPLEMENTATION_SUMMARY.md`, `backend/scratch_test.py`, and `.vscode/settings.json`.

---

### Example: Self-Audit Process

```bash
# Step 1: Check current changes
git --no-pager diff --name-only main

# Output shows:
# backend/services/session_service.py
# backend/tests/test_session_service.py
# notes.md                              ← REMOVE
# FR028_SUMMARY.md                      ← REMOVE
# backend/scratch_test.py               ← REMOVE

# Step 2: Remove unnecessary files
git rm notes.md FR028_SUMMARY.md backend/scratch_test.py

# Step 3: Commit cleanup
git commit -m "Remove temporary files per MVC guidelines"

# Step 4: Verify CI passes
make ci

# Step 5: Push cleanup
git push
```

---

## Integration with Existing Workflow

This guide integrates with the existing contribution workflow documented in [CONTRIBUTING.md](../CONTRIBUTING.md):

1. **Before Development:** Review this guide to understand what files should and should not be committed.
2. **During Development:** Keep only necessary files. Use `/tmp/` for temporary files.
3. **Before PR Submission:** Complete the [Pre-Merge Checklist](#pre-merge-checklist).
4. **During Review:** Reviewers will verify compliance with this guide.

---

## Rationale

### Why is this important?

1. **Build Performance:** Every unnecessary file adds to the Podman build context, increasing build times.
2. **Repository Hygiene:** Temporary files clutter the repository and confuse future contributors.
3. **Review Efficiency:** Focused PRs are faster to review and less likely to introduce bugs.
4. **Deployment Efficiency:** Clean builds are faster to deploy and easier to debug.
5. **Documentation Clarity:** Official documentation stays accurate when temporary notes are excluded.

### What is the cost of not following this guide?

- Slower CI/CD pipelines (longer build times)
- Confused contributors (which files are important?)
- Outdated documentation (temporary notes contradict official docs)
- Harder code reviews (reviewers must audit every file)
- Technical debt accumulation (temporary files pile up over time)

---

## FAQ

### Q: Where should I put temporary notes during development?

**A:** Use `/tmp/` for temporary files that should not be committed. Example:
```bash
# Good: Temporary notes that won't be committed
echo "TODO: Test edge case" > /tmp/notes.md

# Bad: Notes in repository root
echo "TODO: Test edge case" > notes.md
```

### Q: What if I need to document my implementation approach?

**A:** If the documentation is valuable for future contributors:
- Create a final, polished document in `docs/`
- Follow the existing documentation style
- Remove any temporary drafts

If the documentation is only for your own reference:
- Keep it in `/tmp/` or on your local machine
- Do not commit it

### Q: How do I know if a dependency is necessary?

**A:** Ask:
1. Is the dependency used in production code? (Check imports)
2. Can the functionality be achieved without the dependency?
3. Does the dependency add value proportional to its size/complexity?

If unsure, ask in the PR description or discuss with reviewers.

### Q: What about test files I used for debugging?

**A:** If the test file:
- **Is part of the permanent test suite:** Keep it (e.g., `test_session_service.py`)
- **Was created for ad-hoc debugging:** Remove it (e.g., `scratch_test.py`, `test_temp.py`)

---

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - General contribution guidelines
- [docs/TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing best practices
- [docs/local-development.md](local-development.md) - Local development setup
- [.gitignore](../.gitignore) - Files excluded from version control
- [.dockerignore](../.dockerignore) - Files excluded from build context

---

## Revision History

| Date | Version | Description |
|:-----|:--------|:------------|
| 2024-11-02 | 1.0 | Initial policy creation (FR#050) |

---

**This guide is a living document.** As the project evolves, this guide will be updated to reflect new best practices and lessons learned. If you have suggestions for improvement, please open an issue or submit a PR.
