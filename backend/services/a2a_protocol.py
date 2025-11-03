"""
Enhanced A2A Protocol Service (Feature Request #027)

Implements the formal Agent2Agent (A2A) Protocol with:
- Typed message handling using Pydantic models
- Security verification via Workload Identity
- Comprehensive traceability and logging
- Message queue management with priorities

This replaces the basic A2AProtocol class in base_agent.py with
a production-ready implementation.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Type, Union
from collections import defaultdict
import json

from models.a2a_messages import (
    A2AMessageBase,
    TaskDelegationMessage,
    SummarizationCompletedMessage,
    RelationshipMappedMessage,
    VisualizationReadyMessage,
    KnowledgeTransferMessage,
    AgentStatusMessage,
    A2AMessagePriority,
    A2AMessageStatus,
    create_message_id,
    create_correlation_id,
)
from services.a2a_security import get_security_service

logger = logging.getLogger(__name__)


class A2AProtocolService:
    """
    Enhanced A2A Protocol Service with security and traceability

    Manages all agent-to-agent communication using formal message schemas,
    security verification, and comprehensive logging.
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize A2A Protocol Service

        Args:
            session_id: Optional session ID for correlation tracking
        """
        self.session_id = session_id or f"session_{int(time.time())}"
        self.correlation_id = create_correlation_id(self.session_id)

        # Message queue (priority-sorted)
        self._message_queue: List[A2AMessageBase] = []

        # Message history for traceability
        self._message_history: List[A2AMessageBase] = []

        # Shared context store (for backward compatibility)
        self._context_store: Dict[str, Any] = {}

        # Message subscriptions (agent -> message_types)
        self._subscriptions: Dict[str, List[str]] = defaultdict(list)

        # Security service
        self._security_service = get_security_service()

        logger.info(f"🔄 A2A Protocol Service initialized")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   Correlation ID: {self.correlation_id}")

    async def send_message(self, message: A2AMessageBase):
        """
        Send an A2A Protocol message with security and traceability

        Args:
            message: A2AMessageBase or subclass instance

        Raises:
            ValueError: If message validation fails
            SecurityError: If security validation fails
        """
        try:
            # Ensure message has trace context
            if not hasattr(message, "trace") or not message.trace:
                from models.a2a_messages import A2ATraceContext

                message.trace = A2ATraceContext(correlation_id=self.correlation_id)

            # Convert to dict for security processing
            message_dict = message.model_dump()

            # Add security context
            message_dict = self._security_service.enhance_message_with_security(
                message_dict
            )

            # Validate security
            validation_result = self._security_service.validate_message_security(
                message_dict
            )

            if not validation_result["is_valid"]:
                logger.error(
                    f"❌ Message security validation failed: {validation_result['issues']}"
                )
                raise ValueError(
                    f"Security validation failed: {validation_result['issues']}"
                )

            # Update message with security context
            message.security.signature = message_dict["security"]["signature"]
            message.security.service_account_id = message_dict["security"][
                "service_account_id"
            ]
            message.security.verified = True

            # Log message with structured metadata
            self._log_message_event("message_sent", message)

            # Add to queue (sorted by priority)
            self._message_queue.append(message)
            self._sort_message_queue()

            # Add to history for traceability
            self._message_history.append(message)

            # Update shared context if it's a knowledge transfer
            if isinstance(message, KnowledgeTransferMessage):
                self._context_store.update(message.knowledge_data)

            logger.info(
                f"📨 A2A Message Sent: {message.from_agent} → {message.to_agent} "
                f"[{message.message_type}] (priority: {message.priority})"
            )

        except Exception as e:
            logger.error(f"❌ Failed to send A2A message: {e}")
            raise

    async def get_messages_for_agent(
        self, agent_name: str, message_types: Optional[List[str]] = None
    ) -> List[A2AMessageBase]:
        """
        Get pending messages for a specific agent

        Args:
            agent_name: Name of the agent
            message_types: Optional filter for specific message types

        Returns:
            List of messages for the agent
        """
        # Filter messages for this agent
        agent_messages = [
            msg
            for msg in self._message_queue
            if (msg.to_agent == agent_name or msg.to_agent == "*")
            and (not message_types or msg.message_type in message_types)
            and not msg.is_expired()
        ]

        # Remove retrieved messages from queue
        self._message_queue = [
            msg for msg in self._message_queue if msg not in agent_messages
        ]

        # Mark messages as processing
        for msg in agent_messages:
            msg.status = A2AMessageStatus.PROCESSING
            self._log_message_event("message_received", msg, {"recipient": agent_name})

        logger.info(
            f"📥 Retrieved {len(agent_messages)} messages for agent '{agent_name}'"
        )

        return agent_messages

    def _sort_message_queue(self):
        """Sort message queue by priority"""
        priority_order = {
            A2AMessagePriority.CRITICAL: 4,
            A2AMessagePriority.HIGH: 3,
            A2AMessagePriority.MEDIUM: 2,
            A2AMessagePriority.LOW: 1,
        }

        self._message_queue.sort(
            key=lambda m: (priority_order.get(m.priority, 0), -m.timestamp),
            reverse=True,
        )

    def get_shared_context(self) -> Dict[str, Any]:
        """
        Get shared context (for backward compatibility)

        Returns:
            Dictionary of shared context data
        """
        return self._context_store.copy()

    def update_shared_context(self, key: str, value: Any):
        """
        Update shared context (for backward compatibility)

        Args:
            key: Context key
            value: Context value
        """
        self._context_store[key] = value
        logger.debug(f"📋 Updated shared context: {key}")

    def get_message_history(
        self,
        agent_name: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[A2AMessageBase]:
        """
        Get message history for traceability

        Args:
            agent_name: Optional filter by agent
            message_type: Optional filter by message type
            limit: Maximum number of messages to return

        Returns:
            List of historical messages
        """
        history = self._message_history

        # Apply filters
        if agent_name:
            history = [
                msg
                for msg in history
                if msg.from_agent == agent_name or msg.to_agent == agent_name
            ]

        if message_type:
            history = [msg for msg in history if msg.message_type == message_type]

        # Apply limit
        return history[-limit:]

    def get_protocol_stats(self) -> Dict[str, Any]:
        """
        Get protocol statistics for monitoring

        Returns:
            Dictionary of protocol statistics
        """
        message_types = defaultdict(int)
        agent_activity = defaultdict(int)

        for msg in self._message_history:
            message_types[msg.message_type] += 1
            agent_activity[msg.from_agent] += 1

        return {
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "total_messages": len(self._message_history),
            "pending_messages": len(self._message_queue),
            "message_types": dict(message_types),
            "agent_activity": dict(agent_activity),
            "shared_context_keys": list(self._context_store.keys()),
        }

    def _log_message_event(
        self,
        event_type: str,
        message: A2AMessageBase,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Log message event with structured metadata for Cloud Logging

        Args:
            event_type: Type of event (message_sent, message_received, etc.)
            message: The A2A message
            additional_data: Additional event data
        """

        # Helper to safely extract enum values
        def get_enum_value(field, enum_type):
            """Extract enum value safely"""
            return field.value if isinstance(field, enum_type) else field

        # Build structured log entry
        log_entry = {
            "event_type": event_type,
            "timestamp": time.time(),
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "a2a_protocol": {
                "message_id": message.message_id,
                "message_type": message.message_type,
                "from_agent": message.from_agent,
                "to_agent": message.to_agent,
                "priority": get_enum_value(message.priority, A2AMessagePriority),
                "status": get_enum_value(message.status, A2AMessageStatus),
            },
            "trace_context": {
                "correlation_id": (
                    message.trace.correlation_id if hasattr(message, "trace") else None
                ),
                "parent_message_id": (
                    message.trace.parent_message_id
                    if hasattr(message, "trace")
                    else None
                ),
            },
            "security_context": {
                "service_account_id": (
                    message.security.service_account_id
                    if hasattr(message, "security")
                    else None
                ),
                "verified": (
                    message.security.verified if hasattr(message, "security") else False
                ),
            },
        }

        if additional_data:
            log_entry.update(additional_data)

        # In production, this would send to Cloud Logging with proper severity
        logger.info(f"A2A_EVENT: {json.dumps(log_entry, default=str)}")

    def subscribe_agent(self, agent_name: str, message_types: List[str]):
        """
        Subscribe an agent to specific message types

        Args:
            agent_name: Name of the agent
            message_types: List of message types to subscribe to
        """
        self._subscriptions[agent_name].extend(message_types)
        logger.info(f"📢 Agent '{agent_name}' subscribed to: {message_types}")

    async def broadcast_message(self, message: A2AMessageBase):
        """
        Broadcast message to all subscribed agents

        Args:
            message: Message to broadcast
        """
        message.to_agent = "*"
        await self.send_message(message)


