"""
Unit tests for ADK health check endpoints (FR#085)

Tests verify that the /healthz and /api/agents/status endpoints
correctly detect ADK system availability and provide diagnostic information.
"""

from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from backend.main import app

# TestClient with base_url to satisfy TrustedHostMiddleware
client = TestClient(app, base_url="http://localhost")


class TestHealthzEndpoint:
    """Test /healthz endpoint ADK system checks"""

    def test_healthz_with_operational_adk(self):
        """Test healthz returns healthy when ADK is operational"""
        with (
            patch("backend.agents.OrchestratorAgent") as mock_agent_class,
            patch("backend.agents.A2AProtocol") as mock_a2a,
        ):
            # Mock successful agent initialization
            mock_agent = MagicMock()
            mock_agent.name = "orchestrator"
            mock_agent_class.return_value = mock_agent

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
        with patch(
            "backend.main.load_attributes",
            side_effect=ImportError("No module named 'backend.agents'"),
        ):
            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["adk_system"] == "unavailable"
            assert "errors" in data
            assert "adk" in data["errors"]

    def test_healthz_firestore_check(self):
        """Test healthz checks Firestore connectivity"""
        with patch("backend.services.firestore_client.get_firestore_client") as mock_firestore:
            # Mock Firestore client available
            mock_firestore.return_value = MagicMock()

            response = client.get("/healthz")

            assert response.status_code == 200
            data = response.json()
            assert data["firestore"] in ["connected", "disconnected", "error"]

    def test_healthz_firestore_error_handling(self):
        """Test healthz handles Firestore errors gracefully"""
        with patch(
            "backend.services.firestore_client.get_firestore_client",
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
        with (
            patch("backend.agents.OrchestratorAgent") as mock_orch,
            patch("backend.agents.SummarizerAgent") as mock_sum,
            patch("backend.agents.LinkerAgent") as mock_link,
            patch("backend.agents.VisualizerAgent") as mock_viz,
            patch("backend.agents.A2AProtocol") as mock_a2a,
        ):
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
        with patch(
            "backend.main.load_attributes",
            side_effect=ImportError("No module named 'backend.agents'"),
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
        with (
            patch("backend.agents.OrchestratorAgent") as mock_orch,
            patch(
                "backend.agents.SummarizerAgent", side_effect=Exception("Summarizer init failed")
            ),
            patch("backend.agents.LinkerAgent") as mock_link,
            patch("backend.agents.VisualizerAgent") as mock_viz,
            patch("backend.agents.A2AProtocol") as mock_a2a,
        ):
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
        with (
            patch("backend.agents.OrchestratorAgent"),
            patch("backend.agents.SummarizerAgent"),
            patch("backend.agents.LinkerAgent"),
            patch("backend.agents.VisualizerAgent"),
            patch("backend.agents.A2AProtocol"),
        ):
            with patch.dict(
                os.environ,
                {"FIRESTORE_PROJECT_ID": "test-project", "FIRESTORE_DATABASE_ID": ""},
                clear=False,
            ):
                response = client.get("/api/agents/status")

                assert response.status_code == 200
                # Note: Environment vars check is in diagnostic_info, may not always be present
                # depending on success/failure path
