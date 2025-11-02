# Feature Request #005 Implementation Guide

## Overview

This document describes the implementation of Feature Request #005: Core Multi-Agent Workflow Implementation (ADK + A2A Protocol). The implementation provides a complete, sequential multi-agent system using the Google Agent Development Kit (ADK) patterns with the Agent2Agent (A2A) Protocol.

## Architecture

### SessionContext Model

The `SessionContext` is the core data structure that flows through the entire multi-agent workflow. It is defined as a Pydantic model in `backend/models/context_model.py`.

**Key Fields:**

- `raw_input`: Original document/codebase content
- `summary_text`: Output from Summarizer Agent
- `key_entities`: List of key entities from Linker Agent
- `relationships`: List of entity relationships from Linker Agent
- `graph_json`: Final visualization JSON from Visualizer Agent
- `completed_agents`: Track which agents have completed
- `workflow_status`: Current workflow state
- `errors`: List of any errors encountered

### Sequential Workflow

The workflow executes agents in a strict order:

1. **Orchestrator Agent**: Analyzes content type and delegates tasks
2. **Summarizer Agent**: Creates comprehensive summary → updates `summary_text`
3. **Linker Agent**: Identifies entities and relationships → updates `key_entities` and `relationships`
4. **Visualizer Agent**: Generates visualization → updates `graph_json`

After each agent completes, the `SessionContext` is persisted to Firestore in the `agent_context` collection for fault tolerance.

### Agent2Agent (A2A) Protocol

Agents communicate via structured A2A messages:

```python
A2AMessage(
    message_id="unique_id",
    from_agent="source_agent",
    to_agent="target_agent",
    message_type="task_delegation|context_update|agent_complete",
    data={"key": "value"},
    priority=1-5
)
```

The A2A Protocol handles:

- Message queuing and priority
- Shared context management
- Agent completion notifications
- Error propagation

## API Usage

### `/api/analyze` Endpoint

**Request:**

```json
{
  "document": "Your document or code content here...",
  "content_type": "document" // or "codebase"
}
```

**Response:**

```json
{
  "summary": "Generated summary text...",
  "visualization": {
    "type": "MIND_MAP",
    "title": "Content Analysis",
    "nodes": [...],
    "edges": [...]
  },
  "agent_workflow": {
    "session_id": "session_123456",
    "workflow_status": "completed",
    "completed_agents": ["orchestrator", "summarizer", "linker", "visualizer"],
    "total_agents": 4,
    "errors": [],
    "firestore_persisted": true
  },
  "processing_time": 5.23
}
```

## Code Examples

### Creating a SessionContext

```python
from models.context_model import SessionContext

context = SessionContext(
    session_id="unique_session_id",
    raw_input="Your document content...",
    content_type="document"
)
```

### Running the Sequential Workflow

```python
from agents import AgentWorkflow, OrchestratorAgent, SummarizerAgent, LinkerAgent, VisualizerAgent
from models.context_model import SessionContext

# Create workflow
workflow = AgentWorkflow()

# Initialize and register agents
orchestrator = OrchestratorAgent(workflow.a2a)
summarizer = SummarizerAgent(workflow.a2a)
linker = LinkerAgent(workflow.a2a)
visualizer = VisualizerAgent(workflow.a2a)

workflow.register_agent(orchestrator)
workflow.register_agent(summarizer)
workflow.register_agent(linker)
workflow.register_agent(visualizer)

# Create initial context
context = SessionContext(
    session_id="session_001",
    raw_input="Document content...",
    content_type="document"
)

# Execute sequential workflow
result_context = await workflow.execute_sequential_workflow(context)

# Access results
print(f"Summary: {result_context.summary_text}")
print(f"Entities: {result_context.key_entities}")
print(f"Graph: {result_context.graph_json}")
```

### Persisting SessionContext to Firestore

```python
from services.context_persistence import get_persistence_service

persistence = get_persistence_service()

# Save context
await persistence.save_context(context)

# Load context
loaded_context = await persistence.load_context("session_001")

# Delete context
await persistence.delete_context("session_001")
```

## Testing

### Running Tests

```bash
# Run FR#005 specific tests
cd backend
python3 test_fr005_workflow.py

# Run all ADK tests
python3 test_adk_system.py
```

### Test Coverage

The test suite validates:

- ✅ SessionContext model creation and validation
- ✅ Pydantic serialization/deserialization
- ✅ Sequential workflow execution
- ✅ Agent result mapping to SessionContext
- ✅ Firestore persistence operations
- ✅ Error handling and graceful degradation

## Firestore Schema

### `agent_context` Collection

Documents in this collection use `session_id` as the document ID.

```json
{
  "session_id": "session_123456",
  "content_type": "document",
  "timestamp": 1234567890.123,
  "raw_input": "Document content...",
  "summary_text": "Summary...",
  "key_entities": ["Entity1", "Entity2"],
  "relationships": [
    {
      "source": "Entity1",
      "target": "Entity2",
      "type": "relates_to",
      "label": "relates to",
      "confidence": "high"
    }
  ],
  "graph_json": {
    "type": "MIND_MAP",
    "nodes": [...],
    "edges": [...]
  },
  "completed_agents": ["orchestrator", "summarizer", "linker", "visualizer"],
  "current_agent": null,
  "workflow_status": "completed",
  "errors": []
}
```

## Configuration

### Environment Variables

- `FIRESTORE_PROJECT_ID`: GCP project ID (default: "agentnav-dev")
- `FIRESTORE_DATABASE_ID`: Firestore database ID (default: "default")
- `FIRESTORE_EMULATOR_HOST`: Firestore emulator host for local dev (e.g., "localhost:8080")
- `GEMMA_SERVICE_URL`: URL for Gemma GPU service
- `ENVIRONMENT`: Deployment environment ("development", "staging", "production")

### Local Development with Firestore Emulator

```bash
# Start Firestore emulator
make start-firestore

# Set environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080
export FIRESTORE_PROJECT_ID=agentnav-dev

# Run tests
make test-backend
```

## Error Handling

The system implements graceful degradation:

1. **Firestore Unavailable**: Workflow continues without persistence
2. **Gemma Service Unavailable**: Falls back to rule-based processing
3. **Individual Agent Failure**: Workflow continues, marks agent as complete with error
4. **Partial Results**: Returns best-effort results even with failures

Errors are logged and included in the `SessionContext.errors` list for debugging.

## Performance Considerations

- **Sequential Execution**: Agents run one at a time (as required by FR#005)
- **Firestore Persistence**: Small overhead (~50-100ms per save) for fault tolerance
- **Memory Usage**: SessionContext grows as agents add data (typically <1MB per session)
- **Timeout Handling**: Each agent has individual timeout protection

## Future Enhancements

Potential improvements beyond FR#005:

- Parallel execution for independent agents (Summarizer and Linker could run in parallel)
- Context compression for large documents
- Caching of intermediate results
- WebSocket support for real-time progress updates
- Multi-session batch processing

## Support

For issues or questions:

- Check test files: `test_fr005_workflow.py` and `test_adk_system.py`
- Review agent implementations in `backend/agents/`
- See API documentation at `/docs` endpoint when server is running
