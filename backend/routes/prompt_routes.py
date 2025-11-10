"""Routes dedicated to Prompt Vault integrations."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.services.workload_identity_auth import verify_workload_identity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prompt-assistant", tags=["prompt-vault"])


class SuggestionRequest(BaseModel):
    prompt: str
    goal: Optional[str] = None
    max_suggestions: int = 3


class SuggestionResponse(BaseModel):
    suggestions: List[str]
    metadata: Dict[str, str]


@router.post("/suggest", response_model=SuggestionResponse)
async def suggest_prompt(
    payload: SuggestionRequest,
    auth_info: Dict = Depends(verify_workload_identity),
):
    """Generate improved prompt suggestions for Prompt Vault users."""

    if not payload.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt text cannot be empty",
        )

    try:
        from backend.services.gemini_client import reason_with_gemini
    except ImportError as exc:
        logger.error("Gemini client unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prompt suggestion service unavailable",
        ) from exc

    base_prompt = (
        "You are an expert prompt engineer. Rewrite the provided prompt to make it"
        " clearer, more concise, and more likely to generate high-quality model"
        " output. Provide {count} improved variations as a markdown bullet list."
    )

    if payload.goal:
        base_prompt += (
            " The improved prompts should focus on the following goal:"
            f" {payload.goal.strip()}"
        )

    llm_prompt = base_prompt.format(count=payload.max_suggestions)
    llm_prompt += f"\n\nOriginal prompt:\n{payload.prompt.strip()}\n"

    suggestions_text = await reason_with_gemini(
        prompt=llm_prompt,
        max_tokens=512,
        temperature=0.2,
    )

    suggestions = [
        item.strip(" -") for item in suggestions_text.splitlines() if item.strip()
    ]

    if not suggestions:
        suggestions = [payload.prompt.strip()]

    logger.info(
        "Generated %s prompt suggestions for %s",
        len(suggestions),
        auth_info.get("email", "unknown-caller"),
    )

    return SuggestionResponse(
        suggestions=suggestions[: payload.max_suggestions],
        metadata={
            "requested_by": auth_info.get("email") or "anonymous",
            "authenticated": str(auth_info.get("authenticated", False)).lower(),
        },
    )
