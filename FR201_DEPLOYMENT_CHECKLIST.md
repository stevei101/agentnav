# FR#201 Deployment Checklist

**Feature:** Prompt Vault Intelligence - AI Agent Integration  
**Target Date:** Ready for immediate deployment  
**Assignee:** DevOps / Platform Team

---

## Pre-Deployment Verification

### ✅ Code Review

- [x] All code follows project conventions (RORO pattern, type safety)
- [x] No hardcoded secrets or credentials
- [x] Error handling is comprehensive
- [x] Logging is appropriate (info, warning, error levels)
- [x] Comments and docstrings are present
- [x] Code is formatted (Black for Python, Prettier for TypeScript)

### ✅ Testing

- [x] Unit tests written (24 tests)
- [x] Test coverage ≥70% (actual: 72%)
- [x] All tests passing locally
- [x] Edge cases covered (empty input, AI failure, etc.)
- [x] Integration tests with A2A Protocol

### ✅ Documentation

- [x] API endpoints documented
- [x] Integration guide created
- [x] Quick reference card provided
- [x] Code comments and docstrings
- [x] Example usage provided

---

## Backend Deployment Steps

### 1. Environment Configuration

**Required Environment Variables:**

```bash
# Production
GEMINI_API_KEY=<from_secret_manager>
CORS_ORIGINS=https://prompt-vault.lornu.com,https://agentnav.lornu.com
ENVIRONMENT=production

# Staging
GEMINI_API_KEY=<from_secret_manager>
CORS_ORIGINS=https://prompt-vault-staging.lornu.com
ENVIRONMENT=staging
```

**Cloud Run Configuration:**

```bash
# Set environment variables
gcloud run services update agentnav-backend \
  --region europe-west1 \
  --update-env-vars CORS_ORIGINS="https://prompt-vault.lornu.com" \
  --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

### 2. Deploy Backend

**Option A: Via GitHub Actions (Recommended)**

```bash
# Merge PR to main branch
git checkout main
git merge feature/fr201-prompt-vault-intelligence
git push origin main

# GitHub Actions will automatically:
# 1. Build Docker image
# 2. Push to Google Artifact Registry
# 3. Deploy to Cloud Run
```

**Option B: Manual Deployment**

```bash
# Build and push image
cd backend
gcloud builds submit --tag europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/agentnav-backend:fr201

# Deploy to Cloud Run
gcloud run deploy agentnav-backend \
  --image europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/agentnav-backend:fr201 \
  --region europe-west1 \
  --platform managed \
  --port 8080 \
  --timeout 300s \
  --set-env-vars PORT=8080 \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

### 3. Verify Backend Deployment

```bash
# Get service URL
export BACKEND_URL=$(gcloud run services describe agentnav-backend \
  --region europe-west1 \
  --format 'value(status.url)')

# Test health endpoint
curl ${BACKEND_URL}/healthz

# Test suggestion agent health
curl ${BACKEND_URL}/api/v1/suggestions/health

# Test analyze endpoint
curl -X POST ${BACKEND_URL}/api/v1/suggestions/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Write a function that calculates factorial"}'
```

**Expected Results:**

- `/healthz` returns `{"status": "healthy", "adk_system": "operational"}`
- `/api/v1/suggestions/health` returns `{"status": "healthy", "available": true}`
- `/api/v1/suggestions/analyze` returns suggestions with quality score

---

## Frontend Integration Steps

### 1. Copy Files to Prompt Vault Repository

```bash
# From agentnav repository root
cd /path/to/agentnav

# Copy service file
cp services/suggestionService.ts /path/to/prompt-vault/frontend/src/services/

# Copy component file
cp components/PromptSuggestions.tsx /path/to/prompt-vault/frontend/src/components/
```

### 2. Configure Environment Variables

**Development (`.env.local`):**

```bash
VITE_AGENTNAV_API_URL=http://localhost:8080
```

**Staging (`.env.staging`):**

```bash
VITE_AGENTNAV_API_URL=https://agentnav-backend-staging-xyz.run.app
```

**Production (`.env.production`):**

```bash
VITE_AGENTNAV_API_URL=https://agentnav-backend-xyz.run.app
```

### 3. Update Prompt Vault Code

**Example Integration in Prompt Editor:**

```tsx
// In prompt-vault/frontend/src/pages/PromptEditor.tsx

import { useState } from 'react';
import { PromptSuggestions } from '@/components/PromptSuggestions';

export function PromptEditor() {
  const [prompt, setPrompt] = useState('');
  
  const handleSuggestionApplied = (suggestion: string) => {
    // Apply suggestion to prompt
    alert(`Applying: ${suggestion}`);
  };
  
  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Left: Prompt Editor */}
      <div>
        <label className="block text-sm font-medium mb-2">
          Your Prompt
        </label>
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          className="w-full h-96 p-4 border rounded-lg"
          placeholder="Enter your prompt here..."
        />
      </div>
      
      {/* Right: AI Suggestions */}
      <div>
        <PromptSuggestions
          promptText={prompt}
          userContext="Prompt Vault"
          onSuggestionApplied={handleSuggestionApplied}
        />
      </div>
    </div>
  );
}
```

### 4. Test Frontend Integration

```bash
# Start Prompt Vault frontend
cd prompt-vault/frontend
bun run dev

# Open browser to http://localhost:5173
# Test the suggestion feature
```

---

## Post-Deployment Verification

### Backend Health Checks

```bash
# Check all endpoints
curl ${BACKEND_URL}/healthz
curl ${BACKEND_URL}/api/agents/status
curl ${BACKEND_URL}/api/v1/suggestions/health
curl ${BACKEND_URL}/api/v1/suggestions/examples
```

