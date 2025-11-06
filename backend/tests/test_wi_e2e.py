"""
End-to-End test for Workload Identity (WI) integration between Prompt Vault and Agent Navigator

This test suite validates the complete WI flow:
1. Prompt Vault fetches an ID token for Agent Navigator's public URL
2. Prompt Vault calls Agent Navigator's /api/suggest endpoint with the token
3. Agent Navigator verifies the token and processes the request
4. Unauthorized callers are rejected

Note: These tests use mocking to simulate the metadata server and token verification.
For true E2E tests with real GCP credentials, deploy to Cloud Run and test manually.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestWIE2E:
    """End-to-end Workload Identity integration tests"""

    @pytest.fixture
    def setup_env(self):
        """Setup environment variables for WI tests"""
        os.environ["AGENTNAV_URL"] = "https://agentnav-backend.run.app"
        os.environ["TRUSTED_CALLERS"] = "prompt-mgmt-sa@my-project.iam.gserviceaccount.com"
        yield
        # Cleanup
        if "AGENTNAV_URL" in os.environ:
            del os.environ["AGENTNAV_URL"]
        if "TRUSTED_CALLERS" in os.environ:
            del os.environ["TRUSTED_CALLERS"]

    def test_missing_authorization_header_returns_401(self, setup_env):
        """Test: Caller without Authorization header is rejected"""
        response = client.post(
            "/api/suggest",
            json={"document": "This is a test document"}
        )
        assert response.status_code == 401
        assert "Missing Bearer token" in response.json()["detail"]

    def test_invalid_token_format_returns_401(self, setup_env):
        """Test: Malformed Authorization header is rejected"""
        response = client.post(
            "/api/suggest",
            json={"document": "This is a test document"},
            headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 401

    def test_valid_token_from_trusted_caller_returns_200(self, setup_env):
        """Test: Valid token from trusted caller succeeds"""
        valid_token_payload = {
            "email": "prompt-mgmt-sa@my-project.iam.gserviceaccount.com",
            "sub": "117123456789",
            "aud": "https://agentnav-backend.run.app"
        }

        with patch("services.wi_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = valid_token_payload

            response = client.post(
                "/api/suggest",
                json={"document": "This is a test document"},
                headers={"Authorization": "Bearer valid-token-jwt"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data
            assert data["caller"] == "prompt-mgmt-sa@my-project.iam.gserviceaccount.com"
            assert len(data["suggestions"]) > 0

    def test_token_with_untrusted_caller_returns_403(self, setup_env):
        """Test: Valid token from untrusted caller is rejected"""
        untrusted_token_payload = {
            "email": "random-sa@other-project.iam.gserviceaccount.com",
            "sub": "999999999999",
            "aud": "https://agentnav-backend.run.app"
        }

        with patch("services.wi_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = untrusted_token_payload

            response = client.post(
                "/api/suggest",
                json={"document": "This is a test document"},
                headers={"Authorization": "Bearer valid-but-untrusted-token"}
            )

            assert response.status_code == 403
            assert "Unauthorized caller" in response.json()["detail"]

    def test_token_with_wrong_audience_returns_401(self, setup_env):
        """Test: Token with incorrect audience is rejected"""
        with patch("services.wi_auth.id_token.verify_oauth2_token") as mock_verify:
            # Simulate Google's verification failure due to audience mismatch
            mock_verify.side_effect = Exception("Token audience mismatch")

            response = client.post(
                "/api/suggest",
                json={"document": "This is a test document"},
                headers={"Authorization": "Bearer token-wrong-audience"}
            )

            assert response.status_code == 401
            assert "Invalid or expired ID token" in response.json()["detail"]

    def test_suggestions_are_context_aware(self, setup_env):
        """Test: Suggestions are generated based on document content"""
        valid_token_payload = {
            "email": "prompt-mgmt-sa@my-project.iam.gserviceaccount.com",
            "sub": "117123456789",
            "aud": "https://agentnav-backend.run.app"
        }

        with patch("services.wi_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = valid_token_payload

            # Short document should get expansion suggestion
            response = client.post(
                "/api/suggest",
                json={"document": "Short doc"},
                headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert any("Expand" in suggestion for suggestion in data["suggestions"])

            # Long document should get structuring suggestion
            long_doc = "This is a very long document. " * 20  # ~800 chars
            response = client.post(
                "/api/suggest",
                json={"document": long_doc},
                headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200
            data = response.json()
            # Should have at least one suggestion
            assert len(data["suggestions"]) > 0

    def test_max_suggestions_parameter_respected(self, setup_env):
        """Test: max_suggestions parameter limits response"""
        valid_token_payload = {
            "email": "prompt-mgmt-sa@my-project.iam.gserviceaccount.com",
            "sub": "117123456789",
            "aud": "https://agentnav-backend.run.app"
        }

        with patch("services.wi_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = valid_token_payload

            # Request only 1 suggestion
            response = client.post(
                "/api/suggest",
                json={
                    "document": "This is a test document to suggest improvements for.",
                    "max_suggestions": 1
                },
                headers={"Authorization": "Bearer valid-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestions"]) <= 1

    def test_caller_identity_captured_in_response(self, setup_env):
        """Test: Caller's service account identity is included in response"""
        caller_sa = "prompt-mgmt-sa@my-project.iam.gserviceaccount.com"
        valid_token_payload = {
            "email": caller_sa,
            "sub": "117123456789",
            "aud": "https://agentnav-backend.run.app"
        }

        with patch("services.wi_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = valid_token_payload

            response = client.post(
                "/api/suggest",
                json={"document": "Test document"},
                headers={"Authorization": "Bearer valid-token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["caller"] == caller_sa


class TestWIClientHelper:
    """Tests for the wid_client token fetching helper"""

    @patch("requests.get")
    def test_fetch_id_token_from_metadata_server(self, mock_requests_get):
        """Test: Token is fetched from metadata server on Cloud Run"""
        from services.wid_client import fetch_id_token_for_audience

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        mock_requests_get.return_value = mock_response

        token = fetch_id_token_for_audience("https://agentnav-backend.run.app")

        assert token == "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert mock_requests_get.called
        call_args = mock_requests_get.call_args
        assert "metadata" in call_args[0][0]
        assert "identity" in call_args[0][0]

    @patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/tmp/sa.json"})
    @patch("requests.get")
    @patch("services.wid_client.service_account.IDTokenCredentials.from_service_account_file")
    def test_fetch_id_token_fallback_to_service_account_key(
        self, mock_from_file, mock_requests_get
    ):
        """Test: Token fetching falls back to service account key when metadata server unavailable"""
        from services.wid_client import fetch_id_token_for_audience

        # Simulate metadata server not reachable
        mock_requests_get.side_effect = Exception("Connection refused")

        # Mock service account credentials
        mock_creds = MagicMock()
        mock_creds.token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        mock_from_file.return_value = mock_creds

        with patch("services.wid_client.google_requests.Request"):
            token = fetch_id_token_for_audience("https://agentnav-backend.run.app")

        assert token == "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

    @patch("requests.get")
    def test_fetch_id_token_raises_on_metadata_error(self, mock_requests_get):
        """Test: Appropriate error is raised when token fetch fails"""
        from services.wid_client import fetch_id_token_for_audience

        # Simulate both metadata server and fallback failing
        mock_requests_get.side_effect = Exception("Connection refused")

        with patch.dict(os.environ, {}, clear=True):
            # No GOOGLE_APPLICATION_CREDENTIALS set
            with pytest.raises(RuntimeError):
                fetch_id_token_for_audience("https://agentnav-backend.run.app")


class TestWISecurityScenarios:
    """Test various security scenarios"""

    def test_multiple_trusted_callers(self):
        """Test: Multiple trusted callers can be configured via env var"""
        os.environ["AGENTNAV_URL"] = "https://agentnav-backend.run.app"
        os.environ["TRUSTED_CALLERS"] = (
            "prompt-mgmt-sa@project1.iam.gserviceaccount.com,"
            "prompt-mgmt-sa@project2.iam.gserviceaccount.com"
        )

        from services.wi_auth import _get_trusted_callers

        callers = _get_trusted_callers()
        assert len(callers) == 2
        assert "prompt-mgmt-sa@project1.iam.gserviceaccount.com" in callers
        assert "prompt-mgmt-sa@project2.iam.gserviceaccount.com" in callers

        # Cleanup
        del os.environ["AGENTNAV_URL"]
        del os.environ["TRUSTED_CALLERS"]

    def test_no_trusted_callers_configured_accepts_any_valid_token(self):
        """Test: If TRUSTED_CALLERS not set, any valid token for correct audience is accepted"""
        os.environ["AGENTNAV_URL"] = "https://agentnav-backend.run.app"
        # Don't set TRUSTED_CALLERS

        valid_token_payload = {
            "email": "any-sa@any-project.iam.gserviceaccount.com",
            "sub": "999999999999",
            "aud": "https://agentnav-backend.run.app"
        }

        with patch("services.wi_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = valid_token_payload

            response = client.post(
                "/api/suggest",
                json={"document": "Test"},
                headers={"Authorization": "Bearer valid-token"}
            )

            # Should succeed because TRUSTED_CALLERS is not set
            assert response.status_code == 200

        # Cleanup
        if "AGENTNAV_URL" in os.environ:
            del os.environ["AGENTNAV_URL"]
        if "TRUSTED_CALLERS" in os.environ:
            del os.environ["TRUSTED_CALLERS"]