# ============================================================================
# Helper Functions for Creating Typed Messages
# ============================================================================


def create_task_delegation_message(
    from_agent: str,
    to_agent: str,
    task_name: str,
    task_parameters: Dict[str, Any],
    expected_output: str,
    correlation_id: str,
    depends_on: Optional[List[str]] = None,
    parent_message_id: Optional[str] = None,
) -> TaskDelegationMessage:
    """
    Create a typed TaskDelegationMessage

    Args:
        from_agent: Source agent name
        to_agent: Target agent name
        task_name: Name of the task
        task_parameters: Parameters for the task
        expected_output: Description of expected output
        correlation_id: Correlation ID for tracking
        depends_on: Optional list of prerequisite agents
        parent_message_id: Optional parent message ID

    Returns:
        TaskDelegationMessage instance
    """
    from models.a2a_messages import A2ATraceContext

    return TaskDelegationMessage(
        message_id=create_message_id(from_agent, "task_delegation"),
        from_agent=from_agent,
        to_agent=to_agent,
        task_name=task_name,
        task_parameters=task_parameters,
        expected_output=expected_output,
        depends_on=depends_on or [],
        priority=A2AMessagePriority.HIGH,
        trace=A2ATraceContext(
            correlation_id=correlation_id, parent_message_id=parent_message_id
        ),
    )


