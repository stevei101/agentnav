#!/bin/bash
# Local helper to run detect-secrets (Yelp) via uvx without polluting the repo.

set -euo pipefail

if ! command -v uvx >/dev/null 2>&1; then
  echo "❌ uvx (part of uv) is required. Install uv from https://github.com/astral-sh/uv." >&2
  exit 1
fi

echo "🔍 Scanning repository for secrets..."
uvx detect-secrets scan --update .secrets.baseline --exclude-files "bun.lock"

echo "📝 Launching interactive audit (press 'q' to finish)..."
uvx detect-secrets audit .secrets.baseline

echo "✅ Secret scan complete. Resolve any real findings before committing."
