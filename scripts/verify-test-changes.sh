#!/bin/bash
# Script to verify test changes before pushing
# Verifies: test_gemini_client.py imports and syntax

set -e

echo "🔍 Verifying test_gemini_client.py changes..."

cd "$(dirname "$0")/.."

# 1. Syntax check
echo "1. Checking Python syntax..."
python3 -m py_compile backend/tests/test_gemini_client.py && echo "   ✅ Syntax valid"

# 2. Import check
echo "2. Checking imports..."
python3 << 'EOF'
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
try:
    from services.gemini_client import GeminiClient, reason_with_gemini
    print("   ✅ Imports successful - GeminiClient and reason_with_gemini are available")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    sys.exit(1)
EOF

# 3. Verify test file structure
echo "3. Verifying test file structure..."
if grep -q "from services.gemini_client import" backend/tests/test_gemini_client.py; then
    echo "   ✅ Correct imports found"
else
    echo "   ❌ Missing imports"
    exit 1
fi

if grep -q "class GeminiClient" backend/services/gemini_client.py; then
    echo "   ✅ GeminiClient class exists"
else
    echo "   ❌ GeminiClient class not found"
    exit 1
fi

if grep -q "async def reason_with_gemini" backend/services/gemini_client.py; then
    echo "   ✅ reason_with_gemini function exists"
else
    echo "   ❌ reason_with_gemini function not found"
    exit 1
fi

echo ""
echo "✅ All static checks passed!"
echo "⚠️  Note: Run 'pytest backend/tests/test_gemini_client.py -v' to execute tests"
