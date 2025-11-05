"""A2A Protocol message types and structures."""
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """A2A Protocol message types."""
    # Orchestrator messages
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    
    # Agent request/response messages
    ANALYZE_REQUEST = "analyze_request"
    ANALYZE_COMPLETE = "analyze_complete"
    OPTIMIZE_REQUEST = "optimize_request"
    OPTIMIZATION_COMPLETE = "optimization_complete"
    TEST_REQUEST = "test_request"
    TEST_COMPLETE = "test_complete"
    COMPARE_REQUEST = "compare_request"
    COMPARISON_COMPLETE = "comparison_complete"
    SUGGEST_REQUEST = "suggest_request"
    SUGGESTION_COMPLETE = "suggestion_complete"
    
    # Agent collaboration messages
    ANALYSIS_RESULT = "analysis_result"
    WEAKNESS_DETECTED = "weakness_detected"
    OPTIMIZATION_SUGGESTION = "optimization_suggestion"
    TEST_RESULTS = "test_results"
    BEST_VERSION_FOUND = "best_version_found"
    PATTERN_LEARNED = "pattern_learned"
    
    # Error messages
    AGENT_ERROR = "agent_error"
    WORKFLOW_ERROR = "workflow_error"


class A2AMessage(BaseModel):
    """A2A Protocol message structure."""
    from_agent: str = Field(..., description="Source agent name")
    to_agent: str = Field(..., description="Target agent name")
    message_type: MessageType = Field(..., description="Message type")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    session_id: str = Field(..., description="Session identifier")
    workflow_id: Optional[str] = Field(None, description="Workflow identifier")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Message timestamp")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request/response tracking")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "from_agent": "orchestrator",
                "to_agent": "analyzer",
                "message_type": "analyze_request",
                "payload": {"prompt_id": "uuid", "prompt": "..."},
                "session_id": "session_123",
                "workflow_id": "workflow_456",
            }
        }
    }


class A2AProtocol:
    """A2A Protocol handler for message routing and processing."""
    
    def __init__(self, firestore_client):
        """Initialize A2A Protocol handler."""
        self.firestore_client = firestore_client
        self.message_handlers: Dict[str, list] = {}
    
    async def send_message(self, message: A2AMessage) -> None:
        """Send an A2A message and persist it to Firestore."""
        # Persist message to Firestore
        await self.firestore_client.save_a2a_message(
            message.session_id,
            message.model_dump()
        )
    
    async def register_handler(self, message_type: MessageType, handler: callable) -> None:
        """Register a message handler for a specific message type."""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    async def process_message(self, message: A2AMessage) -> Optional[Dict[str, Any]]:
        """Process an A2A message by calling registered handlers."""
        handlers = self.message_handlers.get(message.message_type, [])
        results = []
        
        for handler in handlers:
            try:
                result = await handler(message)
                if result:
                    results.append(result)
            except Exception as e:
                # Log error but continue processing other handlers
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing message {message.message_type} with handler: {e}")
        
        return results[0] if results else None

