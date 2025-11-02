#!/bin/bash
# PR Recovery Automation Script - Shell Wrapper
# FR#110: PR Recovery Automation After Force Push Remediation
#
# This is a convenience wrapper for restore_closed_prs.py
# It provides a simple interface and ensures dependencies are met.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default to the force push timestamp from FR#095 (Nov 2, 2025 ~16:26)
DEFAULT_SINCE="${1:-2025-11-02T16:00:00Z}"
DRY_RUN="${2:-true}"

echo "🔄 PR Recovery Automation - FR#110"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    exit 1
fi

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is required but not found."
    echo "   Install: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI not authenticated."
    echo "   Run: gh auth login"
    exit 1
fi

# Run the Python script
cd "$REPO_ROOT"

if [ "$DRY_RUN" = "true" ] || [ "$DRY_RUN" = "1" ]; then
    echo "🔍 Running in DRY RUN mode (no PRs will be created)"
    echo ""
    python3 "$SCRIPT_DIR/restore_closed_prs.py" --since "$DEFAULT_SINCE" --dry-run
else
    echo "⚠️  LIVE MODE - PRs will be created!"
    echo "   Press Ctrl+C to cancel, or wait 3 seconds..."
    sleep 3
    python3 "$SCRIPT_DIR/restore_closed_prs.py" --since "$DEFAULT_SINCE" --interactive
fi

