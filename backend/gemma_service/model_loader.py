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
        """Detect available device (CUDA or CPU)"""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"   CUDA version: {torch.version.cuda}")
            logger.info(f"   GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        else:
            device = "cpu"
            logger.warning("⚠️  No GPU detected, falling back to CPU")
        return device
    
    def load_model(self):
        """Load Gemma model and tokenizer"""
        if self._loaded:
            logger.info("Model already loaded")
            return
            
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            logger.info(f"🔄 Loading model: {self.model_name}")
            logger.info(f"   Device: {self.device}")
            
            # Get Hugging Face token (only use if not dummy/placeholder)
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            if hf_token and hf_token.strip() and hf_token.lower() not in ["dummy-token-value", "placeholder", ""]:
                logger.info("   Using Hugging Face token for authentication")
                token_kwargs = {"token": hf_token}
            else:
                logger.warning("   No valid Hugging Face token found - model may require authentication")
                token_kwargs = {}
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                **token_kwargs
            )
            
            # Load model with GPU support
            model_kwargs = {
                "torch_dtype": torch.float16 if self.device == "cuda" else torch.float32,
                "device_map": "auto" if self.device == "cuda" else None,
            }
            model_kwargs.update(token_kwargs)  # Add token if available
            
            # Use 8-bit quantization if memory constrained (optional)
            if os.getenv("USE_8BIT_QUANTIZATION", "false").lower() == "true":
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0
                )
                model_kwargs["quantization_config"] = quantization_config
                logger.info("   Using 8-bit quantization")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            # When device_map="auto" is used, model placement is handled automatically
            # No need to manually move to device in that case
            
            # Set to evaluation mode
            self.model.eval()
            
            self._loaded = True
            logger.info("✅ Model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
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

