#!/bin/bash
# Restart Prompt Vault and ensure it's on the correct port

set -euo pipefail

echo "🔄 Restarting Prompt Vault..."

# Kill existing processes
pkill -f "vite.*prompt" 2>/dev/null || true
lsof -ti :5175 | xargs kill -9 2>/dev/null || true
sleep 2

# Start on port 5175
cd "$(dirname "$0")/../prompt-vault/frontend"
bun run dev > /tmp/prompt-vault.log 2>&1 &

# Wait for startup
sleep 5

# Verify
if lsof -i :5175 | grep -q LISTEN; then
    echo "✅ Prompt Vault running on port 5175"
    curl -s -I http://localhost:5175 | head -1
else
    echo "❌ Failed to start on port 5175"
    tail -10 /tmp/prompt-vault.log
    exit 1
fi
