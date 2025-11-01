"""
SessionContext Model - Shared Context for Multi-Agent Workflow
Implements the shared session context as specified in FR#005
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import time


class EntityRelationship(BaseModel):
    """
    Relationship between two entities
    Used by Linker Agent to store relationship data
    """
    source: str = Field(..., description="Source entity ID or label")
    target: str = Field(..., description="Target entity ID or label")
    type: str = Field(..., description="Type of relationship (e.g., 'relates_to', 'inherits', 'calls')")
    label: Optional[str] = Field(None, description="Human-readable label for the relationship")
    confidence: Optional[str] = Field(None, description="Confidence level (high, medium, low)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "ClassA",
                "target": "ClassB",
                "type": "inherits",
                "label": "inherits from",
                "confidence": "high"
            }
        }


class SessionContext(BaseModel):
    """
    Shared Session Context for Multi-Agent Workflow
    
    This model represents the complete state of an analysis session
    and is passed between agents via the A2A Protocol. Each agent
    updates specific fields based on its role.
    
    As specified in FR#005:
    - raw_input: Original document/codebase (input)
    - summary_text: Output from Summarizer Agent
    - key_entities: Output from Linker Agent (list of entity names/IDs)
    - relationships: Output from Linker Agent (list of EntityRelationship)
    - graph_json: Final visualization-ready output from Visualizer Agent
    """
    
    # Session metadata
    session_id: str = Field(..., description="Unique session identifier")
    content_type: str = Field(default="document", description="Type of content: 'document' or 'codebase'")
    timestamp: float = Field(default_factory=time.time, description="Session creation timestamp")
    
    # Input data
    raw_input: str = Field(..., description="Original document or codebase content")
    
    # Summarizer Agent outputs
    summary_text: Optional[str] = Field(None, description="Comprehensive summary from Summarizer Agent")
    summary_insights: Optional[Dict[str, Any]] = Field(None, description="Additional insights from summarization")
    
    # Linker Agent outputs
    key_entities: List[str] = Field(default_factory=list, description="List of key entities identified by Linker Agent")
    relationships: List[EntityRelationship] = Field(
        default_factory=list,
        description="Relationships between entities identified by Linker Agent"
    )
    entity_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about entities")
    
    # Visualizer Agent outputs
    graph_json: Optional[Dict[str, Any]] = Field(None, description="Final visualization-ready graph from Visualizer Agent")
    
    # Workflow tracking
    completed_agents: List[str] = Field(default_factory=list, description="List of agents that have completed processing")
    current_agent: Optional[str] = Field(None, description="Currently processing agent")
    workflow_status: str = Field(default="initializing", description="Current workflow status")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="List of errors encountered during workflow")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_12345",
                "content_type": "document",
                "raw_input": "Machine learning is a subset of artificial intelligence...",
                "summary_text": "This document discusses machine learning fundamentals...",
                "key_entities": ["Machine Learning", "Neural Networks", "Deep Learning"],
                "relationships": [
                    {
                        "source": "Deep Learning",
                        "target": "Machine Learning",
                        "type": "subset_of",
                        "label": "is a subset of"
                    }
                ],
                "graph_json": {
                    "type": "MIND_MAP",
                    "nodes": [{"id": "ml", "label": "Machine Learning"}],
                    "edges": []
                },
                "completed_agents": ["orchestrator", "summarizer", "linker", "visualizer"],
                "workflow_status": "completed"
            }
        }
    
    def mark_agent_complete(self, agent_name: str):
        """Mark an agent as completed in the workflow"""
        if agent_name not in self.completed_agents:
            self.completed_agents.append(agent_name)
    
    def set_current_agent(self, agent_name: str):
        """Set the currently processing agent"""
        self.current_agent = agent_name
    
    def add_error(self, agent_name: str, error_message: str):
        """Record an error from an agent"""
        self.errors.append({
            "agent": agent_name,
            "error": error_message,
            "timestamp": time.time()
        })
    
    def is_complete(self) -> bool:
        """Check if all required agents have completed"""
        required_agents = ["orchestrator", "summarizer", "linker", "visualizer"]
        return all(agent in self.completed_agents for agent in required_agents)
    
    def to_firestore_dict(self) -> Dict[str, Any]:
        """
        Convert to Firestore-compatible dictionary
        Handles nested Pydantic models and timestamps
        """
        data = self.model_dump()
        
        # Convert EntityRelationship objects to dicts
        if self.relationships:
            data["relationships"] = [
                rel.model_dump() if isinstance(rel, EntityRelationship) else rel
                for rel in self.relationships
            ]
        
        return data
    
    @classmethod
    def from_firestore_dict(cls, data: Dict[str, Any]) -> "SessionContext":
        """
        Create SessionContext from Firestore document data
        Handles conversion of nested dictionaries to Pydantic models
        """
        # Convert relationship dicts to EntityRelationship objects
        if "relationships" in data and data["relationships"]:
            data["relationships"] = [
                EntityRelationship(**rel) if isinstance(rel, dict) else rel
                for rel in data["relationships"]
            ]
        
        return cls(**data)
