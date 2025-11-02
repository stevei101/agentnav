"""
WebSocket Stream Event Models for FR#020 Interactive Agent Dashboard

Pydantic models for real-time event streaming during agent workflow execution.
These models define the schema for all WebSocket messages between backend and frontend.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class AgentStatusEnum(str, Enum):
    """Agent execution status during workflow"""
    QUEUED = "queued"          # Waiting to start
    PROCESSING = "processing"  # Currently executing
    COMPLETE = "complete"      # Finished successfully
    ERROR = "error"            # Failed with error
    SKIPPED = "skipped"        # Skipped (e.g., fallback)


class AgentTypeEnum(str, Enum):
    """Types of agents in the workflow"""
    ORCHESTRATOR = "orchestrator"
    SUMMARIZER = "summarizer"
    LINKER = "linker"
    VISUALIZER = "visualizer"


class ErrorType(str, Enum):
    """Types of errors that can occur during streaming"""
    SERVICE_UNAVAILABLE = "service_unavailable"  # Backend service down
    TIMEOUT = "timeout"                          # Agent exceeded time limit
    VALIDATION_ERROR = "validation_error"        # Invalid input
    WORKFLOW_ERROR = "workflow_error"            # Inter-agent communication failed
    GEMMA_ERROR = "gemma_error"                 # Gemma GPU service error
    FIRESTORE_ERROR = "firestore_error"         # Firestore access failed
    UNKNOWN = "unknown"                         # Unknown error


class EventMetadata(BaseModel):
    """Metadata about event timing and progress"""
    
    elapsed_ms: int = Field(
        ...,
        description="Milliseconds since workflow start"
    )
    step: int = Field(
        ...,
        ge=1,
        le=4,
        description="Current step number (1-4)"
    )
    total_steps: int = Field(
        default=4,
        description="Total steps in workflow"
    )
    agent_sequence: List[str] = Field(
        default=["orchestrator", "summarizer", "linker", "visualizer"],
        description="Order of agents in workflow"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "elapsed_ms": 1234,
                "step": 2,
                "total_steps": 4,
                "agent_sequence": ["orchestrator", "summarizer", "linker", "visualizer"]
            }
        }


class ErrorPayload(BaseModel):
    """Error details within event payload"""
    
    error: str = Field(
        ...,
        description="Error type/name"
    )
    error_type: ErrorType = Field(
        ...,
        description="Categorized error type"
    )
    error_details: Optional[str] = Field(
        default=None,
        description="Detailed error message"
    )
    recoverable: bool = Field(
        default=False,
        description="Whether the error can be recovered"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "SummarizationError",
                "error_type": "timeout",
                "error_details": "Gemma service timeout after 30 seconds",
                "recoverable": False
            }
        }


class AgentEventPayload(BaseModel):
    """Payload data from agent processing"""
    
    # Summarizer outputs
    summary: Optional[str] = Field(
        default=None,
        description="Generated summary text"
    )
    
    # Linker outputs
    entities: Optional[List[str]] = Field(
        default=None,
        description="List of identified entities"
    )
    relationships: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of entity relationships"
    )
    
    # Visualizer outputs
    visualization: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Graph visualization data"
    )
    
    # Error information
    error: Optional[ErrorPayload] = Field(
        default=None,
        description="Error details if status is 'error'"
    )
    
    # Partial/streaming results
    partial_results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Partial results during processing"
    )
    
    # Metrics
    metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Performance metrics (latency, tokens, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "This document describes the key features...",
                "entities": None,
                "relationships": None,
                "visualization": None,
                "error": None,
                "partial_results": None,
                "metrics": {
                    "processing_time_ms": 1234,
                    "tokens_used": 450
                }
            }
        }


class AgentStreamEvent(BaseModel):
    """Complete WebSocket event message"""
    
    id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}",
        description="Unique event ID"
    )
    agent: AgentTypeEnum = Field(
        ...,
        description="Which agent generated this event"
    )
    status: AgentStatusEnum = Field(
        ...,
        description="Current status of the agent"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="ISO 8601 timestamp of event"
    )
    metadata: EventMetadata = Field(
        ...,
        description="Event timing and progress metadata"
    )
    payload: AgentEventPayload = Field(
        default_factory=AgentEventPayload,
        description="Event payload with results or error"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "evt_abc12345",
                "agent": "summarizer",
                "status": "complete",
                "timestamp": "2025-11-02T12:34:56.789Z",
                "metadata": {
                    "elapsed_ms": 2345,
                    "step": 2,
                    "total_steps": 4,
                    "agent_sequence": ["orchestrator", "summarizer", "linker", "visualizer"]
                },
                "payload": {
                    "summary": "This document covers...",
                    "entities": None,
                    "relationships": None,
                    "visualization": None,
                    "error": None,
                    "metrics": {"processing_time_ms": 2340}
                }
            }
        }


class WorkflowStreamRequest(BaseModel):
    """Request body for WebSocket stream endpoint"""
    
    document: str = Field(
        ...,
        min_length=1,
        max_length=100000,  # 100KB limit
        description="Document or code content to analyze"
    )
    content_type: Optional[str] = Field(
        default="document",
        pattern="^(document|codebase)$",
        description="Type of content: 'document' or 'codebase'"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include detailed metadata in events"
    )
    include_partial_results: bool = Field(
        default=True,
        description="Include partial results during processing"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document": "This is the document to analyze...",
                "content_type": "document",
                "include_metadata": True,
                "include_partial_results": True
            }
        }


class WorkflowStreamResponse(BaseModel):
    """Response body with final workflow results"""
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    workflow_status: str = Field(
        ...,
        description="Final workflow status"
    )
    completed_agents: List[str] = Field(
        default=[],
        description="List of successfully completed agents"
    )
    total_execution_time_ms: int = Field(
        ...,
        description="Total execution time in milliseconds"
    )
    events_count: int = Field(
        default=0,
        description="Total events streamed"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Final summary text"
    )
    visualization: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Final visualization data"
    )
    error: Optional[ErrorPayload] = Field(
        default=None,
        description="Error information if workflow failed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_abc123",
                "workflow_status": "completed",
                "completed_agents": ["orchestrator", "summarizer", "linker", "visualizer"],
                "total_execution_time_ms": 5234,
                "events_count": 8,
                "summary": "...",
                "visualization": {...},
                "error": None
            }
        }


class ClientCommand(BaseModel):
    """Commands client can send to server during streaming"""
    
    action: str = Field(
        ...,
        pattern="^(cancel|pause|resume)$",
        description="Action to perform"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for the action"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "cancel",
                "reason": "User clicked cancel button"
            }
        }


# Event factory functions for common event types

def create_agent_queued_event(
    agent: AgentTypeEnum,
    step: int,
    elapsed_ms: int = 0
) -> AgentStreamEvent:
    """Create a 'queued' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.QUEUED,
        metadata=EventMetadata(
            elapsed_ms=elapsed_ms,
            step=step,
            total_steps=4
        ),
        payload=AgentEventPayload()
    )


