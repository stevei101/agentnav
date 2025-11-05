"""A2A Protocol message bus for agent communication."""
import logging
from typing import Dict, Optional, Callable, Awaitable
from app.a2a.protocol import A2AMessage, MessageType, A2AProtocol
from app.services.firestore_client import firestore_client

logger = logging.getLogger(__name__)


class MessageBus:
    """Message bus for routing A2A messages between agents."""
    
    def __init__(self, a2a_protocol: A2AProtocol):
        """Initialize message bus."""
        self.protocol = a2a_protocol
        self.agents: Dict[str, any] = {}  # Registered agents by name
    
    def register_agent(self, agent_name: str, agent_instance: any) -> None:
        """Register an agent with the message bus."""
        self.agents[agent_name] = agent_instance
        logger.info(f"Registered agent: {agent_name}")
    
    async def send(self, message: A2AMessage) -> None:
        """Send a message to an agent via A2A Protocol."""
        # Persist message
        await self.protocol.send_message(message)
        
        # Route to target agent if registered
        if message.to_agent in self.agents:
            target_agent = self.agents[message.to_agent]
            try:
                # Call agent's message handler
                if hasattr(target_agent, 'handle_message'):
                    await target_agent.handle_message(message)
                else:
                    logger.warning(f"Agent {message.to_agent} does not have handle_message method")
            except Exception as e:
                logger.error(f"Error routing message to {message.to_agent}: {e}")
                # Send error message back
                error_message = A2AMessage(
                    from_agent=message.to_agent,
                    to_agent=message.from_agent,
                    message_type=MessageType.AGENT_ERROR,
                    payload={"error": str(e), "original_message": message.model_dump()},
                    session_id=message.session_id,
                    workflow_id=message.workflow_id,
                    correlation_id=message.correlation_id,
                )
                await self.protocol.send_message(error_message)
        else:
            logger.warning(f"Agent {message.to_agent} not found in message bus")
    
    async def broadcast(self, message: A2AMessage, agent_names: list[str]) -> None:
        """Broadcast a message to multiple agents."""
        for agent_name in agent_names:
            broadcast_message = A2AMessage(
                from_agent=message.from_agent,
                to_agent=agent_name,
                message_type=message.message_type,
                payload=message.payload,
                session_id=message.session_id,
                workflow_id=message.workflow_id,
                correlation_id=message.correlation_id,
            )
            await self.send(broadcast_message)


# Global message bus instance
a2a_protocol = A2AProtocol(firestore_client)
message_bus = MessageBus(a2a_protocol)

