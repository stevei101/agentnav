"""Workflow request and response models."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import UUID


class OptimizeRequest(BaseModel):
    """Request model for prompt optimization workflow."""
    prompt_id: str = Field(..., description="Prompt ID to optimize")
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optimization options (e.g., test_optimized, generate_variants)"
    )


class TestRequest(BaseModel):
    """Request model for prompt testing workflow."""
    prompt_id: str = Field(..., description="Prompt ID to test")
    scenarios: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Test scenarios (optional, will be generated if not provided)"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Test options (e.g., model, temperature)"
    )


class CompareRequest(BaseModel):
    """Request model for version comparison workflow."""
    prompt_id: str = Field(..., description="Prompt ID")
    version_ids: List[str] = Field(..., description="Version IDs to compare")


class SuggestRequest(BaseModel):
    """Request model for prompt suggestion workflow."""
    requirements: Dict[str, Any] = Field(
        ...,
        description="Prompt requirements (purpose, target_model, constraints, etc.)"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Suggestion options (e.g., num_suggestions, learn_from_my_prompts)"
    )


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""
    success: bool
    workflow_id: str
    workflow_type: str
    result: Dict[str, Any]
    message: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status check."""
    workflow_id: str
    workflow_type: str
    status: str  # in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

