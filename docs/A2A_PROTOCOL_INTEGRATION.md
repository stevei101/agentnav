# A2A Protocol Integration Documentation (FR#027)

## Overview

This document describes the full integration of the **Agent2Agent (A2A) Protocol** in the Agentic Navigator system, implementing formal message schemas, security features, and enhanced traceability.

## Architecture

### Components

1. **Formal Message Schemas** (`models/a2a_messages.py`)
   - Pydantic-based typed message models
   - Security and traceability metadata
   - Message validation and serialization

2. **Security Service** (`services/a2a_security.py`)
   - Cloud Run Workload Identity integration
   - Message signing and verification
   - Authorization policies
   - Security audit logging

3. **Protocol Service** (`services/a2a_protocol.py`)
   - Enhanced A2A Protocol implementation
   - Message queue management
   - Traceability and correlation tracking
   - Integration with security service

4. **Agent Integration** (`agents/base_agent.py`)
   - Backward-compatible agent base class
   - Support for both legacy and enhanced A2A
   - Typed message notifications

## Message Types

### Base Message Structure

All A2A messages inherit from `A2AMessageBase`:

```python
{
    "message_id": "unique_message_id",
    "message_type": "task_delegation|knowledge_transfer|agent_status|...",
    "from_agent": "source_agent_name",
    "to_agent": "target_agent_name (or * for broadcast)",
    "priority": "low|medium|high|critical",
    "status": "pending|processing|completed|failed",
    "timestamp": 1699999999.0,
    "ttl_seconds": 3600,
    "security": {
        "service_account_id": "backend@project.iam.gserviceaccount.com",
        "signature": "hmac_signature",
        "signature_algorithm": "PBKDF2-HMAC-SHA256",
        "verified": true
    },
    "trace": {
        "correlation_id": "session_123_workflow_456",
        "parent_message_id": "parent_msg_id",
        "span_id": "span_abc123",
        "trace_metadata": {}
    },
    "data": {}
}
```

### Specialized Message Types

#### 1. TaskDelegationMessage

Used by Orchestrator to delegate tasks to specialized agents:

```python
from models.a2a_messages import TaskDelegationMessage, A2ATraceContext

message = TaskDelegationMessage(
    message_id="msg_orch_to_summ_001",
    from_agent="orchestrator",
    to_agent="summarizer",
    task_name="create_summary",
    task_parameters={
        "content": "Document text...",
        "content_type": "document"
    },
    expected_output="comprehensive_summary",
    depends_on=[],
    trace=A2ATraceContext(
        correlation_id="session_001_workflow_001"
    )
)
```

#### 2. SummarizationCompletedMessage

Sent by Summarizer Agent upon completion:

```python
from models.a2a_messages import SummarizationCompletedMessage

message = SummarizationCompletedMessage(
    message_id="msg_summ_complete_001",
    from_agent="summarizer",
    to_agent="*",  # Broadcast
    summary_text="This document discusses...",
    insights={
        "word_count": 1500,
        "reading_time_minutes": 7
    },
    content_type="document",
    trace=A2ATraceContext(
        correlation_id="session_001_workflow_001",
        parent_message_id="msg_orch_to_summ_001"
    )
)
```

#### 3. RelationshipMappedMessage

Sent by Linker Agent with entity relationship data:

```python
from models.a2a_messages import RelationshipMappedMessage

message = RelationshipMappedMessage(
    message_id="msg_linker_complete_001",
    from_agent="linker",
    to_agent="visualizer",
    entities=[
        {"id": "entity_1", "label": "Machine Learning", "type": "concept"}
    ],
    relationships=[
        {"from": "entity_1", "to": "entity_2", "type": "relates_to"}
    ],
    entity_count=10,
    relationship_count=15,
    trace=A2ATraceContext(
        correlation_id="session_001_workflow_001"
    )
)
```

#### 4. VisualizationReadyMessage

Sent by Visualizer Agent with final visualization:

```python
from models.a2a_messages import VisualizationReadyMessage

message = VisualizationReadyMessage(
    message_id="msg_viz_ready_001",
    from_agent="visualizer",
    to_agent="*",
    visualization_type="MIND_MAP",
    graph_json={
        "type": "MIND_MAP",
        "nodes": [...],
        "edges": [...]
    },
    node_count=12,
    edge_count=18,
    generation_method="gemma-gpu-service",
    trace=A2ATraceContext(
        correlation_id="session_001_workflow_001"
    )
)
```

#### 5. KnowledgeTransferMessage

Generic message for sharing intermediate results:

