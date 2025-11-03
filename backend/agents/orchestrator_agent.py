"""
Orchestrator Agent - ADK Implementation
Team lead that determines content type and delegates tasks to specialized agents
"""
import logging
from typing import Dict, Any, Optional
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
    - Emit real-time events for FR#020 streaming dashboard
    """
    
    def __init__(self, a2a_protocol=None, event_emitter: Optional[Any] = None, model_type: str = "gemini"):
        super().__init__("orchestrator", a2a_protocol)
        self._prompt_template = None
        self.event_emitter = event_emitter  # For FR#020 WebSocket streaming
        self.model_type = model_type  # "gemini" (cloud) or "gemma" (local GPU)
        self.model_type = model_type  # "gemini" (cloud) or "gemma" (local GPU)
    
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
        
        # Emit processing event for FR#020
        if self.event_emitter:
            await self.event_emitter.emit_agent_processing(
                agent="orchestrator",
                step=1,
                partial_results={"status": "analyzing content"}
            )
        
        # Step 1: Analyze content type and characteristics
        content_analysis = await self._analyze_content(document)
        
        # Step 2: Send delegation messages to specialized agents via A2A Protocol
        await self._delegate_to_agents(content_analysis, document)
        
        # Step 3: Set up workflow coordination
        workflow_plan = self._create_workflow_plan(content_analysis)
        
        # Emit complete event for FR#020
        if self.event_emitter:
            await self.event_emitter.emit_agent_complete(
                agent="orchestrator",
                step=1,
                metrics={
                    "content_type": content_analysis["content_type"],
                    "complexity": content_analysis["complexity_level"],
                    "topics_identified": len(content_analysis["key_topics"])
                }
            )
        
        return {
            "agent": "orchestrator",
            "content_analysis": content_analysis,
            "workflow_plan": workflow_plan,
            "delegated_agents": ["summarizer", "linker", "visualizer"],
            "orchestration_complete": True
        }
    
    async def _analyze_content(self, document: str) -> Dict[str, Any]:
        """Analyze content to determine type and characteristics using AI reasoning"""
        
        # Try AI-powered analysis first, fall back to heuristics
        try:
            return await self._analyze_content_with_ai(document)
        except Exception as e:
            self.logger.warning(f"⚠️ AI analysis failed: {e}. Using heuristics.")
            return self._analyze_content_with_heuristics(document)
    
    async def _analyze_content_with_ai(self, document: str) -> Dict[str, Any]:
        """Use Gemini/Gemma to analyze content type and characteristics"""
        from services.gemini_client import reason_with_gemini
        
        analysis_prompt = f"""
Analyze the following content and provide structured analysis.
Return your response in this exact format:

CONTENT_TYPE: [document|codebase]
COMPLEXITY: [simple|moderate|complex]
KEY_TOPICS: [comma-separated list of 3-5 main topics]
SUMMARY: [1-2 sentence summary]

Content to analyze:
{document[:3000]}
"""
        
        response = await reason_with_gemini(
            prompt=analysis_prompt,
            max_tokens=300,
            temperature=0.3,
            model_type=self.model_type
        )
        
        # Parse structured response
        return self._parse_analysis_response(response, document)
    
    def _parse_analysis_response(self, response: str, document: str) -> Dict[str, Any]:
        """Parse structured analysis response from AI model"""
        
        lines = response.strip().split('\n')
        parsed = {
            "content_type": "document",
            "complexity_level": "moderate",
            "key_topics": [],
            "content_summary": "",
            "analysis_timestamp": time.time()
        }
        
        try:
            for line in lines:
                if line.startswith("CONTENT_TYPE:"):
                    content_type = line.split(":", 1)[1].strip().lower()
                    if content_type in ["document", "codebase"]:
                        parsed["content_type"] = content_type
                elif line.startswith("COMPLEXITY:"):
                    complexity = line.split(":", 1)[1].strip().lower()
                    if complexity in ["simple", "moderate", "complex"]:
                        parsed["complexity_level"] = complexity
                elif line.startswith("KEY_TOPICS:"):
                    topics_str = line.split(":", 1)[1].strip()
                    parsed["key_topics"] = [t.strip() for t in topics_str.split(",")][:5]
                elif line.startswith("SUMMARY:"):
                    parsed["content_summary"] = line.split(":", 1)[1].strip()
        except Exception as e:
            self.logger.warning(f"⚠️ Could not parse analysis: {e}")
        
        # Ensure summary exists
        if not parsed["content_summary"]:
            lines_count = len(document.split('\n'))
            words_count = len(document.split())
            parsed["content_summary"] = f"{parsed['content_type'].title()} with {lines_count} lines, {words_count} words"
        
        return parsed
    
    def _analyze_content_with_heuristics(self, document: str) -> Dict[str, Any]:
        """Fallback: Analyze content using simple heuristics"""
        
        # Simple heuristics for content type detection
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
            "analysis_timestamp": time.time(),
            "analysis_method": "heuristic"
        }
    
    async def _delegate_to_agents(self, content_analysis: Dict[str, Any], document: str):
        """
        Send delegation messages to specialized agents via A2A Protocol
        
        FR#027: Uses typed TaskDelegationMessage when enhanced A2A is available
        """
        # Check if using enhanced A2A Protocol
        if self.using_enhanced_a2a:
            await self._delegate_with_typed_messages(content_analysis, document)
        else:
            await self._delegate_with_legacy_messages(content_analysis, document)
    
    async def _delegate_with_typed_messages(self, content_analysis: Dict[str, Any], document: str):
        """Send typed delegation messages (FR#027)"""
        from services.a2a_protocol import create_task_delegation_message
        
        correlation_id = getattr(self.a2a, 'correlation_id', 'unknown')
        
        # Message to Summarizer Agent
        summarizer_message = create_task_delegation_message(
            from_agent=self.name,
            to_agent="summarizer",
            task_name="create_summary",
            task_parameters={
                "content": document,
                "content_type": content_analysis["content_type"]
            },
            expected_output="comprehensive_summary",
            correlation_id=correlation_id
        )
        await self.a2a.send_message(summarizer_message)
        
        # Message to Linker Agent
        linker_message = create_task_delegation_message(
            from_agent=self.name,
            to_agent="linker",
            task_name="identify_relationships",
            task_parameters={
                "content": document,
                "content_type": content_analysis["content_type"],
                "key_topics": content_analysis["key_topics"]
            },
            expected_output="entity_relationships",
            correlation_id=correlation_id
        )
        await self.a2a.send_message(linker_message)
        
        # Message to Visualizer Agent
        visualizer_message = create_task_delegation_message(
            from_agent=self.name,
            to_agent="visualizer",
            task_name="create_visualization",
            task_parameters={
                "content": document,
                "content_type": content_analysis["content_type"],
                "complexity_level": content_analysis["complexity_level"]
            },
            expected_output="interactive_graph",
            correlation_id=correlation_id,
            depends_on=["summarizer", "linker"]
        )
        await self.a2a.send_message(visualizer_message)
        
        self.logger.info("📨 Sent typed delegation messages to all specialized agents (FR#027)")
    
    async def _delegate_with_legacy_messages(self, content_analysis: Dict[str, Any], document: str):
        """Send legacy delegation messages (backward compatibility)"""
        from .base_agent import A2AMessage
        
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