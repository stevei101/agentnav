#!/bin/bash
# Diagnostic script for agentnav service availability issues

set -euo pipefail

echo "🔍 Agent Navigator Service Availability Diagnostics"
echo "=================================================="
echo ""

# Check if running locally or in production
if [ -n "${BACKEND_API_URL:-}" ]; then
  BACKEND_URL="${BACKEND_API_URL}"
  echo "📍 Using BACKEND_API_URL: ${BACKEND_URL}"
else
  BACKEND_URL="${BACKEND_API_URL:-http://localhost:8080}"
  echo "📍 Using default backend URL: ${BACKEND_URL}"
fi

echo ""
echo "1️⃣ Checking Backend API Health..."
echo "   URL: ${BACKEND_URL}/healthz"
echo ""

if curl -f -s "${BACKEND_URL}/healthz" > /dev/null 2>&1; then
  echo "   ✅ Backend API is healthy"
  echo ""
  echo "   Health check response:"
  curl -s "${BACKEND_URL}/healthz" | jq . || curl -s "${BACKEND_URL}/healthz"
else
  echo "   ❌ Backend API is not responding"
  echo ""
  echo "   Troubleshooting steps:"
  echo "   - Is the backend service running?"
  echo "   - Check: make ps (for local) or gcloud run services list (for Cloud Run)"
  echo "   - Verify backend is listening on the correct port"
  echo "   - Check backend logs: make logs-backend (local) or Cloud Logging (Cloud Run)"
fi

echo ""
echo "2️⃣ Checking Agent Status Endpoint..."
echo "   URL: ${BACKEND_URL}/api/agents/status"
echo ""

if curl -f -s "${BACKEND_URL}/api/agents/status" > /dev/null 2>&1; then
  echo "   ✅ Agent status endpoint accessible"
  echo ""
  echo "   Agent status:"
  curl -s "${BACKEND_URL}/api/agents/status" | jq . || curl -s "${BACKEND_URL}/api/agents/status"
else
  echo "   ❌ Agent status endpoint not accessible"
  echo "   Error details:"
  curl -s "${BACKEND_URL}/api/agents/status" 2>&1 || echo "   Connection failed"
fi

echo ""
echo "3️⃣ Checking Analyze Endpoint (POST)..."
echo "   URL: ${BACKEND_URL}/api/analyze"
echo ""

TEST_REQUEST='{"document":"test","content_type":"text"}'
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "${TEST_REQUEST}" \
  "${BACKEND_URL}/api/analyze" 2>&1 || echo "CONNECTION_FAILED")

if echo "$RESPONSE" | grep -q "HTTP_CODE:200"; then
  echo "   ✅ Analyze endpoint is working"
elif echo "$RESPONSE" | grep -q "CONNECTION_FAILED"; then
  echo "   ❌ Cannot connect to analyze endpoint"
  echo "   $RESPONSE"
else
  HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
  echo "   ⚠️  Analyze endpoint returned HTTP ${HTTP_CODE}"
  echo "   Response:"
  echo "$RESPONSE" | grep -v "HTTP_CODE" | head -10
fi

echo ""
echo "4️⃣ Checking Cloud Run Services (if deployed)..."
echo ""

if command -v gcloud &> /dev/null; then
  PROJECT_ID="${GCP_PROJECT_ID:-}"
  if [ -n "$PROJECT_ID" ]; then
    echo "   Checking Cloud Run services in project: ${PROJECT_ID}"
    echo ""
    
    echo "   Backend Service:"
    if gcloud run services describe agentnav-backend \
      --region=europe-west1 \
      --project="${PROJECT_ID}" \
      --format="value(status.url)" 2>/dev/null | grep -q "http"; then
      BACKEND_CLOUD_URL=$(gcloud run services describe agentnav-backend \
        --region=europe-west1 \
        --project="${PROJECT_ID}" \
        --format="value(status.url)")
      echo "   ✅ URL: ${BACKEND_CLOUD_URL}"
      
      # Check if Cloud Run backend is healthy
      if curl -f -s "${BACKEND_CLOUD_URL}/healthz" > /dev/null 2>&1; then
        echo "   ✅ Cloud Run backend is healthy"
      else
        echo "   ❌ Cloud Run backend is not responding"
      fi
    else
      echo "   ❌ Backend service not found or not deployed"
    fi
    
    echo ""
    echo "   Gemma Service:"
    if gcloud run services describe gemma-service \
      --region=europe-west1 \
      --project="${PROJECT_ID}" \
      --format="value(status.url)" 2>/dev/null | grep -q "http"; then
      GEMMA_URL=$(gcloud run services describe gemma-service \
        --region=europe-west1 \
        --project="${PROJECT_ID}" \
        --format="value(status.url)")
      echo "   ✅ URL: ${GEMMA_URL}"
      
      if curl -f -s "${GEMMA_URL}/healthz" > /dev/null 2>&1; then
        echo "   ✅ Gemma service is healthy"
      else
        echo "   ❌ Gemma service is not responding"
      fi
    else
      echo "   ❌ Gemma service not found or not deployed"
    fi
  else
    echo "   ⚠️  GCP_PROJECT_ID not set, skipping Cloud Run checks"
  fi
else
  echo "   ⚠️  gcloud CLI not found, skipping Cloud Run checks"
fi

echo ""
echo "5️⃣ Checking Local Services (if running locally)..."
echo ""

if command -v podman &> /dev/null; then
  if podman ps --format "{{.Names}}" | grep -q "agentnav-backend"; then
    echo "   ✅ Backend container is running locally"
    echo "   Container status:"
    podman ps --filter "name=agentnav-backend" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  else
    echo "   ❌ Backend container is not running"
    echo "   Start with: make up"
  fi
else
  echo "   ⚠️  Podman not found, skipping local container checks"
fi

echo ""
echo "6️⃣ Network Connectivity Check..."
echo ""

if [ "${BACKEND_URL}" = "http://localhost:8080" ]; then
  if nc -z localhost 8080 2>/dev/null; then
    echo "   ✅ Port 8080 is listening"
  else
    echo "   ❌ Port 8080 is not accessible"
    echo "   The backend service may not be running"
  fi
fi

echo ""
echo "=================================================="
echo "✅ Diagnostics complete"
echo ""
echo "📋 Next Steps:"
echo "  1. If backend is not running locally: make up"
echo "  2. If backend is unhealthy: check logs (make logs-backend)"
echo "  3. If using Cloud Run: verify deployment status"
echo "  4. Check frontend VITE_API_URL matches backend URL"
echo ""

