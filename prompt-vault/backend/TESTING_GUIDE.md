# Testing Guide for Suggestion Agent

## Quick Start

### 1. Set Environment Variables

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

### 2. Activate Virtual Environment

```bash
cd prompt-vault/backend
source .venv/bin/activate
```

### 3. Run Test Script

```bash
python3 test_suggestion_agent.py
```

## Testing via API

### Start the Server

```bash
cd prompt-vault/backend
source .venv/bin/activate
export GEMINI_API_KEY="your-key"
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Test Analyze Endpoint

```bash
# Test with prompt text
curl -X POST http://localhost:8080/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_text": "Write a function that sorts a list of numbers."
  }'

# Test with prompt_id (requires user_id)
curl -X POST http://localhost:8080/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_id": "your-prompt-uuid",
    "user_id": "your-user-uuid"
  }'
```

### Test Suggest Endpoint

```bash
curl -X POST http://localhost:8080/api/agents/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {
      "purpose": "Code review assistant",
      "target_model": "gemini-pro",
      "constraints": ["Must output JSON"],
      "examples": []
    },
    "options": {
      "num_suggestions": 3
    }
  }'
```

## Expected Output

### Analyze Endpoint Response

```json
{
  "success": true,
  "workflow_id": "uuid",
  "workflow_type": "analyze",
  "result": {
    "success": true,
    "suggestions": {
      "optimization_suggestions": [
        {
          "type": "system_instructions",
          "suggestion": "Add clear system instructions...",
          "priority": "high"
        }
      ],
      "structured_output": {
        "recommended": true,
        "schema": {
          "type": "object",
          "properties": {...}
        }
      },
      "function_calling": {
        "recommended": false,
        "functions": []
      },
      "assessment": {
        "strength_score": 7,
        "strengths": ["Clear task", "Specific"],
        "weaknesses": ["Missing examples"],
        "priority_improvements": ["Add examples", "Clarify output format"]
      }
    },
    "analysis": {
      "prompt_length": 45,
      "has_system_instructions": false,
      "has_examples": false,
      "has_constraints": false
    }
  }
}
```

### Suggest Endpoint Response

```json
{
  "success": true,
  "workflow_id": "uuid",
  "workflow_type": "suggest",
  "result": {
    "success": true,
    "suggestions": [
      {
        "prompt": "You are a code review assistant...",
        "rationale": "Based on requirements...",
        "confidence": 0.87,
        "features": ["system_instructions", "structured_output", "examples"]
      }
    ]
  }
}
```

## Troubleshooting

### Error: "Gemini API not configured"

**Solution:** Make sure `GEMINI_API_KEY` is exported:
```bash
export GEMINI_API_KEY="your-key"
echo $GEMINI_API_KEY  # Verify it's set
```

### Error: "Failed to generate suggestions"

**Possible causes:**
1. Invalid API key
2. API quota exceeded
3. Network issues
4. Gemini API service unavailable

**Check:**
- Verify API key is correct
- Check Gemini API status
- Review error logs for details

### Error: "Failed to parse JSON from Gemini response"

**Solution:** The agent will return raw response as fallback. This is expected behavior if Gemini returns non-JSON format. The parsing can be improved in future iterations.

## Testing Checklist

- [ ] Test analyze endpoint with prompt_text
- [ ] Test analyze endpoint with prompt_id (requires Supabase setup)
- [ ] Test suggest endpoint with requirements
- [ ] Verify optimization suggestions are returned
- [ ] Verify structured output schema is generated when appropriate
- [ ] Verify function calling suggestions are generated when appropriate
- [ ] Verify overall assessment is included
- [ ] Test error handling (invalid API key, network errors)
- [ ] Test with various prompt types (simple, complex, with examples, etc.)

