"""
Gemma GPU Service - FastAPI Application
Serves Gemma model on Cloud Run with GPU acceleration and Workload Identity authentication
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List

from .model_loader import ModelLoader
from .inference import GemmaInference

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None
) -> bool:
    """
    Verify Workload Identity ID token for Cloud Run service-to-service authentication
    
    In production (Cloud Run), this verifies the JWT token from the caller.
    In development (local), authentication is disabled.
    
    Args:
        credentials: HTTP Bearer credentials from request header
        request: FastAPI request object
        
    Returns:
        True if authenticated, raises HTTPException if not
    """
    # Check if we're running on Cloud Run (production)
    # Cloud Run sets K_SERVICE environment variable
    is_cloud_run = os.getenv("K_SERVICE") is not None
    
    if not is_cloud_run:
        # Local development - skip authentication
        logger.debug("Running locally, skipping authentication")
        return True
    
    # In production, verify token if REQUIRE_AUTH is enabled
    require_auth = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
    
    if not require_auth:
        logger.debug("Authentication not required (REQUIRE_AUTH=false)")
        return True
    
    if not credentials:
        logger.warning("Missing authentication credentials")
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    token = credentials.credentials
    
    # In a full implementation, we would verify the JWT token here
    # For now, we just check that a token is present
    # TODO: Add full JWT verification using google.auth or similar
    if not token or len(token) < 10:
        logger.warning("Invalid token format")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    
    logger.debug("Token verification passed")
    return True

# Global model instance
# Note: These are set during lifespan startup and are read-only after initialization.
# The lifespan function ensures model loading completes before the app accepts requests,
# so race conditions during startup are not a concern for normal operation.
model_loader: Optional[ModelLoader] = None
inference_engine: Optional[GemmaInference] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown"""
    global model_loader, inference_engine
    
    # Startup: Load model
    try:
        model_name = os.getenv("MODEL_NAME", "google/gemma-7b-it")
        logger.info(f"🚀 Starting Gemma GPU Service")
        logger.info(f"   Model: {model_name}")
        
        model_loader = ModelLoader(model_name=model_name)
        model_loader.load_model()
        
        inference_engine = GemmaInference(
            model=model_loader.model,
            tokenizer=model_loader.tokenizer,
            device=model_loader.device,
        )
        
        logger.info("✅ Gemma service ready")
        
    except Exception as e:
        logger.error(f"❌ Failed to load model: {e}")
        raise
    
    yield
    
    # Shutdown: Cleanup
    logger.info("🛑 Shutting down Gemma service")
    model_loader = None
    inference_engine = None


