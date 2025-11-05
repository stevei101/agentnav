# Prompt Vault Backend

Backend API service for Prompt Vault with multi-agent intelligence powered by Google ADK and A2A Protocol.

## Overview

This FastAPI service provides intelligent prompt management capabilities through a multi-agent architecture:

- **Orchestrator Agent**: Coordinates workflows
- **Analyzer Agent**: Analyzes prompts for improvements
- **Optimizer Agent**: Generates optimized prompt versions
- **Tester Agent**: Tests prompts against various scenarios
- **Comparator Agent**: Compares prompt versions
- **Suggestion Agent**: Generates new prompts based on requirements

## Architecture

See [PROMPT_VAULT_AGENT_ARCHITECTURE_PLAN.md](../../docs/PROMPT_VAULT_AGENT_ARCHITECTURE_PLAN.md) for detailed architecture documentation.

## Local Development

### Prerequisites

- Python 3.11+
- Supabase account and project
- Google Cloud project with Firestore enabled
- Gemini API key

### Setup

1. **Install dependencies**:
   ```bash
   cd prompt-vault/backend
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Create a `.env` file:
   ```bash
   # Application
   ENVIRONMENT=development
   DEBUG=true

   # Supabase
   SUPABASE_URL=https://<project>.supabase.co
   SUPABASE_SERVICE_KEY=<service_role_key>

   # Firestore
   FIRESTORE_PROJECT_ID=<gcp_project_id>
   FIRESTORE_DATABASE_ID=(default)

   # Gemini API
   GEMINI_API_KEY=<api_key>

   # ADK Configuration
   A2A_PROTOCOL_ENABLED=true
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

4. **Test the health endpoint**:
   ```bash
   curl http://localhost:8080/healthz
   ```

## API Endpoints

### Health Checks

- `GET /health` - Basic health check
- `GET /healthz` - Cloud Run health check
- `GET /health/detailed` - Detailed health check with dependencies

### Agent Workflows

- `POST /api/agents/optimize` - Optimize a prompt
- `POST /api/agents/test` - Test a prompt
- `POST /api/agents/compare` - Compare prompt versions
- `POST /api/agents/suggest` - Generate prompt suggestions
- `GET /api/agents/workflow/{workflow_id}` - Get workflow status

See API documentation at `/docs` when running the server.

## Testing

Run tests with pytest:

```bash
pytest tests/ -v --cov=app --cov-report=html
```

The project requires 70% test coverage minimum.

## Deployment

The service is designed to run on Google Cloud Run. See the architecture plan for deployment instructions.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py             # Base Agent class
│   │   ├── orchestrator.py     # Orchestrator Agent
│   │   ├── analyzer.py         # Analyzer Agent (TODO)
│   │   ├── optimizer.py        # Optimizer Agent (TODO)
│   │   ├── tester.py           # Tester Agent (TODO)
│   │   ├── comparator.py       # Comparator Agent (TODO)
│   │   └── suggestion.py       # Suggestion Agent (TODO)
│   ├── a2a/
│   │   ├── __init__.py
│   │   ├── protocol.py         # A2A Protocol
│   │   └── message_bus.py      # Message routing
│   ├── services/
│   │   ├── __init__.py
│   │   ├── supabase_client.py  # Supabase client
│   │   └── firestore_client.py # Firestore client
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py           # Health endpoints
│   │   └── agents.py           # Agent workflow endpoints
│   └── models/
│       ├── __init__.py
│       └── workflows.py        # Request/response models
├── tests/                      # Test files (TODO)
├── requirements.txt
├── Dockerfile
└── README.md
```

## Status

**Phase 1 (Foundation) - In Progress**:
- ✅ FastAPI project structure
- ✅ Configuration management
- ✅ Supabase client
- ✅ Firestore client
- ✅ A2A Protocol implementation
- ✅ Base Agent class
- ✅ Orchestrator Agent skeleton
- ✅ API endpoints
- ✅ Health checks
- ⏳ Specialized agents (Phase 2)
- ⏳ Tests (Phase 4)

