"""
Tests for Gemma Service JWT Authentication
"""

import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gemma_service.auth import verify_jwt_token, REQUIRE_AUTH


class TestJWTAuthentication:
    """Test JWT authentication for Gemma service"""

    def test_auth_bypass_when_disabled(self):
        """Test that authentication is bypassed when REQUIRE_AUTH is False"""
        with patch.dict(os.environ, {"REQUIRE_AUTH": "false"}):
            # Reload module to pick up new env var
            import importlib
            import gemma_service.auth

            importlib.reload(gemma_service.auth)

            # Should return True without requiring token
            result = gemma_service.auth.verify_jwt_token(None)
            assert result is True

    def test_auth_required_when_enabled_no_header(self):
        """Test that authentication fails when required but no header provided"""
        with patch.dict(os.environ, {"REQUIRE_AUTH": "true"}):
            import importlib
            import gemma_service.auth

            importlib.reload(gemma_service.auth)

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                gemma_service.auth.verify_jwt_token(None)

            assert exc_info.value.status_code == 401
            assert "Missing Authorization header" in str(exc_info.value.detail)

    def test_auth_invalid_header_format(self):
        """Test that invalid Authorization header format is rejected"""
        with patch.dict(os.environ, {"REQUIRE_AUTH": "true"}):
            import importlib
            import gemma_service.auth

            importlib.reload(gemma_service.auth)

            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                gemma_service.auth.verify_jwt_token("InvalidFormat token123")

            assert exc_info.value.status_code == 401
            assert "Invalid Authorization header format" in str(exc_info.value.detail)

    @patch("gemma_service.auth.jwt")
    def test_auth_valid_token(self, mock_jwt):
        """Test that valid JWT token passes authentication"""
        with patch.dict(os.environ, {"REQUIRE_AUTH": "true"}):
            import importlib
            import gemma_service.auth
            from google.auth.transport import requests

            importlib.reload(gemma_service.auth)

            # Mock JWT decode to return valid token
            mock_jwt.decode.return_value = {
                "iss": "https://accounts.google.com",
                "aud": "test-service-url",
                "exp": 9999999999,
            }

            with patch("gemma_service.auth.requests.Request"):
                result = gemma_service.auth.verify_jwt_token("Bearer valid_token_123")
                assert result is True
                mock_jwt.decode.assert_called_once()

    @patch("gemma_service.auth.jwt")
    def test_auth_invalid_token(self, mock_jwt):
        """Test that invalid JWT token fails authentication"""
        with patch.dict(os.environ, {"REQUIRE_AUTH": "true"}):
            import importlib
            import gemma_service.auth

            importlib.reload(gemma_service.auth)

            from fastapi import HTTPException

            # Mock JWT decode to raise exception (invalid token)
            mock_jwt.decode.side_effect = Exception("Invalid token signature")

            with patch("gemma_service.auth.requests.Request"):
                with pytest.raises(HTTPException) as exc_info:
                    gemma_service.auth.verify_jwt_token("Bearer invalid_token")

                assert exc_info.value.status_code == 401
                assert "JWT token verification failed" in str(exc_info.value.detail)

    def test_auth_google_auth_not_installed(self):
        """Test graceful handling when google-auth is not installed"""
        with patch.dict(os.environ, {"REQUIRE_AUTH": "true"}):
            import importlib
            import gemma_service.auth

            importlib.reload(gemma_service.auth)

            # Mock ImportError for google.auth
            with patch.dict("sys.modules", {"google.auth": None}):
                with patch(
                    "builtins.__import__", side_effect=ImportError("No module named 'google.auth'")
                ):
                    # Should allow request but log warning
                    result = gemma_service.auth.verify_jwt_token("Bearer token")
                    assert result is True
