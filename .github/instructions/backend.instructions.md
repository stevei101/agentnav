---
applies_to:
  - backend/**/*
  - backend/*
---

# Backend Development Instructions (Python/FastAPI/ADK)

## Technology Stack
- **Python 3.11+** with type hints
- **FastAPI** for async REST API
- **Google Agent Development Kit (ADK)** for agent orchestration
- **Agent2Agent (A2A) Protocol** for inter-agent communication
- **uv** for fast Python package management
- **Firestore** for persistent state and session memory

## Development Setup

### Environment Setup
```bash
cd backend
uv venv                              # Create virtual environment
source .venv/bin/activate            # Activate venv
uv pip install -r requirements.txt   # Install dependencies
```

### Running Locally
```bash
PORT=8080 uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

**CRITICAL:** Always read `PORT` environment variable for Cloud Run compatibility:
```python
import os
port = int(os.getenv('PORT', 8080))
```

## Code Conventions

### FastAPI Routes
- Use async/await for all I/O operations
- Use Pydantic models for request/response validation
- Implement RORO pattern (Receive Object, Return Object)
- Always add proper type hints

**Example:**
```python
from fastapi import APIRouter
from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    content: str
    content_type: str

class AnalyzeResponse(BaseModel):
    summary: str
    visualization: dict

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest):
    # Handler logic...
    return AnalyzeResponse(summary="...", visualization={})
```

### ADK Agent Development
- Inherit from base `Agent` class
- Implement async `process()` method
- Use A2A Protocol for inter-agent communication
- Store agent state in Firestore
- Handle errors gracefully and propagate via A2A Protocol

**Example:**
```python
from google.adk import Agent, A2AProtocol

class SummarizerAgent(Agent):
    async def process(self, context: dict) -> dict:
        result = await self.summarize(context['document'])
        
        # Share via A2A Protocol
        await self.a2a.send_message({
            'agent': 'visualizer',
            'type': 'summary_complete',
            'data': result
        })
        
        return result
```

## Multi-Agent Architecture

The system uses four specialized agents:
1. **Orchestrator Agent** - Team lead, delegates tasks
2. **Summarizer Agent** - Generates content summaries
3. **Linker Agent** - Identifies entity relationships
4. **Visualizer Agent** - Creates graph structures

All agents communicate via A2A Protocol and persist state in Firestore.

## Firestore Integration

### Collections Schema
- `sessions/` - User session data (session_id, agent_states, user_input)
- `knowledge_cache/` - Cached analysis results (content_hash, summary, visualization_data)
- `agent_context/` - Shared agent context (session_id, context_data, last_updated_by)
- `agent_prompts/` - Agent prompt configurations

### Best Practices
- Use async Firestore operations
- Implement connection pooling
- Cache results before reprocessing
- Batch writes for efficiency
- Set TTL on cached entries

## Cloud Run Requirements

**MANDATORY for Cloud Run compatibility:**
1. Read `PORT` environment variable (Cloud Run sets automatically)
2. Bind to `0.0.0.0` (not `127.0.0.1`)
3. Implement `/healthz` health check endpoint
4. Log to stdout/stderr (Cloud Run captures automatically)
5. Handle SIGTERM for graceful shutdown

**Example health check:**
```python
@app.get('/healthz')
async def healthz():
    return {'status': 'healthy'}
```

## Environment Variables

Backend service requires:
- `PORT` - Set by Cloud Run
- `GEMINI_API_KEY` - From Secret Manager
- `GEMMA_SERVICE_URL` - URL of Gemma GPU service
- `FIRESTORE_PROJECT_ID`
- `FIRESTORE_DATABASE_ID`
- `ADK_AGENT_CONFIG_PATH`
- `A2A_PROTOCOL_ENABLED=true`

## Testing Requirements

### Running Tests
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

### Coverage Requirement
**MANDATORY:** All new code must achieve ≥70% test coverage before merge:
```bash
pytest tests/ --cov=. --cov-report=term --cov-fail-under=70
```

### Test Organization
- Unit tests for FastAPI routes
- Unit tests for agent logic
- Integration tests for ADK workflows
- A2A Protocol communication tests
- Firestore operations with mocked clients
- Error handling and edge cases

## Common Pitfalls

❌ **Mistake:** Hardcoding port 8080 instead of reading PORT env var
✅ **Solution:** `port = int(os.getenv('PORT', 8080))`

❌ **Mistake:** Binding to 127.0.0.1 instead of 0.0.0.0
✅ **Solution:** `uvicorn.run(app, host='0.0.0.0', port=port)`

❌ **Mistake:** Missing /healthz endpoint
✅ **Solution:** Add `@app.get('/healthz')` that returns 200 OK

❌ **Mistake:** Not handling ADK agent failures
✅ **Solution:** Implement try/except, propagate errors via A2A Protocol

## Security Requirements

1. **Never embed credentials** in code or containers
2. Use **Secret Manager** for all secrets
3. Use **Workload Identity** for Cloud Run service authentication
4. Validate and sanitize all user inputs with Pydantic
5. Implement rate limiting
6. Use least-privilege IAM roles

## Performance Optimization

- Use async Firestore operations
- Cache analysis results in Firestore
- Implement connection pooling for Firestore clients
- Call Gemma GPU service only for complex tasks
- Cache GPU service results to reduce redundant inference
