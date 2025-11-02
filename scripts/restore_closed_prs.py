#!/usr/bin/env python3
"""
PR Recovery Automation Script - FR#110

Identifies and restores Pull Requests that were closed due to a force push event.

This script:
1. Lists all closed (non-merged) PRs closed after a specified timestamp
2. Verifies source branches still exist
3. Recreates PRs with original metadata (title, body, linked issues, reviewers)

Usage:
    python3 scripts/restore_closed_prs.py [--since TIMESTAMP] [--dry-run] [--interactive]
    
Example:
    python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --dry-run
"""

import subprocess
import json
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Optional


def run_gh_command(cmd: List[str], capture_output: bool = True) -> Dict:
    """Run a GitHub CLI command and return JSON output."""
    try:
        result = subprocess.run(
            ["gh"] + cmd,
            capture_output=capture_output,
            text=True,
            check=True
        )
        if capture_output:
            return json.loads(result.stdout)
        return {}
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {' '.join(cmd)}")
        print(f"   {e.stderr}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        return {}


def get_closed_prs(since_timestamp: Optional[str] = None) -> List[Dict]:
    """Get all closed (non-merged) PRs, optionally filtered by timestamp."""
    cmd = ["pr", "list", "--state", "closed", "--json", 
           "number,title,headRefName,baseRefName,closedAt,mergedAt,body,author,url,labels"]
    
    prs = run_gh_command(cmd)
    
    if not prs:
        return []
    
    # Filter to only non-merged PRs
    closed_only = [pr for pr in prs if pr.get("mergedAt") is None]
    
    # Filter by timestamp if provided
    if since_timestamp:
        since_dt = datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))
        filtered = []
        for pr in closed_only:
            closed_at = pr.get("closedAt")
            if closed_at:
                closed_dt = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
                if closed_dt >= since_dt:
                    filtered.append(pr)
        return filtered
    
    return closed_only


def verify_branch_exists(branch_name: str) -> bool:
    """Verify that a branch exists in the remote repository."""
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch_name],
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def extract_issue_numbers(body: str) -> List[str]:
    """Extract issue numbers from PR body (Fixes #X, Closes #X, etc.)."""
    import re
    # Match patterns like "Fixes #123", "Closes #456", or just "#789"
    patterns = [
        r'(?:Fixes|Closes|Resolves|Related to|Addresses)\s*#(\d+)',
        r'#(\d+)'  # Generic issue reference
    ]
    issues = set()
    for pattern in patterns:
        matches = re.findall(pattern, body or "", re.IGNORECASE)
        issues.update(matches)
    return sorted(list(issues), key=int)


def recreate_pr(pr_data: Dict, dry_run: bool = False) -> Optional[Dict]:
    """Recreate a closed PR with original metadata."""
    pr_number = pr_data.get("number")
    title = pr_data.get("title")
    body = pr_data.get("body") or ""
    head_branch = pr_data.get("headRefName")
    base_branch = pr_data.get("baseRefName", "main")
    author = pr_data.get("author", {}).get("login", "")
    
    print(f"\n📋 PR #{pr_number}: {title}")
    print(f"   Branch: {head_branch} → {base_branch}")
    print(f"   Author: {author}")
    
    # Verify branch exists
    if not verify_branch_exists(head_branch):
        print(f"   ⚠️  Source branch '{head_branch}' does not exist. Skipping.")
        return None
    
    print(f"   ✅ Source branch exists")
    
    # Extract linked issues
    issues = extract_issue_numbers(body)
    if issues:
        print(f"   📌 Linked issues: {', '.join(['#' + i for i in issues])}")
    
    if dry_run:
        print(f"   🔍 DRY RUN: Would recreate PR with:")
        print(f"      Title: {title}")
        print(f"      Body length: {len(body)} chars")
        print(f"      Issues: {issues if issues else 'None'}")
        return None
    
    # Prepare PR body with recovery notice
    recovery_notice = f"""⚠️ **PR Recovery Notice**

This PR was automatically recreated after a force push to `{base_branch}` (FR#095 security fix).

**Original PR:** #{pr_number}
**Recovery Date:** {datetime.now().isoformat()}

---

{body}"""
    
    # Build gh pr create command
    cmd = [
        "pr", "create",
        "--base", base_branch,
        "--head", head_branch,
        "--title", title,
        "--body", recovery_notice
    ]
    
    # Add issue references if any
    for issue in issues:
        cmd.extend(["--body", f"Fixes #{issue}"])
    
    try:
        result = subprocess.run(
            ["gh"] + cmd,
            capture_output=True,
            text=True,
            check=True
        )
        new_pr_url = result.stdout.strip()
        print(f"   ✅ Created: {new_pr_url}")
        return {"url": new_pr_url, "original": pr_number}
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to create PR: {e.stderr}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Restore closed Pull Requests after force push",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - show what would be restored
  python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --dry-run
  
  # Interactive mode - confirm each PR
  python3 scripts/restore_closed_prs.py --since 2025-11-02T16:00:00Z --interactive
  
  # Restore all (non-merged) closed PRs
  python3 scripts/restore_closed_prs.py --dry-run
        """
    )
    parser.add_argument(
        "--since",
        type=str,
        help="ISO timestamp to filter PRs closed after (e.g., 2025-11-02T16:00:00Z)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be restored without actually creating PRs"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt before recreating each PR"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of PRs to process (default: 50)"
    )
    
    args = parser.parse_args()
    
    # Verify gh CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI (gh) is required but not found.")
        print("   Install: https://cli.github.com/")
        sys.exit(1)
    
    # Verify authentication
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ GitHub CLI not authenticated.")
        print("   Run: gh auth login")
        sys.exit(1)
    
    print("🔍 Identifying closed Pull Requests...")
    if args.since:
        print(f"   Filtering PRs closed after: {args.since}")
    
    closed_prs = get_closed_prs(args.since)
    
    if not closed_prs:
        print("✅ No closed PRs found matching criteria.")
        return
    
    # Limit results
    closed_prs = closed_prs[:args.limit]
    
    print(f"\n📊 Found {len(closed_prs)} closed (non-merged) PR(s):")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No PRs will be created\n")
    
    restored = []
    skipped = []
    
    for pr in closed_prs:
        if args.interactive:
            response = input(f"\nRestore PR #{pr.get('number')}: {pr.get('title')}? [y/N]: ")
            if response.lower() != 'y':
                skipped.append(pr.get('number'))
                continue
        
        result = recreate_pr(pr, dry_run=args.dry_run)
        if result:
            restored.append(result)
        else:
            skipped.append(pr.get('number'))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Recovery Summary:")
    print(f"   ✅ Restored: {len(restored)} PR(s)")
    print(f"   ⏭️  Skipped: {len(skipped)} PR(s)")
    
    if restored and not args.dry_run:
        print(f"\n📝 Restored PRs:")
        for item in restored:
            print(f"   {item['url']} (original: #{item['original']})")
    
    if args.dry_run:
        print(f"\n💡 Run without --dry-run to actually restore these PRs")


if __name__ == "__main__":
    main()

