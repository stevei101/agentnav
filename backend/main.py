"""
Agentic Navigator Backend - FastAPI Application
Development server with hot-reload support
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

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


# Gemma Service Integration Example
# Uncomment when Gemma service is deployed
# from services.gemma_service import generate_with_gemma

# @app.post("/api/generate", tags=["agents"])
# async def generate_text(prompt: str, max_tokens: int = 500):
#     """
#     Generate text using Gemma GPU service
#     Example integration endpoint
#     """
#     try:
#         text = await generate_with_gemma(
#             prompt=prompt,
#             max_tokens=max_tokens,
#         )
#         return {"generated_text": text}
#     except Exception as e:
#         from fastapi import HTTPException
#         raise HTTPException(status_code=503, detail=f"Gemma service unavailable: {str(e)}")

