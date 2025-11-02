# PR Recovery Workflow After Force Push

**Feature Request #110** - Automated PR Recovery After Force Push Remediation

This guide explains how to recover Pull Requests that were automatically closed due to a force push to the `main` branch (typically from security fixes like FR#095).

---

## Quick Recovery (Automated)

If you're a repository maintainer, use the automated recovery script:

```bash
# Dry run - see what would be restored
./scripts/restore_closed_prs.sh

# Or manually specify timestamp
python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --dry-run

# Interactive mode - confirm each PR
python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --interactive
```

The script will:
1. ✅ Identify all closed (non-merged) PRs closed after the force push
2. ✅ Verify your source branch still exists
3. ✅ Recreate the PR with original title, body, and linked issues
4. ✅ Notify you of the new PR URL

---

## Manual Recovery (For Contributors)

If your PR was closed due to a force push, follow these steps:

### Step 1: Rebase Your Feature Branch

**This is mandatory** - Your branch history must align with the new `main` branch.

```bash
# Ensure you're on your feature branch
git checkout your-feature-branch

# Fetch latest from remote
git fetch origin

# Rebase onto the new main
git rebase origin/main

# Force push your rebased branch
git push --force-with-lease origin your-feature-branch
```

> ⚠️ **Important:** Always use `--force-with-lease` instead of `--force` for safety. This prevents overwriting others' work.

### Step 2: Verify Your Branch

Ensure your branch is properly rebased and up to date:

```bash
# Check your branch is ahead of main
git log origin/main..HEAD --oneline

# Verify no conflicts
git status
```

### Step 3: Create New PR

Since GitHub prevents re-opening PRs with mismatched history, create a new PR:

```bash
# Using GitHub CLI
gh pr create \
  --base main \
  --head your-feature-branch \
  --title "Your Original PR Title" \
  --body "Your original PR description

⚠️ **PR Recovery Notice**

This PR was recreated after a force push to main (FR#095 security fix).

Original PR: #XXX"
```

Or use the GitHub web interface:
1. Go to your repository on GitHub
2. Click "New Pull Request"
3. Select your rebased branch → `main`
4. Add original title and description
5. Reference the original PR number in the description

---

## Why Force Push Closed My PR?

When a force push occurs on `main` (the base branch), GitHub automatically closes all open PRs targeting that branch because:

1. **History Mismatch:** The PR's base commit no longer exists in `main`
2. **Safety:** GitHub prevents merging PRs with invalid base commits
3. **Security:** Force pushes typically indicate history rewrites (e.g., removing secrets)

**This is normal behavior** - PRs must be rebased and recreated after a force push.

---

## Automated Recovery Script Details

### Prerequisites

- **GitHub CLI (`gh`):** [Installation Guide](https://cli.github.com/)
- **Python 3:** Usually pre-installed on macOS/Linux
- **Authentication:** Run `gh auth login` if not already authenticated

### Usage

```bash
# Basic usage - dry run
python3 scripts/restore_closed_prs.py --dry-run

# Filter by timestamp (force push event)
python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --dry-run

# Interactive mode - confirm each PR
python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --interactive

# Actually restore PRs (removes --dry-run)
python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z
```

### What the Script Does

1. **Identifies Closed PRs:**
   - Lists all closed (non-merged) PRs
   - Filters by timestamp if `--since` is provided
   - Excludes already-merged PRs

2. **Validates Branches:**
   - Checks if source branches still exist
   - Skips PRs with deleted branches

3. **Extracts Metadata:**
   - Original PR title and description
   - Linked issues (Fixes #X, Closes #Y, etc.)
   - Base and head branches
   - Original author

4. **Recreates PRs:**
   - Creates new PR with original metadata
   - Adds recovery notice to PR body
   - Preserves linked issue references
   - Outputs new PR URL

### Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--since TIMESTAMP` | Only process PRs closed after this time | `--since 2025-11-02T16:00:00Z` |
| `--dry-run` | Show what would be restored without creating PRs | Always recommended first |
| `--interactive` | Prompt before recreating each PR | Useful for selective recovery |
| `--limit N` | Maximum number of PRs to process | `--limit 20` |

---

## Troubleshooting

### Issue: "Source branch does not exist"

**Cause:** The source branch was deleted or never pushed.

**Solution:**
1. Check if you still have the branch locally: `git branch -a`
2. If local branch exists, push it: `git push origin branch-name`
3. If branch was deleted, you'll need to restore it from your local copy

### Issue: "GitHub CLI not authenticated"

**Solution:**
```bash
gh auth login
# Follow the prompts to authenticate
```

### Issue: "Rebase conflicts"

**Cause:** Your changes conflict with new commits in `main`.

**Solution:**
```bash
# During rebase, resolve conflicts
git rebase origin/main

# For each conflict:
# 1. Edit conflicted files
# 2. git add <file>
# 3. git rebase --continue

# If stuck, abort and seek help
git rebase --abort
```

### Issue: "PR already exists"

**Cause:** Someone already recreated the PR, or you ran the script twice.

**Solution:**
- Check existing open PRs: `gh pr list`
- Close duplicate if needed: `gh pr close <number>`

---

## Best Practices

### For Contributors

1. **Always rebase before force push recovery:**
   ```bash
   git fetch origin
   git rebase origin/main
   git push --force-with-lease
   ```

2. **Preserve original PR context:**
   - Reference original PR number in new PR description
   - Include original reviewers if applicable
   - Mention linked issues

3. **Test after rebase:**
   - Ensure your code still works after rebase
   - Run tests: `make test`
   - Verify no merge conflicts

### For Maintainers

1. **Always run in dry-run mode first:**
   ```bash
   python3 scripts/restore_closed_prs.py --dry-run
   ```

2. **Notify affected contributors:**
   - Post in team chat/issue tracker
   - Provide clear instructions
   - Share this documentation link

3. **Monitor restored PRs:**
   - Check that restored PRs have correct metadata
   - Verify linked issues are preserved
   - Ensure CI checks run on new PRs

---

## Examples

### Example 1: Automated Recovery (Maintainer)

```bash
# 1. Dry run to see what would be restored
python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --dry-run

# Output shows 5 PRs that would be restored

# 2. Run interactively to confirm each
python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --interactive

# 3. Script recreates PRs and outputs URLs
```

### Example 2: Manual Recovery (Contributor)

```bash
# Your PR #61 was closed by force push

# 1. Rebase your branch
git checkout copilot/add-branch-protection-main
git fetch origin
git rebase origin/main
git push --force-with-lease origin copilot/add-branch-protection-main

# 2. Create new PR
gh pr create \
  --base main \
  --head copilot/add-branch-protection-main \
  --title "FR#070: Add staging deployment gate for main branch protection" \
  --body "⚠️ PR Recovery Notice

This PR was recreated after force push to main (FR#095).

Original PR: #61

[Your original PR description here...]

Fixes #60"

# 3. New PR #87 created successfully
```

---

## Related Documentation

- **FR#095:** Security hardening - Purge .env from Git History (the force push that closed PRs)
- **FR#050:** PR Discipline Guide (clean PR practices)
- **CONTRIBUTING.md:** General contribution guidelines

---

## Support

If you encounter issues not covered in this guide:

1. Check existing issues: `gh issue list`
2. Create a new issue describing your problem
3. Tag maintainers: `@stevei101`

---

**Last Updated:** 2025-11-02  
**Feature Request:** #110  
**Status:** Active