def create_knowledge_transfer_message(
    from_agent: str,
    to_agent: str,
    knowledge_type: str,
    knowledge_data: Dict[str, Any],
    correlation_id: str,
    priority: A2AMessagePriority = A2AMessagePriority.MEDIUM,
    parent_message_id: Optional[str] = None,
) -> KnowledgeTransferMessage:
    """
    Create a typed KnowledgeTransferMessage

    Args:
        from_agent: Source agent name
        to_agent: Target agent name
        knowledge_type: Type of knowledge
        knowledge_data: Knowledge payload
        correlation_id: Correlation ID for tracking
        priority: Message priority
        parent_message_id: Optional parent message ID

    Returns:
        KnowledgeTransferMessage instance
    """
    from models.a2a_messages import A2ATraceContext

    return KnowledgeTransferMessage(
        message_id=create_message_id(from_agent, "knowledge_transfer"),
        from_agent=from_agent,
        to_agent=to_agent,
        knowledge_type=knowledge_type,
        knowledge_data=knowledge_data,
        priority=priority,
        trace=A2ATraceContext(
            correlation_id=correlation_id, parent_message_id=parent_message_id
        ),
    )


def create_status_message(
    from_agent: str,
    agent_status: str,
    correlation_id: str,
    processing_time_seconds: Optional[float] = None,
    error_message: Optional[str] = None,
    result_summary: Optional[str] = None,
    parent_message_id: Optional[str] = None,
) -> AgentStatusMessage:
    """
    Create a typed AgentStatusMessage

    Args:
        from_agent: Source agent name
        agent_status: Agent status (started, completed, failed)
        correlation_id: Correlation ID for tracking
        processing_time_seconds: Optional processing time
        error_message: Optional error message
        result_summary: Optional result summary
        parent_message_id: Optional parent message ID

    Returns:
        AgentStatusMessage instance
    """
    from models.a2a_messages import A2ATraceContext

    return AgentStatusMessage(
        message_id=create_message_id(from_agent, "status"),
        from_agent=from_agent,
        to_agent="*",  # Broadcast status
        agent_status=agent_status,
        processing_time_seconds=processing_time_seconds,
        error_message=error_message,
        result_summary=result_summary,
        priority=A2AMessagePriority.MEDIUM,
        trace=A2ATraceContext(
            correlation_id=correlation_id, parent_message_id=parent_message_id
        ),
    )
