"""
Suggestion Agent - ADK Implementation for Prompt Vault Intelligence (FR#201)

This agent analyzes raw prompt text and provides intelligent suggestions for
prompt improvement, structured output generation, and function calling hints.

Integrates with the Prompt Vault application via ADK/A2A Protocol to provide
AI-driven prompt optimization suggestions.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from .base_agent import Agent, A2AMessage

logger = logging.getLogger(__name__)


class SuggestionAgent(Agent):
    """
    Suggestion Agent using ADK and A2A Protocol
    
    Responsibilities:
    - Analyze raw prompt text for improvement opportunities
    - Suggest structured output JSON schemas
    - Recommend function calling definitions
    - Provide optimization suggestions for clarity and effectiveness
    - Communicate findings via A2A Protocol
    
    Feature Request: FR#201 - Prompt Vault Intelligence
    """
    
    def __init__(self, a2a_protocol=None, event_emitter: Optional[Any] = None):
        super().__init__("suggestion", a2a_protocol)
        self._prompt_template = None
        self.event_emitter = event_emitter
    
    def _get_prompt_template(self) -> str:
        """Get prompt template for suggestion analysis"""
        if self._prompt_template:
            return self._prompt_template
        
        try:
            from services.prompt_loader import get_prompt
            
            self._prompt_template = get_prompt("suggestion_agent_system_instruction")
            logger.info("✅ Loaded suggestion agent prompt from Firestore")
            return self._prompt_template
        except Exception as e:
            logger.warning(f"⚠️ Could not load prompt from Firestore: {e}")
            # Fallback prompt
            self._prompt_template = """
You are the Suggestion Agent, an expert in prompt engineering and optimization.

Your task is to analyze user prompts and provide intelligent suggestions for improvement.

Analyze the following prompt and provide:

1. OPTIMIZATION SUGGESTIONS:
   - Clarity improvements (more specific instructions, better structure)
   - Constraint additions (output format, length, style requirements)
   - Example additions (few-shot learning opportunities)
   - Context enhancements (background information that would help)

2. STRUCTURED OUTPUT SUGGESTION:
   - If the prompt expects structured data, suggest a JSON schema
   - Include field names, types, descriptions, and constraints
   - Ensure schema is compatible with Gemini's structured output format

3. FUNCTION CALLING HINT:
   - Identify if the task could benefit from tool/function calling
   - Suggest function definitions with parameters and descriptions
   - Explain when and why function calling would be beneficial

4. PROMPT QUALITY SCORE:
   - Rate the prompt quality (1-10)
   - Identify strengths and weaknesses
   - Provide specific actionable improvements

Format your response as:

OPTIMIZATION_SUGGESTIONS:
[List 3-5 specific suggestions for improving the prompt]

STRUCTURED_OUTPUT_SCHEMA:
[JSON schema if applicable, or "NOT_APPLICABLE"]

FUNCTION_CALLING_HINT:
[Function definition if applicable, or "NOT_APPLICABLE"]

QUALITY_SCORE: [1-10]
STRENGTHS: [List strengths]
WEAKNESSES: [List weaknesses]
ACTIONABLE_IMPROVEMENTS: [List specific improvements]

