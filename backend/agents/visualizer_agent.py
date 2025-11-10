"""
Visualizer Agent - ADK Implementation
Generates knowledge graphs using Gemini
Integrates with Linker and Summarizer agents via A2A Protocol
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

from .base_agent import A2AMessage, A2AMessageLike, Agent

logger = logging.getLogger(__name__)

# Constants
MAX_PROMPT_LENGTH = 2000  # Maximum length of document content in prompt

# Fallback prompt (used if Firestore unavailable)
FALLBACK_PROMPT = """Generate a {viz_type} visualization for the following content.

Content:
{content}

Return a JSON structure with:
- nodes: array of {{id, label, group}}
- edges: array of {{from, to, label}}

Focus on key concepts and their relationships."""


class VisualizerAgent(Agent):
    """
    Visualizer Agent using ADK and A2A Protocol

    Responsibilities:
    - Generate knowledge graphs (Mind Maps for documents, Dependency Graphs for codebases)
    - Use data from Summarizer and Linker agents via A2A Protocol
    - Enhance visualizations using Gemini
    - Render visualization-ready JSON
    """

    def __init__(self, a2a_protocol, event_emitter=None):
        super().__init__("visualizer", a2a_protocol)
        self.event_emitter = event_emitter
        self._prompt_template: Optional[str] = None
        self._linked_data: Optional[Dict[str, Any]] = None
        self._summary_data: Optional[Dict[str, Any]] = None

    def _get_prompt_template(self) -> str:
        """
        Get prompt template from Firestore or fallback

        Returns:
            Prompt template string

        Raises:
            RuntimeError: If Firestore unavailable in production/staging
        """
        # If already loaded, return cached version
        if self._prompt_template:
            return self._prompt_template

        try:
            # Try to load from Firestore
            from backend.services.prompt_loader import get_prompt

            self._prompt_template = get_prompt("visualizer_graph_generation")
            logger.info("✅ Loaded prompt from Firestore")
            return self._prompt_template
        except Exception as e:
            # Fallback behavior depends on environment
            environment = os.getenv("ENVIRONMENT", "development")

            if environment in ["production", "staging"]:
                # Critical error in production - enforce prompt management
                error_msg = f"CRITICAL: Failed to load prompt from Firestore in {environment} environment"
                logger.error(error_msg)
                logger.error(f"   Error: {e}")
                raise RuntimeError(error_msg)
            else:
                # Allow fallback for development only
                logger.warning(f"⚠️  Could not load prompt from Firestore: {e}")
                logger.info("Using fallback prompt (development mode only)")
                self._prompt_template = FALLBACK_PROMPT
                return self._prompt_template

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content and generate visualization using ADK and A2A Protocol integration.

        Args:
            context: Contains 'document' (text content) and optionally 'content_type'

        Returns:
            Visualization data with nodes and edges
        """
        start_time = time.time()
        document = context.get("document", "")
        content_type = context.get(
            "content_type", "document"
        )  # 'document' or 'codebase'

        if not document:
            raise ValueError("Document content is required")

        # Emit processing event
        if self.event_emitter:
            await self.event_emitter.emit_agent_processing(
                agent_name="Visualizer",
                metadata={
                    "sessionId": context.get("sessionId"),
                    "contentType": content_type,
                },
            )

        self.logger.info(f"🎨 Visualizer creating {content_type} visualization")

        try:
            # Check if we have data from other agents via A2A Protocol
            await self._process_a2a_messages()

            # Use linked data if available from Linker Agent
            if self._linked_data:
                self.logger.info(
                    "📊 Using entity and relationship data from Linker Agent"
                )
                result = await self._create_visualization_from_linked_data(
                    self._linked_data, content_type, document
                )
            else:
                # Fallback to original implementation if no linked data
                self.logger.info(
                    "⚙️ Fallback: Generating visualization directly with Gemini"
                )
                result = await self._create_visualization_with_gemini(
                    document, content_type
                )

            # Emit completion event with metrics
            if self.event_emitter:
                duration = time.time() - start_time
                await self.event_emitter.emit_agent_complete(
                    agent_name="Visualizer",
                    payload={
                        "summary": f"Generated {len(result.get('nodes', []))} nodes",
                        "visualization": {
                            "nodes": result.get("nodes", []),
                            "edges": result.get("edges", []),
                        },
                        "metrics": {
                            "processingTime": duration,
                            "tokensProcessed": len(document),
                        },
                    },
                )

            return result

        except Exception as e:
            # Emit error event
            if self.event_emitter:
                await self.event_emitter.emit_agent_error(
                    agent_name="Visualizer", error_message=str(e)
                )
            raise

    async def _create_visualization_from_linked_data(
        self, linked_data: Dict[str, Any], content_type: str, document: str
    ) -> Dict[str, Any]:
        """Create visualization using data from Linker Agent"""

        # Use the graph data prepared by Linker Agent
        graph_data = linked_data.get("graph_data", {})

        if graph_data and graph_data.get("nodes") and graph_data.get("edges"):
            # Enhance the visualization with additional processing
            enhanced_graph = await self._enhance_visualization(
                graph_data, document, content_type
            )

            result = {
                "type": enhanced_graph.get("type", "MIND_MAP"),
                "title": enhanced_graph.get(
                    "title", f"{content_type.title()} Visualization"
                ),
                "nodes": enhanced_graph["nodes"],
                "edges": enhanced_graph["edges"],
                "generated_by": "adk_multi_agent",
                "agent_collaboration": {
                    "linker_entities": len(linked_data.get("entities", [])),
                    "linker_relationships": len(linked_data.get("relationships", [])),
                    "enhanced_by_visualizer": True,
                },
                "timestamp": time.time(),
            }

            # Notify completion via A2A Protocol
            await self._notify_visualization_complete(result)

            return result
        else:
            # Fallback if linked data is incomplete
            return await self._create_visualization_with_gemini(document, content_type)

    async def _create_visualization_with_gemini(
        self, document: str, content_type: str
    ) -> Dict[str, Any]:
        """Visualization method using Gemini"""
        # Determine visualization type
        viz_type = "MIND_MAP" if content_type == "document" else "DEPENDENCY_GRAPH"

        # Get prompt template from Firestore (or fallback)
        prompt_template = self._get_prompt_template()

        # Create prompt for Gemini to generate graph structure
        graph_prompt = prompt_template.format(
            viz_type=viz_type, content=document[:MAX_PROMPT_LENGTH]
        )

        try:
            from backend.services.gemini_client import reason_with_gemini

            logger.info(f"Calling Gemini service for {viz_type} generation...")
            graph_text = await reason_with_gemini(
                prompt=graph_prompt,
                max_tokens=1000,
                temperature=0.7,
            )

            # Parse the response (Gemini should return JSON)
            try:
                # Try to extract JSON from the response
                graph_data = json.loads(graph_text)
            except json.JSONDecodeError:
                # If not pure JSON, try to extract it
                json_match = re.search(r"\{.*\}", graph_text, re.DOTALL)
                if json_match:
                    graph_data = json.loads(json_match.group())
                else:
                    # Fallback: create basic structure
                    logger.warning(
                        "Could not parse JSON from Gemini response, using fallback"
                    )
                    return self._create_fallback_graph(document, viz_type)

            result = {
                "type": viz_type,
                "title": f"{viz_type} Visualization",
                "nodes": graph_data.get("nodes", []),
                "edges": graph_data.get("edges", []),
                "generated_by": "gemini-service",
            }

            # Notify completion via A2A Protocol
            await self._notify_visualization_complete(result)

            return result

        except Exception as e:
            logger.error(f"Error in Visualizer Agent: {e}")
            # Fallback to basic structure if Gemini service unavailable
            fallback_result = self._create_fallback_graph(document, viz_type)
            await self._notify_visualization_complete(fallback_result)
            return fallback_result

    async def _enhance_visualization(
        self, graph_data: Dict[str, Any], document: str, content_type: str
    ) -> Dict[str, Any]:
        """Enhance visualization using Gemini and summary context"""
        try:
            # Use summary data if available
            summary_context = ""
            if self._summary_data:
                summary = self._summary_data.get("summary", "")
                summary_context = f"\n\nSummary context: {summary[:500]}"

            enhancement_prompt = f"""
Enhance this visualization graph with better node groupings and edge labels.

Original graph has {len(graph_data.get('nodes', []))} nodes and {len(graph_data.get('edges', []))} edges.

Content type: {content_type}
{summary_context}

Current nodes: {[node.get('label', 'Unknown') for node in graph_data.get('nodes', [])[:10]]}

Suggest improvements to make the visualization clearer and more informative.
Return enhanced node groups and edge labels.
"""

            from backend.services.gemini_client import reason_with_gemini

            enhancement_text = await reason_with_gemini(
                prompt=enhancement_prompt, max_tokens=400, temperature=0.5
            )

            # Apply enhancements (simplified implementation)
            enhanced_graph = graph_data.copy()

            # Add metadata from enhancement
            enhanced_graph["enhancement_applied"] = True
            enhanced_graph["enhancement_context"] = enhancement_text[:200]

            return enhanced_graph

        except Exception as e:
            self.logger.warning(f"Could not enhance visualization: {e}")
            return graph_data

    async def _notify_visualization_complete(self, result: Dict[str, Any]):
        """Notify that visualization is complete via A2A Protocol"""
        message = A2AMessage(
            message_id=f"visualizer_complete_{int(time.time())}",
            from_agent=self.name,
            to_agent="*",
            message_type="visualization_complete",
            data={
                "visualization_type": result.get("type"),
                "node_count": len(result.get("nodes", [])),
                "edge_count": len(result.get("edges", [])),
                "generated_by": result.get("generated_by"),
                "ready_for_display": True,
            },
            priority=2,
        )
        await self._send_a2a_message(message)

        self.logger.info(
            "📤 Sent visualization completion notification via A2A Protocol"
        )

    async def _handle_a2a_message(self, message: A2AMessageLike):
        """Handle incoming A2A messages specific to Visualizer"""
        await super()._handle_a2a_message(message)

        if message.message_type == "context_update":
            if message.from_agent == "linker":
                self.logger.info("📥 Received linked data from Linker Agent")
                self._linked_data = message.data

            elif message.from_agent == "summarizer":
                self.logger.info("📥 Received summary data from Summarizer Agent")
                self._summary_data = message.data

        elif message.message_type == "task_delegation":
            task = message.data.get("task")
            if task == "create_visualization":
                self.logger.info(
                    f"📥 Received visualization task from {message.from_agent}"
                )
                depends_on = message.data.get("depends_on", [])
                if depends_on:
                    self.logger.info(f"📋 Visualization depends on: {depends_on}")

    def _create_fallback_graph(self, document: str, viz_type: str) -> Dict[str, Any]:
        """
        Create a basic fallback graph structure.

        Returns consistent structure matching successful response format:
        - type: visualization type
        - title: visualization title
        - nodes: array of graph nodes
        - edges: array of graph edges
        - generated_by: service identifier
        """
        result = {
            "type": viz_type,
            "title": f"{viz_type} Visualization",
            "nodes": [{"id": "root", "label": "Content Root", "group": "main"}],
            "edges": [],
            "generated_by": "fallback",
            "timestamp": time.time(),
        }

        # Create a simple fallback structure
        return result
