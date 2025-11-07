# FR#201: Prompt Vault Intelligence - Integration Guide

**Feature Status:** ✅ Implemented  
**Priority:** High (Product Value / Architectural Synthesis)  
**Implementation Date:** 2025-11-06

---

## Overview

This feature integrates AI-driven prompt analysis capabilities from the **agentnav** backend into the **Prompt Vault** application, providing intelligent suggestions for prompt improvement, structured output generation, and function calling hints.

## Architecture

### System Components

```
┌─────────────────────┐         HTTP/REST          ┌──────────────────────┐
│   Prompt Vault      │ ─────────────────────────> │  agentnav Backend    │
│   Frontend          │                             │  (FastAPI + ADK)     │
│                     │ <───────────────────────── │                      │
│  - React/TypeScript │    Suggestion Response      │  - Suggestion Agent  │
│  - suggestionService│                             │  - A2A Protocol      │
│  - PromptSuggestions│                             │  - Gemini API        │
└─────────────────────┘                             └──────────────────────┘
```

### Key Technologies

- **Backend:** FastAPI, Google ADK, A2A Protocol, Gemini 1.5 Pro
- **Frontend:** React, TypeScript, Tailwind CSS
- **Communication:** REST API (HTTP/JSON)
- **Security:** CORS, API authentication (optional)

---

## Backend Implementation

### 1. Suggestion Agent (`backend/agents/suggestion_agent.py`)

The Suggestion Agent is an ADK-compatible agent that analyzes prompts using Gemini AI:

**Key Features:**

- Prompt quality scoring (1-10)
- Optimization suggestions
- Structured output schema generation
- Function calling hints
- A2A Protocol integration

**Usage Example:**

```python
from backend.agents import SuggestionAgent, A2AProtocol

# Initialize agent
a2a = A2AProtocol()
agent = SuggestionAgent(a2a)

# Analyze prompt
context = {
    "prompt_text": "Write a function that calculates factorial",
    "user_context": "Educational tutorial"
}

result = await agent.execute(context)
```

### 2. API Endpoints (`backend/routes/suggestion_routes.py`)

**POST `/api/v1/suggestions/analyze`**

- Analyzes a prompt and returns AI-driven suggestions
- Request body: `PromptSuggestionRequest`
- Response: `PromptSuggestionResponse`

**GET `/api/v1/suggestions/health`**

- Checks if Suggestion Agent is available
- Returns agent health status

**GET `/api/v1/suggestions/examples`**

- Returns example prompts for testing

### 3. Pydantic Models (`backend/models/suggestion_models.py`)

**Request Model:**

```python
class PromptSuggestionRequest(BaseModel):
    prompt_text: str  # Required, 1-10000 chars
    user_context: Optional[str]  # Optional context
    existing_schema: Optional[Dict[str, Any]]  # Optional schema to refine
```

**Response Model:**

```python
class PromptSuggestionResponse(BaseModel):
    agent: str
    prompt_analyzed: str
    optimization_suggestions: List[str]
    structured_output_schema: Optional[StructuredOutputSchema]
    function_calling_hint: Optional[FunctionCallingHint]
    quality_score: int  # 1-10
    strengths: List[str]
    weaknesses: List[str]
    actionable_improvements: List[str]
    processing_complete: bool
    timestamp: float
```

---

## Frontend Implementation

### 1. Suggestion Service (`services/suggestionService.ts`)

TypeScript client for calling the Suggestion Agent API:

**Key Functions:**

```typescript
// Analyze a prompt
const response = await analyzePrompt({
  prompt_text: 'Your prompt here',
  user_context: 'Optional context',
});

// Check agent health
const health = await checkSuggestionAgentHealth();

// Get example prompts
const examples = await getExamplePrompts();
```

**Configuration:**

Set the API base URL via environment variable:

```bash
VITE_AGENTNAV_API_URL=https://agentnav-backend-xyz.run.app
```

### 2. React Component (`components/PromptSuggestions.tsx`)

Ready-to-use React component for displaying suggestions:

**Props:**