# Create FastAPI app
app = FastAPI(
    title="Gemma GPU Service",
    description="GPU-accelerated Gemma model serving on Cloud Run",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ReasonRequest(BaseModel):
    """Request model for reasoning/text generation"""
    prompt: str = Field(..., description="Input prompt for generation")
    context: Optional[str] = Field(None, description="Additional context for reasoning")
    max_tokens: int = Field(500, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: int = Field(50, ge=1, le=100, description="Top-k sampling parameter")


class ReasonResponse(BaseModel):
    """Response model for reasoning/text generation"""
    text: str = Field(..., description="Generated text")
    tokens_generated: Optional[int] = Field(None, description="Number of tokens generated")
    model: str = Field(..., description="Model name used")
    device: str = Field(..., description="Device used (cuda/cpu)")


class EmbedRequest(BaseModel):
    """Request model for embedding generation (batch support)"""
    texts: List[str] = Field(..., description="Batch of text strings to generate embeddings for")


class EmbedResponse(BaseModel):
    """Response model for embeddings (batch support)"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model name used")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    model: str = Field(..., description="Model name")
    device: str = Field(..., description="Device (cuda/cpu)")
    gpu_available: bool = Field(..., description="GPU available")
    model_loaded: bool = Field(..., description="Model loaded")
    gpu_name: Optional[str] = Field(None, description="GPU name if available")
    gpu_memory_gb: Optional[float] = Field(None, description="GPU memory in GB if available")


# API Endpoints
@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "service": "Gemma GPU Service",
        "version": "0.1.0",
        "endpoints": ["/healthz", "/reason", "/embed"]
    }


@app.get("/healthz", tags=["health"], response_model=HealthResponse)
async def health_check():
    """
    Enhanced health check endpoint (Cloud Run requirement)
    Returns service status, GPU information, and model readiness
    
    Returns:
        503 if model is not loaded or not ready
        200 if model is loaded and ready for inference
    """
    if not model_loader:
        raise HTTPException(
            status_code=503, 
            detail="Model loader not initialized"
        )
    
    model_info = model_loader.get_model_info()
    
    # Check if model is actually loaded and ready
    if not model_info["loaded"]:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded - service starting up"
        )
    
    # Verify inference engine is ready
    if not inference_engine:
        raise HTTPException(
            status_code=503,
            detail="Inference engine not initialized"
        )
    
    # Additional CUDA readiness check if GPU is expected
    if model_info.get("gpu_available", False):
        try:
            import torch
            if not torch.cuda.is_available():
                logger.warning("GPU was available but is no longer accessible")
                model_info["gpu_available"] = False
        except Exception as e:
            logger.error(f"Error checking CUDA status: {e}")
            model_info["gpu_available"] = False
    
    return HealthResponse(
        status="healthy",
        model=model_info["model"],
        device=model_info["device"],
        gpu_available=model_info.get("gpu_available", False),
        model_loaded=model_info["loaded"],
        gpu_name=model_info.get("gpu_name"),
        gpu_memory_gb=model_info.get("gpu_memory_gb"),
    )


@app.post("/reason", tags=["inference"], response_model=ReasonResponse)
async def reason(
    request: ReasonRequest,
    authenticated: bool = Depends(verify_token)
):
    """
    Generate reasoning/text using Gemma model with optional context
    
    Requires authentication when running on Cloud Run with REQUIRE_AUTH=true
    
    Args:
        request: Reasoning parameters including prompt and optional context
        authenticated: Authentication status (injected by dependency)
        
    Returns:
        Generated text
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Combine prompt with context if provided
        full_prompt = request.prompt
        if request.context:
            full_prompt = f"Context: {request.context}\n\nPrompt: {request.prompt}"
        
        generated_text = inference_engine.generate(
            prompt=full_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
        )
        
        # Estimate tokens (simple approximation)
        # Rough multiplier: average token length ~1.3 words (language-dependent)
        TOKEN_ESTIMATION_MULTIPLIER = 1.3
        tokens_generated = len(generated_text.split()) * TOKEN_ESTIMATION_MULTIPLIER
        
        return ReasonResponse(
            text=generated_text,
            tokens_generated=int(tokens_generated),
            model=model_loader.model_name,
            device=model_loader.device,
        )
        
    except Exception as e:
        logger.error(f"Reasoning error: {e}")
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")


@app.post("/embed", tags=["inference"], response_model=EmbedResponse)
async def embed(
    request: EmbedRequest,
    authenticated: bool = Depends(verify_token)
):
    """
    Generate embeddings for a batch of text strings
    
    Requires authentication when running on Cloud Run with REQUIRE_AUTH=true
    
    Args:
        request: Batch of texts to embed
        authenticated: Authentication status (injected by dependency)
        
    Returns:
        List of embedding vectors
    """
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Generate embeddings for each text in the batch
        all_embeddings = []
        for text in request.texts:
            embeddings = inference_engine.generate_embeddings(text)
            all_embeddings.append(embeddings)
        
        # All embeddings should have the same dimension
        dimension = len(all_embeddings[0]) if all_embeddings else 0
        
        return EmbedResponse(
            embeddings=all_embeddings,
            dimension=dimension,
            model=model_loader.model_name,
        )
        
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


# Cloud Run compatibility: Read PORT from environment
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info",
    )