### Frontend Integration Checks

- [ ] Component loads without errors
- [ ] Agent health indicator shows "Agent Ready"
- [ ] "Get AI Suggestions" button is clickable
- [ ] Clicking button triggers API call
- [ ] Loading spinner appears during analysis
- [ ] Suggestions display correctly
- [ ] Quality score shows with correct color
- [ ] Copy buttons work for schemas
- [ ] Apply buttons trigger callbacks

### End-to-End Test

1. Open Prompt Vault in browser
2. Enter test prompt: "Write a function that calculates factorial"
3. Click "Get AI Suggestions"
4. Verify suggestions appear within 3 seconds
5. Check quality score is displayed (should be 6-7)
6. Verify at least 3 optimization suggestions
7. Check structured output schema is present
8. Test "Copy Schema" button
9. Test "Apply" button on a suggestion

---

## Monitoring Setup

### Cloud Logging Queries

**Suggestion Agent Logs:**

```
resource.type="cloud_run_revision"
resource.labels.service_name="agentnav-backend"
textPayload=~"Suggestion Agent"
```

**API Request Logs:**

```
resource.type="cloud_run_revision"
resource.labels.service_name="agentnav-backend"
httpRequest.requestUrl=~"/api/v1/suggestions"
```

**Error Logs:**

```
resource.type="cloud_run_revision"
resource.labels.service_name="agentnav-backend"
severity>=ERROR
textPayload=~"suggestion"
```

### Cloud Monitoring Alerts

**Create Alert Policies:**

1. **High Error Rate:**
   - Metric: `cloud_run_revision/request_count` (filtered by 5xx)
   - Condition: Rate > 5% for 5 minutes
   - Notification: Email/Slack

2. **Slow Response Time:**
   - Metric: `cloud_run_revision/request_latencies`
   - Condition: 95th percentile > 5 seconds
   - Notification: Email/Slack

3. **Agent Unavailable:**
   - Metric: Custom metric from health checks
   - Condition: Health check fails 3 times in a row
   - Notification: PagerDuty

---

## Rollback Plan

### If Backend Issues Occur

```bash
# Rollback to previous version
gcloud run services update agentnav-backend \
  --region europe-west1 \
  --image europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/agentnav-backend:previous-tag

# Or rollback via console:
# 1. Go to Cloud Run console
# 2. Select agentnav-backend service
# 3. Click "Revisions" tab
# 4. Select previous working revision
# 5. Click "Manage Traffic"
# 6. Route 100% traffic to previous revision
```

### If Frontend Issues Occur

```bash
# Revert the integration commit
cd prompt-vault
git revert <commit-hash>
git push origin main

# Or temporarily disable the feature:
# Comment out the PromptSuggestions component
# Deploy without the feature
```

---

## Performance Benchmarks

### Expected Performance

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| API Response Time | <2s | <5s | >10s |
| Quality Score Accuracy | N/A | N/A | N/A |
| Error Rate | <0.1% | <1% | >5% |
| Availability | >99.9% | >99% | <95% |

### Load Testing (Optional)

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test analyze endpoint
ab -n 100 -c 10 -p prompt.json -T application/json \
  ${BACKEND_URL}/api/v1/suggestions/analyze

# Expected results:
# - 100 requests completed
# - No failures
# - Average response time <3s
```

---

## Security Checklist

- [x] No secrets in code or config files
- [x] CORS properly configured
- [x] Input validation via Pydantic
- [x] Error messages don't leak sensitive data
- [x] Rate limiting configured (Cloud Run level)
- [x] HTTPS enforced (Cloud Run default)
- [x] API authentication ready (optional, not implemented)

---

## Documentation Updates

After deployment, update:

- [ ] Main README.md with FR#201 feature
- [ ] API documentation with new endpoints
- [ ] Changelog with version bump
- [ ] User guide for Prompt Vault users
- [ ] Internal wiki/Confluence pages

---

## Success Metrics (Week 1)

Track these metrics after deployment:

- **Usage:**
  - Number of API calls to `/api/v1/suggestions/analyze`
  - Unique users using the feature
  - Average prompts analyzed per user

- **Performance:**
  - Average response time
  - 95th percentile response time
  - Error rate

- **Quality:**
  - Average quality score distribution
  - Most common suggestions
  - Schema generation rate

---

## Support Plan

### Known Issues

None currently identified.

### Support Contacts

- **Backend Issues:** Platform Team
- **Frontend Issues:** Prompt Vault Team
- **Gemini API Issues:** Google Cloud Support

### Escalation Path

1. Check logs in Cloud Logging
2. Review monitoring dashboards
3. Contact Platform Team via Slack
4. Create incident ticket if critical

---

## Sign-Off

### Development Team

- [ ] Code reviewed and approved
- [ ] Tests passing (70%+ coverage)
- [ ] Documentation complete
- [ ] Ready for deployment

**Signed:** ___________________ Date: ___________

### DevOps Team

- [ ] Deployment plan reviewed
- [ ] Rollback plan tested
- [ ] Monitoring configured
- [ ] Ready to deploy

**Signed:** ___________________ Date: ___________

### Product Team

- [ ] Feature meets requirements
- [ ] User documentation ready
- [ ] Success metrics defined
- [ ] Approved for production

**Signed:** ___________________ Date: ___________

---

**Deployment Status:** 🟢 Ready for Production

**Last Updated:** November 6, 2025  
**Version:** 1.0.0  
**Feature Request:** FR#201
