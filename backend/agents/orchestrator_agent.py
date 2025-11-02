"""
Orchestrator Agent - ADK Implementation
Team lead that determines content type and delegates tasks to specialized agents
"""
import logging
from typing import Dict, Any
from .base_agent import Agent, A2AMessage
import time

logger = logging.getLogger(__name__)


class OrchestratorAgent(Agent):
    """
    Orchestrator Agent using ADK and A2A Protocol
    
    Responsibilities:
    - Receive user input
    - Determine content type (document vs codebase)
    - Delegate tasks to specialized agents via A2A Protocol
    - Coordinate the overall analysis workflow
    """
    
    def __init__(self, a2a_protocol):
        super().__init__("orchestrator", a2a_protocol)
        self._prompt_template = None
    
    def _get_prompt_template(self) -> str:
        """Get prompt template from Firestore or fallback"""
        if self._prompt_template:
            return self._prompt_template
        
        try:
            from services.prompt_loader import get_prompt
            self._prompt_template = get_prompt("orchestrator_system_instruction")
            logger.info("✅ Loaded orchestrator prompt from Firestore")
            return self._prompt_template
        except Exception as e:
            logger.warning(f"⚠️ Could not load prompt from Firestore: {e}")
            # Fallback prompt
            self._prompt_template = """
You are the Orchestrator Agent in a multi-agent analysis system.

Your task is to:
1. Analyze the provided content to determine if it's a document or codebase
2. Extract key metadata and structure information
3. Delegate appropriate tasks to specialized agents

Content to analyze:
{content}

Determine:
- content_type: "document" or "codebase"  
- content_summary: Brief description of what this content contains
- complexity_level: "simple", "moderate", or "complex"
- key_topics: List of main topics/themes identified
"""
            return self._prompt_template
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrator processing: analyze content and delegate to specialized agents
        """
        document = context.get("document", "")
        if not document:
            raise ValueError("Document content is required for orchestration")
        
        self.logger.info("🎯 Orchestrator analyzing content and planning workflow")
        
        # Step 1: Analyze content type and characteristics
        content_analysis = await self._analyze_content(document)
        
        # Step 2: Send delegation messages to specialized agents via A2A Protocol
        await self._delegate_to_agents(content_analysis, document)
        
        # Step 3: Set up workflow coordination
        workflow_plan = self._create_workflow_plan(content_analysis)
        
        return {
            "agent": "orchestrator",
            "content_analysis": content_analysis,
            "workflow_plan": workflow_plan,
            "delegated_agents": ["summarizer", "linker", "visualizer"],
            "orchestration_complete": True
        }
    
    async def _analyze_content(self, document: str) -> Dict[str, Any]:
        """Analyze content to determine type and characteristics"""
        
        # Simple heuristics for content type detection
        # In a full implementation, this could use Gemini for more sophisticated analysis
        
        code_indicators = [
            'import ', 'from ', 'class ', 'def ', 'function', 'var ', 'let ', 'const ',
            '#!/', '<?php', '<html', '<script', 'package ', 'public class', 'void main'
        ]
        
        document_lower = document.lower()
        code_score = sum(1 for indicator in code_indicators if indicator in document_lower)
        
        # Determine content type
        content_type = "codebase" if code_score >= 2 else "document"
        
        # Analyze complexity based on length and structure
        complexity_level = "simple"
        if len(document) > 5000:
            complexity_level = "complex"
        elif len(document) > 1000:
            complexity_level = "moderate"
        
        # Extract key topics (simple keyword extraction)
        lines = document.split('\n')
        key_topics = []
        
        if content_type == "codebase":
            # Look for function/class names
            for line in lines[:20]:  # Check first 20 lines
                line = line.strip()
                if line.startswith('def ') or line.startswith('class '):
                    key_topics.append(line.split()[1].split('(')[0])
        else:
            # Look for headings and important phrases
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line and (line.startswith('#') or len(line) < 100):
                    key_topics.append(line.replace('#', '').strip())
        
        return {
            "content_type": content_type,
            "content_summary": f"{content_type.title()} with {len(lines)} lines, {len(document.split())} words",
            "complexity_level": complexity_level,
            "key_topics": key_topics[:5],  # Top 5 topics
            "analysis_timestamp": time.time()
        }
    
    async def _delegate_to_agents(self, content_analysis: Dict[str, Any], document: str):
        """Send delegation messages to specialized agents via A2A Protocol"""
        
        # Message to Summarizer Agent
        summarizer_message = A2AMessage(
            message_id=f"orchestrator_to_summarizer_{int(time.time())}",
            from_agent=self.name,
            to_agent="summarizer",
            message_type="task_delegation",
            data={
                "task": "create_summary",
                "content": document,
                "content_type": content_analysis["content_type"],
                "priority": "high",
                "expected_output": "comprehensive_summary"
            },
            priority=4
        )
        await self.a2a.send_message(summarizer_message)
        
        # Message to Linker Agent
        linker_message = A2AMessage(
            message_id=f"orchestrator_to_linker_{int(time.time())}",
            from_agent=self.name,
            to_agent="linker",
            message_type="task_delegation",
            data={
                "task": "identify_relationships",
                "content": document,
                "content_type": content_analysis["content_type"],
                "key_topics": content_analysis["key_topics"],
                "expected_output": "entity_relationships"
            },
            priority=3
        )
        await self.a2a.send_message(linker_message)
        
        # Message to Visualizer Agent
        visualizer_message = A2AMessage(
            message_id=f"orchestrator_to_visualizer_{int(time.time())}",
            from_agent=self.name,
            to_agent="visualizer",
            message_type="task_delegation",
            data={
                "task": "create_visualization",
                "content": document,
                "content_type": content_analysis["content_type"],
                "complexity_level": content_analysis["complexity_level"],
                "depends_on": ["summarizer", "linker"],  # Visualizer should wait for these
                "expected_output": "interactive_graph"
            },
            priority=2
        )
        await self.a2a.send_message(visualizer_message)
        
        self.logger.info("📨 Sent delegation messages to all specialized agents")
    
    def _create_workflow_plan(self, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a workflow execution plan based on content analysis"""
        
        # Determine optimal execution order
        if content_analysis["complexity_level"] == "simple":
            execution_strategy = "parallel"
        else:
            execution_strategy = "sequential"
        
        return {
            "execution_strategy": execution_strategy,
            "estimated_duration": self._estimate_processing_time(content_analysis),
            "visualization_type": "DEPENDENCY_GRAPH" if content_analysis["content_type"] == "codebase" else "MIND_MAP",
            "agent_priorities": {
                "summarizer": 4,  # High priority
                "linker": 3,      # Medium priority
                "visualizer": 2   # Lower priority (depends on others)
            }
        }
    
    def _estimate_processing_time(self, content_analysis: Dict[str, Any]) -> int:
        """Estimate processing time in seconds based on content analysis"""
        base_time = 10  # Base processing time
        
        # Adjust based on complexity
        complexity_multiplier = {
            "simple": 1.0,
            "moderate": 1.5,
            "complex": 2.0
        }
        
        multiplier = complexity_multiplier.get(content_analysis["complexity_level"], 1.0)
        estimated_time = int(base_time * multiplier)
        
        return estimated_time
    
    async def _handle_a2a_message(self, message: A2AMessage):
        """Handle incoming A2A messages specific to Orchestrator"""
        await super()._handle_a2a_message(message)
        
        if message.message_type == "agent_complete":
            agent_name = message.data.get("agent")
            self.logger.info(f"📋 Received completion notification from {agent_name}")
            
            # Update workflow progress in shared context
            self.a2a.update_shared_context("workflow_progress", {
                "completed_agents": self.a2a.get_shared_context().get("completed_agents", []) + [agent_name],
                "last_update": time.time()
            })
        
        elif message.message_type == "agent_error":
            agent_name = message.data.get("agent")
            error = message.data.get("error")
            self.logger.warning(f"⚠️ Agent {agent_name} reported error: {error}")
            
            # Could implement error recovery strategies here
            # For now, just log and continue