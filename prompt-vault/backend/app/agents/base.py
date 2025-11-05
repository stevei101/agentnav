"""Base Agent class for ADK-compatible agents."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from uuid import uuid4
from app.a2a.protocol import A2AMessage, MessageType
from app.a2a.message_bus import message_bus
from app.services.firestore_client import firestore_client
from app.services.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the Prompt Vault system."""
    
    def __init__(self, agent_name: str):
        """Initialize base agent."""
        self.agent_name = agent_name
        self.message_bus = message_bus
        self.firestore_client = firestore_client
        self.supabase_client = supabase_client
        
        # Register agent with message bus
        self.message_bus.register_agent(agent_name, self)
        logger.info(f"Initialized agent: {agent_name}")
    
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return a result.
        
        Args:
            context: Context dictionary containing request data
            
        Returns:
            Result dictionary with agent output
        """
        pass
    
    async def handle_message(self, message: A2AMessage) -> Optional[Dict[str, Any]]:
        """
        Handle an incoming A2A message.
        
        Args:
            message: A2A protocol message
            
        Returns:
            Result dictionary if processing is synchronous, None otherwise
        """
        try:
            # Extract context from message payload
            context = {
                **message.payload,
                "session_id": message.session_id,
                "workflow_id": message.workflow_id,
                "correlation_id": message.correlation_id,
            }
            
            # Process the request
            result = await self.process(context)
            
            # Send response message if needed
            if message.message_type in [
                MessageType.ANALYZE_REQUEST,
                MessageType.OPTIMIZE_REQUEST,
                MessageType.TEST_REQUEST,
                MessageType.COMPARE_REQUEST,
                MessageType.SUGGEST_REQUEST,
            ]:
                response_type_map = {
                    MessageType.ANALYZE_REQUEST: MessageType.ANALYZE_COMPLETE,
                    MessageType.OPTIMIZE_REQUEST: MessageType.OPTIMIZATION_COMPLETE,
                    MessageType.TEST_REQUEST: MessageType.TEST_COMPLETE,
                    MessageType.COMPARE_REQUEST: MessageType.COMPARISON_COMPLETE,
                    MessageType.SUGGEST_REQUEST: MessageType.SUGGESTION_COMPLETE,
                }
                
                response_message = A2AMessage(
                    from_agent=self.agent_name,
                    to_agent=message.from_agent,
                    message_type=response_type_map[message.message_type],
                    payload={"result": result},
                    session_id=message.session_id,
                    workflow_id=message.workflow_id,
                    correlation_id=message.correlation_id,
                )
                await self.message_bus.send(response_message)
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling message in {self.agent_name}: {e}", exc_info=True)
            
            # Send error message
            error_message = A2AMessage(
                from_agent=self.agent_name,
                to_agent=message.from_agent,
                message_type=MessageType.AGENT_ERROR,
                payload={"error": str(e), "agent": self.agent_name},
                session_id=message.session_id,
                workflow_id=message.workflow_id,
                correlation_id=message.correlation_id,
            )
            await self.message_bus.send(error_message)
            raise
    
    async def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Save agent state to Firestore."""
        if not self.firestore_client.is_available():
            logger.debug(f"Firestore not available, skipping state save for {self.agent_name}/{session_id}")
            return
        await self.firestore_client.save_agent_state(
            self.agent_name,
            session_id,
            state
        )
    
    async def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get agent state from Firestore."""
        return await self.firestore_client.get_agent_state(
            self.agent_name,
            session_id
        )
    
    async def send_message(
        self,
        to_agent: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        session_id: str,
        workflow_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Send a message to another agent via A2A Protocol."""
        message = A2AMessage(
            from_agent=self.agent_name,
            to_agent=to_agent,
            message_type=message_type,
            payload=payload,
            session_id=session_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id or str(uuid4()),
        )
        await self.message_bus.send(message)

