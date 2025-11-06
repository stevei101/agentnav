"""
Session Service
Manages session metadata in Firestore 'sessions/' collection
"""

import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing session metadata in Firestore

    Stores session metadata in the 'sessions/' collection as specified in FR#029.
    Each session document contains metadata about the analysis job, timestamps,
    and agent state information.
    """

    def __init__(self, firestore_client=None):
        """
        Initialize session service

        Args:
            firestore_client: Optional Firestore client (will get default if not provided)
        """
        self.firestore_client = firestore_client
        self._collection_name = "sessions"

    def _get_client(self):
        """Get Firestore client (lazy initialization)"""
        if self.firestore_client is None:
            from services.firestore_client import get_firestore_client

            self.firestore_client = get_firestore_client()
        return self.firestore_client

    async def create_session(
        self,
        session_id: str,
        user_input: str,
        content_type: str = "document",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Create a new session document in Firestore

        Args:
            session_id: Unique session identifier
            user_input: Original user input/document
            content_type: Type of content ('document' or 'codebase')
            metadata: Optional additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, session_id)

            # Create session document
            session_data = {
                "session_id": session_id,
                "created_at": time.time(),
                "updated_at": time.time(),
                "user_input": user_input,
                "content_type": content_type,
                "agent_states": {},  # Will be updated as agents complete
                "workflow_status": "initializing",
                "metadata": metadata or {},
            }

            doc_ref.set(session_data)

            logger.info(f"📝 Created session in Firestore: {session_id}")
            logger.debug(f"   Content type: {content_type}")
            logger.debug(f"   Input length: {len(user_input)} chars")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to create session in Firestore: {e}")
            logger.warning("⚠️  Continuing without session persistence")
            return False

    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session document with new data

        Args:
            session_id: Session ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, session_id)

            # Add updated_at timestamp
            updates["updated_at"] = time.time()

            doc_ref.update(updates)

            logger.debug(f"💾 Updated session: {session_id}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to update session in Firestore: {e}")
            return False

    async def update_agent_state(
        self, session_id: str, agent_name: str, state: Dict[str, Any]
    ) -> bool:
        """
        Update agent state in session document

        Args:
            session_id: Session ID
            agent_name: Name of the agent
            state: Agent state data

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, session_id)

            # Update agent state using dot notation for nested update
            # Filter out None values to avoid Firestore errors
            agent_state_data = {
                "status": state.get("status", "completed"),
                "timestamp": time.time(),
            }

            # Only include non-None values
            if state.get("execution_time") is not None:
                agent_state_data["execution_time"] = state.get("execution_time")
            if state.get("result_summary") is not None:
                agent_state_data["result_summary"] = state.get("result_summary")

            updates = {
                f"agent_states.{agent_name}": agent_state_data,
                "updated_at": time.time(),
            }

            doc_ref.update(updates)

            logger.debug(
                f"🤖 Updated agent state for {agent_name} in session {session_id}"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Failed to update agent state in Firestore: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session document from Firestore

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session data dictionary if found, None otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, session_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"⚠️  Session not found: {session_id}")
                return None

            session_data = doc.to_dict()
            logger.info(f"📂 Retrieved session from Firestore: {session_id}")

            return session_data

        except Exception as e:
            logger.error(f"❌ Failed to retrieve session from Firestore: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session document from Firestore

        Args:
            session_id: Session ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, session_id)
            doc_ref.delete()

            logger.info(f"🗑️  Deleted session from Firestore: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete session from Firestore: {e}")
            return False

    async def list_sessions(
        self, limit: int = 10, order_by: str = "created_at"
    ) -> list:
        """
        List recent sessions

        Args:
            limit: Maximum number of sessions to return
            order_by: Field to order by (default: created_at)

        Returns:
            List of session dictionaries
        """
        try:
            client = self._get_client()
            collection = client.get_collection(self._collection_name)

            # Get recent sessions ordered by timestamp
            docs = (
                collection.order_by(order_by, direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            sessions = [doc.to_dict() for doc in docs]

            logger.info(f"📋 Listed {len(sessions)} sessions")
            return sessions

        except Exception as e:
            logger.error(f"❌ Failed to list sessions: {e}")
            return []


# Global singleton instance
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """
    Get or create global SessionService singleton

    Returns:
        SessionService instance
    """
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