def create_agent_processing_event(
    agent: AgentTypeEnum,
    step: int,
    elapsed_ms: int,
    partial_results: Optional[Dict[str, Any]] = None
) -> AgentStreamEvent:
    """Create a 'processing' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.PROCESSING,
        metadata=EventMetadata(
            elapsed_ms=elapsed_ms,
            step=step,
            total_steps=4
        ),
        payload=AgentEventPayload(
            partial_results=partial_results
        )
    )


def create_agent_complete_event(
    agent: AgentTypeEnum,
    step: int,
    elapsed_ms: int,
    payload: AgentEventPayload
) -> AgentStreamEvent:
    """Create a 'complete' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.COMPLETE,
        metadata=EventMetadata(
            elapsed_ms=elapsed_ms,
            step=step,
            total_steps=4
        ),
        payload=payload
    )


def create_agent_error_event(
    agent: AgentTypeEnum,
    step: int,
    elapsed_ms: int,
    error: str,
    error_type: ErrorType,
    error_details: Optional[str] = None,
    recoverable: bool = False
) -> AgentStreamEvent:
    """Create an 'error' status event"""
    return AgentStreamEvent(
        agent=agent,
        status=AgentStatusEnum.ERROR,
        metadata=EventMetadata(
            elapsed_ms=elapsed_ms,
            step=step,
            total_steps=4
        ),
        payload=AgentEventPayload(
            error=ErrorPayload(
                error=error,
                error_type=error_type,
                error_details=error_details,
                recoverable=recoverable
            )
        )
    )
