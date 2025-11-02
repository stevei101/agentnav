"""
Test Health and Agent Status Endpoints (FR#085)

These tests ensure that the ADK system health checks work correctly
and prevent regression of the "ADK System: Offline" bug.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


def test_healthz_endpoint_returns_healthy(client):
    """
    Test that /healthz endpoint returns healthy status
    
    This is the Cloud Run standard health check endpoint.
    If this fails, the frontend will show "ADK System: Offline".
    """
    response = client.get("/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "environment" in data


def test_health_endpoint_returns_healthy_deprecated(client):
    """
    Test that /health endpoint returns healthy status (deprecated)
    
    This endpoint is deprecated but maintained for backward compatibility.
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "environment" in data


def test_agent_status_endpoint_returns_operational(client):
    """
    Test that /api/agents/status endpoint returns operational status
    
    This endpoint is checked by the frontend to determine if ADK system is online.
    Critical test case for FR#085.
    """
    response = client.get("/api/agents/status")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields
    assert "total_agents" in data
    assert "agents" in data
    assert "adk_system" in data
    assert "a2a_protocol" in data
    
    # Verify ADK system is operational
    assert data["adk_system"] == "operational"
    assert data["a2a_protocol"] == "enabled"
    
    # Verify expected number of agents
    assert data["total_agents"] == 4
    
    # Verify all agents are available
    expected_agents = ["orchestrator", "summarizer", "linker", "visualizer"]
    for agent_name in expected_agents:
        assert agent_name in data["agents"]
        agent = data["agents"][agent_name]
        
        assert agent["name"] == agent_name
        assert agent["state"] == "idle"
        assert agent["available"] is True
        assert "execution_history_count" in agent


def test_root_endpoint_returns_api_info(client):
    """
    Test that root endpoint returns API information
    """
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "message" in data
    assert "version" in data
    assert data["message"] == "Agentic Navigator API"


def test_api_docs_endpoint_available(client):
    """
    Test that API documentation endpoint is available
    """
    response = client.get("/api/docs")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "docs_url" in data
    assert data["docs_url"] == "/docs"


def test_import_dependencies_succeed():
    """
    Test that critical dependencies can be imported
    
    This ensures the fix for absolute imports is working.
    """
    # Test that routes can be imported
    from routes.stream_routes import router
    assert router is not None
    
    # Test that services can be imported
    from services.event_emitter import get_event_emitter_manager
    assert get_event_emitter_manager is not None
    
    # Test that agents can be imported
    from agents import (
        OrchestratorAgent,
        SummarizerAgent,
        LinkerAgent,
        VisualizerAgent,
        AgentWorkflow
    )
    assert OrchestratorAgent is not None
    assert SummarizerAgent is not None
    assert LinkerAgent is not None
    assert VisualizerAgent is not None
    assert AgentWorkflow is not None


def test_pydantic_models_work_with_v2():
    """
    Test that Pydantic models work with Pydantic v2
    
    This ensures the fix for regex -> pattern migration is working.
    """
    from models.stream_event_model import WorkflowStreamRequest, ClientCommand
    
    # Test WorkflowStreamRequest with pattern validation
    request = WorkflowStreamRequest(
        document="Test document",
        content_type="document"
    )
    assert request.content_type == "document"
    
    # Test invalid content_type raises validation error
    with pytest.raises(Exception):
        WorkflowStreamRequest(
            document="Test document",
            content_type="invalid_type"  # Should fail pattern validation
        )
    
    # Test ClientCommand with pattern validation
    command = ClientCommand(action="cancel")
    assert command.action == "cancel"
    
    # Test invalid action raises validation error
    with pytest.raises(Exception):
        ClientCommand(action="invalid_action")  # Should fail pattern validation


@pytest.mark.asyncio
async def test_agent_workflow_can_be_created():
    """
    Test that AgentWorkflow can be instantiated
    
    This is a smoke test to ensure the ADK system is properly initialized.
    """
    from agents import AgentWorkflow, A2AProtocol
    
    # Test with legacy A2A Protocol
    workflow = AgentWorkflow(use_enhanced_a2a=False)
    assert workflow is not None
    assert isinstance(workflow.a2a, A2AProtocol)
    
    # Test that workflow can check status
    status = workflow.get_workflow_status()
    assert "agents" in status
    assert "dependencies" in status
    assert "shared_context_keys" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
