"""
Models package for Agentic Navigator
Pydantic models for data validation and serialization
"""

from .a2a_messages import (
    A2AMessageBase,
    A2AMessagePriority,
    A2AMessageStatus,
    A2ASecurityContext,
    A2ATraceContext,
    AgentStatusMessage,
    KnowledgeTransferMessage,
    RelationshipMappedMessage,
    SummarizationCompletedMessage,
    TaskDelegationMessage,
    VisualizationReadyMessage,
    create_correlation_id,
    create_message_id,
)
from .context_model import EntityRelationship, SessionContext
from .prompt_models import (
    Prompt,
    PromptCreate,
    PromptUpdate,
    PromptVersion,
    TestResult,
    TestResultCreate,
    UserInfo,
)

__all__ = [
    # Context models
    "SessionContext",
    "EntityRelationship",
    # A2A Protocol messages (FR#027)
    "A2AMessageBase",
    "A2AMessagePriority",
    "A2AMessageStatus",
    "A2ASecurityContext",
    "A2ATraceContext",
    "TaskDelegationMessage",
    "SummarizationCompletedMessage",
    "RelationshipMappedMessage",
    "VisualizationReadyMessage",
    "KnowledgeTransferMessage",
    "AgentStatusMessage",
    "create_message_id",
    "create_correlation_id",
    # Prompt management models
    "Prompt",
    "PromptCreate",
    "PromptUpdate",
    "PromptVersion",
    "TestResult",
    "TestResultCreate",
    "UserInfo",
]
