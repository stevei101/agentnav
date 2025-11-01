"""
Visualizer Agent
Uses Gemma GPU service for complex graph generation tasks
"""
import os
import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Constants
MAX_PROMPT_LENGTH = 2000  # Maximum length of document content in prompt


class VisualizerAgent:
    """
    Visualizer Agent that uses Gemma GPU service for complex visualization tasks.
    
    This agent generates knowledge graphs (Mind Maps for documents, 
    Dependency Graphs for codebases) using the Gemma GPU-accelerated service.
    """
    
    def __init__(self, gemma_service_url: Optional[str] = None):
        self.gemma_service_url = gemma_service_url or os.getenv("GEMMA_SERVICE_URL")
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content and generate visualization using Gemma GPU service.
        
        Args:
            context: Contains 'document' (text content) and optionally 'content_type'
            
        Returns:
            Visualization data with nodes and edges
        """
        document = context.get("document", "")
        content_type = context.get("content_type", "document")  # 'document' or 'codebase'
        
        if not document:
            raise ValueError("Document content is required")
        
        # Determine visualization type
        viz_type = "MIND_MAP" if content_type == "document" else "DEPENDENCY_GRAPH"
        
        # Create prompt for Gemma to generate graph structure
        graph_prompt = f"""Generate a {viz_type} visualization for the following content.
        
Content:
{document[:MAX_PROMPT_LENGTH]}

Return a JSON structure with:
- nodes: array of {{id, label, group}}
- edges: array of {{from, to, label}}

Focus on key concepts and their relationships."""

        try:
            # Call Gemma GPU service for complex graph generation
            from services.gemma_service import generate_with_gemma
            
            logger.info(f"Calling Gemma GPU service for {viz_type} generation...")
            graph_text = await generate_with_gemma(
                prompt=graph_prompt,
                max_tokens=1000,
                temperature=0.7,
            )
            
            # Parse the response (Gemma should return JSON)
            try:
                # Try to extract JSON from the response
                graph_data = json.loads(graph_text)
            except json.JSONDecodeError:
                # If not pure JSON, try to extract it
                json_match = re.search(r'\{.*\}', graph_text, re.DOTALL)
                if json_match:
                    graph_data = json.loads(json_match.group())
                else:
                    # Fallback: create basic structure
                    logger.warning("Could not parse JSON from Gemma response, using fallback")
                    return self._create_fallback_graph(document, viz_type)
            
            return {
                "type": viz_type,
                "title": f"{viz_type} Visualization",
                "nodes": graph_data.get("nodes", []),
                "edges": graph_data.get("edges", []),
                "generated_by": "gemma-gpu-service",
            }
            
        except Exception as e:
            logger.error(f"Error in Visualizer Agent: {e}")
            # Fallback to basic structure if Gemma service unavailable
            return self._create_fallback_graph(document, viz_type)
    
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
        return {
            "type": viz_type,
            "title": f"{viz_type} Visualization",
            "nodes": [
                {"id": "root", "label": "Content Root", "group": "main"}
            ],
            "edges": [],
            "generated_by": "fallback",
        }

