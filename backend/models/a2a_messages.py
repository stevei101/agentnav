"""
Formal A2A Protocol Message Schemas (Feature Request #027)

This module defines typed Pydantic models for Agent2Agent (A2A) Protocol messages,
providing structured, validated communication between agents with built-in security
and traceability features.

Key Features:
- Formal Pydantic message schemas for type safety
- Security metadata (signatures, service account IDs)
- Traceability fields (correlation IDs, timestamps, parent messages)
- Support for Workload Identity authentication
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class A2AMessagePriority(str, Enum):
    """Message priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class A2AMessageStatus(str, Enum):
    """Message processing status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class A2ASecurityContext(BaseModel):
    """
    Security context for A2A messages

    Supports Cloud Run Workload Identity authentication:
    - service_account_id: GCP Service Account email (e.g., backend@project.iam.gserviceaccount.com)
    - signature: HMAC signature of message payload
    - signature_algorithm: Signature algorithm used (default: SHA256)
    """

    service_account_id: Optional[str] = Field(
        None, description="GCP Service Account ID from Cloud Run Workload Identity"
    )
    signature: Optional[str] = Field(None, description="Message signature for verification")
    signature_algorithm: str = Field(
        default="SHA256", description="Algorithm used for signature generation"
    )
    verified: bool = Field(
        default=False, description="Whether the message signature has been verified"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service_account_id": "backend@agentnav-project.iam.gserviceaccount.com",
                "signature": "a3f8b2c1d4e5f6...",
                "signature_algorithm": "SHA256",
                "verified": True,
            }
        }
    )


class A2ATraceContext(BaseModel):
    """
    Traceability context for A2A messages

    Enables comprehensive message tracking and correlation:
    - correlation_id: Tracks all messages in a workflow
    - parent_message_id: Links messages in a conversation chain
    - trace_metadata: Custom metadata for observability
    """

    correlation_id: str = Field(
        ..., description="Unique ID to track all messages in a workflow session"
    )
    parent_message_id: Optional[str] = Field(
        None, description="ID of the parent message in the conversation chain"
    )
    span_id: Optional[str] = Field(
        None, description="Distributed tracing span ID (for Cloud Trace integration)"
    )
    trace_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata for observability and debugging"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "correlation_id": "session_12345_workflow_001",
                "parent_message_id": "msg_orchestrator_001",
                "span_id": "span_abc123",
                "trace_metadata": {"user_id": "user_123", "request_id": "req_456"},
            }
        }
    )


class A2AMessageBase(BaseModel):
    """
    Base A2A Protocol Message

    All specialized message types inherit from this base model.
    Provides common fields for identification, routing, security, and traceability.
    """

    message_id: str = Field(..., description="Unique message identifier")
    message_type: str = Field(
        ..., description="Type of A2A message (e.g., 'task_delegation', 'knowledge_transfer')"
    )
    from_agent: str = Field(..., description="Source agent name")
    to_agent: str = Field(..., description="Target agent name (use '*' for broadcast)")
    priority: A2AMessagePriority = Field(
        default=A2AMessagePriority.MEDIUM, description="Message priority level"
    )
    status: A2AMessageStatus = Field(
        default=A2AMessageStatus.PENDING, description="Current message processing status"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Message creation timestamp (Unix epoch)"
    )
    ttl_seconds: Optional[int] = Field(
        default=3600, description="Time-to-live in seconds (default: 1 hour)"
    )

    # Security context
    security: A2ASecurityContext = Field(
        default_factory=A2ASecurityContext,
        description="Security context for Workload Identity authentication",
    )

    # Traceability context
    trace: A2ATraceContext = Field(..., description="Traceability context for message tracking")

    # Message payload (subclasses define specific structure)
    data: Dict[str, Any] = Field(default_factory=dict, description="Message payload data")

    @field_validator("message_id")
    @classmethod
    def validate_message_id(cls, v: str) -> str:
        """Ensure message_id is not empty"""
        if not v or not v.strip():
            raise ValueError("message_id cannot be empty")
        return v

    @field_validator("from_agent", "to_agent")
    @classmethod
    def validate_agent_names(cls, v: str) -> str:
        """Ensure agent names are valid"""
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        return v

    def is_expired(self) -> bool:
        """Check if message has exceeded its TTL"""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.timestamp) > self.ttl_seconds

    # Note: Signature generation and verification is handled by
    # services.a2a_security.A2ASecurityService for better separation of concerns
    # and to avoid code duplication.

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_summarizer_001",
                "message_type": "knowledge_transfer",
                "from_agent": "summarizer",
                "to_agent": "linker",
                "priority": "high",
                "status": "pending",
                "timestamp": 1699999999.0,
                "ttl_seconds": 3600,
                "security": {
                    "service_account_id": "backend@project.iam.gserviceaccount.com",
                    "signature": "abc123...",
                    "verified": True,
                },
                "trace": {
                    "correlation_id": "session_001",
                    "parent_message_id": "msg_orchestrator_001",
                },
                "data": {},
            }
        }
    )


# ============================================================================
# Specialized Message Types for Agent Communication
# ============================================================================


class TaskDelegationMessage(A2AMessageBase):
    """
    Task delegation message sent from Orchestrator to specialized agents

    Used when the Orchestrator delegates specific analysis tasks to
    Summarizer, Linker, or Visualizer agents.
    """

    message_type: Literal["task_delegation"] = "task_delegation"

    # Task-specific data structure
    task_name: str = Field(..., description="Name of the task being delegated")
    task_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters for task execution"
    )
    expected_output: str = Field(..., description="Description of expected output")
    depends_on: List[str] = Field(
        default_factory=list, description="List of prerequisite agent names"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_orch_to_summ_001",
                "from_agent": "orchestrator",
                "to_agent": "summarizer",
                "task_name": "create_summary",
                "task_parameters": {"content": "Document text...", "content_type": "document"},
                "expected_output": "comprehensive_summary",
                "depends_on": [],
            }
        }
    )


class SummarizationCompletedMessage(A2AMessageBase):
    """
    Message sent by Summarizer Agent upon completion

    Notifies other agents that summarization is complete and
    provides the summary text and insights.
    """

    message_type: Literal["summarization_completed"] = "summarization_completed"

    # Summarization results
    summary_text: str = Field(..., description="Generated summary text")
    insights: Dict[str, Any] = Field(
        default_factory=dict, description="Additional insights from summarization"
    )
    content_type: str = Field(..., description="Type of content summarized")
    word_count: Optional[int] = Field(None, description="Word count of summary")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_summ_complete_001",
                "from_agent": "summarizer",
                "to_agent": "*",
                "summary_text": "This document discusses...",
                "insights": {"word_count": 1500, "reading_time_minutes": 7},
                "content_type": "document",
            }
        }
    )


class RelationshipMappedMessage(A2AMessageBase):
    """
    Message sent by Linker Agent with entity relationship data

    Communicates identified entities and their relationships to
    downstream agents (particularly the Visualizer).
    """

    message_type: Literal["relationship_mapped"] = "relationship_mapped"

    # Entity and relationship data
    entities: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of identified entities"
    )
    relationships: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of relationships between entities"
    )
    entity_count: int = Field(..., description="Number of entities identified")
    relationship_count: int = Field(..., description="Number of relationships identified")
    graph_data: Optional[Dict[str, Any]] = Field(
        None, description="Preliminary graph data structure"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_linker_complete_001",
                "from_agent": "linker",
                "to_agent": "visualizer",
                "entities": [{"id": "entity_1", "label": "Machine Learning", "type": "concept"}],
                "relationships": [{"from": "entity_1", "to": "entity_2", "type": "relates_to"}],
                "entity_count": 10,
                "relationship_count": 15,
            }
        }
    )


class VisualizationReadyMessage(A2AMessageBase):
    """
    Message sent by Visualizer Agent with final visualization

    Communicates the final visualization graph structure, marking
    the completion of the analysis workflow.
    """

    message_type: Literal["visualization_ready"] = "visualization_ready"

    # Visualization data
    visualization_type: str = Field(
        ..., description="Type of visualization (MIND_MAP, DEPENDENCY_GRAPH)"
    )
    graph_json: Dict[str, Any] = Field(..., description="Complete visualization graph structure")
    node_count: int = Field(..., description="Number of nodes in the graph")
    edge_count: int = Field(..., description="Number of edges in the graph")
    generation_method: str = Field(..., description="Method used to generate visualization")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_viz_ready_001",
                "from_agent": "visualizer",
                "to_agent": "*",
                "visualization_type": "MIND_MAP",
                "graph_json": {"type": "MIND_MAP", "nodes": [], "edges": []},
                "node_count": 12,
                "edge_count": 18,
                "generation_method": "gemma-gpu-service",
            }
        }
    )


class KnowledgeTransferMessage(A2AMessageBase):
    """
    Generic knowledge transfer message for agent collaboration

    Used for sharing intermediate results, context updates, or
    other knowledge artifacts between agents.
    """

    message_type: Literal["knowledge_transfer"] = "knowledge_transfer"

    # Knowledge payload
    knowledge_type: str = Field(..., description="Type of knowledge being transferred")
    knowledge_data: Dict[str, Any] = Field(
        default_factory=dict, description="Knowledge payload data"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the knowledge"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_knowledge_001",
                "from_agent": "summarizer",
                "to_agent": "linker",
                "knowledge_type": "summary_context",
                "knowledge_data": {
                    "summary": "Document summary...",
                    "key_themes": ["theme1", "theme2"],
                },
            }
        }
    )


class AgentStatusMessage(A2AMessageBase):
    """
    Agent status notification message

    Used to broadcast agent state changes (started, completed, failed).
    """

    message_type: Literal["agent_status"] = "agent_status"

    # Status information
    agent_status: Literal["started", "in_progress", "completed", "failed"] = Field(
        ..., description="Current agent status"
    )
    processing_time_seconds: Optional[float] = Field(
        None, description="Time taken for processing (if completed)"
    )
    error_message: Optional[str] = Field(None, description="Error message (if failed)")
    result_summary: Optional[str] = Field(
        None, description="Brief summary of results (if completed)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_status_001",
                "from_agent": "summarizer",
                "to_agent": "*",
                "agent_status": "completed",
                "processing_time_seconds": 5.23,
                "result_summary": "Generated summary with 500 words",
            }
        }
    )


# ============================================================================
# Message Factory Functions
# ============================================================================


def create_message_id(agent_name: str, message_type: str) -> str:
    """
    Generate a unique message ID

    Args:
        agent_name: Name of the agent creating the message
        message_type: Type of message being created

    Returns:
        Unique message ID string
    """
    timestamp = int(time.time() * 1000)  # Millisecond precision
    return f"msg_{agent_name}_{message_type}_{timestamp}"


def create_correlation_id(session_id: str, workflow_id: Optional[str] = None) -> str:
    """
    Generate a correlation ID for message tracking

    Args:
        session_id: Session identifier
        workflow_id: Optional workflow identifier

    Returns:
        Correlation ID string
    """
    if workflow_id:
        return f"{session_id}_workflow_{workflow_id}"
    return f"{session_id}_workflow_{int(time.time())}"
