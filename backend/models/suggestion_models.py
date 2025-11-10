"""
Pydantic Models for Suggestion Agent API (FR#201)

Request and response models for the Prompt Vault Intelligence feature.
Provides structured validation for prompt analysis requests and suggestions.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PromptSuggestionRequest(BaseModel):
    """
    Request model for prompt suggestion analysis
    
    Used by Prompt Vault application to request AI-driven suggestions
    for prompt improvement.
    """
    
    prompt_text: str = Field(
        ...,
        description="The raw prompt text to analyze",
        min_length=1,
        max_length=10000,
    )
    
    user_context: Optional[str] = Field(
        None,
        description="Optional context about the intended use case for the prompt",
        max_length=1000,
    )
    
    existing_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional existing structured output schema to refine",
    )
    
    @field_validator("prompt_text")
    @classmethod
    def validate_prompt_text(cls, v: str) -> str:
        """Ensure prompt text is not empty or just whitespace"""
        if not v or not v.strip():
            raise ValueError("Prompt text cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_text": "Write a function that calculates the factorial of a number",
                "user_context": "Educational coding tutorial for beginners",
                "existing_schema": None,
            }
        }


class StructuredOutputSchema(BaseModel):
    """
    Structured output schema suggestion
    
    Represents a JSON schema for structured output generation,
    compatible with Gemini's structured output format.
    """
    
    type: str = Field(
        default="object",
        description="JSON schema type (typically 'object')",
    )
    
    properties: Optional[Dict[str, Any]] = Field(
        None,
        description="Schema properties defining the structure",
    )
    
    required: Optional[List[str]] = Field(
        None,
        description="List of required property names",
    )
    
    description: Optional[str] = Field(
        None,
        description="Human-readable description of the schema",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "object",
                "properties": {
                    "result": {"type": "number", "description": "The factorial result"},
                    "steps": {"type": "array", "description": "Calculation steps"},
                },
                "required": ["result"],
                "description": "Factorial calculation result",
            }
        }


class FunctionCallingHint(BaseModel):
    """
    Function calling suggestion
    
    Represents a function definition that could be used with
    Gemini's function calling capabilities.
    """
    
    name: Optional[str] = Field(
        None,
        description="Suggested function name",
    )
    
    description: Optional[str] = Field(
        None,
        description="Description of what the function does",
    )
    
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Function parameters schema",
    )
    
    rationale: Optional[str] = Field(
        None,
        description="Explanation of why function calling would be beneficial",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "calculate_factorial",
                "description": "Calculates the factorial of a given number",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "n": {"type": "integer", "description": "The number to calculate factorial for"}
                    },
                    "required": ["n"],
                },
                "rationale": "Function calling would allow the model to delegate actual calculation to a tool",
            }
        }


class PromptSuggestionResponse(BaseModel):
    """
    Response model for prompt suggestion analysis
    
    Contains AI-generated suggestions for prompt improvement,
    structured output schemas, and function calling hints.
    """
    
    agent: str = Field(
        default="suggestion",
        description="Agent that generated the suggestions",
    )
    
    prompt_analyzed: str = Field(
        ...,
        description="Preview of the analyzed prompt (truncated)",
    )
    
    optimization_suggestions: List[str] = Field(
        default_factory=list,
        description="List of specific suggestions for improving the prompt",
    )
    
    structured_output_schema: Optional[StructuredOutputSchema] = Field(
        None,
        description="Suggested JSON schema for structured output (if applicable)",
    )
    
    function_calling_hint: Optional[FunctionCallingHint] = Field(
        None,
        description="Suggested function calling definition (if applicable)",
    )
    
    quality_score: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Prompt quality rating (1-10)",
    )
    
    strengths: List[str] = Field(
        default_factory=list,
        description="Identified strengths of the prompt",
    )
    
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Identified weaknesses of the prompt",
    )
    
    actionable_improvements: List[str] = Field(
        default_factory=list,
        description="Specific actionable improvements",
    )
    
    processing_complete: bool = Field(
        default=True,
        description="Whether the analysis completed successfully",
    )
    
    timestamp: float = Field(
        ...,
        description="Unix timestamp of when the analysis was completed",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent": "suggestion",
                "prompt_analyzed": "Write a function that calculates the factorial...",
                "optimization_suggestions": [
                    "Add input validation requirements",
                    "Specify the programming language",
                    "Include error handling expectations",
                ],
                "structured_output_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "The function code"},
                        "explanation": {"type": "string", "description": "Explanation of the code"},
                    },
                    "required": ["code"],
                },
                "function_calling_hint": None,
                "quality_score": 6,
                "strengths": ["Clear task definition", "Concise"],
                "weaknesses": ["Lacks context", "No output format specified"],
                "actionable_improvements": [
                    "Specify the programming language (e.g., Python, JavaScript)",
                    "Add examples of expected input and output",
                ],
                "processing_complete": True,
                "timestamp": 1699999999.0,
            }
        }


class PromptSuggestionError(BaseModel):
    """
    Error response model for suggestion API
    """
    
    error: str = Field(
        ...,
        description="Error type or code",
    )
    
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Prompt text cannot be empty",
                "details": {"field": "prompt_text"},
            }
        }
