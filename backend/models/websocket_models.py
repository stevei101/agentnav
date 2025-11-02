"""
WebSocket Models for Real-time Agent Status Communication
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentName(str, Enum):
    """Agent names matching frontend types"""
    ORCHESTRATOR = "Orchestrator"
    SUMMARIZER = "Summarizer"
    LINKER = "Linker"
    VISUALIZER = "Visualizer"


class AgentStatus(str, Enum):
    """Agent status values matching frontend types"""
    IDLE = "Idle"
    PROCESSING = "Processing"
    DONE = "Done"
    ERROR = "Error"


class MessageType(str, Enum):
    """WebSocket message types"""
    AGENT_STATUS_UPDATE = "agent_status_update"
    AGENT_HANDOFF = "agent_handoff"
    NAVIGATION_START = "navigation_start"
    NAVIGATION_COMPLETE = "navigation_complete"
    NAVIGATION_ERROR = "navigation_error"
    CONNECTION_ACK = "connection_ack"
    HEARTBEAT = "heartbeat"


class BaseMessage(BaseModel):
    """Base class for all WebSocket messages with common timestamp field"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentStatusMessage(BaseMessage):
    """Agent status update message"""
    message_type: MessageType = MessageType.AGENT_STATUS_UPDATE
    agent_name: AgentName
    status: AgentStatus
    details: str
    progress_percentage: Optional[int] = None  # 0-100 for progress bars
    duration_ms: Optional[int] = None  # How long this step took
    metadata: Optional[Dict[str, Any]] = None  # Additional context


class AgentHandoffMessage(BaseMessage):
    """Agent-to-agent handoff message"""
    message_type: MessageType = MessageType.AGENT_HANDOFF
    from_agent: AgentName
    to_agent: AgentName
    handoff_data: Dict[str, Any]  # Data passed between agents
    details: str


class NavigationStartMessage(BaseMessage):
    """Navigation session start message"""
    message_type: MessageType = MessageType.NAVIGATION_START
    session_id: str
    document_preview: str  # First 100 chars of document
    expected_agents: list[AgentName]


class NavigationCompleteMessage(BaseMessage):
    """Navigation session complete message"""
    message_type: MessageType = MessageType.NAVIGATION_COMPLETE
    session_id: str
    total_duration_ms: int
    result_summary: str


class NavigationErrorMessage(BaseMessage):
    """Navigation session error message"""
    message_type: MessageType = MessageType.NAVIGATION_ERROR
    session_id: str
    error_message: str
    failed_agent: Optional[AgentName] = None


class ConnectionAckMessage(BaseMessage):
    """WebSocket connection acknowledgment"""
    message_type: MessageType = MessageType.CONNECTION_ACK
    client_id: str
    server_version: str = "0.1.0"


class HeartbeatMessage(BaseMessage):
    """WebSocket heartbeat message"""
    message_type: MessageType = MessageType.HEARTBEAT


# Union type for all possible WebSocket messages
WebSocketMessage = (
    AgentStatusMessage
    | AgentHandoffMessage
    | NavigationStartMessage
    | NavigationCompleteMessage
    | NavigationErrorMessage
    | ConnectionAckMessage
    | HeartbeatMessage
)


class NavigationRequest(BaseModel):
    """WebSocket navigation request from client"""
    document: str
    content_type: Optional[str] = "document"  # 'document' or 'codebase'
    client_id: Optional[str] = None


class WebSocketResponse(BaseModel):
    """Standard WebSocket response wrapper"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Made with Bob
