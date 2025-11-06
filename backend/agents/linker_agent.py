"""
Linker Agent - ADK Implementation
Identifies key entities and their relationships for visualization
"""

import logging
from typing import Dict, Any, List, Optional
from .base_agent import Agent, A2AMessage
import time
import re

logger = logging.getLogger(__name__)


class LinkerAgent(Agent):
    """
    Linker Agent using ADK and A2A Protocol

    Responsibilities:
    - Identify key entities (concepts, functions, classes)
    - Map relationships between entities
    - Communicate findings via A2A Protocol
    - Prepare data structure for visualization
    - Emit real-time events for FR#020 streaming dashboard
    """

    def __init__(self, a2a_protocol=None, event_emitter: Optional[Any] = None):
        super().__init__("linker", a2a_protocol)
        self._prompt_template = None
        self.event_emitter = event_emitter  # For FR#020 WebSocket streaming

    def _get_prompt_template(self) -> str:
        """Get prompt template from Firestore or fallback"""
        if self._prompt_template:
            return self._prompt_template

        try:
            from services.prompt_loader import get_prompt

            self._prompt_template = get_prompt("linker_system_instruction")
            logger.info("✅ Loaded linker prompt from Firestore")
            return self._prompt_template
        except Exception as e:
            logger.warning(f"⚠️ Could not load prompt from Firestore: {e}")
            # Fallback prompt
            self._prompt_template = """
You are the Linker Agent in a multi-agent analysis system.

Your task is to identify key entities and their relationships for visualization.

For DOCUMENTS:
- Identify key concepts, themes, and topics
- Find relationships between concepts (e.g., "supports", "contradicts", "builds on")
- Note hierarchical relationships (main topics vs subtopics)
- Identify causal relationships and dependencies

For CODEBASES:
- Identify functions, classes, modules, and variables
- Map function calls and dependencies
- Find inheritance relationships
- Note import dependencies and module structure

Content to analyze:
{content}

Content Type: {content_type}

Return a structured analysis of entities and their relationships.
"""
            return self._prompt_template

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Linker processing: identify entities and relationships
        """
        start_time = time.time()
        document = context.get("document", "")
        content_type = context.get("content_type", "document")
        shared_context = context.get("shared_context", {})

        if not document:
            raise ValueError("Document content is required for relationship analysis")

        # Emit processing event
        if self.event_emitter:
            await self.event_emitter.emit_agent_processing(
                agent_name="Linker",
                metadata={
                    "sessionId": context.get("sessionId"),
                    "contentType": content_type,
                },
            )

        self.logger.info(f"🔗 Linker analyzing {content_type} relationships")

        try:
            # Extract entities based on content type
            entities = await self._extract_entities(document, content_type)

            # Identify relationships between entities
            relationships = await self._identify_relationships(
                document, content_type, entities
            )

            # Use summary from shared context if available
            summary_context = shared_context.get("summarizer_result", {})
            if summary_context:
                self.logger.info(
                    "📋 Using summary context for enhanced relationship analysis"
                )
                relationships = self._enhance_with_summary_context(
                    relationships, summary_context
                )

            # Prepare visualization data structure
            graph_data = self._prepare_graph_data(entities, relationships, content_type)

            # Notify other agents via A2A Protocol
            await self._notify_linking_complete(entities, relationships, graph_data)

            result = {
                "agent": "linker",
                "entities": entities,
                "relationships": relationships,
                "graph_data": graph_data,
                "content_type": content_type,
                "processing_complete": True,
                "timestamp": time.time(),
            }

            # Emit completion event with metrics
            if self.event_emitter:
                duration = time.time() - start_time
                await self.event_emitter.emit_agent_complete(
                    agent_name="Linker",
                    payload={
                        "summary": f"Identified {len(entities)} entities and {len(relationships)} relationships",
                        "entities": entities,
                        "relationships": relationships,
                        "metrics": {
                            "processingTime": duration,
                            "entitiesFound": len(entities),
                            "relationshipsFound": len(relationships),
                            "tokensProcessed": len(document),
                        },
                    },
                )

            return result

        except Exception as e:
            # Emit error event
            if self.event_emitter:
                await self.event_emitter.emit_agent_error(
                    agent_name="Linker", error_message=str(e)
                )
            raise

    async def _extract_entities(
        self, document: str, content_type: str
    ) -> List[Dict[str, Any]]:
        """Extract key entities from the content"""

        if content_type == "codebase":
            return self._extract_code_entities(document)
        else:
            return await self._extract_document_entities(document)

    def _extract_code_entities(self, document: str) -> List[Dict[str, Any]]:
        """Extract entities from code content"""
        entities = []
        lines = document.split("\n")

        # Extract functions
        for i, line in enumerate(lines):
            line = line.strip()

            # Python function definitions
            if line.startswith("def "):
                match = re.match(r"def\s+(\w+)\s*\(", line)
                if match:
                    entities.append(
                        {
                            "id": f"func_{match.group(1)}",
                            "label": match.group(1),
                            "type": "function",
                            "group": "Function",
                            "line_number": i + 1,
                            "signature": line,
                        }
                    )

            # Python class definitions
            elif line.startswith("class "):
                match = re.match(r"class\s+(\w+)", line)
                if match:
                    entities.append(
                        {
                            "id": f"class_{match.group(1)}",
                            "label": match.group(1),
                            "type": "class",
                            "group": "Class",
                            "line_number": i + 1,
                            "signature": line,
                        }
                    )

            # Import statements
            elif line.startswith("import ") or line.startswith("from "):
                module = (
                    line.split()[1] if line.startswith("import ") else line.split()[1]
                )
                entities.append(
                    {
                        "id": f"import_{module.replace('.', '_')}",
                        "label": module,
                        "type": "import",
                        "group": "Import",
                        "line_number": i + 1,
                    }
                )

        # Add JavaScript/TypeScript entities if detected
        if any(
            keyword in document for keyword in ["function", "const ", "let ", "var "]
        ):
            entities.extend(self._extract_js_entities(document))

        return entities

    def _extract_js_entities(self, document: str) -> List[Dict[str, Any]]:
        """Extract JavaScript/TypeScript entities"""
        entities = []
        lines = document.split("\n")

        for i, line in enumerate(lines):
            line = line.strip()

            # Function declarations
            if "function " in line:
                match = re.search(r"function\s+(\w+)\s*\(", line)
                if match:
                    entities.append(
                        {
                            "id": f"js_func_{match.group(1)}",
                            "label": match.group(1),
                            "type": "function",
                            "group": "Function",
                            "line_number": i + 1,
                        }
                    )

            # Variable declarations
            elif any(keyword in line for keyword in ["const ", "let ", "var "]):
                match = re.search(r"(?:const|let|var)\s+(\w+)", line)
                if match:
                    entities.append(
                        {
                            "id": f"js_var_{match.group(1)}",
                            "label": match.group(1),
                            "type": "variable",
                            "group": "Variable",
                            "line_number": i + 1,
                        }
                    )

        return entities

    async def _extract_document_entities(self, document: str) -> List[Dict[str, Any]]:
        """Extract entities from document content using Gemini"""
        try:
            # Use standardized Gemini client for cloud-based or local reasoning
            from services.gemini_client import reason_with_gemini

            prompt = f"""
