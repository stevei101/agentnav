"""
Tests for enhanced ModelLoader functionality
Tests GPU detection, 8-bit quantization, and error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock torch and transformers before importing
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gemma_service.model_loader import ModelLoader


@pytest.fixture
def mock_torch():
    """Create a mock torch module with proper attributes for testing"""
    torch_mock = MagicMock()
    torch_mock.cuda.is_available.return_value = True
    torch_mock.cuda.device_count.return_value = 1
    torch_mock.cuda.get_device_name.return_value = "NVIDIA L4"
    
    # Mock version with proper string
    version_mock = MagicMock()
    version_mock.cuda = "12.1"
    torch_mock.version = version_mock
    
    # Mock GPU properties with real numbers (not MagicMock)
    gpu_props = type('GPUProps', (), {
        'total_memory': 16000000000,  # 16 GB as real number
        'major': 8,
        'minor': 9
    })()
    torch_mock.cuda.get_device_properties.return_value = gpu_props
    
    # Mock tensor operations - return a properly configured tensor
    test_tensor = MagicMock()
    cuda_tensor = MagicMock()
    cuda_tensor.__mul__ = Mock(return_value=cuda_tensor)
    test_tensor.cuda.return_value = cuda_tensor
    torch_mock.tensor.return_value = test_tensor
    
    # Mock float types
    torch_mock.float16 = "float16"
    torch_mock.float32 = "float32"
    
    return torch_mock


@pytest.fixture
def mock_torch_no_gpu():
    """Create a mock torch module without GPU"""
    torch_mock = MagicMock()
    torch_mock.cuda.is_available.return_value = False
    return torch_mock


def test_gpu_detection_success(mock_torch):
    """Test successful GPU detection with verification"""
    # Need to patch torch where it's imported in model_loader
    with patch('gemma_service.model_loader.torch', mock_torch):
        loader = ModelLoader(model_name="google/gemma-7b-it")
        
        assert loader.device == "cuda"
        mock_torch.cuda.is_available.assert_called()
        mock_torch.cuda.device_count.assert_called()


def test_gpu_detection_no_devices(mock_torch):
    """Test GPU detection when CUDA is available but no devices"""
    mock_torch.cuda.device_count.return_value = 0
    
    with patch('gemma_service.model_loader.torch', mock_torch):
        loader = ModelLoader(model_name="google/gemma-7b-it")
        
        assert loader.device == "cpu"


def test_gpu_detection_test_failure(mock_torch):
    """Test GPU detection when test operation fails"""
    mock_torch.tensor.return_value.cuda.side_effect = RuntimeError("CUDA error")
    
    with patch('gemma_service.model_loader.torch', mock_torch):
        loader = ModelLoader(model_name="google/gemma-7b-it")
        
        assert loader.device == "cpu"


def test_cpu_fallback(mock_torch_no_gpu):
    """Test CPU fallback when no GPU is available"""
    with patch('gemma_service.model_loader.torch', mock_torch_no_gpu):
        loader = ModelLoader(model_name="google/gemma-7b-it")
        
        assert loader.device == "cpu"


def test_8bit_quantization_enabled(mock_torch):
    """Test model loading with 8-bit quantization enabled"""
    with patch('gemma_service.model_loader.torch', mock_torch):
        with patch.dict(os.environ, {'USE_8BIT_QUANTIZATION': 'true'}):
            loader = ModelLoader(model_name="google/gemma-7b-it")
            loader.device = "cuda"  # Force GPU
            
            # Mock transformers
            mock_transformers = MagicMock()
            mock_model = MagicMock()
            mock_tokenizer = MagicMock()
            mock_transformers.AutoModelForCausalLM.from_pretrained.return_value = mock_model
            mock_transformers.AutoTokenizer.from_pretrained.return_value = mock_tokenizer
            
            with patch.dict('sys.modules', {'transformers': mock_transformers}):
                loader.load_model()
                
                # Verify model was loaded
                assert loader._loaded
                assert loader.model == mock_model
                assert loader.tokenizer == mock_tokenizer


def test_8bit_quantization_cpu_warning(mock_torch_no_gpu):
    """Test that 8-bit quantization is not used on CPU"""
    with patch('gemma_service.model_loader.torch', mock_torch_no_gpu):
        with patch.dict(os.environ, {'USE_8BIT_QUANTIZATION': 'true'}):
            loader = ModelLoader(model_name="google/gemma-7b-it")
            
            assert loader.device == "cpu"
            # Quantization should be skipped on CPU


def test_model_info_with_gpu(mock_torch):
    """Test get_model_info with GPU available"""
    with patch('gemma_service.model_loader.torch', mock_torch):
        loader = ModelLoader(model_name="google/gemma-7b-it")
        loader._loaded = True
        
        info = loader.get_model_info()
        
        assert info["model"] == "google/gemma-7b-it"
        assert info["device"] == "cuda"
        assert info["loaded"] is True
        assert info["gpu_available"] is True
        assert "gpu_name" in info
        assert "gpu_memory_gb" in info


def test_model_info_without_gpu(mock_torch_no_gpu):
    """Test get_model_info without GPU"""
    with patch('gemma_service.model_loader.torch', mock_torch_no_gpu):
        loader = ModelLoader(model_name="google/gemma-7b-it")
        loader._loaded = True
        
        info = loader.get_model_info()
        
        assert info["model"] == "google/gemma-7b-it"
        assert info["device"] == "cpu"
        assert info["loaded"] is True
        assert info["gpu_available"] is False


def test_is_loaded():
    """Test is_loaded method"""
    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = False
    
    with patch('gemma_service.model_loader.torch', mock_torch):
        loader = ModelLoader(model_name="google/gemma-7b-it")
        
        assert loader.is_loaded() is False
        
        loader._loaded = True
        assert loader.is_loaded() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
