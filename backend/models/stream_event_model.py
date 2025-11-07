"""
WebSocket Stream Event Models for FR#020 Interactive Agent Dashboard

Pydantic models for real-time event streaming during agent workflow execution.
These models define the schema for all WebSocket messages between backend and frontend.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class AgentStatusEnum(str, Enum):
    """Agent execution status during workflow"""

    QUEUED = "queued"  # Waiting to start
    PROCESSING = "processing"  # Currently executing
    COMPLETE = "complete"  # Finished successfully
    ERROR = "error"  # Failed with error
    SKIPPED = "skipped"  # Skipped (e.g., fallback)


class AgentTypeEnum(str, Enum):
    """Types of agents in the workflow"""

    ORCHESTRATOR = "orchestrator"
    SUMMARIZER = "summarizer"
    LINKER = "linker"
    VISUALIZER = "visualizer"


class ErrorType(str, Enum):
    """Types of errors that can occur during streaming"""

    SERVICE_UNAVAILABLE = "service_unavailable"  # Backend service down
    TIMEOUT = "timeout"  # Agent exceeded time limit
    VALIDATION_ERROR = "validation_error"  # Invalid input
    WORKFLOW_ERROR = "workflow_error"  # Inter-agent communication failed
    FIRESTORE_ERROR = "firestore_error"  # Firestore access failed
    UNKNOWN = "unknown"  # Unknown error


class EventMetadata(BaseModel):
    """Metadata about event timing and progress"""

    elapsed_ms: Optional[int] = Field(
        default=None, description="Milliseconds since workflow start"
    )
    step: Optional[int] = Field(
        default=None, ge=1, le=4, description="Current step number (1-4)"
    )
<<<<<<< HEAD
    total_steps: Optional[int] = Field(
        default=4, description="Total steps in workflow"
    )
=======
    total_steps: Optional[int] = Field(default=4, description="Total steps in workflow")
>>>>>>> origin/main
    agent_sequence: List[str] = Field(
        default_factory=lambda: [
            "orchestrator",
            "summarizer",
            "linker",
            "visualizer",
        ],
        description="Order of agents in workflow",
    )
    session_id: Optional[str] = Field(
        default=None, description="Optional session identifier for event"
    )

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "elapsed_ms": 1234,
                "step": 2,
                "total_steps": 4,
                "agent_sequence": [
                    "orchestrator",
                    "summarizer",
                    "linker",
                    "visualizer",
                ],
            }
        },
    )


class ErrorPayload(BaseModel):
    """Error details within event payload"""

    error: str = Field(..., description="Error type/name")
    error_type: ErrorType = Field(..., description="Categorized error type")
    error_details: Optional[str] = Field(
        default=None, description="Detailed error message"
    )
    recoverable: bool = Field(
        default=False, description="Whether the error can be recovered"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "SummarizationError",
                "error_type": "timeout",
                "error_details": "Service timeout after 30 seconds",
                "recoverable": False,
            }
        }
    )


class EventPayload(BaseModel):
    """Backward-compatible payload schema for streaming events"""

    summary: Optional[str] = Field(default=None, description="Generated summary text")
    entities: Optional[List[str]] = Field(
        default=None, description="List of identified entities"
    )
    relationships: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="List of entity relationships"
    )
    visualization: Optional[Dict[str, Any]] = Field(
        default=None, description="Graph visualization data"
    )
    error: Optional[ErrorPayload] = Field(
        default=None, description="Structured error details"
    )
    error_message: Optional[str] = Field(
        default=None, description="Human-readable error message"
    )
    error_type: Optional[str] = Field(default=None, description="Legacy error type")
    error_details: Optional[str] = Field(
        default=None, description="Legacy error details"
    )
    recoverable: Optional[bool] = Field(
        default=None, description="Legacy recoverable flag"
    )
    partial_results: Optional[Dict[str, Any]] = Field(
        default=None, description="Partial results during processing"
    )
    metrics: Optional[Dict[str, Any]] = Field(
        default=None, description="Performance metrics (latency, tokens, etc.)"
    )

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "summary": "This document describes the key features...",
                "entities": None,
                "relationships": None,
                "visualization": None,
                "error_message": None,
                "error_type": None,
                "partial_results": None,
                "metrics": {"processing_time_ms": 1234, "tokens_used": 450},
            }
        },
    )

    def model_post_init(self, __context: Any) -> None:  # type: ignore[override]
        # Bridge legacy error fields into structured error payload
        if self.error is None and (self.error_message or self.error_type):
            try:
                error_type_enum = ErrorType(self.error_type or "unknown")
            except ValueError:
                error_type_enum = ErrorType.UNKNOWN

            self.error = ErrorPayload(
                error=self.error_message or "AgentError",
                error_type=error_type_enum,
                error_details=self.error_details,
                recoverable=self.recoverable if self.recoverable is not None else False,
            )


class AgentEventPayload(EventPayload):
    """Alias for newer naming used in backend services"""
<<<<<<< HEAD
=======

>>>>>>> origin/main
    pass


class AgentStreamEvent(BaseModel):
    """Complete WebSocket event message"""

    id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}",
        description="Unique event ID",
    )
    agent: AgentTypeEnum = Field(..., description="Which agent generated this event")
    status: AgentStatusEnum = Field(..., description="Current status of the agent")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp of event",
    )
    metadata: EventMetadata = Field(
        default_factory=EventMetadata, description="Event timing and progress metadata"
    )
    payload: EventPayload = Field(
        default_factory=EventPayload,
        description="Event payload with results or error",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "evt_abc12345",
                "agent": "summarizer",
                "status": "complete",
                "timestamp": "2025-11-02T12:34:56.789Z",
                "metadata": {
                    "elapsed_ms": 2345,
                    "step": 2,
                    "total_steps": 4,
                    "agent_sequence": [
                        "orchestrator",
                        "summarizer",
                        "linker",
                        "visualizer",
                    ],
                },
                "payload": {
                    "summary": "This document covers...",
                    "entities": None,
                    "relationships": None,
                    "visualization": None,
                    "error": None,
                    "metrics": {"processing_time_ms": 2340},
                },
            }
        }
    )


class WorkflowStreamRequest(BaseModel):
    """Request body for WebSocket stream endpoint"""

    document: str = Field(
        ...,
        min_length=1,
        max_length=100000,  # 100KB limit
        description="Document or code content to analyze",
    )
    content_type: Optional[str] = Field(
        default="document",
        pattern="^(document|codebase)$",
        description="Type of content: 'document' or 'codebase'",
    )
    include_metadata: bool = Field(
        default=True, description="Include detailed metadata in events"
    )
    include_partial_results: bool = Field(
        default=True, description="Include partial results during processing"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document": "This is the document to analyze...",
                "content_type": "document",
                "include_metadata": True,
                "include_partial_results": True,
            }
        }
    )


class WorkflowStreamResponse(BaseModel):
    """Response body with final workflow results"""

    session_id: str = Field(..., description="Unique session identifier")
    workflow_status: str = Field(..., description="Final workflow status")
    completed_agents: List[str] = Field(
        default=[], description="List of successfully completed agents"
    )
    total_execution_time_ms: int = Field(
        ..., description="Total execution time in milliseconds"
    )
    events_count: int = Field(default=0, description="Total events streamed")
    summary: Optional[str] = Field(default=None, description="Final summary text")
    visualization: Optional[Dict[str, Any]] = Field(
        default=None, description="Final visualization data"
    )
    error: Optional[ErrorPayload] = Field(
        default=None, description="Error information if workflow failed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "session_abc123",
                "workflow_status": "completed",
                "completed_agents": [
                    "orchestrator",
                    "summarizer",
                    "linker",
                    "visualizer",
                ],
                "total_execution_time_ms": 5234,
                "events_count": 8,
                "summary": "...",
                "visualization": {...},
                "error": None,
            }
        }
    )


class ClientCommand(BaseModel):
    """Commands client can send to server during streaming"""

    action: str = Field(
        ...,
        pattern="^(cancel|pause|resume)$",
        description="Action to perform",
    )
    reason: Optional[str] = Field(default=None, description="Reason for the action")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"action": "cancel", "reason": "User clicked cancel button"}
        }
    )


# Event factory functions for common event types


def create_agent_queued_event(
    agent: AgentTypeEnum, step: int, elapsed_ms: int = 0
) -> AgentStreamEvent:
    """Create a 'queued' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.QUEUED,
        metadata=EventMetadata(elapsed_ms=elapsed_ms, step=step, total_steps=4),
        payload=AgentEventPayload(),
    )


