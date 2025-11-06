"""
Prompt Management API Routes (Feature Request #335 - WI Secured)
FastAPI routes for prompt CRUD operations with Workload Identity authentication
"""
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Depends
from models.prompt_models import (
    Prompt, PromptCreate, PromptUpdate, PromptVersion, 
    TestResultCreate, UserInfo
)
from services.prompt_service import get_prompt_service
from services.workload_identity_auth import verify_workload_identity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


async def get_user_from_wi_token(
    auth_info: Dict[str, Any] = Depends(verify_workload_identity)
) -> UserInfo:
    """
    Extract user info from Workload Identity token (Feature Request #335)
    
    In production with WI enabled, this uses the service account email as the user ID.
    In development mode, this returns a default user.
    
    Args:
        auth_info: Authenticated identity from WI token (injected by FastAPI)
        
    Returns:
        UserInfo with service account details
    """
    # Extract service account email from WI token
    email = auth_info.get("email", "unknown@unknown.iam.gserviceaccount.com")
    
    # Use service account email as user ID
    # Format: "service-account-name@project.iam.gserviceaccount.com"
    # Extract service account name for display
    name = email.split("@")[0] if "@" in email else email
    
    return UserInfo(
        id=email,
        email=email,
        name=name
    )


@router.get("/", response_model=List[Prompt])
async def list_prompts(
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    List all prompts (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    """
    try:
        service = get_prompt_service()
        prompts = service.list_prompts(user_id=user.id)
        return prompts
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/{prompt_id}", response_model=Prompt)
async def get_prompt(
    prompt_id: str,
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    Get a prompt by ID (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    """
    try:
        service = get_prompt_service()
        prompt = service.get_prompt(prompt_id)
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("/", response_model=Prompt, status_code=201)
async def create_prompt(
    prompt_data: PromptCreate,
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    Create a new prompt (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    """
    try:
        service = get_prompt_service()
        prompt = service.create_prompt(
            prompt_data.dict(),
            user_id=user.id,
            user_name=user.name
        )
        return prompt
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create prompt: {str(e)}")


@router.put("/{prompt_id}", response_model=Prompt)
async def update_prompt(
    prompt_id: str,
    prompt_data: PromptUpdate,
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    Update a prompt (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    """
    try:
        service = get_prompt_service()
        
        # Only include fields that were provided
        updates = {k: v for k, v in prompt_data.dict().items() if v is not None}
        
        if not updates:
            # Return existing prompt if no updates
            prompt = service.get_prompt(prompt_id)
            if not prompt:
                raise HTTPException(status_code=404, detail="Prompt not found")
            return prompt
        
        prompt = service.update_prompt(
            prompt_id,
            updates,
            user_id=user.id,
            user_name=user.name
        )
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update prompt: {str(e)}")


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: str,
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    Delete a prompt (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    """
    try:
        service = get_prompt_service()
        success = service.delete_prompt(prompt_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete prompt: {str(e)}")


@router.get("/{prompt_id}/versions", response_model=List[PromptVersion])
async def get_versions(
    prompt_id: str,
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    Get version history for a prompt (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    """
    try:
        service = get_prompt_service()
        versions = service.get_versions(prompt_id)
        return versions
    except Exception as e:
        logger.error(f"Error getting versions for prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.post("/{prompt_id}/tests", response_model=Prompt)
async def add_test_result(
    prompt_id: str,
    test_data: TestResultCreate,
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    Add a test result to a prompt (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    """
    try:
        service = get_prompt_service()
        prompt = service.add_test_result(
            prompt_id,
            test_data.dict(),
            user_id=user.id,
            user_name=user.name
        )
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding test result to prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add test result: {str(e)}")


@router.get("/user/info", response_model=UserInfo)
async def get_user_info(
    user: UserInfo = Depends(get_user_from_wi_token)
):
    """
    Get current user information (WI Authenticated - FR#335)
    
    Requires valid Workload Identity ID token from authorized service account.
    Returns the authenticated service account information.
    """
    return user

