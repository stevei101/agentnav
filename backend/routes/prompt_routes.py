"""
Prompt Management API Routes
FastAPI routes for prompt CRUD operations
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Depends
from models.prompt_models import (
    Prompt, PromptCreate, PromptUpdate, PromptVersion, 
    TestResultCreate, UserInfo
)
from services.prompt_service import get_prompt_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


async def get_user_from_header(
    authorization: Optional[str] = Header(None)
) -> Optional[UserInfo]:
    """
    Extract user info from authorization header
    
    For now, we'll use a simple approach:
    - In production, this would verify JWT tokens
    - For fast-track, we accept user info in a custom header or JWT payload
    - TODO: Implement proper Google OAuth verification
    
    For now, we'll use a simple user_id header for development
    """
    # TODO: Implement proper authentication
    # For now, accept user info from headers or use default
    # In production, verify JWT token from Google OAuth
    
    # Temporary: Use default user for development
    # In production, decode JWT from Authorization header
    return UserInfo(
        id=authorization or "default-user",
        email="user@example.com",
        name="User"
    )


@router.get("/", response_model=List[Prompt])
async def list_prompts(
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """List all prompts"""
    try:
        service = get_prompt_service()
        prompts = service.list_prompts(user_id=user.id if user else None)
        return prompts
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/{prompt_id}", response_model=Prompt)
async def get_prompt(
    prompt_id: str,
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """Get a prompt by ID"""
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
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """Create a new prompt"""
    try:
        service = get_prompt_service()
        prompt = service.create_prompt(
            prompt_data.dict(),
            user_id=user.id if user else "anonymous",
            user_name=user.name if user else "Anonymous"
        )
        return prompt
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create prompt: {str(e)}")


@router.put("/{prompt_id}", response_model=Prompt)
async def update_prompt(
    prompt_id: str,
    prompt_data: PromptUpdate,
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """Update a prompt"""
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
            user_id=user.id if user else "anonymous",
            user_name=user.name if user else "Anonymous"
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
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """Delete a prompt"""
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
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """Get version history for a prompt"""
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
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """Add a test result to a prompt"""
    try:
        service = get_prompt_service()
        prompt = service.add_test_result(
            prompt_id,
            test_data.dict(),
            user_id=user.id if user else "anonymous",
            user_name=user.name if user else "Anonymous"
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
    user: Optional[UserInfo] = Depends(get_user_from_header)
):
    """Get current user information"""
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

