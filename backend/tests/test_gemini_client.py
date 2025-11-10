"""
Unit tests for Gemini Client Service (FR#090)

Tests verify that the Gemini client can be initialized correctly
without hardcoded credentials, supporting both Workload Identity
and API key authentication methods.

Updated to match current gemini_client.py API:
- Uses GeminiClient class instead of get_gemini_client function
- Tests reason_with_gemini helper function
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

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
        mock_genai.Client = MagicMock(return_value=mock_client)

        client = GeminiClient()

        # Verify Client was created (uses Application Default Credentials)
        mock_genai.Client.assert_called_once()
        assert client._client == mock_client

    @patch("services.gemini_client.genai")
    def test_init_fallback_to_module(self, mock_genai):
        """Test client initialization falls back to module when Client() fails"""
        # Mock Client() raising an exception
        mock_genai.Client = MagicMock(side_effect=Exception("Client init failed"))
        mock_genai.side_effect = None  # Ensure genai module itself is available

        client = GeminiClient()

        # Should fall back to using genai module directly
        assert client._client == mock_genai

    @patch("services.gemini_client.genai", None)
    def test_init_without_sdk_raises_error(self):
        """Test that initialization fails gracefully when SDK is not installed"""
        with pytest.raises(RuntimeError, match="google-genai SDK is not installed"):
            GeminiClient()

    @patch("services.gemini_client.genai")
    def test_init_with_custom_client(self, mock_genai):
        """Test client initialization with custom client (for testing)"""
        custom_client = MagicMock()
        client = GeminiClient(client=custom_client)

        assert client._client == custom_client
        # Should not call genai.Client when custom client is provided
        mock_genai.Client.assert_not_called()


@pytest.mark.asyncio
class TestGeminiClientGenerate:
    """Test Gemini client generate method"""

    @patch("services.gemini_client.genai")
    @patch("asyncio.to_thread")
    async def test_generate_with_models_generate(self, mock_to_thread, mock_genai):
        """Test generate method using client.models.generate pattern"""
        mock_client = MagicMock()
        mock_models = MagicMock()
        mock_client.models = mock_models
        mock_genai.Client = MagicMock(return_value=mock_client)

        # Mock the sync call result
        mock_response = {"candidates": [{"content": {"text": "Test response"}}]}
        mock_to_thread.return_value = mock_response

        client = GeminiClient()
        result = await client.generate(model="gemini-1", prompt="Test prompt")

        assert result == mock_response
        mock_to_thread.assert_called_once()

    @patch("services.gemini_client.genai")
    @patch("asyncio.to_thread")
    async def test_generate_with_client_generate(self, mock_to_thread, mock_genai):
        """Test generate method using client.generate pattern"""
        mock_client = MagicMock()
        # Remove models attribute to test fallback
        del mock_client.models
        mock_genai.Client = MagicMock(return_value=mock_client)

        mock_response = "Test response"
        mock_to_thread.return_value = mock_response

        client = GeminiClient()
        result = await client.generate(model="gemini-1", prompt="Test prompt")

        assert result == mock_response


@pytest.mark.asyncio
class TestReasonWithGemini:
    """Test reason_with_gemini helper function"""

    @patch("services.gemini_client.GeminiClient")
    @patch("os.environ.get")
    async def test_reason_with_gemini_default_model(
        self, mock_env_get, mock_client_class
    ):
        """Test reason_with_gemini uses default model when not specified"""
        mock_env_get.return_value = None  # No GEMINI_MODEL env var
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Test response")
        mock_client_class.return_value = mock_client

        result = await reason_with_gemini(prompt="Test prompt")

        assert result == "Test response"
        mock_client.generate.assert_called_once()
        # Should use default model "gemini-1"
        call_args = mock_client.generate.call_args
        assert call_args[1]["model"] == "gemini-1"

    @patch("services.gemini_client.GeminiClient")
    @patch("os.environ.get")
    async def test_reason_with_gemini_env_model(self, mock_env_get, mock_client_class):
        """Test reason_with_gemini uses GEMINI_MODEL env var when set"""
        mock_env_get.return_value = "gemini-2.0"
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Test response")
        mock_client_class.return_value = mock_client

        result = await reason_with_gemini(prompt="Test prompt")

        assert result == "Test response"
        call_args = mock_client.generate.call_args
        assert call_args[1]["model"] == "gemini-2.0"

    @patch("services.gemini_client.GeminiClient")
    async def test_reason_with_gemini_explicit_model(self, mock_client_class):
        """Test reason_with_gemini uses explicit model parameter"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Test response")
        mock_client_class.return_value = mock_client

        result = await reason_with_gemini(prompt="Test prompt", model="gemini-pro")

        assert result == "Test response"
        call_args = mock_client.generate.call_args
        assert call_args[1]["model"] == "gemini-pro"

    @patch("services.gemini_client.GeminiClient")
    async def test_reason_with_gemini_dict_response(self, mock_client_class):
        """Test reason_with_gemini handles dict response format"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(
            return_value={"candidates": [{"content": {"text": "Extracted text"}}]}
        )
        mock_client_class.return_value = mock_client

        result = await reason_with_gemini(prompt="Test prompt")

        assert result == "Extracted text"

    @patch("services.gemini_client.GeminiClient")
    async def test_reason_with_gemini_string_response(self, mock_client_class):
        """Test reason_with_gemini handles string response format"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Direct string response")
        mock_client_class.return_value = mock_client

        result = await reason_with_gemini(prompt="Test prompt")

        assert result == "Direct string response"
