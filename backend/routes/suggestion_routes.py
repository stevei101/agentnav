"""
Suggestion Routes for Prompt Vault Intelligence (FR#201)

API endpoints for AI-driven prompt analysis and suggestions.
Integrates Suggestion Agent with Prompt Vault application via ADK/A2A Protocol.
"""

import logging
import time
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.models.suggestion_models import (
    PromptSuggestionRequest,
    PromptSuggestionResponse,
    StructuredOutputSchema,
    FunctionCallingHint,
    PromptSuggestionError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/suggestions", tags=["suggestions"])


@router.post(
    "/analyze",
    response_model=PromptSuggestionResponse,
    summary="Analyze prompt and provide suggestions",
    description="""
    Analyze a raw prompt text and provide AI-driven suggestions for improvement.
    
    This endpoint uses the Suggestion Agent (ADK/A2A Protocol) to:
    - Suggest prompt optimizations for clarity and effectiveness
    - Generate structured output JSON schemas (if applicable)
    - Recommend function calling definitions (if applicable)
    - Provide quality scoring and actionable improvements
    
    Feature Request: FR#201 - Prompt Vault Intelligence
    """,
)
async def analyze_prompt(request: PromptSuggestionRequest) -> PromptSuggestionResponse:
    """
    Analyze prompt and provide AI-driven suggestions
    
    Args:
        request: PromptSuggestionRequest containing prompt_text and optional context
    
    Returns:
        PromptSuggestionResponse with optimization suggestions, schemas, and quality metrics
    
    Raises:
        HTTPException: If agent system is unavailable or analysis fails
    """
    start_time = time.time()
    
    try:
        from backend.agents import SuggestionAgent, A2AProtocol
        
        logger.info(f"📝 Analyzing prompt: {request.prompt_text[:50]}...")
        
        # Create A2A Protocol instance for agent communication
        a2a = A2AProtocol()
        
        # Initialize Suggestion Agent
        suggestion_agent = SuggestionAgent(a2a)
        
        # Prepare context for agent execution
        context = {
            "prompt_text": request.prompt_text,
            "user_context": request.user_context or "",
            "existing_schema": request.existing_schema,
        }
        
        # Execute agent analysis
        result = await suggestion_agent.execute(context)
        
        # Convert result to response model
        response = _convert_to_response_model(result)
        
        processing_time = time.time() - start_time
        logger.info(
            f"✅ Prompt analysis completed in {processing_time:.2f}s "
            f"(quality score: {response.quality_score}/10)"
        )
        
        return response
    
    except ImportError as e:
        logger.error(f"❌ Suggestion Agent not available: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "ServiceUnavailable",
                "message": "Suggestion Agent system not available",
                "details": {"import_error": str(e)},
            },
        )
    
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": str(e),
                "details": {"field": "prompt_text"},
            },
        )
    
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Prompt analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AnalysisError",
                "message": f"Prompt analysis failed after {processing_time:.2f}s",
                "details": {"error": str(e)},
            },
        )


def _convert_to_response_model(result: Dict[str, Any]) -> PromptSuggestionResponse:
    """
    Convert agent result to PromptSuggestionResponse model
    
    Args:
        result: Raw result dictionary from Suggestion Agent
    
    Returns:
        PromptSuggestionResponse with properly structured data
    """
    # Extract structured output schema if present
    structured_schema = None
    if result.get("structured_output_schema"):
        schema_data = result["structured_output_schema"]
        if isinstance(schema_data, dict):
            structured_schema = StructuredOutputSchema(**schema_data)
    
    # Extract function calling hint if present
    function_hint = None
    if result.get("function_calling_hint"):
        hint_data = result["function_calling_hint"]
        if isinstance(hint_data, dict):
            function_hint = FunctionCallingHint(**hint_data)
    
    # Build response
    return PromptSuggestionResponse(
        agent=result.get("agent", "suggestion"),
        prompt_analyzed=result.get("prompt_analyzed", ""),
        optimization_suggestions=result.get("optimization_suggestions", []),
        structured_output_schema=structured_schema,
        function_calling_hint=function_hint,
        quality_score=result.get("quality_score", 5),
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        actionable_improvements=result.get("actionable_improvements", []),
        processing_complete=result.get("processing_complete", True),
        timestamp=result.get("timestamp", time.time()),
    )


@router.get(
    "/health",
    summary="Check Suggestion Agent health",
    description="Check if the Suggestion Agent is available and operational",
)
async def check_suggestion_agent_health() -> Dict[str, Any]:
    """
    Check Suggestion Agent health and availability
    
    Returns:
        Dictionary with agent status and availability information
    """
    try:
        from backend.agents import SuggestionAgent, A2AProtocol
        
        # Test agent instantiation
        a2a = A2AProtocol()
        agent = SuggestionAgent(a2a)
        
        if agent and hasattr(agent, "name"):
            return {
                "status": "healthy",
                "agent": "suggestion",
                "available": True,
                "state": agent.state.value,
                "message": "Suggestion Agent is operational",
            }
        else:
            return {
                "status": "degraded",
                "agent": "suggestion",
                "available": False,
                "message": "Suggestion Agent instantiation incomplete",
            }
    
    except ImportError as e:
        logger.error(f"❌ Suggestion Agent import failed: {e}")
        return {
            "status": "unavailable",
            "agent": "suggestion",
            "available": False,
            "error": "ImportError",
            "message": f"Suggestion Agent not available: {str(e)}",
        }
    
    except Exception as e:
        logger.error(f"❌ Suggestion Agent health check failed: {e}")
        return {
            "status": "error",
            "agent": "suggestion",
            "available": False,
            "error": type(e).__name__,
            "message": str(e),
        }


@router.get(
    "/examples",
    summary="Get example prompts for testing",
    description="Get example prompts that can be used to test the suggestion API",
)
async def get_example_prompts() -> Dict[str, Any]:
    """
    Get example prompts for testing the suggestion API
    
    Returns:
        Dictionary with example prompts for different use cases
    """
    return {
        "examples": [
            {
                "name": "Simple Task",
                "prompt_text": "Write a function that calculates the factorial of a number",
                "user_context": "Educational coding tutorial",
                "expected_suggestions": [
                    "Specify programming language",
                    "Add input validation requirements",
                    "Include error handling expectations",
                ],
            },
            {
                "name": "Data Analysis",
                "prompt_text": "Analyze the sales data and provide insights",
                "user_context": "Business intelligence dashboard",
                "expected_suggestions": [
                    "Specify data format and structure",
                    "Define what types of insights are needed",
                    "Add output format requirements",
                ],
            },
            {
                "name": "Creative Writing",
                "prompt_text": "Write a short story about a robot",
                "user_context": "Creative writing exercise",
                "expected_suggestions": [
                    "Specify story length and style",
                    "Add character and setting details",
                    "Define target audience",
                ],
            },
            {
                "name": "Code Review",
                "prompt_text": "Review this code and suggest improvements",
                "user_context": "Code quality improvement",
                "expected_suggestions": [
                    "Specify review criteria (performance, security, readability)",
                    "Add context about the codebase",
                    "Define output format for suggestions",
                ],
            },
        ],
        "usage_tips": [
            "Provide context about the intended use case",
            "Be specific about expected output format",
            "Include constraints and requirements",
            "Add examples when possible",
        ],
    }
