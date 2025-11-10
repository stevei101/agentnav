#!/bin/bash
# Run detect-secrets locally using the official Yelp project.
# This script is intentionally not wired into CI; run it before committing.

set -euo pipefail

if ! command -v uvx >/dev/null 2>&1; then
  echo "❌ uvx (part of uv) is required. Install uv from https://github.com/astral-sh/uv and retry." >&2
  exit 1
fi

echo "🔍 Scanning repository for secrets (baseline will be updated)..."
uvx detect-secrets scan --update .secrets.baseline --exclude-files "bun.lock"

echo "📝 Launching interactive audit (press 'q' to exit when finished)..."
uvx detect-secrets audit .secrets.baseline

echo "✅ Secret scan complete. Review any real findings before committing."
