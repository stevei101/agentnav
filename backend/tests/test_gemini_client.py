"""
Unit tests for Gemini Client Service (FR#090)

Tests verify that the Gemini client can be initialized correctly
without hardcoded credentials, supporting both Workload Identity
and API key authentication methods.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.gemini_client import GeminiClient, reason_with_gemini


class TestGeminiClientInitialization:
    """Test Gemini client initialization without hardcoded credentials"""

    @patch("services.gemini_client.genai")
    def test_init_with_workload_identity(self, mock_genai):
        """Test client initialization using Workload Identity (GCP environment)"""
        # Mock the Client constructor
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        # Create client instance
        client = GeminiClient()

        # Verify Client was created (uses Application Default Credentials)
        mock_genai.Client.assert_called_once()
        assert client._client == mock_client

    @patch("services.gemini_client.genai")
    def test_init_with_client_provided(self, mock_genai):
        """Test client initialization with provided client"""
        mock_client = MagicMock()
        client = GeminiClient(client=mock_client)

        # Should use provided client, not create new one
        assert client._client == mock_client
        mock_genai.Client.assert_not_called()

    @patch("services.gemini_client.genai", None)
    def test_init_without_genai_raises_error(self):
        """Test that initialization fails when genai is not available"""
        with pytest.raises(RuntimeError, match="google-genai SDK is not installed"):
            GeminiClient()


@pytest.mark.asyncio
class TestGeminiContentGeneration:
    """Test content generation methods"""

    @patch("services.gemini_client.genai")
    @patch("asyncio.to_thread")
    async def test_client_generate(self, mock_to_thread, mock_genai):
        """Test GeminiClient.generate async method"""
        # Setup mocks
        mock_client = MagicMock()
        mock_client.models.generate.return_value = {"text": "Generated response text"}
        mock_genai.Client.return_value = mock_client

        client = GeminiClient()

        # Mock asyncio.to_thread
        mock_to_thread.return_value = {"text": "Generated response text"}

        # Test generate
        result = await client.generate(
            model="gemini-1.5-flash", prompt="Test prompt", max_tokens=256, temperature=0.7
        )

        # Verify to_thread was called (async wrapper)
        mock_to_thread.assert_called_once()
        assert result == {"text": "Generated response text"}

    @patch.dict(os.environ, {"AGENTNAV_MODEL_TYPE": "gemini"})
    @patch("services.gemini_client.GeminiClient")
    async def test_reason_with_gemini(self, mock_client_class):
        """Test reason_with_gemini convenience function"""
        # Setup mocks - generate is async, so we need an async mock
        async def mock_generate(*args, **kwargs):
            return "Generated response"

        mock_client_instance = MagicMock()
        mock_client_instance.generate = mock_generate
        mock_client_class.return_value = mock_client_instance

        # Test reason_with_gemini
        result = await reason_with_gemini(
            prompt="Test prompt", max_tokens=256, temperature=0.7
        )

        # Verify result
        assert isinstance(result, str)
        assert result == "Generated response"
        # Verify GeminiClient was instantiated
        mock_client_class.assert_called_once()