Prompt to analyze:
{prompt_text}
"""
            return self._prompt_template
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggestion Agent processing: analyze prompt and provide suggestions
        
        Args:
            context: Dictionary containing:
                - prompt_text: The raw prompt text to analyze
                - user_context: Optional user context (e.g., intended use case)
                - existing_schema: Optional existing structured output schema
        
        Returns:
            Dictionary containing:
                - optimization_suggestions: List of improvement suggestions
                - structured_output_schema: Suggested JSON schema (if applicable)
                - function_calling_hint: Suggested function definition (if applicable)
                - quality_score: Prompt quality rating (1-10)
                - strengths: List of prompt strengths
                - weaknesses: List of prompt weaknesses
                - actionable_improvements: List of specific improvements
        """
        prompt_text = context.get("prompt_text", "")
        user_context = context.get("user_context", "")
        
        if not prompt_text:
            raise ValueError("Prompt text is required for suggestion analysis")
        
        self.logger.info("💡 Suggestion Agent analyzing prompt for improvements")
        
        # Emit processing event
        if self.event_emitter:
            await self.event_emitter.emit_agent_processing(
                agent="suggestion",
                step=1,
                partial_results={"status": "analyzing prompt"},
            )
        
        # Step 1: Analyze prompt using Gemini
        analysis_result = await self._analyze_prompt_with_ai(prompt_text, user_context)
        
        # Step 2: Parse and structure the analysis
        structured_suggestions = self._structure_analysis(analysis_result, prompt_text)
        
        # Step 3: Notify other agents via A2A Protocol
        await self._notify_suggestions_complete(structured_suggestions)
        
        # Emit complete event
        if self.event_emitter:
            await self.event_emitter.emit_agent_complete(
                agent="suggestion",
                step=1,
                metrics={
                    "quality_score": structured_suggestions.get("quality_score", 0),
                    "suggestions_count": len(structured_suggestions.get("optimization_suggestions", [])),
                    "has_schema": structured_suggestions.get("structured_output_schema") is not None,
                    "has_function_hint": structured_suggestions.get("function_calling_hint") is not None,
                },
            )
        
        return {
            "agent": "suggestion",
            "prompt_analyzed": prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text,
            **structured_suggestions,
            "processing_complete": True,
            "timestamp": time.time(),
        }
    
    async def _analyze_prompt_with_ai(self, prompt_text: str, user_context: str) -> str:
        """Use Gemini to analyze prompt and generate suggestions"""
        try:
            from services.gemini_client import reason_with_gemini
            
            prompt_template = self._get_prompt_template()
            
            # Add user context if provided
            context_section = ""
            if user_context:
                context_section = f"\n\nUser Context: {user_context}\n"
            
            analysis_prompt = prompt_template.format(
                prompt_text=prompt_text[:4000],  # Limit for token size
            ) + context_section
            
            self.logger.info("🤖 Calling Gemini service for prompt analysis")
            response = await reason_with_gemini(
                prompt=analysis_prompt,
                max_tokens=1500,
                temperature=0.4,  # Moderate temperature for creative but consistent suggestions
            )
            
            return response.strip()
        
        except Exception as e:
            self.logger.error(f"Error analyzing prompt with AI: {e}")
            # Fallback to basic analysis
            return self._create_fallback_analysis(prompt_text)
    
    def _create_fallback_analysis(self, prompt_text: str) -> str:
        """Create basic fallback analysis when Gemini service unavailable"""
        word_count = len(prompt_text.split())
        has_examples = "example" in prompt_text.lower() or "e.g." in prompt_text.lower()
        has_constraints = any(word in prompt_text.lower() for word in ["must", "should", "format", "length"])
        
        suggestions = []
        if word_count < 20:
            suggestions.append("Add more context and specific instructions")
        if not has_examples:
            suggestions.append("Consider adding examples to clarify expected output")
        if not has_constraints:
            suggestions.append("Add constraints for output format, length, or style")
        
        quality_score = 5
        if word_count > 50:
            quality_score += 1
        if has_examples:
            quality_score += 2
        if has_constraints:
            quality_score += 1
        
        return f"""
OPTIMIZATION_SUGGESTIONS:
{chr(10).join(f"- {s}" for s in suggestions)}

STRUCTURED_OUTPUT_SCHEMA:
NOT_APPLICABLE

FUNCTION_CALLING_HINT:
NOT_APPLICABLE

QUALITY_SCORE: {quality_score}
STRENGTHS: Basic prompt structure
WEAKNESSES: Limited detail and constraints
ACTIONABLE_IMPROVEMENTS: Add more specific instructions and examples
"""
    
    def _structure_analysis(self, analysis_result: str, original_prompt: str) -> Dict[str, Any]:
        """Parse and structure the AI analysis into a structured format"""
        structured = {
            "optimization_suggestions": [],
            "structured_output_schema": None,
            "function_calling_hint": None,
            "quality_score": 5,
            "strengths": [],
            "weaknesses": [],
            "actionable_improvements": [],
        }
        
        try:
            lines = analysis_result.split("\n")
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                
                # Detect section headers
                if line.startswith("OPTIMIZATION_SUGGESTIONS:"):
                    current_section = "optimization_suggestions"
                    current_content = []
                elif line.startswith("STRUCTURED_OUTPUT_SCHEMA:"):
                    if current_section == "optimization_suggestions":
                        structured["optimization_suggestions"] = self._parse_list_items(current_content)
                    current_section = "structured_output_schema"
                    current_content = []
                elif line.startswith("FUNCTION_CALLING_HINT:"):
                    if current_section == "structured_output_schema":
                        structured["structured_output_schema"] = self._parse_schema(current_content)
                    current_section = "function_calling_hint"
                    current_content = []
                elif line.startswith("QUALITY_SCORE:"):
                    if current_section == "function_calling_hint":
                        structured["function_calling_hint"] = self._parse_function_hint(current_content)
                    current_section = "quality_score"
                    # Extract score
                    score_text = line.replace("QUALITY_SCORE:", "").strip()
                    try:
                        structured["quality_score"] = int(score_text.split()[0])
                    except (ValueError, IndexError):
                        structured["quality_score"] = 5
                elif line.startswith("STRENGTHS:"):
                    current_section = "strengths"
                    current_content = []
                elif line.startswith("WEAKNESSES:"):
                    if current_section == "strengths":
                        structured["strengths"] = self._parse_list_items(current_content)
                    current_section = "weaknesses"
                    current_content = []
                elif line.startswith("ACTIONABLE_IMPROVEMENTS:"):
                    if current_section == "weaknesses":
                        structured["weaknesses"] = self._parse_list_items(current_content)
                    current_section = "actionable_improvements"
                    current_content = []
                elif line and current_section:
                    current_content.append(line)
            
            # Parse final section
            if current_section == "actionable_improvements":
                structured["actionable_improvements"] = self._parse_list_items(current_content)
        
        except Exception as e:
            self.logger.warning(f"⚠️ Error parsing analysis: {e}")
        
        return structured
    
    def _parse_list_items(self, lines: List[str]) -> List[str]:
        """Parse list items from lines (handles bullet points and numbered lists)"""
        items = []
        for line in lines:
            # Remove common list markers
            cleaned = line.lstrip("- •*123456789.").strip()
            if cleaned:
                items.append(cleaned)
        return items
    
    def _parse_schema(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Parse JSON schema from lines"""
        content = "\n".join(lines).strip()
        
        if content.upper() == "NOT_APPLICABLE" or not content:
            return None
        
        try:
            import json
            # Try to parse as JSON
            schema = json.loads(content)
            return schema
        except json.JSONDecodeError:
            # If not valid JSON, return as text description
            return {"description": content, "type": "object"}
    
    def _parse_function_hint(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Parse function calling hint from lines"""
        content = "\n".join(lines).strip()
        
        if content.upper() == "NOT_APPLICABLE" or not content:
            return None
        
        try:
            import json
            # Try to parse as JSON
            function_def = json.loads(content)
            return function_def
        except json.JSONDecodeError:
            # If not valid JSON, return as text description
            return {"description": content}
    
    async def _notify_suggestions_complete(self, suggestions: Dict[str, Any]):
        """Notify other agents that suggestions are complete via A2A Protocol"""
        message = A2AMessage(
            message_id=f"suggestion_complete_{int(time.time())}",
            from_agent=self.name,
            to_agent="*",  # Broadcast to all agents
            message_type="suggestion_complete",
            data={
                "quality_score": suggestions.get("quality_score", 0),
                "suggestions_count": len(suggestions.get("optimization_suggestions", [])),
                "has_schema": suggestions.get("structured_output_schema") is not None,
                "has_function_hint": suggestions.get("function_calling_hint") is not None,
            },
            priority=3,
        )
        await self.a2a.send_message(message)
        
        self.logger.info("📤 Sent suggestion completion notification via A2A Protocol")
    
    async def _handle_a2a_message(self, message: A2AMessage):
        """Handle incoming A2A messages specific to Suggestion Agent"""
        await super()._handle_a2a_message(message)
        
        if message.message_type == "task_delegation":
            task = message.data.get("task")
            if task == "analyze_prompt":
                self.logger.info(
                    f"📥 Received prompt analysis task from {message.from_agent}"
                )
                # Task parameters are already in the message data
                # The main process() method will handle the actual analysis
        
        elif message.message_type == "priority_update":
            new_priority = message.data.get("priority", "normal")
            self.logger.info(f"📋 Priority updated to: {new_priority}")
            # Could adjust processing behavior based on priority
