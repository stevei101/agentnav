"""
Event Emitter Service for FR#020 WebSocket Streaming

Manages event queuing and broadcasting to connected WebSocket clients.
Allows agents to emit status events that are streamed to frontend in real-time.
"""

import asyncio
import logging
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
import json

from backend.models.stream_event_model import (
    AgentStreamEvent,
    AgentStatusEnum,
    AgentTypeEnum,
    AgentEventPayload,
    ErrorType,
    ErrorPayload,
    EventMetadata,
    create_agent_queued_event,
    create_agent_processing_event,
    create_agent_complete_event,
    create_agent_error_event,
)

logger = logging.getLogger(__name__)


class EventEmitter:
    """
    Manages event emission and broadcasting to WebSocket clients.

    Each workflow session has its own event emitter instance.
    Agents emit events through this service, which queues and broadcasts them.
    """

    def __init__(self, session_id: str):
        """
        Initialize event emitter for a session.

        Args:
            session_id: Unique identifier for the workflow session
        """
        self.session_id = session_id
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.connected_clients: Set[asyncio.Queue] = set()
        self.events_emitted: List[AgentStreamEvent] = []
        self.start_time: float = datetime.utcnow().timestamp() * 1000
        self.logger = logger.getChild(f"emitter.{session_id[:8]}")

        self.logger.info(f"📡 EventEmitter initialized for session {session_id}")

    def register_client(self, client_queue: asyncio.Queue) -> None:
        """
        Register a new WebSocket client to receive events.

        Args:
            client_queue: AsyncIO queue for sending events to client
        """
        self.connected_clients.add(client_queue)
        self.logger.debug(
            f"✅ Client registered. Total clients: {len(self.connected_clients)}"
        )

    def unregister_client(self, client_queue: asyncio.Queue) -> None:
        """
        Unregister a WebSocket client.

        Args:
            client_queue: Client queue to unregister
        """
        self.connected_clients.discard(client_queue)
        self.logger.debug(
            f"❌ Client unregistered. Total clients: {len(self.connected_clients)}"
        )

    def _calculate_elapsed_ms(self) -> int:
        """Calculate milliseconds elapsed since workflow start."""
        current_time = datetime.utcnow().timestamp() * 1000
        return int(current_time - self.start_time)

    async def emit_event(self, event: AgentStreamEvent) -> None:
        """
        Emit an event to all connected clients.

        Args:
            event: Event to emit
        """
        # Update elapsed time
        event.metadata.elapsed_ms = self._calculate_elapsed_ms()

        # Store event in history
        self.events_emitted.append(event)

        self.logger.info(
            f"📤 Event emitted: {event.agent.value}::{event.status.value} "
            f"(step {event.metadata.step}/{event.metadata.total_steps})"
        )

        # Broadcast to all connected clients
        disconnected_clients = set()
        for client_queue in self.connected_clients:
            try:
                # Convert event to JSON-serializable dict
                event_dict = event.model_dump(mode="json")
                await asyncio.wait_for(client_queue.put(event_dict), timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("⚠️  Client queue full, removing client")
                disconnected_clients.add(client_queue)
            except Exception as e:
                self.logger.error(f"❌ Error broadcasting to client: {e}")
                disconnected_clients.add(client_queue)

        # Clean up disconnected clients
        for client_queue in disconnected_clients:
            self.unregister_client(client_queue)

    # Convenience methods for specific event types

    async def emit_agent_queued(self, agent: AgentTypeEnum, step: int) -> None:
        """Emit agent queued event."""
        event = create_agent_queued_event(
            agent=agent, step=step, elapsed_ms=self._calculate_elapsed_ms()
        )
        await self.emit_event(event)

    async def emit_agent_processing(
        self,
        agent: AgentTypeEnum,
        step: int,
        partial_results: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit agent processing event."""
        event = create_agent_processing_event(
            agent=agent,
            step=step,
            elapsed_ms=self._calculate_elapsed_ms(),
            partial_results=partial_results,
        )
        await self.emit_event(event)

    async def emit_agent_complete(
        self,
        agent: AgentTypeEnum,
        step: int,
        summary: Optional[str] = None,
        entities: Optional[List[str]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        visualization: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit agent complete event."""
        payload = AgentEventPayload(
            summary=summary,
            entities=entities,
            relationships=relationships,
            visualization=visualization,
            metrics=metrics,
        )
        event = create_agent_complete_event(
            agent=agent,
            step=step,
            elapsed_ms=self._calculate_elapsed_ms(),
            payload=payload,
        )
        await self.emit_event(event)

    async def emit_agent_error(
        self,
        agent: AgentTypeEnum,
        step: int,
        error: str,
        error_type: ErrorType,
        error_details: Optional[str] = None,
        recoverable: bool = False,
    ) -> None:
        """Emit agent error event."""
        event = create_agent_error_event(
            agent=agent,
            step=step,
            elapsed_ms=self._calculate_elapsed_ms(),
            error=error,
            error_type=error_type,
            error_details=error_details,
            recoverable=recoverable,
        )
        await self.emit_event(event)

    def get_event_history(self) -> List[Dict[str, Any]]:
        """
        Get all events emitted so far.

        Returns:
            List of events as dictionaries
        """
        return [event.model_dump(mode="json") for event in self.events_emitted]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about emitted events.

        Returns:
            Dictionary with event statistics
        """
        status_counts = {}
        agent_counts = {}

        for event in self.events_emitted:
            status = event.status.value
            agent = event.agent.value
            status_counts[status] = status_counts.get(status, 0) + 1
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            "total_events": len(self.events_emitted),
            "connected_clients": len(self.connected_clients),
            "status_breakdown": status_counts,
            "agent_breakdown": agent_counts,
            "elapsed_ms": self._calculate_elapsed_ms(),
            "session_id": self.session_id,
        }


class EventEmitterManager:
    """
    Manages multiple EventEmitter instances for concurrent workflows.

    This singleton manages all active sessions' event emitters.
    """

    def __init__(self):
        """Initialize the event emitter manager."""
        self.emitters: Dict[str, EventEmitter] = {}
        self.logger = logger.getChild("manager")
        self.logger.info("🚀 EventEmitterManager initialized")

    def create_emitter(self, session_id: str) -> EventEmitter:
        """
        Create a new event emitter for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            New EventEmitter instance
        """
        if session_id in self.emitters:
            self.logger.warning(f"⚠️  Emitter already exists for {session_id}")
            return self.emitters[session_id]

        emitter = EventEmitter(session_id)
        self.emitters[session_id] = emitter
        self.logger.info(f"✅ Created emitter for session {session_id}")
        return emitter

    def get_emitter(self, session_id: str) -> Optional[EventEmitter]:
        """
        Get an existing event emitter.

        Args:
            session_id: Session identifier

        Returns:
            EventEmitter if exists, None otherwise
        """
        return self.emitters.get(session_id)

    def remove_emitter(self, session_id: str) -> None:
        """
        Remove an event emitter (cleanup).

        Args:
            session_id: Session identifier
        """
        if session_id in self.emitters:
            del self.emitters[session_id]
            self.logger.info(f"🗑️  Removed emitter for session {session_id}")

    def cleanup_inactive_emitters(self, max_age_ms: int = 3600000) -> int:
        """
        Remove emitters older than max age (default 1 hour).

        Args:
            max_age_ms: Maximum age in milliseconds

        Returns:
            Number of emitters removed
        """
        now_ms = datetime.utcnow().timestamp() * 1000
        expired = []

        for session_id, emitter in self.emitters.items():
            age = now_ms - emitter.start_time
            if age > max_age_ms:
                expired.append(session_id)

        for session_id in expired:
            self.remove_emitter(session_id)

        if expired:
            self.logger.info(f"🧹 Cleaned up {len(expired)} expired emitters")

        return len(expired)

    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all active emitters.

        Returns:
            Dictionary with stats for each session
        """
        return {
            session_id: emitter.get_stats()
            for session_id, emitter in self.emitters.items()
        }


# Global singleton instance
_emitter_manager: Optional[EventEmitterManager] = None


def get_event_emitter_manager() -> EventEmitterManager:
    """
    Get the global EventEmitterManager instance.

    Returns:
        Singleton EventEmitterManager
    """
    global _emitter_manager
    if _emitter_manager is None:
        _emitter_manager = EventEmitterManager()
    return _emitter_manager
