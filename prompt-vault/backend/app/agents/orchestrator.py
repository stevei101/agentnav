"""Orchestrator Agent for coordinating multi-agent workflows."""
import logging
from typing import Dict, Any, Optional
from uuid import uuid4
from enum import Enum
from app.agents.base import BaseAgent
from app.a2a.protocol import MessageType, A2AMessage
from app.services.firestore_client import firestore_client

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Workflow types."""
    OPTIMIZE = "optimize"
    TEST = "test"
    COMPARE = "compare"
    SUGGEST = "suggest"


class OrchestratorAgent(BaseAgent):
    """Orchestrator agent that coordinates multi-agent workflows."""
    
    def __init__(self):
        """Initialize orchestrator agent."""
        super().__init__("orchestrator")
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a workflow request and coordinate agents.
        
        Args:
            context: Context containing workflow_type and request data
            
        Returns:
            Workflow result
        """
        workflow_type = context.get("workflow_type")
        session_id = context.get("session_id", str(uuid4()))
        workflow_id = context.get("workflow_id", str(uuid4()))
        
        # Save workflow context
        await firestore_client.save_workflow_context(workflow_id, {
            "workflow_type": workflow_type,
            "status": "in_progress",
            "session_id": session_id,
            "started_at": None,  # Firestore will set timestamp
        })
        
        try:
            # Route to appropriate workflow handler
            if workflow_type == WorkflowType.OPTIMIZE:
                result = await self._handle_optimize_workflow(context, session_id, workflow_id)
            elif workflow_type == WorkflowType.TEST:
                result = await self._handle_test_workflow(context, session_id, workflow_id)
            elif workflow_type == WorkflowType.COMPARE:
                result = await self._handle_compare_workflow(context, session_id, workflow_id)
            elif workflow_type == WorkflowType.SUGGEST:
                result = await self._handle_suggest_workflow(context, session_id, workflow_id)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            # Update workflow context
            await firestore_client.save_workflow_context(workflow_id, {
                "status": "completed",
                "result": result,
            })
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "result": result,
            }
            
        except Exception as e:
            logger.error(f"Error in workflow {workflow_type}: {e}", exc_info=True)
            
            # Update workflow context with error
            await firestore_client.save_workflow_context(workflow_id, {
                "status": "failed",
                "error": str(e),
            })
            
            raise
    
    async def _handle_optimize_workflow(
        self,
        context: Dict[str, Any],
        session_id: str,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """Handle optimization workflow: Analyzer → Optimizer → (optional) Tester."""
        prompt_id = context.get("prompt_id")
        options = context.get("options", {})
        
        # Send analyze request to Analyzer Agent
        correlation_id = str(uuid4())
        await self.send_message(
            to_agent="analyzer",
            message_type=MessageType.ANALYZE_REQUEST,
            payload={"prompt_id": prompt_id},
            session_id=session_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        )
        
        # TODO: Wait for analyzer response and route to optimizer
        # For now, return placeholder
        return {
            "message": "Optimization workflow initiated",
            "prompt_id": prompt_id,
            "status": "pending",
        }
    
    async def _handle_test_workflow(
        self,
        context: Dict[str, Any],
        session_id: str,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """Handle testing workflow: Tester Agent."""
        prompt_id = context.get("prompt_id")
        
        # Send test request to Tester Agent
        correlation_id = str(uuid4())
        await self.send_message(
            to_agent="tester",
            message_type=MessageType.TEST_REQUEST,
            payload={"prompt_id": prompt_id, "scenarios": context.get("scenarios", [])},
            session_id=session_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        )
        
        # TODO: Wait for tester response
        # For now, return placeholder
        return {
            "message": "Test workflow initiated",
            "prompt_id": prompt_id,
            "status": "pending",
        }
    
    async def _handle_compare_workflow(
        self,
        context: Dict[str, Any],
        session_id: str,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """Handle comparison workflow: Comparator Agent."""
        prompt_id = context.get("prompt_id")
        version_ids = context.get("version_ids", [])
        
        # Send compare request to Comparator Agent
        correlation_id = str(uuid4())
        await self.send_message(
            to_agent="comparator",
            message_type=MessageType.COMPARE_REQUEST,
            payload={"prompt_id": prompt_id, "version_ids": version_ids},
            session_id=session_id,
            workflow_id=workflow_id,
            correlation_id=correlation_id,
        )
        
        # TODO: Wait for comparator response
        # For now, return placeholder
        return {
            "message": "Comparison workflow initiated",
            "prompt_id": prompt_id,
            "version_ids": version_ids,
            "status": "pending",
        }
    
    async def _handle_suggest_workflow(
        self,
        context: Dict[str, Any],
        session_id: str,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """Handle suggestion workflow: Suggestion Agent."""
        requirements = context.get("requirements", {})
        
        # Import here to avoid circular dependency
        from app.agents.suggestion import SuggestionAgent
        
        # Create suggestion agent instance and process directly
        suggestion_agent = SuggestionAgent()
        result = await suggestion_agent.process({
            "requirements": requirements,
            "session_id": session_id,
            "workflow_id": workflow_id,
        })
        
        return result

