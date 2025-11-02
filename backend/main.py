"""
Agentic Navigator Backend - FastAPI Application
Development server with hot-reload support
Multi-agent system with ADK and A2A Protocol
"""
import os
import logging
from typing import Optional, Dict, Any
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


# Unified Analysis API - ADK Multi-Agent Orchestration
class AnalyzeRequest(BaseModel):
    """Request model for unified analysis endpoint"""
    document: str
    content_type: Optional[str] = None  # Auto-detected if not provided


class AnalyzeResponse(BaseModel):
    """Response model for unified analysis"""
    summary: str
    visualization: Dict[str, Any]
    agent_workflow: Dict[str, Any]
    processing_time: float
    generated_by: str = "adk_multi_agent"


@app.post("/api/analyze", tags=["agents"], response_model=AnalyzeResponse)
async def analyze_content(request: AnalyzeRequest):
    """
    Unified content analysis using ADK Multi-Agent System with SessionContext (FR#005)
    
    This endpoint orchestrates all agents (Orchestrator, Summarizer, Linker, Visualizer)
    using the Agent Development Kit (ADK) and Agent2Agent (A2A) Protocol.
    
    Implements the sequential workflow specified in FR#005:
    1. Creates SessionContext with raw_input
    2. Orchestrator analyzes content and delegates
    3. Summarizer updates SessionContext.summary_text
    4. Linker updates SessionContext.key_entities and relationships
    5. Visualizer updates SessionContext.graph_json
    6. Returns final SessionContext (summary + graph)
    
    SessionContext is persisted to Firestore after each agent step.
    """
    import time
    start_time = time.time()
    
    try:
        from agents import (
            AgentWorkflow, OrchestratorAgent, SummarizerAgent, 
            LinkerAgent, VisualizerAgent
        )
        from models.context_model import SessionContext
        
        logger.info("🎬 Starting ADK Multi-Agent Analysis (FR#005 Sequential Workflow)")
        
        # Step 1: Initialize SessionContext with raw_input
        session_context = SessionContext(
            session_id=f"session_{int(start_time)}",
            raw_input=request.document,
            content_type=request.content_type or "document",
            workflow_status="initializing"
        )
        
        logger.info(f"📋 Created SessionContext: {session_context.session_id}")
        
        # Step 2: Create agent workflow
        workflow = AgentWorkflow()
        
        # Initialize all agents
        orchestrator = OrchestratorAgent(workflow.a2a)
        summarizer = SummarizerAgent(workflow.a2a)
        linker = LinkerAgent(workflow.a2a)
        visualizer = VisualizerAgent(workflow.a2a)
        
        # Register agents with workflow
        workflow.register_agent(orchestrator)
        workflow.register_agent(summarizer) 
        workflow.register_agent(linker)
        workflow.register_agent(visualizer)
        
        # Step 3: Execute sequential workflow (FR#005)
        # This replaces the parallel execute_workflow with sequential execution
        session_context = await workflow.execute_sequential_workflow(session_context)
        
        # Step 4: Extract results from SessionContext
        summary = session_context.summary_text or "Analysis completed"
        
        # Use graph_json from SessionContext, or create fallback visualization
        visualization = session_context.graph_json or {
            "type": "MIND_MAP",
            "title": "Content Analysis",
            "nodes": [{"id": "root", "label": "Content", "group": "main"}],
            "edges": []
        }
        
        # Agent workflow status
        agent_workflow = {
            "session_id": session_context.session_id,
            "workflow_status": session_context.workflow_status,
            "completed_agents": session_context.completed_agents,
            "total_agents": len(workflow.agents),
            "errors": session_context.errors,
            "firestore_persisted": workflow.persistence_service is not None,
            "session_service_enabled": workflow.session_service is not None,
            "cache_service_enabled": workflow.cache_service is not None,
            "from_cache": session_context.workflow_status == "completed_from_cache"
        }
        
        processing_time = time.time() - start_time
        
        logger.info(f"🏁 ADK Multi-Agent Analysis completed in {processing_time:.2f}s")
        logger.info(f"   Summary: {len(summary)} chars")
        logger.info(f"   Entities: {len(session_context.key_entities)}")
        logger.info(f"   Relationships: {len(session_context.relationships)}")
        logger.info(f"   Graph nodes: {len(visualization.get('nodes', []))}")
        
        return AnalyzeResponse(
            summary=summary,
            visualization=visualization,
            agent_workflow=agent_workflow,
            processing_time=processing_time
        )
        
    except ImportError as e:
        logger.error(f"ADK agents not available: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=503,
            detail="ADK multi-agent system not available. Check agent implementations."
        )
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Multi-agent analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed after {processing_time:.2f}s: {str(e)}"
        )


# Legacy endpoints for backward compatibility

# Visualizer Agent Integration (Legacy)
class VisualizeRequest(BaseModel):
    """Request model for visualization (Legacy)"""
    document: str
    content_type: Optional[str] = "document"  # 'document' or 'codebase'


@app.post("/api/visualize", tags=["agents"], deprecated=True)
async def visualize_content(request: VisualizeRequest):
    """
    Generate visualization using Visualizer Agent (LEGACY)
    
    This endpoint is deprecated in favor of /api/analyze which provides
    complete multi-agent analysis. This endpoint will be removed in a future version.
    """
    try:
        from agents import VisualizerAgent, A2AProtocol
        
        # Create minimal A2A Protocol for standalone operation
        a2a = A2AProtocol()
        agent = VisualizerAgent(a2a)
        
        result = await agent.execute({
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


# Agent Status API
@app.get("/api/agents/status", tags=["agents"])
async def get_agent_status():
    """
    Get status of all available agents in the ADK system
    """
    try:
        from agents import (
            OrchestratorAgent, SummarizerAgent, LinkerAgent, VisualizerAgent, A2AProtocol
        )
        
        # Create temporary agents to check status
        a2a = A2AProtocol()
        agents = {
            "orchestrator": OrchestratorAgent(a2a),
            "summarizer": SummarizerAgent(a2a), 
            "linker": LinkerAgent(a2a),
            "visualizer": VisualizerAgent(a2a)
        }
        
        agent_status = {}
        for name, agent in agents.items():
            agent_status[name] = {
                "name": agent.name,
                "state": agent.state.value,
                "available": True,
                "execution_history_count": len(agent.execution_history)
            }
        
        return {
            "total_agents": len(agents),
            "agents": agent_status,
            "adk_system": "operational",
            "a2a_protocol": "enabled"
        }
        
    except ImportError as e:
        return {
            "total_agents": 0,
            "agents": {},
            "adk_system": "unavailable",
            "error": str(e)
        }


