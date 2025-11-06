"""
Base Agent - ADK-Compatible Agent Framework
Implements Agent Development Kit (ADK) patterns and Agent2Agent (A2A) Protocol

Updated for FR#027: Full A2A Protocol Integration with formal message schemas
and security features.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Import new A2A Protocol components (FR#027)
try:
    from services.a2a_protocol import A2AProtocolService, create_status_message
    from models.a2a_messages import A2AMessageBase, AgentStatusMessage

    HAS_ENHANCED_A2A = True
except ImportError as e:
    HAS_ENHANCED_A2A = False
    logger.warning(f"⚠️  Enhanced A2A Protocol not available, using legacy implementation: {e}")


class AgentState(Enum):
    """Agent execution states"""

    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class A2AMessage:
    """Agent2Agent Protocol Message Structure"""

    message_id: str
    from_agent: str
    to_agent: str
    message_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    priority: int = 1  # 1=low, 5=high

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "priority": self.priority,
        }


class A2AProtocol:
    """
    Agent2Agent Protocol Implementation
    Handles message passing and coordination between agents
    """

    def __init__(self):
        self._message_queue: List[A2AMessage] = []
        self._subscribers: Dict[str, List[str]] = {}  # message_type -> [agent_names]
        self._context_store: Dict[str, Any] = {}  # Shared context between agents

    async def send_message(self, message: A2AMessage):
        """Send A2A Protocol message to target agent(s)"""
        logger.info(f"📨 A2A: {message.from_agent} → {message.to_agent} [{message.message_type}]")

        # Add to queue (sorted by priority)
        self._message_queue.append(message)
        self._message_queue.sort(key=lambda m: m.priority, reverse=True)

        # Store in shared context if needed
        if message.message_type == "context_update":
            self._context_store.update(message.data)

    async def get_messages_for_agent(self, agent_name: str) -> List[A2AMessage]:
        """Get pending messages for specific agent"""
        messages = [msg for msg in self._message_queue if msg.to_agent == agent_name]
        # Remove retrieved messages from queue
        self._message_queue = [msg for msg in self._message_queue if msg.to_agent != agent_name]
        return messages

    def get_shared_context(self) -> Dict[str, Any]:
        """Get shared context accessible to all agents"""
        return self._context_store.copy()

    def update_shared_context(self, key: str, value: Any):
        """Update shared context"""
        self._context_store[key] = value


class Agent(ABC):
    """
    ADK-Compatible Base Agent Class

    All agents inherit from this base class and implement the process() method.
    Provides A2A Protocol integration and common agent capabilities.

    FR#027 Updates:
    - Supports both legacy A2AProtocol and new A2AProtocolService
    - Uses typed A2A messages with security and traceability
    - Enhanced logging with structured metadata
    """

    def __init__(self, name: str, a2a_protocol: Union["A2AProtocol", "A2AProtocolService"]):
        self.name = name
        self.state = AgentState.IDLE
        self.a2a = a2a_protocol
        self.execution_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"agent.{name}")

        # Check if using enhanced A2A Protocol
        self.using_enhanced_a2a = (
            HAS_ENHANCED_A2A and isinstance(a2a_protocol, A2AProtocolService)
            if HAS_ENHANCED_A2A
            else False
        )

        if self.using_enhanced_a2a:
            self.logger.info(f"🔄 Agent '{name}' using Enhanced A2A Protocol (FR#027)")
        else:
            self.logger.info(f"🔄 Agent '{name}' using Legacy A2A Protocol")

    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core agent processing method - must be implemented by subclasses

        Args:
            context: Input context and data for processing

        Returns:
            Dict containing processing results
        """
        pass

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent with ADK lifecycle management
        Handles state transitions, error handling, and A2A communication
        """
        execution_start = time.time()
        execution_id = f"{self.name}_{int(execution_start)}"

        try:
            self.logger.info(f"🚀 Agent {self.name} starting execution [{execution_id}]")
            self.state = AgentState.PROCESSING

            # Process any pending A2A messages
            await self._process_a2a_messages()

            # Add shared context to processing context
            shared_context = self.a2a.get_shared_context()
            merged_context = {**context, "shared_context": shared_context}

            # Execute main processing
            result = await self.process(merged_context)

            # Update execution history
            execution_time = time.time() - execution_start
            self._record_execution(execution_id, execution_time, result, None)

            self.state = AgentState.COMPLETED
            self.logger.info(f"✅ Agent {self.name} completed successfully [{execution_time:.2f}s]")

            # Notify other agents of completion
            await self._notify_completion(result)

            return result

        except Exception as e:
            execution_time = time.time() - execution_start
            self._record_execution(execution_id, execution_time, None, str(e))
            self.state = AgentState.ERROR
            self.logger.error(f"❌ Agent {self.name} failed: {e}")

            # Notify other agents of failure
            await self._notify_error(str(e))

            raise

    async def _process_a2a_messages(self):
        """Process pending A2A Protocol messages for this agent"""
        messages = await self.a2a.get_messages_for_agent(self.name)
        for message in messages:
            self.logger.info(
                f"📥 Processing A2A message: {message.message_type} from {message.from_agent}"
            )
            await self._handle_a2a_message(message)

    async def _handle_a2a_message(self, message: Union["A2AMessage", "A2AMessageBase"]):
        """
        Handle incoming A2A message - can be overridden by subclasses

        FR#027: Supports both legacy A2AMessage and new typed messages
        """
        # Extract message type (works for both formats)
        if hasattr(message, "message_type"):
            msg_type = message.message_type
        else:
            msg_type = "unknown"

        # Extract from_agent (works for both formats)
        if hasattr(message, "from_agent"):
            from_agent = message.from_agent
        else:
            from_agent = "unknown"

        # Handle common message types
        if msg_type == "context_update":
            self.logger.info(f"📋 Received context update from {from_agent}")
        elif msg_type == "dependency_complete":
            self.logger.info(f"✅ Dependency {from_agent} completed")
        elif msg_type == "agent_status":
            # Handle typed AgentStatusMessage (FR#027)
            if hasattr(message, "agent_status"):
                status = message.agent_status
                self.logger.info(f"📊 Agent {from_agent} status: {status}")
            else:
                self.logger.info(f"📊 Agent {from_agent} status update")
        elif msg_type in [
            "summarization_completed",
            "relationship_mapped",
            "visualization_ready",
        ]:
            # Handle specialized typed messages (FR#027)
            self.logger.info(f"📨 Received {msg_type} from {from_agent}")
        else:
            self.logger.warning(f"🤷 Unknown A2A message type: {msg_type}")

    async def _notify_completion(self, result: Dict[str, Any]):
        """
        Notify other agents that this agent has completed

        FR#027: Uses typed AgentStatusMessage when enhanced A2A is available
        """
        execution_time = result.get("processing_time", 0.0)
        result_summary = self._summarize_result(result)

        if self.using_enhanced_a2a and HAS_ENHANCED_A2A:
            # Use typed AgentStatusMessage (FR#027)
            message = create_status_message(
                from_agent=self.name,
                agent_status="completed",
                correlation_id=getattr(self.a2a, "correlation_id", "unknown"),
                processing_time_seconds=execution_time,
                result_summary=result_summary,
            )
        else:
            # Legacy message format
            message = A2AMessage(
                message_id=f"{self.name}_complete_{int(time.time())}",
                from_agent=self.name,
                to_agent="*",  # Broadcast to all agents
                message_type="agent_complete",
                data={"agent": self.name, "result_summary": result_summary},
            )

        await self.a2a.send_message(message)

    async def _notify_error(self, error: str):
        """
        Notify other agents of an error

        FR#027: Uses typed AgentStatusMessage when enhanced A2A is available
        """
        if self.using_enhanced_a2a and HAS_ENHANCED_A2A:
            # Use typed AgentStatusMessage (FR#027)
            message = create_status_message(
                from_agent=self.name,
                agent_status="failed",
                correlation_id=getattr(self.a2a, "correlation_id", "unknown"),
                error_message=error,
            )
        else:
            # Legacy message format
            message = A2AMessage(
                message_id=f"{self.name}_error_{int(time.time())}",
                from_agent=self.name,
                to_agent="*",  # Broadcast to all agents
                message_type="agent_error",
                data={"agent": self.name, "error": error},
            )

        await self.a2a.send_message(message)

    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Create a brief summary of the result for A2A communication"""
        if "type" in result:
            return f"Generated {result['type']}"
        return "Processing completed"

    def _record_execution(
        self,
        execution_id: str,
        execution_time: float,
        result: Optional[Dict[str, Any]],
        error: Optional[str],
    ):
        """Record execution in agent history"""
        self.execution_history.append(
            {
                "execution_id": execution_id,
                "timestamp": time.time(),
                "execution_time": execution_time,
                "state": self.state.value,
                "success": error is None,
                "result_summary": self._summarize_result(result) if result else None,
                "error": error,
            }
        )

        # Keep only last 10 executions
        if len(self.execution_history) > 10:
            self.execution_history = self.execution_history[-10:]

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status for monitoring"""
        return {
            "name": self.name,
            "state": self.state.value,
            "last_execution": (self.execution_history[-1] if self.execution_history else None),
            "total_executions": len(self.execution_history),
        }


class AgentWorkflow:
    """
    ADK Workflow Engine
    Orchestrates multiple agents with dependency management and A2A Protocol

    FR#027 Updates:
    - Supports both legacy A2AProtocol and new A2AProtocolService
    - Can be initialized with session_id for enhanced traceability
    """

    def __init__(self, session_id: Optional[str] = None, use_enhanced_a2a: bool = True):
        """
        Initialize AgentWorkflow

        Args:
            session_id: Optional session ID for correlation tracking
            use_enhanced_a2a: Whether to use enhanced A2A Protocol (FR#027)
        """
        # Choose A2A Protocol implementation
        if use_enhanced_a2a and HAS_ENHANCED_A2A:
            from services.a2a_protocol import A2AProtocolService

            self.a2a = A2AProtocolService(session_id=session_id)
            logger.info("🔄 Using Enhanced A2A Protocol Service (FR#027)")
        else:
            self.a2a = A2AProtocol()
            logger.info("🔄 Using Legacy A2A Protocol")

        self.agents: Dict[str, Agent] = {}
        self.dependencies: Dict[str, List[str]] = {}  # agent -> [prerequisite_agents]
        self.persistence_service = None  # Lazy initialization
        self.session_service = None  # Lazy initialization
        self.cache_service = None  # Lazy initialization

    def register_agent(self, agent: Agent):
        """Register an agent with the workflow"""
        self.agents[agent.name] = agent
        agent.a2a = self.a2a  # Ensure all agents use the same A2A Protocol instance
        logger.info(f"📋 Registered agent: {agent.name}")

    def set_dependencies(self, agent_name: str, prerequisite_agents: List[str]):
        """Set dependencies for an agent"""
        self.dependencies[agent_name] = prerequisite_agents
        logger.info(f"🔗 Set dependencies for {agent_name}: {prerequisite_agents}")

    async def execute_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete agent workflow with dependency resolution
        """
        logger.info("🎬 Starting ADK Agent Workflow")

        executed_agents = set()
        workflow_results = {}

        while len(executed_agents) < len(self.agents):
            # Find agents ready to execute (dependencies satisfied)
            ready_agents = []
            for agent_name, agent in self.agents.items():
                if agent_name not in executed_agents:
                    prerequisites = self.dependencies.get(agent_name, [])
                    if all(dep in executed_agents for dep in prerequisites):
                        ready_agents.append((agent_name, agent))

            if not ready_agents:
                # Check for circular dependencies or other issues
                remaining = set(self.agents.keys()) - executed_agents
                logger.error(f"❌ Workflow deadlock: remaining agents {remaining}")
                break

            # Execute ready agents (can be parallel if no interdependencies)
            for agent_name, agent in ready_agents:
                try:
                    logger.info(f"🔄 Executing agent: {agent_name}")
                    result = await agent.execute(context)
                    workflow_results[agent_name] = result
                    executed_agents.add(agent_name)

                    # Update shared context with results
                    self.a2a.update_shared_context(f"{agent_name}_result", result)

                except Exception as e:
                    logger.error(f"❌ Agent {agent_name} failed: {e}")
                    # Continue with other agents - depending agents will handle the failure
                    executed_agents.add(agent_name)  # Mark as processed to avoid infinite loop

        logger.info("🏁 ADK Agent Workflow completed")
        return workflow_results

    async def execute_sequential_workflow(self, session_context) -> "SessionContext":
        """
        Execute the workflow sequentially using SessionContext (FR#005 + FR#029)

        This method implements the sequential workflow as specified in FR#005:
        1. Orchestrator analyzes and delegates
        2. Summarizer processes and updates SessionContext
        3. Linker processes and updates SessionContext
        4. Visualizer processes and updates SessionContext

        FR#029 additions:
        - Creates session document in 'sessions/' collection
        - Checks knowledge cache before processing
        - Stores results in knowledge cache after completion
        - Updates agent states in session document

        Each agent updates the SessionContext, which is persisted to Firestore
        after each step for fault tolerance.

        Args:
            session_context: SessionContext object with raw_input populated

        Returns:
            Updated SessionContext with all agent outputs

        Raises:
            TypeError: If session_context is not a SessionContext instance
        """
        from models.context_model import SessionContext

        # Validate input type
        if not isinstance(session_context, SessionContext):
            raise TypeError(
                f"session_context must be a SessionContext instance, got {type(session_context)}"
            )

        # Initialize services if not already done
        if self.persistence_service is None:
            try:
                from services.context_persistence import get_persistence_service

                self.persistence_service = get_persistence_service()
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize persistence service: {e}")

        if self.session_service is None:
            try:
                from services.session_service import get_session_service

                self.session_service = get_session_service()
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize session service: {e}")

        if self.cache_service is None:
            try:
                from services.knowledge_cache_service import get_knowledge_cache_service

                self.cache_service = get_knowledge_cache_service()
            except Exception as e:
                logger.warning(f"⚠️  Could not initialize cache service: {e}")

        logger.info("🎬 Starting Sequential ADK Agent Workflow (FR#005 + FR#029)")

        # FR#029: Create session document
        if self.session_service:
            await self.session_service.create_session(
                session_id=session_context.session_id,
                user_input=session_context.raw_input,
                content_type=session_context.content_type,
                metadata={"workflow_version": "FR#029"},
            )

        # FR#029: Check knowledge cache before processing
        if self.cache_service:
            cached_result = await self.cache_service.check_cache(
                content=session_context.raw_input,
                content_type=session_context.content_type,
            )

            if cached_result:
                logger.info("🎯 Using cached results, skipping agent execution")

                # Populate SessionContext from cache
                session_context.summary_text = cached_result.get("summary")
                session_context.key_entities = cached_result.get("key_entities", [])

                # Convert relationship dicts to EntityRelationship objects
                from models.context_model import EntityRelationship

                cached_relationships = cached_result.get("relationships", [])
                session_context.relationships = [
                    EntityRelationship(**rel) if isinstance(rel, dict) else rel
                    for rel in cached_relationships
                ]

                session_context.graph_json = cached_result.get("visualization_data")
                session_context.workflow_status = "completed_from_cache"

                # Mark all agents as complete (from cache)
                from models.context_model import STANDARD_AGENT_ORDER

                for agent_name in STANDARD_AGENT_ORDER:
                    session_context.mark_agent_complete(agent_name)

                # Increment cache hit count
                content_hash = self.cache_service.generate_content_hash(
                    session_context.raw_input, session_context.content_type
                )
                await self.cache_service.increment_hit_count(content_hash)

                # Update session with cache hit info
                if self.session_service:
                    await self.session_service.update_session(
                        session_context.session_id,
                        {"workflow_status": "completed_from_cache", "cache_hit": True},
                    )

                return session_context

        # No cache hit - proceed with normal workflow execution
        session_context.workflow_status = "in_progress"

        # Update session status
        if self.session_service:
            await self.session_service.update_session(
                session_context.session_id, {"workflow_status": "in_progress"}
            )

        # Define execution order for sequential workflow
        # Uses standard agent order from context_model
        from models.context_model import STANDARD_AGENT_ORDER

        execution_order = STANDARD_AGENT_ORDER

        for agent_name in execution_order:
            if agent_name not in self.agents:
                logger.warning(f"⚠️  Agent '{agent_name}' not registered, skipping")
                continue

            agent = self.agents[agent_name]
            agent_start_time = time.time()

            try:
                logger.info(f"🔄 Executing agent: {agent_name}")
                session_context.set_current_agent(agent_name)

                # Convert SessionContext to dict for agent execution
                context_dict = {
                    "document": session_context.raw_input,
                    "content_type": session_context.content_type,
                    "session_id": session_context.session_id,
                    "session_context": session_context,  # Pass the full context
                }

                # Execute agent
                result = await agent.execute(context_dict)
                agent_execution_time = time.time() - agent_start_time

                # Update SessionContext based on agent type and results
                self._update_session_context_from_result(session_context, agent_name, result)

                # Mark agent as complete
                session_context.mark_agent_complete(agent_name)

                # FR#029: Update agent state in session document
                if self.session_service:
                    await self.session_service.update_agent_state(
                        session_id=session_context.session_id,
                        agent_name=agent_name,
                        state={
                            "status": "completed",
                            "execution_time": agent_execution_time,
                            "result_summary": result.get("agent", agent_name),
                        },
                    )

                # Persist context to Firestore after each step
                if self.persistence_service:
                    await self.persistence_service.save_context(session_context)

                logger.info(f"✅ Agent {agent_name} completed successfully")

            except Exception as e:
                agent_execution_time = time.time() - agent_start_time
                logger.error(f"❌ Agent {agent_name} failed: {e}")
                session_context.add_error(agent_name, str(e))

                # Continue with next agent even if one fails (graceful degradation)
                session_context.mark_agent_complete(agent_name)

                # FR#029: Update agent state with error
                if self.session_service:
                    await self.session_service.update_agent_state(
                        session_id=session_context.session_id,
                        agent_name=agent_name,
                        state={
                            "status": "failed",
                            "execution_time": agent_execution_time,
                            "error": str(e),
                        },
                    )

                if self.persistence_service:
                    await self.persistence_service.save_context(session_context)

        # Mark workflow as complete
        session_context.workflow_status = (
            "completed" if session_context.is_complete() else "partially_completed"
        )
        session_context.current_agent = None

        # FR#029: Store results in knowledge cache (including partial results)
        if self.cache_service and session_context.workflow_status in [
            "completed",
            "partially_completed",
        ]:
            await self.cache_service.store_cache(
                content=session_context.raw_input,
                content_type=session_context.content_type,
                summary=session_context.summary_text or "",
                visualization_data=session_context.graph_json or {},
                key_entities=session_context.key_entities,
                relationships=[rel.model_dump() for rel in session_context.relationships],
            )

        # Final persistence
        if self.persistence_service:
            await self.persistence_service.save_context(session_context)

        # FR#029: Update final session status
        if self.session_service:
            await self.session_service.update_session(
                session_context.session_id,
                {
                    "workflow_status": session_context.workflow_status,
                    "completed_at": time.time(),
                },
            )

        logger.info(
            f"🏁 Sequential ADK Agent Workflow completed: {session_context.workflow_status}"
        )

        return session_context

    def _update_session_context_from_result(
        self, session_context, agent_name: str, result: Dict[str, Any]
    ):
        """
        Update SessionContext with agent-specific results

        Maps agent results to SessionContext fields as specified in FR#005
        """
        if agent_name == "summarizer":
            # Summarizer updates summary_text
            if "summary" in result:
                session_context.summary_text = result["summary"]
            if "insights" in result:
                session_context.summary_insights = result["insights"]

        elif agent_name == "linker":
            # Linker updates key_entities and relationships
            if "entities" in result:
                # Extract entity labels/IDs
                entities = result["entities"]
                session_context.key_entities = [
                    entity.get("label", entity.get("id", "unknown")) for entity in entities
                ]

            if "relationships" in result:
                # Convert relationship dicts to EntityRelationship objects
                from models.context_model import EntityRelationship

                relationships = result["relationships"]
                session_context.relationships = [
                    EntityRelationship(
                        source=rel.get("from", rel.get("source", "unknown")),
                        target=rel.get("to", rel.get("target", "unknown")),
                        type=rel.get("type", "related"),
                        label=rel.get("label"),
                        confidence=rel.get("confidence"),
                    )
                    for rel in relationships
                ]

            if "graph_data" in result:
                session_context.entity_metadata = result["graph_data"]

        elif agent_name == "visualizer":
            # Visualizer updates graph_json
            # Extract the visualization data, excluding agent metadata
            graph_json = {}
            for key in ["type", "title", "nodes", "edges"]:
                if key in result:
                    graph_json[key] = result[key]

            if graph_json:
                session_context.graph_json = graph_json

        elif agent_name == "orchestrator":
            # Orchestrator doesn't update specific fields but may set metadata
            pass

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get status of all agents in the workflow"""
        return {
            "agents": {name: agent.get_status() for name, agent in self.agents.items()},
            "dependencies": self.dependencies,
            "shared_context_keys": list(self.a2a.get_shared_context().keys()),
        }
