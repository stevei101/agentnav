"""
Tests for Workload Identity authentication in GemmaServiceClient
Tests ID token fetching and authentication headers
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import sys
import os

# Mock dependencies before importing
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.gemma_client import GemmaServiceClient, get_cloud_run_id_token


@pytest.mark.asyncio
async def test_get_cloud_run_id_token_not_on_cloud_run():
    """Test ID token fetch when not on Cloud Run"""
    with patch.dict(os.environ, {}, clear=True):
        token = await get_cloud_run_id_token("https://test.run.app")
        assert token is None


@pytest.mark.asyncio
async def test_get_cloud_run_id_token_success():
    """Test successful ID token fetch"""
    with patch.dict(os.environ, {"GCP_PROJECT": "test-project"}):
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "test-id-token-abc123"
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            token = await get_cloud_run_id_token("https://test.run.app")
            
            assert token == "test-id-token-abc123"
            mock_client_instance.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_cloud_run_id_token_failure():
    """Test ID token fetch failure"""
    with patch.dict(os.environ, {"GCP_PROJECT": "test-project"}):
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_response = Mock()
            mock_response.status_code = 404
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            token = await get_cloud_run_id_token("https://test.run.app")
            
            assert token is None


@pytest.mark.asyncio
async def test_get_auth_headers_local_development():
    """Test auth headers in local development (no token)"""
    client = GemmaServiceClient(base_url="http://localhost:8080")
    
    headers = await client._get_auth_headers()
    
    assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_get_auth_headers_cloud_run():
    """Test auth headers for Cloud Run URL with token"""
    client = GemmaServiceClient(base_url="https://gemma-service-xyz.run.app")
    
    with patch('services.gemma_client.get_cloud_run_id_token') as mock_get_token:
        mock_get_token.return_value = "test-token-123"
        
        headers = await client._get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token-123"


@pytest.mark.asyncio
async def test_get_auth_headers_token_caching():
    """Test that ID token is cached and reused"""
    client = GemmaServiceClient(base_url="https://gemma-service-xyz.run.app")
    
    with patch('services.gemma_client.get_cloud_run_id_token') as mock_get_token:
        mock_get_token.return_value = "cached-token"
        
        # First call should fetch token
        headers1 = await client._get_auth_headers()
        assert mock_get_token.call_count == 1
        
        # Second call should use cached token
        headers2 = await client._get_auth_headers()
        assert mock_get_token.call_count == 1  # Still 1, not called again
        
        assert headers1 == headers2


@pytest.mark.asyncio
async def test_reason_with_authentication():
    """Test reason() method includes authentication headers"""
    client = GemmaServiceClient(base_url="https://gemma-service-xyz.run.app")
    
    with patch('services.gemma_client.get_cloud_run_id_token') as mock_get_token:
        mock_get_token.return_value = "auth-token"
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_response = Mock()
            mock_response.json = Mock(return_value={"text": "Generated text"})
            mock_response.raise_for_status = Mock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await client.reason(prompt="Test prompt")
            
            assert result == "Generated text"
            
            # Verify post was called with auth headers
            call_args = mock_client_instance.post.call_args
            headers = call_args.kwargs.get('headers', {})
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer auth-token"


@pytest.mark.asyncio
async def test_embed_with_authentication():
    """Test embed() method includes authentication headers"""
    client = GemmaServiceClient(base_url="https://gemma-service-xyz.run.app")
    
    with patch('services.gemma_client.get_cloud_run_id_token') as mock_get_token:
        mock_get_token.return_value = "auth-token"
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_response = Mock()
            mock_response.json = Mock(return_value={
                "embeddings": [[0.1, 0.2], [0.3, 0.4]],
                "dimension": 2
            })
            mock_response.raise_for_status = Mock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await client.embed(texts=["Text 1", "Text 2"])
            
            assert len(result) == 2
            
            # Verify post was called with auth headers
            call_args = mock_client_instance.post.call_args
            headers = call_args.kwargs.get('headers', {})
            assert "Authorization" in headers


@pytest.mark.asyncio
async def test_health_check_with_authentication():
    """Test health_check() method includes authentication headers"""
    client = GemmaServiceClient(base_url="https://gemma-service-xyz.run.app")
    
    with patch('services.gemma_client.get_cloud_run_id_token') as mock_get_token:
        mock_get_token.return_value = "auth-token"
        
        with patch('httpx.AsyncClient') as mock_async_client:
            mock_response = Mock()
            mock_response.json = Mock(return_value={"status": "healthy"})
            mock_response.raise_for_status = Mock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_async_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await client.health_check()
            
            assert result["status"] == "healthy"
            
            # Verify get was called with auth headers
            call_args = mock_client_instance.get.call_args
            headers = call_args.kwargs.get('headers', {})
            assert "Authorization" in headers


@pytest.mark.asyncio
async def test_reason_http_error_with_details():
    """Test that HTTP errors include response text for debugging"""
    client = GemmaServiceClient(base_url="http://test:8080")
    
    with patch('httpx.AsyncClient') as mock_async_client:
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service unavailable: Model not loaded"
        mock_response.raise_for_status = Mock(
            side_effect=__import__('httpx').HTTPStatusError(
                "503", request=Mock(), response=mock_response
            )
        )
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance
        
        with pytest.raises(Exception) as exc_info:
            await client.reason(prompt="Test")
        
        assert "503" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
