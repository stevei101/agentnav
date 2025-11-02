"""
Tests for enhanced Gemma service health check endpoint
Tests model readiness and GPU status validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Mock dependencies
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import after mocking
from fastapi.testclient import TestClient


@pytest.fixture
def mock_model_loader():
    """Create a mock model loader"""
    loader = Mock()
    loader.model_name = "google/gemma-7b-it"
    loader.device = "cuda"
    loader.model = Mock()
    loader.tokenizer = Mock()
    return loader


@pytest.fixture
def mock_inference_engine():
    """Create a mock inference engine"""
    engine = Mock()
    return engine


def test_health_check_model_loaded_gpu():
    """Test health check when model is loaded on GPU"""
    # Import and patch the module
    with patch('gemma_service.main.model_loader') as mock_loader, \
         patch('gemma_service.main.inference_engine') as mock_engine:
        
        mock_loader.get_model_info.return_value = {
            "model": "google/gemma-7b-it",
            "device": "cuda",
            "loaded": True,
            "gpu_available": True,
            "gpu_name": "NVIDIA L4",
            "gpu_memory_gb": 16.0
        }
        
        from gemma_service.main import app
        client = TestClient(app)
        
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert data["gpu_available"] is True
        assert data["device"] == "cuda"


def test_health_check_model_not_loaded():
    """Test health check when model is not loaded (startup)"""
    with patch('gemma_service.main.model_loader') as mock_loader, \
         patch('gemma_service.main.inference_engine') as mock_engine:
        
        mock_loader.get_model_info.return_value = {
            "model": "google/gemma-7b-it",
            "device": "cuda",
            "loaded": False,
            "gpu_available": True
        }
        
        from gemma_service.main import app
        client = TestClient(app)
        
        response = client.get("/healthz")
        
        assert response.status_code == 503
        assert "not loaded" in response.json()["detail"].lower()


def test_health_check_inference_engine_not_ready():
    """Test health check when inference engine is not initialized"""
    with patch('gemma_service.main.model_loader') as mock_loader, \
         patch('gemma_service.main.inference_engine', None):
        
        mock_loader.get_model_info.return_value = {
            "model": "google/gemma-7b-it",
            "device": "cuda",
            "loaded": True,
            "gpu_available": True
        }
        
        from gemma_service.main import app
        client = TestClient(app)
        
        response = client.get("/healthz")
        
        assert response.status_code == 503
        assert "inference engine" in response.json()["detail"].lower()


def test_health_check_model_loader_not_initialized():
    """Test health check when model loader is not initialized"""
    with patch('gemma_service.main.model_loader', None):
        from gemma_service.main import app
        client = TestClient(app)
        
        response = client.get("/healthz")
        
        assert response.status_code == 503
        assert "not initialized" in response.json()["detail"].lower()


def test_health_check_cpu_fallback():
    """Test health check when running on CPU"""
    with patch('gemma_service.main.model_loader') as mock_loader, \
         patch('gemma_service.main.inference_engine') as mock_engine:
        
        mock_loader.get_model_info.return_value = {
            "model": "google/gemma-7b-it",
            "device": "cpu",
            "loaded": True,
            "gpu_available": False
        }
        
        from gemma_service.main import app
        client = TestClient(app)
        
        response = client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert data["gpu_available"] is False
        assert data["device"] == "cpu"


def test_health_check_gpu_lost_during_operation():
    """Test health check when GPU becomes unavailable"""
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False  # GPU lost
    
    with patch('gemma_service.main.model_loader') as mock_loader, \
         patch('gemma_service.main.inference_engine') as mock_engine, \
         patch.dict('sys.modules', {'torch': mock_torch}):
        
        mock_loader.get_model_info.return_value = {
            "model": "google/gemma-7b-it",
            "device": "cuda",
            "loaded": True,
            "gpu_available": True,  # Was available
        }
        
        from gemma_service.main import app
        client = TestClient(app)
        
        response = client.get("/healthz")
        
        # Should still return 200 but GPU status should be updated
        assert response.status_code == 200
        data = response.json()
        # GPU available should be False in response (updated check)
        assert data["gpu_available"] is False


def test_root_endpoint():
    """Test root endpoint returns service info"""
    from gemma_service.main import app
    client = TestClient(app)
    
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Gemma GPU Service"
    assert "/healthz" in data["endpoints"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
