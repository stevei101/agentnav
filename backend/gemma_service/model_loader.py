"""
Model Loader for Gemma
Handles GPU detection, model loading, and device management
"""
import os
import logging
import torch

logger = logging.getLogger(__name__)


class ModelLoader:
    """Loads and manages Gemma model with GPU support"""
    
    def __init__(self, model_name: str = "google/gemma-7b-it"):
        self.model_name = model_name
        self.device = self._detect_device()
        self.model = None
        self.tokenizer = None
        self._loaded = False
        
    def _detect_device(self) -> str:
        """
        Detect available device (CUDA or CPU) with robust GPU validation
        
        Returns:
            Device string: "cuda" if GPU is available and functional, "cpu" otherwise
        """
        if torch.cuda.is_available():
            try:
                # Verify CUDA is actually functional by attempting a simple operation
                device_count = torch.cuda.device_count()
                if device_count == 0:
                    logger.warning("⚠️  CUDA available but no devices found, falling back to CPU")
                    return "cpu"
                
                # Test GPU with a simple tensor operation
                test_tensor = torch.tensor([1.0]).cuda()
                _ = test_tensor * 2
                
                device = "cuda"
                gpu_props = torch.cuda.get_device_properties(0)
                logger.info(f"✅ GPU detected and verified: {torch.cuda.get_device_name(0)}")
                logger.info(f"   CUDA version: {torch.version.cuda}")
                logger.info(f"   GPU memory: {gpu_props.total_memory / 1e9:.2f} GB")
                logger.info(f"   GPU compute capability: {gpu_props.major}.{gpu_props.minor}")
                logger.info(f"   Number of GPUs: {device_count}")
                return device
                
            except Exception as e:
                logger.error(f"❌ GPU detection failed: {e}")
                logger.warning("⚠️  Falling back to CPU despite CUDA being available")
                return "cpu"
        else:
            logger.warning("⚠️  No GPU detected (CUDA not available), falling back to CPU")
            return "cpu"
    
    def load_model(self):
        """
        Load Gemma model and tokenizer with memory optimization
        
        Supports 8-bit quantization for reduced memory usage on GPU.
        Falls back to CPU if GPU fails.
        """
        if self._loaded:
            logger.info("Model already loaded")
            return
            
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            logger.info(f"🔄 Loading model: {self.model_name}")
            logger.info(f"   Device: {self.device}")
            
            # Load tokenizer
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                token=hf_token
            )
            
            # Check if 8-bit quantization should be enabled
            use_8bit = os.getenv("USE_8BIT_QUANTIZATION", "false").lower() == "true"
            
            # Build model loading configuration
            model_kwargs = {
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "device_map": "auto" if self.device == "cuda" else None,
                "token": hf_token,
            }
            
            # Add 8-bit quantization if enabled (GPU only)
            if use_8bit and self.device == "cuda":
                try:
                    from transformers import BitsAndBytesConfig
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_threshold=6.0,
                        llm_int8_has_fp16_weight=False,
                    )
                    model_kwargs["quantization_config"] = quantization_config
                    logger.info("   ✅ Using 8-bit quantization for memory efficiency")
                except ImportError as e:
                    logger.warning(f"   ⚠️  bitsandbytes not available: {e}")
                    logger.warning("   Continuing without quantization")
            elif use_8bit and self.device == "cpu":
                logger.warning("   ⚠️  8-bit quantization requested but not supported on CPU")
            
            # Load model with error handling
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    **model_kwargs,
                )
                
                # Set to evaluation mode
                self.model.eval()
                
                # Log memory usage if on GPU
                if self.device == "cuda":
                    allocated = torch.cuda.memory_allocated(0) / 1e9
                    reserved = torch.cuda.memory_reserved(0) / 1e9
                    logger.info(f"   GPU memory allocated: {allocated:.2f} GB")
                    logger.info(f"   GPU memory reserved: {reserved:.2f} GB")
                
                self._loaded = True
                logger.info("✅ Model loaded successfully")
                
            except Exception as model_load_error:
                logger.error(f"❌ Error loading model: {model_load_error}")
                
                # If GPU loading failed, try CPU fallback
                if self.device == "cuda":
                    logger.warning("   Attempting CPU fallback...")
                    self.device = "cpu"
                    model_kwargs["torch_dtype"] = torch.float32
                    model_kwargs["device_map"] = None
                    model_kwargs.pop("quantization_config", None)
                    
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        **model_kwargs,
                    )
                    self.model.eval()
                    self._loaded = True
                    logger.warning("✅ Model loaded on CPU (GPU fallback)")
                else:
                    raise
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            self._loaded = False
            raise
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._loaded
    
    def get_device(self) -> str:
        """Get current device"""
        return self.device
    
    def get_model_info(self) -> dict:
        """Get model and device information"""
        info = {
            "model": self.model_name,
            "device": self.device,
            "loaded": self._loaded,
        }
        
        if self.device == "cuda" and torch.cuda.is_available():
            info.update({
                "gpu_available": True,
                "gpu_name": torch.cuda.get_device_name(0),
                "gpu_memory_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 2),
            })
        else:
            info["gpu_available"] = False
            
        return info

