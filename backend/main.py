"""
Agentic Navigator Backend - FastAPI Application
Development server with hot-reload support
"""
import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Navigator API",
    description="Multi-agent knowledge exploration system",
    version="0.1.0"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    environment: str

@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {"message": "Agentic Navigator API", "version": "0.1.0"}

@app.get("/health", tags=["health"], response_model=HealthResponse, deprecated=True)
async def health_check():
    """
    Health check endpoint (DEPRECATED)
    
    This endpoint is deprecated in favor of /healthz (Cloud Run standard).
    Please migrate to /healthz. This endpoint will be removed in a future version.
    """
    return HealthResponse(
        status="healthy",
        environment=os.getenv("ENVIRONMENT", "development")
    )

@app.get("/healthz", tags=["health"], response_model=HealthResponse)
async def healthz_check():
    """Health check endpoint (Cloud Run standard)"""
    return HealthResponse(
        status="healthy",
        environment=os.getenv("ENVIRONMENT", "development")
    )

@app.get("/api/docs", tags=["docs"])
async def api_docs():
    """API documentation endpoint"""
    return {"docs_url": "/docs"}


# Gemma Service Integration
# Endpoint to call Gemma GPU service for text generation

class GenerateRequest(BaseModel):
    """Request model for Gemma text generation"""
    prompt: str
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7


class GenerateResponse(BaseModel):
    """Response model for Gemma generation"""
    generated_text: str
    service_used: str = "gemma-gpu-service"


@app.post("/api/generate", tags=["agents"], response_model=GenerateResponse)
async def generate_text(request: GenerateRequest):
    """
    Generate text using Gemma GPU service
    
    This endpoint calls the Gemma GPU service deployed on Cloud Run.
    Requires GEMMA_SERVICE_URL environment variable to be set.
    """
    try:
        from services.gemma_service import generate_with_gemma
        
        text = await generate_with_gemma(
            prompt=request.prompt,
            max_tokens=request.max_tokens or 500,
            temperature=request.temperature or 0.7,
        )
        return GenerateResponse(generated_text=text)
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Gemma service client not available. Check your Python environment and ensure all dependencies are installed."
        )
    except Exception as e:
        logger.error(f"Gemma service error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Gemma service unavailable: {str(e)}. Check GEMMA_SERVICE_URL environment variable."
        )


# Visualizer Agent Integration
# Endpoint that uses Gemma GPU service for complex graph generation
class VisualizeRequest(BaseModel):
    """Request model for visualization"""
    document: str
    content_type: Optional[str] = "document"  # 'document' or 'codebase'


@app.post("/api/visualize", tags=["agents"])
async def visualize_content(request: VisualizeRequest):
    """
    Generate visualization using Visualizer Agent and Gemma GPU service
    
    This endpoint uses the Visualizer Agent which calls the Gemma GPU service
    to generate knowledge graphs (Mind Maps or Dependency Graphs).
    """
    try:
        from agents.visualizer_agent import VisualizerAgent
        
        agent = VisualizerAgent()
        result = await agent.process({
            "document": request.document,
            "content_type": request.content_type,
        })
        
        return result
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Visualizer Agent not available"
        )
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Visualization failed: {str(e)}"
        )

