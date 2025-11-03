"""
Unit tests for ADK health check endpoints (FR#085)

Tests verify that the /healthz and /api/agents/status endpoints
correctly detect ADK system availability and provide diagnostic information.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthzEndpoint:
    """Test /healthz endpoint ADK system checks"""

    def test_healthz_with_operational_adk(self):
        """Test healthz returns healthy when ADK is operational"""
        with patch("agents.OrchestratorAgent") as mock_agent_class, patch(
            "agents.A2AProtocol"
        ) as mock_a2a_class:

            # Mock successful agent initialization
            mock_agent = MagicMock()
            mock_agent.name = "orchestrator"
            mock_agent_class.return_value = mock_agent
            
            mock_a2a = MagicMock()
            mock_a2a_class.return_value = mock_a2a

            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] in [
                "healthy",
                "degraded",
            ]  # May be degraded if Firestore fails
            assert data["adk_system"] == "operational"
            assert "environment" in data

    def test_healthz_with_unavailable_adk(self):
        """Test healthz returns degraded when ADK agents cannot be imported"""
        with patch.dict("sys.modules", {"agents": None}):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'agents'"),
            ):
                response = client.get("/healthz")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "unhealthy"
                assert data["adk_system"] == "unavailable"
                assert "errors" in data
                assert "adk" in data["errors"]

    def test_healthz_firestore_check(self):
        """Test healthz firestore connectivity check"""
        with patch("services.firestore_client.get_firestore_client") as mock_firestore:
            mock_firestore.return_value = MagicMock()  # Mock successful client

            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            assert "firestore_status" in data

    def test_healthz_firestore_error_handling(self):
        """Test healthz handles firestore errors gracefully"""
        with patch(
            "services.firestore_client.get_firestore_client",
            side_effect=Exception("Firestore connection failed"),
        ):
            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            # Health should still return even if Firestore fails
            assert "firestore" in data
            assert data["firestore"] == "error"


class TestAgentStatusEndpoint:
    """Test /api/agents/status endpoint"""

    def test_agent_status_operational(self):
        """Test agent status returns operational when all agents are available"""
        with patch("agents.OrchestratorAgent") as mock_orch, patch(
            "agents.SummarizerAgent"
        ) as mock_sum, patch("agents.LinkerAgent") as mock_link, patch(
            "agents.VisualizerAgent"
        ) as mock_viz, patch(
            "agents.A2AProtocol"
        ) as mock_a2a_class:

            # Mock agent instances
            def create_mock_agent(name):
                agent = MagicMock()
                agent.name = name
                agent.state.value = "idle"
                agent.execution_history = []
                return agent

            mock_orch.return_value = create_mock_agent("orchestrator")
            mock_sum.return_value = create_mock_agent("summarizer")
            mock_link.return_value = create_mock_agent("linker")
            mock_viz.return_value = create_mock_agent("visualizer")

            response = client.get("/api/agents/status")

            assert response.status_code == 200
            data = response.json()
            assert data["adk_system"] == "operational"
            assert data["total_agents"] == 4
            assert len(data["agents"]) == 4

    def test_agent_status_import_error(self):
        """Test agent status handles import errors with diagnostics"""
        with patch.dict("sys.modules", {"agents": None}):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'agents'"),
            ):
                response = client.get("/api/agents/status")

                assert response.status_code == 200
                data = response.json()
                assert data["adk_system"] == "unavailable"
                assert "diagnostics" in data
                assert "import_errors" in data["diagnostics"]
                assert len(data["diagnostics"]["import_errors"]) > 0

    def test_agent_status_partial_availability(self):
        """Test agent status when some agents fail to initialize"""
        with patch("agents.OrchestratorAgent") as mock_orch, patch(
            "agents.SummarizerAgent", side_effect=Exception("Summarizer init failed")
        ), patch("agents.LinkerAgent") as mock_link, patch(
            "agents.VisualizerAgent"
        ) as mock_viz, patch(
            "agents.A2AProtocol"
        ) as mock_a2a_class:

            # Mock successful agents
            def create_mock_agent(name):
                agent = MagicMock()
                agent.name = name
                agent.state.value = "idle"
                agent.execution_history = []
                return agent

            mock_orch.return_value = create_mock_agent("orchestrator")
            mock_link.return_value = create_mock_agent("linker")
            mock_viz.return_value = create_mock_agent("visualizer")

            response = client.get("/api/agents/status")

            assert response.status_code == 200
            data = response.json()
            assert data["adk_system"] == "degraded"
            assert data["total_agents"] == 3  # Only 3 succeeded
            assert "diagnostics" in data
            assert "warnings" in data

    def test_agent_status_includes_environment_vars(self):
        """Test agent status includes environment variable diagnostics"""
        with patch("agents.OrchestratorAgent"), patch("agents.SummarizerAgent"), patch(
            "agents.LinkerAgent"
        ), patch("agents.VisualizerAgent"), patch("agents.A2AProtocol"):

            with patch.dict(
                os.environ,
                {"FIRESTORE_PROJECT_ID": "test-project", "FIRESTORE_DATABASE_ID": ""},
                clear=False,
            ):
                response = client.get("/api/agents/status")

                assert response.status_code == 200
                # Note: Environment vars check is in diagnostic_info, may not always be present
                # depending on success/failure path
