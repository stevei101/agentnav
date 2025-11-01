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

@app.get("/health", tags=["health"], response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        environment=os.getenv("ENVIRONMENT", "development")
    )

@app.get("/api/docs", tags=["docs"])
async def api_docs():
    """API documentation endpoint"""
    return {"docs_url": "/docs"}

