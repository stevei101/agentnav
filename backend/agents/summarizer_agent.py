"""
Summarizer Agent - ADK Implementation
Creates concise, comprehensive summaries of content
"""

import hashlib
import logging
from typing import Dict, Any, Optional
from .base_agent import Agent, A2AMessage
import time

logger = logging.getLogger(__name__)


class SummarizerAgent(Agent):
    """
    Summarizer Agent using ADK and A2A Protocol

    Responsibilities:
    - Read entire content and generate concise summaries
    - Store intermediate results in Firestore
    - Communicate findings via A2A Protocol
    - Emit real-time events for FR#020 streaming dashboard
    """

    def __init__(self, a2a_protocol=None, event_emitter: Optional[Any] = None):
        super().__init__("summarizer", a2a_protocol)
        self._prompt_template = None
        self.event_emitter = event_emitter  # For FR#020 WebSocket streaming

    def _get_prompt_template(self) -> str:
        """Get prompt template from Firestore or fallback"""
        if self._prompt_template:
            return self._prompt_template

        try:
            from services.prompt_loader import get_prompt

            self._prompt_template = get_prompt("summarizer_system_instruction")
            logger.info("✅ Loaded summarizer prompt from Firestore")
            return self._prompt_template
        except Exception as e:
            logger.warning(f"⚠️ Could not load prompt from Firestore: {e}")
            # Fallback prompt
            self._prompt_template = """
You are the Summarizer Agent in a multi-agent analysis system.

Your task is to analyze the provided content and create a comprehensive yet concise summary.

For DOCUMENTS:
- Identify main themes and key points
- Extract important facts and conclusions
- Note any significant arguments or findings
- Highlight key relationships between concepts

For CODEBASES:
- Identify main functionality and purpose
- List key functions, classes, and modules
- Note important dependencies and interactions
- Highlight architectural patterns

Content to summarize:
{content}

Content Type: {content_type}

Create a comprehensive summary that captures the essence and key information.
"""
            return self._prompt_template

    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarizer processing: create comprehensive summary of content
        """
        document = context.get("document", "")
        content_type = context.get("content_type", "document")

        if not document:
            raise ValueError("Document content is required for summarization")

        self.logger.info(f"📝 Summarizer analyzing {content_type} content")

        # Emit processing event for FR#020
        if self.event_emitter:
            await self.event_emitter.emit_agent_processing(
                agent="summarizer", step=2, partial_results={"status": "generating summary"}
            )

        # Generate summary using Gemini
        summary = await self._generate_summary(document, content_type)

        # Extract key insights
        insights = self._extract_insights(document, content_type, summary)

        # Store results in Firestore for persistence
        await self._store_summary_results(summary, insights)

        # Notify other agents via A2A Protocol
        await self._notify_summary_complete(summary, insights)

        # Emit complete event for FR#020
        if self.event_emitter:
            await self.event_emitter.emit_agent_complete(
                agent="summarizer",
                step=2,
                summary=summary,
                metrics={
                    "summary_length_words": len(summary.split()),
                    "insights_count": len(insights),
                },
            )

        return {
            "agent": "summarizer",
            "summary": summary,
            "insights": insights,
            "content_type": content_type,
            "processing_complete": True,
            "timestamp": time.time(),
        }

    async def _generate_summary(self, document: str, content_type: str) -> str:
        """Generate summary using Gemini via Gemma service"""
        try:
            from services.gemma_service import generate_with_gemma

            prompt_template = self._get_prompt_template()
            prompt = prompt_template.format(
                content=document[:4000], content_type=content_type  # Limit content for prompt size
            )

            self.logger.info("🤖 Calling Gemma service for summary generation")
            summary = await generate_with_gemma(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3,  # Lower temperature for more consistent summaries
            )

            return summary.strip()

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            # Fallback to basic summary
            return self._create_fallback_summary(document, content_type)

    def _create_fallback_summary(self, document: str, content_type: str) -> str:
        """Create basic fallback summary when Gemma service unavailable"""
        lines = document.split("\n")
        words = document.split()

        if content_type == "codebase":
            # Basic code analysis
            functions = [line.strip() for line in lines if "def " in line or "function" in line]
            classes = [line.strip() for line in lines if "class " in line]

            summary = f"This codebase contains {len(lines)} lines of code with {len(words)} words. "
            if functions:
                summary += f"Key functions include: {', '.join(functions[:3])}. "
            if classes:
                summary += f"Key classes include: {', '.join(classes[:3])}. "

        else:
            # Basic document analysis
            first_lines = [line.strip() for line in lines[:5] if line.strip()]
            summary = f"This document contains {len(lines)} lines with {len(words)} words. "
            if first_lines:
                summary += f"It begins with: {first_lines[0][:100]}..."

        return summary

    def _extract_insights(self, document: str, content_type: str, summary: str) -> Dict[str, Any]:
        """Extract key insights from the content and summary"""
        insights = {
            "word_count": len(document.split()),
            "line_count": len(document.split("\n")),
            "content_type": content_type,
            "key_metrics": {},
        }

        if content_type == "codebase":
            # Code-specific insights
            lines = document.split("\n")
            insights["key_metrics"] = {
                "functions": len([line for line in lines if "def " in line]),
                "classes": len([line for line in lines if "class " in line]),
                "imports": len(
                    [
                        line
                        for line in lines
                        if line.strip().startswith("import ") or line.strip().startswith("from ")
                    ]
                ),
                "comments": len([line for line in lines if line.strip().startswith("#")]),
            }
        else:
            # Document-specific insights
            sentences = document.count(".") + document.count("!") + document.count("?")
            paragraphs = len([para for para in document.split("\n\n") if para.strip()])
            insights["key_metrics"] = {
                "sentences": sentences,
                "paragraphs": paragraphs,
                "avg_words_per_sentence": insights["word_count"] / max(sentences, 1),
                "reading_time_minutes": max(1, insights["word_count"] // 200),  # ~200 WPM average
            }

        insights["summary_length"] = len(summary.split())
        insights["compression_ratio"] = round(
            insights["summary_length"] / insights["word_count"], 3
        )

        return insights

    async def _store_summary_results(self, summary: str, insights: Dict[str, Any]):
        """Store summary results in Firestore for persistence"""
        try:
            from services.firestore_client import get_firestore_client

            db = get_firestore_client()

            # Create document in summaries collection
            doc_data = {
                "summary": summary,
                "insights": insights,
                "agent": "summarizer",
                "timestamp": time.time(),
                "session_id": insights.get("session_id", "default"),  # Could be passed in context
            }

            # Use content hash as document ID for deduplication (deterministic across restarts)
            content_hash = hashlib.sha256(summary.encode("utf-8")).hexdigest()[
                :16
            ]  # Use first 16 chars
            doc_ref = db.get_document("summaries", content_hash)
            doc_ref.set(doc_data)

            self.logger.info(f"💾 Stored summary results in Firestore: {content_hash}")

        except Exception as e:
            self.logger.warning(f"⚠️ Could not store summary in Firestore: {e}")
            # Continue without storage - not critical for operation

    async def _notify_summary_complete(self, summary: str, insights: Dict[str, Any]):
        """Notify other agents that summary is complete via A2A Protocol"""
        message = A2AMessage(
            message_id=f"summarizer_complete_{int(time.time())}",
            from_agent=self.name,
            to_agent="*",  # Broadcast to all agents
            message_type="summary_complete",
            data={
                "summary": (
                    summary[:200] + "..." if len(summary) > 200 else summary
                ),  # Truncated for message
                "insights": insights,
                "full_summary_available": True,
            },
            priority=3,
        )
        await self.a2a.send_message(message)

        # Also send specific notification to visualizer agent
        visualizer_message = A2AMessage(
            message_id=f"summarizer_to_visualizer_{int(time.time())}",
            from_agent=self.name,
            to_agent="visualizer",
            message_type="context_update",
            data={"summary": summary, "insights": insights, "ready_for_visualization": True},
            priority=4,
        )
        await self.a2a.send_message(visualizer_message)

        self.logger.info("📤 Sent summary completion notifications via A2A Protocol")

    async def _handle_a2a_message(self, message: A2AMessage):
        """Handle incoming A2A messages specific to Summarizer"""
        await super()._handle_a2a_message(message)

        if message.message_type == "task_delegation":
            task = message.data.get("task")
            if task == "create_summary":
                self.logger.info(f"📥 Received summarization task from {message.from_agent}")
                # Task parameters are already in the message data
                # The main process() method will handle the actual summarization

        elif message.message_type == "priority_update":
            new_priority = message.data.get("priority", "normal")
            self.logger.info(f"📋 Priority updated to: {new_priority}")
            # Could adjust processing behavior based on priority
