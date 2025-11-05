"""Agent workflow API endpoints."""
import logging
from fastapi import APIRouter, HTTPException, Depends
from uuid import uuid4
from typing import Optional, Dict, Any

from app.models.workflows import (
    OptimizeRequest,
    TestRequest,
    CompareRequest,
    SuggestRequest,
    WorkflowResponse,
    WorkflowStatusResponse,
)
from app.agents.orchestrator import OrchestratorAgent, WorkflowType
from app.agents.suggestion import SuggestionAgent
from app.services.firestore_client import firestore_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize agents
orchestrator = OrchestratorAgent()
suggestion_agent = SuggestionAgent()  # Initialize Suggestion Agent


@router.post("/optimize", response_model=WorkflowResponse)
async def optimize_prompt(request: OptimizeRequest):
    """
    Optimize a prompt using Analyzer + Optimizer agents.
    
    This endpoint triggers the optimization workflow:
    1. Analyzer Agent analyzes the prompt
    2. Optimizer Agent generates optimized version(s)
    3. (Optional) Tester Agent tests the optimized prompt
    """
    try:
        session_id = str(uuid4())
        workflow_id = str(uuid4())
        
        result = await orchestrator.process({
            "workflow_type": WorkflowType.OPTIMIZE,
            "prompt_id": request.prompt_id,
            "options": request.options,
            "session_id": session_id,
            "workflow_id": workflow_id,
        })
        
        return WorkflowResponse(
            success=result["success"],
            workflow_id=result["workflow_id"],
            workflow_type=result["workflow_type"],
            result=result["result"],
        )
    except Exception as e:
        logger.error(f"Error in optimize workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test", response_model=WorkflowResponse)
async def test_prompt(request: TestRequest):
    """
    Test a prompt using Tester Agent.
    
    This endpoint triggers the testing workflow:
    1. Tester Agent generates test scenarios
    2. Executes prompts against Gemini API
    3. Evaluates outputs and generates test report
    """
    try:
        session_id = str(uuid4())
        workflow_id = str(uuid4())
        
        result = await orchestrator.process({
            "workflow_type": WorkflowType.TEST,
            "prompt_id": request.prompt_id,
            "scenarios": request.scenarios,
            "options": request.options,
            "session_id": session_id,
            "workflow_id": workflow_id,
        })
        
        return WorkflowResponse(
            success=result["success"],
            workflow_id=result["workflow_id"],
            workflow_type=result["workflow_type"],
            result=result["result"],
        )
    except Exception as e:
        logger.error(f"Error in test workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=WorkflowResponse)
async def compare_versions(request: CompareRequest):
    """
    Compare prompt versions using Comparator Agent.
    
    This endpoint triggers the comparison workflow:
    1. Comparator Agent loads versions from Supabase
    2. Compares structural differences and test results
    3. Generates comparison report with recommendations
    """
    try:
        session_id = str(uuid4())
        workflow_id = str(uuid4())
        
        result = await orchestrator.process({
            "workflow_type": WorkflowType.COMPARE,
            "prompt_id": request.prompt_id,
            "version_ids": request.version_ids,
            "session_id": session_id,
            "workflow_id": workflow_id,
        })
        
        return WorkflowResponse(
            success=result["success"],
            workflow_id=result["workflow_id"],
            workflow_type=result["workflow_type"],
            result=result["result"],
        )
    except Exception as e:
        logger.error(f"Error in compare workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest", response_model=WorkflowResponse)
async def suggest_prompt(request: SuggestRequest):
    """
    Generate prompt suggestions using Suggestion Agent.
    
    This endpoint triggers the suggestion workflow:
    1. Suggestion Agent learns patterns from user's existing prompts
    2. Generates suggestions using Gemini API
    3. Returns multiple suggestions with rationale
    """
    try:
        session_id = str(uuid4())
        workflow_id = str(uuid4())
        
        result = await orchestrator.process({
            "workflow_type": WorkflowType.SUGGEST,
            "requirements": request.requirements,
            "options": request.options,
            "session_id": session_id,
            "workflow_id": workflow_id,
        })
        
        return WorkflowResponse(
            success=result["success"],
            workflow_id=result["workflow_id"],
            workflow_type=result["workflow_type"],
            result=result["result"],
        )
    except Exception as e:
        logger.error(f"Error in suggest workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=WorkflowResponse)
async def analyze_prompt(request: Dict[str, Any]):
    """
    Analyze an existing prompt and get suggestions for improvements.
    
    This endpoint addresses Issue #200: AI Agent Integration for Prompt Suggestions.
    It analyzes a prompt and provides:
    - Optimization suggestions
    - Structured output schema recommendations
    - Function calling suggestions
    - Overall assessment
    """
    try:
        prompt_text = request.get("prompt_text")
        prompt_id = request.get("prompt_id")
        user_id = request.get("user_id")
        
        if not prompt_text and not prompt_id:
            raise HTTPException(status_code=400, detail="Either 'prompt_text' or 'prompt_id' is required")
        
        if prompt_id and not user_id:
            raise HTTPException(status_code=400, detail="'user_id' is required when using 'prompt_id'")
        
        # Call Suggestion Agent directly for analysis
        context = {
            "prompt_text": prompt_text,
            "prompt_id": prompt_id,
            "user_id": user_id,
            "session_id": str(uuid4()),
        }
        
        result = await suggestion_agent.process(context)
        
        return WorkflowResponse(
            success=result.get("success", True),
            workflow_id=str(uuid4()),
            workflow_type="analyze",
            result=result,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """
    Get workflow status and results.
    
    Retrieves the current status of a workflow execution from Firestore.
    """
    try:
        # Check if Firestore is available
        if not firestore_client.is_available():
            raise HTTPException(status_code=404, detail="Workflow not found (Firestore not configured)")
        
        context = await firestore_client.get_workflow_context(workflow_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            workflow_type=context.get("workflow_type", "unknown"),
            status=context.get("status", "unknown"),
            result=context.get("result"),
            error=context.get("error"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflow status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

