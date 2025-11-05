"""Suggestion Agent for generating prompt suggestions and analyzing prompts."""
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from app.agents.base import BaseAgent
from app.a2a.protocol import MessageType
from app.config import settings
from app.services.supabase_client import supabase_client

logger = logging.getLogger(__name__)


class SuggestionAgent(BaseAgent):
    """Agent that generates prompt suggestions and analyzes existing prompts."""
    
    def __init__(self):
        """Initialize Suggestion Agent."""
        super().__init__("suggestion")
        # Initialize Gemini client
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-pro as default (widely available)
            # Can be overridden via GEMINI_MODEL environment variable
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Suggestion Agent initialized with model: {model_name}")
        else:
            logger.warning("GEMINI_API_KEY not configured - Suggestion Agent will not function")
            self.model = None
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a suggestion request.
        
        Args:
            context: Context containing either:
                - "requirements": For generating new prompts from requirements
                - "prompt_text": For analyzing existing prompts and suggesting improvements
                - "prompt_id": For analyzing existing prompts from Supabase
                
        Returns:
            Dictionary with suggestions and analysis
        """
        if not self.model:
            raise RuntimeError("Gemini API not configured")
        
        # Check if this is a prompt analysis request
        if "prompt_text" in context or "prompt_id" in context:
            return await self._analyze_prompt(context)
        
        # Otherwise, generate suggestions from requirements
        if "requirements" in context:
            return await self._generate_from_requirements(context)
        
        raise ValueError("Context must contain either 'requirements', 'prompt_text', or 'prompt_id'")
    
    async def _analyze_prompt(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an existing prompt and suggest improvements.
        
        This addresses Issue #200: AI Agent Integration for Prompt Suggestions.
        """
        # Get prompt text
        prompt_text = context.get("prompt_text")
        if not prompt_text and "prompt_id" in context:
            # Fetch from Supabase
            prompt_id = context["prompt_id"]
            user_id = context.get("user_id")
            if not user_id:
                raise ValueError("user_id required when using prompt_id")
            
            prompt = await supabase_client.get_prompt(prompt_id, user_id)
            if not prompt:
                raise ValueError(f"Prompt {prompt_id} not found")
            
            prompt_text = prompt.get("content", "")
        
        if not prompt_text:
            raise ValueError("prompt_text is required")
        
        # Generate analysis prompt
        analysis_prompt = self._build_analysis_prompt(prompt_text)
        
        # Get Gemini analysis
        response = await self._call_gemini(analysis_prompt)
        
        # Parse response
        suggestions = self._parse_analysis_response(response)
        
        # Save state
        session_id = context.get("session_id", "unknown")
        await self.save_state(session_id, {
            "prompt_text": prompt_text[:100] + "..." if len(prompt_text) > 100 else prompt_text,
            "suggestions": suggestions,
        })
        
        return {
            "success": True,
            "suggestions": suggestions,
            "analysis": {
                "prompt_length": len(prompt_text),
                "has_system_instructions": "system" in prompt_text.lower() or "you are" in prompt_text.lower(),
                "has_examples": "example" in prompt_text.lower(),
                "has_constraints": any(word in prompt_text.lower() for word in ["must", "should", "required", "constraint"]),
            }
        }
    
    async def _generate_from_requirements(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new prompts from user requirements."""
        requirements = context.get("requirements", {})
        
        # Build generation prompt
        generation_prompt = self._build_generation_prompt(requirements)
        
        # Get Gemini suggestions
        response = await self._call_gemini(generation_prompt)
        
        # Parse response
        suggestions = self._parse_generation_response(response)
        
        # Save state
        session_id = context.get("session_id", "unknown")
        await self.save_state(session_id, {
            "requirements": requirements,
            "suggestions": suggestions,
        })
        
        return {
            "success": True,
            "suggestions": suggestions,
        }
    
    def _build_analysis_prompt(self, prompt_text: str) -> str:
        """Build the prompt for analyzing an existing prompt."""
        return f"""You are an expert prompt engineering assistant. Analyze the following prompt and provide structured suggestions for improvement.

PROMPT TO ANALYZE:
{prompt_text}

Please provide a comprehensive analysis with the following sections:

1. **Optimization Suggestions**: Suggest improvements for clarity, specificity, and effectiveness. Include:
   - Missing system instructions
   - Unclear constraints
   - Better example structures
   - Token optimization opportunities

2. **Structured Output Schema**: If the prompt requests structured output, suggest a robust JSON Schema. Include:
   - Required fields
   - Data types
   - Validation rules
   - Nested structures if needed

3. **Function Calling Suggestions**: If the prompt could benefit from function calling, suggest:
   - Function names
   - Function descriptions
   - Parameter schemas
   - Use cases

4. **Overall Assessment**: Provide:
   - Strength score (1-10)
   - Key strengths
   - Key weaknesses
   - Priority improvements

Format your response as JSON with this structure:
{{
  "optimization_suggestions": [
    {{
      "type": "system_instructions|constraints|examples|token_optimization",
      "suggestion": "detailed suggestion",
      "priority": "high|medium|low"
    }}
  ],
  "structured_output": {{
    "recommended": true|false,
    "schema": {{...}} // JSON Schema if recommended
  }},
  "function_calling": {{
    "recommended": true|false,
    "functions": [
      {{
        "name": "function_name",
        "description": "description",
        "parameters": {{...}} // JSON Schema
      }}
    ]
  }},
  "assessment": {{
    "strength_score": 1-10,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "priority_improvements": ["improvement1", "improvement2"]
  }}
}}
"""
    
    def _build_generation_prompt(self, requirements: Dict[str, Any]) -> str:
        """Build the prompt for generating new prompts from requirements."""
        purpose = requirements.get("purpose", "general task")
        target_model = requirements.get("target_model", "gemini-pro")
        constraints = requirements.get("constraints", [])
        examples = requirements.get("examples", [])
        
        return f"""You are an expert prompt engineering assistant. Generate a well-structured prompt based on the following requirements:

PURPOSE: {purpose}
TARGET MODEL: {target_model}
CONSTRAINTS: {', '.join(constraints) if constraints else 'None'}
EXAMPLES TO LEARN FROM: {len(examples)} examples provided

Generate 3 variations of the prompt, each with:
1. Clear system instructions
2. Specific task description
3. Output format requirements
4. Examples (if applicable)
5. Constraints and validation rules

Format your response as JSON:
{{
  "suggestions": [
    {{
      "prompt": "full prompt text",
      "rationale": "why this approach",
      "confidence": 0.0-1.0,
      "features": ["feature1", "feature2"]
    }}
  ]
}}
"""
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API and return response."""
        import asyncio
        try:
            # Run Gemini API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate suggestions: {e}")
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response for analysis."""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini response")
        
        # Fallback: return raw response
        return {
            "raw_response": response_text,
            "parsed": False,
        }
    
    def _parse_generation_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Gemini response for prompt generation."""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data.get("suggestions", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from Gemini response")
        
        # Fallback: return raw response as single suggestion
        return [{
            "prompt": response_text,
            "rationale": "Generated by Gemini",
            "confidence": 0.7,
            "features": [],
        }]

