"""
Context Persistence Service
Handles storing and retrieving SessionContext from Firestore
"""

import logging
from typing import Optional

from models.context_model import SessionContext

logger = logging.getLogger(__name__)


class ContextPersistenceService:
    """
    Service for persisting SessionContext to Firestore

    Stores context in the 'agent_context' collection as specified in FR#005.
    Each session is stored as a document with session_id as the key.
    """

    def __init__(self, firestore_client=None):
        """
        Initialize persistence service

        Args:
            firestore_client: Optional Firestore client (will get default if not provided)
        """
        self.firestore_client = firestore_client
        self._collection_name = "agent_context"

    def _get_client(self):
        """Get Firestore client (lazy initialization)"""
        if self.firestore_client is None:
            from services.firestore_client import get_firestore_client

            self.firestore_client = get_firestore_client()
        return self.firestore_client

    async def save_context(self, context: SessionContext) -> bool:
        """
        Save SessionContext to Firestore

        Args:
            context: SessionContext to save

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, context.session_id)

            # Convert to Firestore-compatible dict
            data = context.to_firestore_dict()

            # Store in Firestore
            doc_ref.set(data)

            logger.info(f"💾 Saved SessionContext to Firestore: {context.session_id}")
            logger.debug(f"   Completed agents: {context.completed_agents}")
            logger.debug(f"   Workflow status: {context.workflow_status}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to save SessionContext to Firestore: {e}")
            logger.warning(
                "⚠️  Continuing without persistence (context will not be recovered on failure)"
            )
            return False

    async def load_context(self, session_id: str) -> Optional[SessionContext]:
        """
        Load SessionContext from Firestore

        Args:
            session_id: Session ID to load

        Returns:
            SessionContext if found, None otherwise

        Raises:
            ValueError: If session_id is empty or None
        """
        if not session_id:
            raise ValueError("session_id cannot be empty or None")

        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, session_id)
            doc = doc_ref.get()

            if not doc.exists:
                logger.warning(f"⚠️  SessionContext not found: {session_id}")
                return None

            # Convert from Firestore dict to SessionContext
            data = doc.to_dict()
            context = SessionContext.from_firestore_dict(data)

            logger.info(f"📂 Loaded SessionContext from Firestore: {session_id}")
            logger.debug(f"   Completed agents: {context.completed_agents}")
            logger.debug(f"   Workflow status: {context.workflow_status}")

            return context

        except Exception as e:
            logger.error(f"❌ Failed to load SessionContext from Firestore: {e}")
            return None

    async def delete_context(self, session_id: str) -> bool:
        """
        Delete SessionContext from Firestore

        Args:
            session_id: Session ID to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, session_id)
            doc_ref.delete()

            logger.info(f"🗑️  Deleted SessionContext from Firestore: {session_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete SessionContext from Firestore: {e}")
            return False

    async def list_contexts(self, limit: int = 10) -> list:
        """
        List recent SessionContexts

        Args:
            limit: Maximum number of contexts to return

        Returns:
            List of session_ids
        """
        try:
            client = self._get_client()
            collection = client.get_collection(self._collection_name)

            # Get recent documents ordered by timestamp
            docs = (
                collection.order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )

            session_ids = [doc.id for doc in docs]

            logger.info(f"📋 Listed {len(session_ids)} SessionContexts")
            return session_ids

        except Exception as e:
            logger.error(f"❌ Failed to list SessionContexts: {e}")
            return []


# Global singleton instance
_persistence_service: Optional[ContextPersistenceService] = None


def get_persistence_service() -> ContextPersistenceService:
    """
    Get or create global ContextPersistenceService singleton

    Returns:
        ContextPersistenceService instance
    """
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = ContextPersistenceService()
    return _persistence_service
