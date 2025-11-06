"""
Prompt Management Data Models
Pydantic models for prompt management API
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Test result model for prompt validation"""

    id: str
    result: str = Field(
        ..., description="Test result: 'success', 'failure', or 'warning'"
    )
    notes: str = Field(default="", description="Test notes")
    model: str = Field(default="gemini-pro", description="Model used for testing")
    createdAt: str = Field(..., description="ISO timestamp")
    userId: str = Field(..., description="User ID who created the test")
    userName: str = Field(..., description="User name who created the test")


class PromptVersion(BaseModel):
    """Version history model for prompts"""

    id: str
    promptId: str
    version: int
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    createdAt: str = Field(..., description="ISO timestamp")
    userId: str = Field(..., description="User ID who created this version")
    userName: str = Field(..., description="User name who created this version")


class Prompt(BaseModel):
    """Prompt model"""

    id: str
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    createdAt: str = Field(..., description="ISO timestamp")
    updatedAt: str = Field(..., description="ISO timestamp")
    userId: str = Field(..., description="User ID who created the prompt")
    userName: str = Field(..., description="User name who created the prompt")
    version: int = Field(default=1, description="Current version number")
    lastEditedBy: Optional[str] = Field(
        default=None, description="Last user who edited"
    )
    testResults: List[TestResult] = Field(
        default_factory=list, description="Test results"
    )


class PromptCreate(BaseModel):
    """Request model for creating a prompt"""

    title: Optional[str] = Field(default="Untitled Prompt")
    content: Optional[str] = Field(default="")
    tags: Optional[List[str]] = Field(default_factory=list)


class PromptUpdate(BaseModel):
    """Request model for updating a prompt"""

    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class TestResultCreate(BaseModel):
    """Request model for adding a test result"""

    result: str = Field(
        ..., description="Test result: 'success', 'failure', or 'warning'"
    )
    notes: str = Field(default="")
    model: str = Field(default="gemini-pro")


class UserInfo(BaseModel):
    """User information model"""

    id: str
    email: str
    name: str
    avatar: Optional[str] = None
