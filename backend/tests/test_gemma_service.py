"""
Tests for Gemma GPU Service
Tests the API endpoints and client functionality
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mock torch before importing gemma_service
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Now safe to import after mocking
from services.gemma_client import GemmaServiceClient


# Client Tests - These don't require the full app
@pytest.mark.asyncio
async def test_gemma_client_reason():
    """Test GemmaServiceClient.reason() method"""
    client = GemmaServiceClient(base_url="http://test:8080")

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_response = Mock()
        mock_response.json = Mock(
            return_value={"text": "Test response", "model": "google/gemma-7b-it"}
        )
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await client.reason(prompt="Test prompt", context="Test context")

        assert result == "Test response"
        mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
async def test_gemma_client_embed():
    """Test GemmaServiceClient.embed() method"""
    client = GemmaServiceClient(base_url="http://test:8080")

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_response = Mock()
        mock_response.json = Mock(
            return_value={
                "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
                "dimension": 3,
            }
        )
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await client.embed(texts=["Text 1", "Text 2"])

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_gemma_client_legacy_generate():
    """Test backward compatibility with legacy generate() method"""
    client = GemmaServiceClient(base_url="http://test:8080")

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_response = Mock()
        mock_response.json = Mock(return_value={"text": "Legacy response"})
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Legacy method should still work
        result = await client.generate(prompt="Test")

        assert result == "Legacy response"


@pytest.mark.asyncio
async def test_gemma_client_health_check():
    """Test GemmaServiceClient.health_check() method"""
    client = GemmaServiceClient(base_url="http://test:8080")

    with patch("httpx.AsyncClient") as mock_async_client:
        mock_response = Mock()
        mock_response.json = Mock(
            return_value={"status": "healthy", "gpu_available": True}
        )
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        result = await client.health_check()

        assert result["status"] == "healthy"
        assert result["gpu_available"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