def create_agent_processing_event(
    agent: AgentTypeEnum,
    step: int,
    elapsed_ms: int,
    partial_results: Optional[Dict[str, Any]] = None,
) -> AgentStreamEvent:
    """Create a 'processing' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.PROCESSING,
        metadata=EventMetadata(elapsed_ms=elapsed_ms, step=step, total_steps=4),
        payload=AgentEventPayload(partial_results=partial_results),
    )


def create_agent_complete_event(
    agent: AgentTypeEnum, step: int, elapsed_ms: int, payload: AgentEventPayload
) -> AgentStreamEvent:
    """Create a 'complete' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.COMPLETE,
        metadata=EventMetadata(elapsed_ms=elapsed_ms, step=step, total_steps=4),
        payload=payload,
    )


def create_agent_error_event(
    agent: AgentTypeEnum,
    step: int,
    elapsed_ms: int,
    error: str,
    error_type: ErrorType,
    error_details: Optional[str] = None,
    recoverable: bool = False,
) -> AgentStreamEvent:
    """Create an 'error' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.ERROR,
        metadata=EventMetadata(elapsed_ms=elapsed_ms, step=step, total_steps=4),
        payload=AgentEventPayload(
            error=ErrorPayload(
                error=error,
                error_type=error_type,
                error_details=error_details,
                recoverable=recoverable,
            )
        ),
    )