```python
from models.a2a_messages import KnowledgeTransferMessage

message = KnowledgeTransferMessage(
    message_id="msg_knowledge_001",
    from_agent="summarizer",
    to_agent="linker",
    knowledge_type="summary_context",
    knowledge_data={
        "summary": "Document summary...",
        "key_themes": ["theme1", "theme2"]
    },
    trace=A2ATraceContext(
        correlation_id="session_001_workflow_001"
    )
)
```

#### 6. AgentStatusMessage

Broadcast agent state changes:

```python
from models.a2a_messages import AgentStatusMessage

message = AgentStatusMessage(
    message_id="msg_status_001",
    from_agent="summarizer",
    to_agent="*",
    agent_status="completed",
    processing_time_seconds=5.23,
    result_summary="Generated summary with 500 words",
    trace=A2ATraceContext(
        correlation_id="session_001_workflow_001"
    )
)
```

## Security Features

### Workload Identity Integration

The security service integrates with Cloud Run Workload Identity:

```python
from services.a2a_security import get_security_service

security_service = get_security_service()

# Retrieve current Service Account identity
identity = security_service.identity
print(f"Service Account: {identity.email}")
print(f"Project ID: {identity.project_id}")
```

### Message Signing

All messages are automatically signed using HMAC-SHA256:

```python
# Sign message
message_dict = message.model_dump()
enhanced = security_service.enhance_message_with_security(message_dict)

# Signature is added to security context
print(f"Signature: {enhanced['security']['signature']}")
```

### Message Verification

Messages are verified before processing:

```python
# Comprehensive validation
validation_result = security_service.validate_message_security(message_dict)

if validation_result['is_valid']:
    print(f"✅ Valid message (score: {validation_result['security_score']}/100)")
else:
    print(f"❌ Invalid: {validation_result['issues']}")
```

### Authorization Policies

Authorization rules control agent-to-agent communication:

```python
# Check authorization
is_authorized = security_service.authorize_agent_communication(
    from_agent="orchestrator",
    to_agent="summarizer",
    service_account_email="backend@project.iam.gserviceaccount.com"
)

# Authorization rules:
# - Orchestrator can send to anyone
# - Specialized agents can send to orchestrator, visualizer, and broadcast
```

## Using the Enhanced A2A Protocol

### Initialize Workflow with Enhanced A2A

```python
from agents import AgentWorkflow

# Create workflow with enhanced A2A Protocol
workflow = AgentWorkflow(
    session_id="session_123",
    use_enhanced_a2a=True
)
```

### Send Typed Messages

```python
from services.a2a_protocol import (
    create_task_delegation_message,
    create_knowledge_transfer_message
)

# Create typed message
message = create_task_delegation_message(
    from_agent="orchestrator",
    to_agent="summarizer",
    task_name="create_summary",
    task_parameters={"content": "..."},
    expected_output="summary",
    correlation_id=workflow.a2a.correlation_id
)

# Send message (automatically signed and validated)
await workflow.a2a.send_message(message)
```

### Receive Messages

```python
# Get messages for an agent
messages = await workflow.a2a.get_messages_for_agent(
    agent_name="summarizer",
    message_types=["task_delegation"]  # Optional filter
)

for message in messages:
    print(f"Message: {message.message_type}")
    print(f"From: {message.from_agent}")
    print(f"Security verified: {message.security.verified}")
```

### Get Protocol Statistics

```python
# Get statistics for monitoring
stats = workflow.a2a.get_protocol_stats()

print(f"Total messages: {stats['total_messages']}")
print(f"Pending messages: {stats['pending_messages']}")
print(f"Message types: {stats['message_types']}")
print(f"Agent activity: {stats['agent_activity']}")
```

## Traceability and Logging

### Correlation IDs

All messages in a workflow share a correlation ID:

```python
from models.a2a_messages import create_correlation_id

correlation_id = create_correlation_id("session_123", "workflow_001")
# Output: "session_123_workflow_workflow_001"
```

### Message History

Track all messages for audit and debugging:

```python
# Get message history
history = workflow.a2a.get_message_history(
    agent_name="summarizer",  # Optional filter
    message_type="task_delegation",  # Optional filter
    limit=100
)

for msg in history:
    print(f"{msg.timestamp}: {msg.from_agent} → {msg.to_agent}")
```

### Structured Logging

All A2A events are logged with structured metadata:

```json
{
  "event_type": "message_sent",
  "timestamp": 1699999999.0,
  "session_id": "session_123",
  "correlation_id": "session_123_workflow_001",
  "a2a_protocol": {
    "message_id": "msg_001",
    "message_type": "task_delegation",
    "from_agent": "orchestrator",
    "to_agent": "summarizer",
    "priority": "high",
    "status": "pending"
  },
  "trace_context": {
    "correlation_id": "session_123_workflow_001",
    "parent_message_id": null
  },
  "security_context": {
    "service_account_id": "backend@project.iam.gserviceaccount.com",
    "verified": true
  }
}
```

