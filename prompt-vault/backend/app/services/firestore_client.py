"""Firestore client service for agent state and A2A messages."""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
try:
    from google.cloud import firestore
except ImportError:
    # Firestore not available in all environments
    firestore = None
from app.config import settings

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Client for interacting with Firestore database."""
    
    def __init__(self):
        """Initialize Firestore client."""
        if firestore is None:
            logger.warning("google-cloud-firestore not installed - client will be None")
            self.db: Optional[Any] = None
        elif not settings.FIRESTORE_PROJECT_ID:
            logger.warning("Firestore project ID not configured - client will be None")
            self.db: Optional[Any] = None
        else:
            try:
                self.db = firestore.Client(
                    project=settings.FIRESTORE_PROJECT_ID,
                    database=settings.FIRESTORE_DATABASE_ID
                )
                logger.info("Firestore client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Firestore client: {e}")
                self.db = None
    
    def is_available(self) -> bool:
        """Check if Firestore client is available."""
        return self.db is not None
    
    async def save_agent_state(self, agent_name: str, session_id: str, state: Dict[str, Any]) -> None:
        """Save agent state to Firestore."""
        if not self.db:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            doc_ref = self.db.collection("agent_state").document(agent_name).collection("sessions").document(session_id)
            doc_ref.set({
                **state,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "ttl": datetime.utcnow() + timedelta(days=7)  # TTL for cleanup
            })
        except Exception as e:
            logger.error(f"Error saving agent state for {agent_name}/{session_id}: {e}")
            raise
    
    async def get_agent_state(self, agent_name: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state from Firestore."""
        if not self.db:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            doc_ref = self.db.collection("agent_state").document(agent_name).collection("sessions").document(session_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error fetching agent state for {agent_name}/{session_id}: {e}")
            raise
    
    async def save_a2a_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Save A2A protocol message to Firestore."""
        if not self.db or firestore is None:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            doc_ref = self.db.collection("a2a_messages").document(session_id).collection("messages").document()
            doc_ref.set({
                **message,
                "timestamp": firestore.SERVER_TIMESTAMP,
            })
        except Exception as e:
            logger.error(f"Error saving A2A message for session {session_id}: {e}")
            raise
    
    async def get_a2a_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get A2A protocol messages for a session."""
        if not self.db or firestore is None:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            messages_ref = self.db.collection("a2a_messages").document(session_id).collection("messages")
            docs = messages_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error fetching A2A messages for session {session_id}: {e}")
            raise
    
    async def save_workflow_context(self, workflow_id: str, context: Dict[str, Any]) -> None:
        """Save workflow execution context to Firestore."""
        if not self.db or firestore is None:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            doc_ref = self.db.collection("workflow_context").document(workflow_id)
            doc_ref.set({
                **context,
                "updated_at": firestore.SERVER_TIMESTAMP,
                "ttl": datetime.utcnow() + timedelta(days=7)  # TTL for cleanup
            })
        except Exception as e:
            logger.error(f"Error saving workflow context for {workflow_id}: {e}")
            raise
    
    async def get_workflow_context(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution context from Firestore."""
        if not self.db:
            raise RuntimeError("Firestore client not initialized")
        
        try:
            doc_ref = self.db.collection("workflow_context").document(workflow_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error fetching workflow context for {workflow_id}: {e}")
            raise


# Global instance
firestore_client = FirestoreClient()

