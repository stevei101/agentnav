#!/bin/bash
#
# Setup pre-commit hook for agentnav
# This script copies the pre-commit hook template to .git/hooks/
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK_SOURCE="$PROJECT_ROOT/scripts/pre-commit-hook"
HOOK_TARGET="$PROJECT_ROOT/.git/hooks/pre-commit"

echo "🔧 Setting up pre-commit hook..."

# Check if we're in a git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Check if bun is available
if ! command -v bun >/dev/null 2>&1; then
    echo "⚠️  Warning: bun not found"
    echo "   Install bun: https://bun.sh/"
    echo "   Pre-commit hook will skip checks if bun is not available"
fi

# Copy hook template to .git/hooks/
if [ -f "$HOOK_SOURCE" ]; then
    cp "$HOOK_SOURCE" "$HOOK_TARGET"
    chmod +x "$HOOK_TARGET"
    echo "✅ Pre-commit hook installed successfully!"
    echo ""
    echo "   The hook will run on every commit to check:"
    echo "   - ESLint (linting)"
    echo "   - Prettier (formatting)"
    echo ""
    echo "   To bypass (use sparingly): git commit --no-verify"
else
    echo "❌ Error: Hook template not found at $HOOK_SOURCE"
    exit 1
fi