```typescript
interface PromptSuggestionsProps {
  promptText: string; // Prompt to analyze
  userContext?: string; // Optional context
  onSuggestionApplied?: (s: string) => void; // Callback when suggestion applied
  className?: string; // Custom CSS classes
}
```

**Usage Example:**

```tsx
import { PromptSuggestions } from './components/PromptSuggestions';

function PromptEditor() {
  const [prompt, setPrompt] = useState('');

  const handleSuggestionApplied = (suggestion: string) => {
    // Apply suggestion to prompt
    console.log('Applying:', suggestion);
  };

  return (
    <div>
      <textarea value={prompt} onChange={e => setPrompt(e.target.value)} />

      <PromptSuggestions
        promptText={prompt}
        userContext="Educational tutorial"
        onSuggestionApplied={handleSuggestionApplied}
      />
    </div>
  );
}
```

---

## Integration Steps for Prompt Vault

### Step 1: Configure Backend URL

In your Prompt Vault frontend, add the agentnav backend URL to `.env`:

```bash
VITE_AGENTNAV_API_URL=https://agentnav-backend-xyz.run.app
```

### Step 2: Copy Service and Component

Copy these files to your Prompt Vault frontend:

```bash
# Copy service
cp services/suggestionService.ts prompt-vault/frontend/src/services/

# Copy component
cp components/PromptSuggestions.tsx prompt-vault/frontend/src/components/
```

### Step 3: Install Dependencies

Ensure you have the required dependencies:

```bash
cd prompt-vault/frontend
bun add react react-dom
# Tailwind CSS should already be installed
```

### Step 4: Use the Component

In your Prompt Vault prompt editor:

```tsx
import { PromptSuggestions } from '@/components/PromptSuggestions';

function PromptEditor() {
  const [prompt, setPrompt] = useState('');

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Left: Prompt Editor */}
      <div>
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          className="w-full h-64 p-4 border rounded"
          placeholder="Enter your prompt..."
        />
      </div>

      {/* Right: AI Suggestions */}
      <div>
        <PromptSuggestions
          promptText={prompt}
          userContext="Prompt Vault"
          onSuggestionApplied={suggestion => {
            // Handle suggestion application
            alert(`Apply: ${suggestion}`);
          }}
        />
      </div>
    </div>
  );
}
```

---

## API Examples

### Example 1: Analyze a Simple Prompt

**Request:**

```bash
curl -X POST https://agentnav-backend.run.app/api/v1/suggestions/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_text": "Write a function that calculates factorial",
    "user_context": "Educational tutorial"
  }'
```

**Response:**

```json
{
  "agent": "suggestion",
  "prompt_analyzed": "Write a function that calculates factorial",
  "optimization_suggestions": [
    "Specify the programming language (e.g., Python, JavaScript)",
    "Add input validation requirements",
    "Include error handling expectations",
    "Specify output format"
  ],
  "structured_output_schema": {
    "type": "object",
    "properties": {
      "code": { "type": "string", "description": "Function code" },
      "explanation": { "type": "string", "description": "Code explanation" }
    },
    "required": ["code"]
  },
  "function_calling_hint": null,
  "quality_score": 6,
  "strengths": ["Clear task definition", "Concise"],
  "weaknesses": [
    "Lacks programming language context",
    "No output format specified"
  ],
  "actionable_improvements": [
    "Add: 'Write a Python function...'",
    "Add: 'Return the result as an integer'",
    "Add: 'Include docstring and type hints'"
  ],
  "processing_complete": true,
  "timestamp": 1699999999.0
}
```

### Example 2: Check Agent Health

**Request:**

```bash
curl https://agentnav-backend.run.app/api/v1/suggestions/health
```

**Response:**

```json
{
  "status": "healthy",
  "agent": "suggestion",
  "available": true,
  "state": "idle",
  "message": "Suggestion Agent is operational"
}
```

---

## Security Considerations

### 1. CORS Configuration

The agentnav backend is configured to allow requests from Prompt Vault:

```python
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,https://prompt-vault.lornu.com"
).split(",")
```

### 2. API Authentication (Optional)

For production, consider adding API key authentication:

```typescript
// In suggestionService.ts
const response = await fetch(`${SUGGESTIONS_ENDPOINT}/analyze`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.VITE_AGENTNAV_API_KEY, // Add API key
  },
  body: JSON.stringify(request),
});
```

### 3. Rate Limiting

Consider implementing rate limiting on the backend to prevent abuse.

---

## Testing

### Backend Tests

Run the comprehensive test suite:

```bash
cd backend
pytest tests/test_suggestion_agent.py -v
```

**Test Coverage:** 70%+ (as required by project standards)

**Test Categories:**

- Agent initialization and core functionality
- Prompt processing and analysis
- Response parsing (schemas, functions, lists)
- API endpoint behavior (success and error cases)
- Pydantic model validation
- ADK/A2A Protocol integration
- Error handling and fallback mechanisms

### Frontend Testing

Test the component manually:

1. Start the backend: `cd backend && uvicorn main:app --reload`
2. Start the frontend: `cd prompt-vault/frontend && bun run dev`
3. Enter a prompt and click "Get AI Suggestions"
4. Verify suggestions are displayed correctly

---

## Deployment

### Backend Deployment (Cloud Run)

The Suggestion Agent is automatically deployed with the agentnav backend:

```bash
gcloud run deploy agentnav-backend \
  --image europe-west1-docker.pkg.dev/${PROJECT_ID}/agentnav-containers/agentnav-backend:latest \
  --region europe-west1 \
  --platform managed \
  --port 8080 \
  --set-env-vars PORT=8080,GEMINI_API_KEY=${GEMINI_API_KEY}
```

### Frontend Integration

Update Prompt Vault frontend environment variables:

```bash
# .env.production
VITE_AGENTNAV_API_URL=https://agentnav-backend-xyz.run.app
```

---

## Monitoring and Observability

### Backend Logs

View Suggestion Agent logs in Cloud Logging:

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agentnav-backend AND textPayload=~'Suggestion Agent'"
```

### Metrics

Monitor key metrics:

- Request count to `/api/v1/suggestions/analyze`
- Average response time
- Error rate
- Quality score distribution

---

## Troubleshooting

### Issue: Agent Unavailable

**Symptom:** Health check returns `"available": false`

**Solution:**

1. Check if backend is running: `curl https://backend-url/healthz`
2. Verify Gemini API key is configured
3. Check backend logs for import errors

### Issue: CORS Error

**Symptom:** Browser console shows CORS error

**Solution:**

1. Add Prompt Vault domain to `CORS_ORIGINS` in backend
2. Redeploy backend with updated CORS configuration

### Issue: Slow Response

**Symptom:** Analysis takes >10 seconds

**Solution:**

1. Check Gemini API quota and rate limits
2. Consider implementing caching for repeated prompts
3. Optimize prompt template length

---

## Future Enhancements

1. **Caching:** Cache suggestions for identical prompts
2. **Batch Analysis:** Analyze multiple prompts in parallel
3. **Custom Templates:** Allow users to customize suggestion criteria
4. **Version History:** Track prompt improvements over time
5. **A/B Testing:** Compare quality scores before/after applying suggestions

---

## Success Criteria (Completed ✅)

- [x] A new **Suggestion Agent** is defined in the `agentnav` backend
- [x] A new API endpoint is created on the `agentnav` backend to receive prompt text
- [x] The Suggestion Agent's logic includes structured output generation for JSON schema
- [x] The Prompt Vault front-end can successfully call the new endpoint and display suggestions
- [x] Comprehensive tests with 70%+ coverage
- [x] Documentation for integration

---

## Related Documentation

- [FR#201 Feature Request](../FR029_IMPLEMENTATION_SUMMARY.md)
- [ADK Agent Development Guide](./ADK_AGENT_GUIDE.md)
- [A2A Protocol Specification](./A2A_PROTOCOL_SPEC.md)
- [Prompt Vault Isolation Plan](./PROMPT_VAULT_ISOLATION_PLAN.md)

---

**Implementation Complete:** 2025-11-06  
**Implemented By:** AI Agent (Cursor)  
**Estimated Effort:** 2 weeks (80 hours) - Completed in 1 session