Analyze this document and extract key entities (concepts, topics, themes).
Return them as a simple list, one per line.

Document:
{document[:2000]}

Extract 5-10 key entities:
"""

            response = await reason_with_gemini(
                prompt=prompt, max_tokens=300, temperature=0.3
            )

            # Parse response into entities
            entities = []
            lines = response.strip().split("\n")

            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith("-") and len(line) > 2:
                    # Clean up the entity name
                    entity_name = line.replace("-", "").replace("*", "").strip()
                    if entity_name:
                        entities.append(
                            {
                                "id": f"concept_{i}",
                                "label": entity_name,
                                "type": "concept",
                                "group": "Concept",
                                "importance": "high" if i < 3 else "medium",
                            }
                        )

            return entities[:10]  # Limit to 10 entities

        except Exception as e:
            self.logger.warning(f"⚠️  Error using Gemini for entity extraction: {e}")
            self.logger.info("📋 Falling back to basic entity extraction")
            return self._extract_document_entities_fallback(document)

    def _extract_document_entities_fallback(
        self, document: str
    ) -> List[Dict[str, Any]]:
        """Fallback entity extraction for documents"""
        entities = []

        # Extract potential headings and important phrases
        lines = document.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()

            # Markdown headings
            if line.startswith("#"):
                heading = line.replace("#", "").strip()
                if heading:
                    entities.append(
                        {
                            "id": f"heading_{i}",
                            "label": heading,
                            "type": "heading",
                            "group": "Topic",
                            "line_number": i + 1,
                        }
                    )

            # Short lines that might be important (less than 50 chars)
            elif len(line) < 50 and len(line) > 5 and ":" not in line:
                entities.append(
                    {
                        "id": f"phrase_{i}",
                        "label": line,
                        "type": "phrase",
                        "group": "Concept",
                        "line_number": i + 1,
                    }
                )

        return entities[:8]  # Limit to 8 entities

    async def _identify_relationships(
        self, document: str, content_type: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify relationships between entities"""

        if content_type == "codebase":
            return self._identify_code_relationships(document, entities)
        else:
            return await self._identify_document_relationships_with_embeddings(
                document, entities
            )

    def _identify_code_relationships(
        self, document: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify relationships in code"""
        relationships = []
        lines = document.split("\n")

        # Create entity lookup
        entity_names = {entity["label"]: entity["id"] for entity in entities}

        # Find function calls
        for line in lines:
            for entity in entities:
                if entity["type"] == "function":
                    func_name = entity["label"]
                    # Look for calls to this function
                    if f"{func_name}(" in line and not line.strip().startswith("def "):
                        # Find which function/class this call is in
                        # This is simplified - a full implementation would track scope
                        relationships.append(
                            {
                                "from": "unknown",  # Would need scope tracking
                                "to": entity["id"],
                                "type": "calls",
                                "label": "calls",
                            }
                        )

        # Find class inheritance
        for line in lines:
            if line.strip().startswith("class "):
                match = re.match(r"class\s+(\w+)\s*\(\s*(\w+)", line)
                if match:
                    child_class, parent_class = match.groups()
                    child_id = entity_names.get(child_class)
                    parent_id = entity_names.get(parent_class)
                    if child_id and parent_id:
                        relationships.append(
                            {
                                "from": child_id,
                                "to": parent_id,
                                "type": "inherits",
                                "label": "inherits from",
                            }
                        )

        # Find import dependencies
        import_entities = [e for e in entities if e["type"] == "import"]
        function_entities = [e for e in entities if e["type"] == "function"]

        # Simplified: assume functions might use imported modules
        for imp in import_entities[:3]:  # Limit to avoid too many connections
            for func in function_entities[:3]:
                relationships.append(
                    {
                        "from": func["id"],
                        "to": imp["id"],
                        "type": "uses",
                        "label": "imports",
                    }
                )

        return relationships

    async def _identify_document_relationships(
        self, document: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify relationships in document content"""
        relationships = []

        # Simple approach: entities that appear near each other are related
        entity_labels = [entity["label"].lower() for entity in entities]

        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:  # Avoid duplicates and self-references
                    continue

                # Check if entities appear in the same paragraph
                paragraphs = document.split("\n\n")
                for paragraph in paragraphs:
                    para_lower = paragraph.lower()
                    if (
                        entity1["label"].lower() in para_lower
                        and entity2["label"].lower() in para_lower
                    ):

                        relationships.append(
                            {
                                "from": entity1["id"],
                                "to": entity2["id"],
                                "type": "related",
                                "label": "related to",
                            }
                        )
                        break  # Only one relationship per pair

        # Create hierarchical relationships for headings
        heading_entities = [e for e in entities if e.get("type") == "heading"]
        concept_entities = [e for e in entities if e.get("type") == "concept"]

        for heading in heading_entities:
            for concept in concept_entities[:2]:  # Limit connections
                relationships.append(
                    {
                        "from": concept["id"],
                        "to": heading["id"],
                        "type": "belongs_to",
                        "label": "part of",
                    }
                )

        return relationships[:15]  # Limit total relationships

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def _identify_document_relationships_with_embeddings(
        self, document: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify relationships in document content using semantic embeddings

        This method uses simple co-occurrence analysis to identify relationships
        between entities.
        """
        return await self._identify_document_relationships(document, entities)

    async def _enhance_relationships_with_reasoning(
        self,
        document: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Use Gemini reasoning to enhance relationship analysis

        This method asks Gemini to analyze specific entity relationships
        in the context of the full document.
        """
        try:
            from services.gemini_client import reason_with_gemini

            # Take top entities by importance
            top_entities = [e["label"] for e in entities[:5]]

            prompt = f"""
Analyze the relationships between these entities in the given context.
For each pair, describe the relationship type (e.g., "supports", "contradicts", "builds on", "causes", "enables").

Entities: {', '.join(top_entities)}

Context:
{document[:1500]}

Provide relationship insights:
"""

            response = await reason_with_gemini(
                prompt=prompt, max_tokens=400, temperature=0.3
            )

            # Parse reasoning to enhance existing relationships
            for relationship in relationships:
                # Add reasoning context
                relationship["reasoning_context"] = response[:200]  # Store snippet

            self.logger.info("✅ Enhanced relationships with Gemini reasoning")

        except Exception as e:
            self.logger.warning(f"⚠️  Could not enhance with Gemini reasoning: {e}")

        return relationships

    def _enhance_with_summary_context(
        self, relationships: List[Dict[str, Any]], summary_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance relationships using summary context from Summarizer Agent"""
        # This could use summary insights to weight or filter relationships
        insights = summary_context.get("insights", {})

        # For now, just add metadata based on content length
        for relationship in relationships:
            relationship["confidence"] = "high" if len(relationships) < 10 else "medium"
            relationship["source"] = "linker_agent"

        return relationships

    def _prepare_graph_data(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        content_type: str,
    ) -> Dict[str, Any]:
        """Prepare graph data structure for visualization"""

        # Convert entities to visualization nodes
        nodes = []
        for entity in entities:
            nodes.append(
                {
                    "id": entity["id"],
                    "label": entity["label"],
                    "group": entity.get("group", "Default"),
                    "type": entity.get("type", "unknown"),
                    "metadata": {
                        "line_number": entity.get("line_number"),
                        "importance": entity.get("importance", "medium"),
                    },
                }
            )

        # Convert relationships to visualization edges
        edges = []
        for rel in relationships:
            edges.append(
                {
                    "from": rel["from"],
                    "to": rel["to"],
                    "label": rel.get("label", ""),
                    "type": rel.get("type", "related"),
                    "confidence": rel.get("confidence", "medium"),
                }
            )

        viz_type = "DEPENDENCY_GRAPH" if content_type == "codebase" else "MIND_MAP"

        return {
            "type": viz_type,
            "title": f"{viz_type} - Entity Relationships",
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "content_type": content_type,
            },
        }

    async def _notify_linking_complete(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        graph_data: Dict[str, Any],
    ):
        """Notify other agents that linking is complete via A2A Protocol"""

        # Broadcast completion
        message = A2AMessage(
            message_id=f"linker_complete_{int(time.time())}",
            from_agent=self.name,
            to_agent="*",
            message_type="linking_complete",
            data={
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "graph_ready": True,
            },
            priority=3,
        )
        await self.a2a.send_message(message)

        # Send specific data to visualizer
        visualizer_message = A2AMessage(
            message_id=f"linker_to_visualizer_{int(time.time())}",
            from_agent=self.name,
            to_agent="visualizer",
            message_type="context_update",
            data={
                "entities": entities,
                "relationships": relationships,
                "graph_data": graph_data,
                "ready_for_final_visualization": True,
            },
            priority=4,
        )
        await self.a2a.send_message(visualizer_message)

        self.logger.info("📤 Sent linking completion notifications via A2A Protocol")

    async def _handle_a2a_message(self, message: A2AMessage):
        """Handle incoming A2A messages specific to Linker"""
        await super()._handle_a2a_message(message)

        if message.message_type == "task_delegation":
            task = message.data.get("task")
            if task == "identify_relationships":
                self.logger.info(
                    f"📥 Received relationship analysis task from {message.from_agent}"
                )
                # Task will be processed by main process() method

        elif message.message_type == "summary_complete":
            self.logger.info(
                "📋 Received summary completion - can enhance relationship analysis"
            )
            # Could trigger re-analysis with summary context
