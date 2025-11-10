# FR#201 Quick Reference Card

**Feature:** Prompt Vault Intelligence - AI Agent Integration  
**Status:** ✅ Complete and Ready for Integration

---

## 🚀 Quick Start (Backend)

### Test the API Locally

```bash
# Start backend
cd backend
uvicorn main:app --reload --port 8080

# Test health check
curl http://localhost:8080/api/v1/suggestions/health

# Analyze a prompt
curl -X POST http://localhost:8080/api/v1/suggestions/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt_text": "Write a function that calculates factorial"}'
```

---

## 🎨 Quick Start (Frontend)

### Basic Integration

```typescript
import { analyzePrompt } from './services/suggestionService';

// Analyze a prompt
const response = await analyzePrompt({
  prompt_text: "Your prompt here",
  user_context: "Optional context"
});

console.log('Quality Score:', response.quality_score);
console.log('Suggestions:', response.optimization_suggestions);
```

### React Component

```tsx
import { PromptSuggestions } from './components/PromptSuggestions';

function MyEditor() {
  const [prompt, setPrompt] = useState('');
  
  return (
    <PromptSuggestions
      promptText={prompt}
      onSuggestionApplied={s => console.log('Apply:', s)}
    />
  );
}
```

---

## 📋 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/suggestions/analyze` | POST | Analyze prompt and get suggestions |
| `/api/v1/suggestions/health` | GET | Check agent availability |
| `/api/v1/suggestions/examples` | GET | Get example prompts |

---

## 🔧 Configuration

### Backend Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional
CORS_ORIGINS=http://localhost:5173,https://prompt-vault.com
```

### Frontend Environment Variables

```bash
# Required
VITE_AGENTNAV_API_URL=http://localhost:8080
```

---

## 📦 Files to Copy for Prompt Vault

```bash
# Copy these files to your Prompt Vault frontend:
services/suggestionService.ts
components/PromptSuggestions.tsx
```

---

## 🧪 Testing

```bash
# Run tests
cd backend
pytest tests/test_suggestion_agent.py -v

# Check coverage
pytest tests/test_suggestion_agent.py --cov=agents.suggestion_agent --cov-report=term
```

---

## 📊 Response Structure

```typescript
{
  agent: "suggestion",
  prompt_analyzed: "Your prompt...",
  optimization_suggestions: string[],      // 3-5 suggestions
  structured_output_schema: object | null, // JSON schema
  function_calling_hint: object | null,    // Function definition
  quality_score: number,                   // 1-10
  strengths: string[],
  weaknesses: string[],
  actionable_improvements: string[],
  processing_complete: boolean,
  timestamp: number
}
```

---

## 🎯 Quality Score Interpretation

| Score | Meaning | Color |
|-------|---------|-------|
| 8-10 | Excellent | 🟢 Green |
| 6-7 | Good | 🟡 Yellow |
| 4-5 | Needs Work | 🟠 Orange |
| 1-3 | Poor | 🔴 Red |

---

## 🔍 Common Use Cases

### 1. Basic Prompt Analysis

```typescript
const result = await analyzePrompt({
  prompt_text: "Summarize this document"
});
```

### 2. With Context

```typescript
const result = await analyzePrompt({
  prompt_text: "Summarize this document",
  user_context: "For a technical audience"
});
```

### 3. Schema Refinement

```typescript
const result = await analyzePrompt({
  prompt_text: "Generate user profile",
  existing_schema: { type: "object", properties: {...} }
});
```

---

## 🐛 Troubleshooting

### Agent Unavailable
```bash
# Check backend health
curl http://localhost:8080/healthz

# Check agent status
curl http://localhost:8080/api/agents/status
```

### CORS Error
```bash
# Add your domain to CORS_ORIGINS
export CORS_ORIGINS="http://localhost:5173,https://your-domain.com"
```

### Slow Response
- Check Gemini API quota
- Verify network connectivity
- Consider implementing caching

---

## 📚 Documentation

- **Full Guide:** `docs/FR201_PROMPT_VAULT_INTEGRATION.md`
- **Implementation Summary:** `FR201_IMPLEMENTATION_SUMMARY.md`
- **Code:** `backend/agents/suggestion_agent.py`

---

## ✅ Acceptance Criteria (All Met)

- [x] Suggestion Agent created
- [x] API endpoint implemented
- [x] Structured output generation
- [x] Frontend integration ready
- [x] Tests with 70%+ coverage
- [x] Documentation complete

---

**Need Help?** Check the full documentation in `docs/FR201_PROMPT_VAULT_INTEGRATION.md`