## Backward Compatibility

The implementation maintains full backward compatibility:

```python
from agents import AgentWorkflow

# Legacy workflow (uses old A2AProtocol)
legacy_workflow = AgentWorkflow(use_enhanced_a2a=False)

# Enhanced workflow (uses new A2AProtocolService)
enhanced_workflow = AgentWorkflow(use_enhanced_a2a=True)

# Agents automatically detect which protocol they're using
agent = OrchestratorAgent(workflow.a2a)
print(f"Using enhanced A2A: {agent.using_enhanced_a2a}")
```

## Testing

Comprehensive test suite in `test_a2a_protocol.py`:

```bash
cd backend
python3 test_a2a_protocol.py
```

Test coverage:
- ✅ Message schema validation
- ✅ Security features (signing, verification, authentication)
- ✅ Protocol service functionality
- ✅ Agent integration with typed messages

## Environment Configuration

### Required Environment Variables

```bash
# Optional: Specify trusted Service Accounts (comma-separated)
TRUSTED_SERVICE_ACCOUNTS="backend@project.iam.gserviceaccount.com,frontend@project.iam.gserviceaccount.com"

# Optional: Custom signing key (if not using derived key)
A2A_SIGNING_KEY="your-secure-signing-key"

# Optional: Explicitly set Service Account (if not on Cloud Run)
GCP_SERVICE_ACCOUNT_EMAIL="your-sa@project.iam.gserviceaccount.com"
GCP_PROJECT_ID="your-project-id"
```

### Cloud Run Deployment

When deployed to Cloud Run, the security service automatically retrieves the Service Account identity from the metadata service. No additional configuration is needed.

## Best Practices

1. **Always use typed messages**: Use specialized message types instead of generic messages for better type safety and validation.

2. **Include correlation IDs**: Always include correlation IDs in trace context for message tracking.

3. **Use appropriate priorities**: Set message priorities based on urgency:
   - `CRITICAL`: System-critical messages
   - `HIGH`: Task delegation, important updates
   - `MEDIUM`: Knowledge transfer, status updates
   - `LOW`: Informational messages

4. **Set reasonable TTLs**: Configure message TTLs based on expected processing time to prevent stale messages.

5. **Monitor security events**: Review security audit logs regularly for unauthorized access attempts.

6. **Use parent_message_id**: Link related messages using parent_message_id for better traceability.

## Security Considerations

1. **Workload Identity**: Prefer Cloud Run Workload Identity over static Service Account keys.

2. **Trusted Accounts**: Maintain a strict list of trusted Service Account emails.

3. **Message Signatures**: All messages must be signed and verified.

4. **Authorization Policies**: Enforce agent communication policies to prevent unauthorized message routing.

5. **Audit Logging**: All security events are logged for compliance and monitoring.

## Troubleshooting

### Message Validation Fails

Check the validation result for specific issues:

```python
validation_result = security_service.validate_message_security(message_dict)
if not validation_result['is_valid']:
    for issue in validation_result['issues']:
        print(f"Issue: {issue}")
```

Common issues:
- Missing or invalid Service Account ID
- Invalid message signature
- Expired message (TTL exceeded)
- Unauthorized agent communication

### Messages Not Received

Check message queue and history:

```python
# Check pending messages
stats = protocol.get_protocol_stats()
print(f"Pending messages: {stats['pending_messages']}")

# Check message history
history = protocol.get_message_history(agent_name="target_agent")
for msg in history:
    print(f"{msg.message_id}: {msg.status}")
```

### Security Warnings

Review security event logs:

```bash
# Check Cloud Logging for security events
gcloud logging read "jsonPayload.event_type=~'signature_verification_failed|untrusted_service_account|unauthorized_communication'"
```

## Future Enhancements

Potential improvements for future releases:

1. **Message Encryption**: Add end-to-end encryption for sensitive data
2. **Rate Limiting**: Implement per-agent rate limiting
3. **Message Retry**: Add automatic retry for failed messages
4. **Distributed Tracing**: Full integration with Cloud Trace
5. **Metrics Export**: Export A2A metrics to Cloud Monitoring
6. **Message Persistence**: Store messages in Firestore for durability

## References

- [Feature Request #027](https://github.com/stevei101/agentnav/issues/27)
- [Google Agent Development Kit (ADK)](https://cloud.google.com/adk)
- [Cloud Run Workload Identity](https://cloud.google.com/run/docs/securing/service-identity)
- [Pydantic Documentation](https://docs.pydantic.dev/)
