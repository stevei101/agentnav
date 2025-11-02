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

# Import WebSocket streaming routes (FR#020)
from routes.stream_routes import router as stream_router

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

# Include WebSocket streaming routes (FR#020 - Interactive Agent Dashboard)
app.include_router(stream_router)

class HealthResponse(BaseModel):
    status: str
    environment: str
    adk_system: Optional[str] = None
    firestore: Optional[str] = None
    errors: Optional[Dict[str, str]] = None

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
    return await healthz_check()

@app.get("/healthz", tags=["health"], response_model=HealthResponse)
async def healthz_check():
    """
    Health check endpoint (Cloud Run standard)
    
    Checks backend health and ADK system dependencies:
    - Basic service availability
    - ADK agent system status
    - Firestore connectivity
    """
    environment = os.getenv("ENVIRONMENT", "development")
    health_status = "healthy"
    adk_status = None
    firestore_status = None
    errors = {}
    
    # Check ADK System availability
    try:
        from agents import (
            OrchestratorAgent, A2AProtocol
        )
        
        # Lightweight check - just verify imports work
        # Don't instantiate agents on every health check (expensive)
        if OrchestratorAgent and A2AProtocol:
            adk_status = "operational"
            logger.debug("✅ ADK system check passed")
        else:
            adk_status = "degraded"
            errors["adk"] = "Agent classes not available"
            
    except ImportError as e:
        adk_status = "unavailable"
        error_msg = f"ADK agents not available: {str(e)}"
        errors["adk"] = error_msg
        logger.error(f"❌ ADK system check failed: {error_msg}")
        health_status = "degraded"
        
    except Exception as e:
        adk_status = "error"
        error_msg = f"ADK system error: {str(e)}"
        errors["adk"] = error_msg
        logger.error(f"❌ ADK system check failed: {error_msg}")
        health_status = "degraded"
    
    # Check Firestore connectivity (optional - may not be required for basic health)
    try:
        from services.firestore_client import get_firestore_client
        
        firestore_client = get_firestore_client()
        # Simple connectivity test - just check if client was created
        if firestore_client:
            firestore_status = "connected"
            logger.debug("✅ Firestore connectivity check passed")
        else:
            firestore_status = "disconnected"
            errors["firestore"] = "Firestore client not initialized"
            
    except Exception as e:
        firestore_status = "error"
        error_msg = f"Firestore connectivity error: {str(e)}"
        errors["firestore"] = error_msg
        logger.warning(f"⚠️  Firestore connectivity check failed: {error_msg}")
        # Firestore failure doesn't necessarily mean unhealthy if ADK can work without it
    
    # Determine overall health status
    if adk_status == "unavailable" or adk_status == "error":
        health_status = "unhealthy"
    
    return HealthResponse(
        status=health_status,
        environment=environment,
        adk_system=adk_status,
        firestore=firestore_status,
        errors=errors if errors else None
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
    
    Returns detailed status including agent availability, ADK system status,
    and diagnostic information for troubleshooting.
    """
    diagnostic_info = {
        "import_errors": [],
        "initialization_errors": [],
        "environment_vars": {}
    }
    
    # Check required environment variables
    required_env_vars = ["FIRESTORE_PROJECT_ID", "FIRESTORE_DATABASE_ID"]
    for var in required_env_vars:
        value = os.getenv(var)
        diagnostic_info["environment_vars"][var] = "set" if value else "missing"
    
    try:
        from agents import (
            OrchestratorAgent, SummarizerAgent, LinkerAgent, VisualizerAgent, A2AProtocol
        )
        
        logger.info("🔍 Checking ADK agent system status...")
        
        # Create temporary agents to check status
        try:
            a2a = A2AProtocol()
            diagnostic_info["a2a_protocol"] = "initialized"
        except Exception as e:
            diagnostic_info["initialization_errors"].append(f"A2A Protocol initialization failed: {str(e)}")
            logger.error(f"❌ A2A Protocol initialization failed: {e}")
            return {
                "total_agents": 0,
                "agents": {},
                "adk_system": "unavailable",
                "a2a_protocol": "error",
                "diagnostics": diagnostic_info,
                "error": f"A2A Protocol initialization failed: {str(e)}"
            }
        
        agents = {}
        agent_errors = []
        
        # Test each agent individually to identify specific failures
        agent_classes = {
            "orchestrator": OrchestratorAgent,
            "summarizer": SummarizerAgent, 
            "linker": LinkerAgent,
            "visualizer": VisualizerAgent
        }
        
        for name, agent_class in agent_classes.items():
            try:
                agent = agent_class(a2a)
                agents[name] = agent
                logger.debug(f"✅ {name} agent initialized successfully")
            except Exception as e:
                error_msg = f"{name} agent initialization failed: {str(e)}"
                agent_errors.append(error_msg)
                diagnostic_info["initialization_errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        if not agents:
            return {
                "total_agents": 0,
                "agents": {},
                "adk_system": "unavailable",
                "a2a_protocol": "enabled" if a2a else "disabled",
                "diagnostics": diagnostic_info,
                "error": "All agent initializations failed. Check diagnostic_info for details.",
                "agent_errors": agent_errors
            }
        
        # Get status for successfully initialized agents
        agent_status = {}
        for name, agent in agents.items():
            try:
                agent_status[name] = {
                    "name": agent.name,
                    "state": agent.state.value,
                    "available": True,
                    "execution_history_count": len(agent.execution_history)
                }
            except Exception as e:
                agent_status[name] = {
                    "name": name,
                    "state": "error",
                    "available": False,
                    "error": str(e)
                }
        
        # Check Firestore connectivity if agents use it
        try:
            from services.firestore_client import get_firestore_client
            firestore_client = get_firestore_client()
            if firestore_client:
                firestore_status = "connected"
            else:
                firestore_status = "disconnected"
        except Exception as e:
            firestore_status = f"error: {str(e)}"
            diagnostic_info["initialization_errors"].append(f"Firestore check failed: {str(e)}")
        
        response = {
            "total_agents": len(agents),
            "agents": agent_status,
            "adk_system": "operational" if len(agents) == len(agent_classes) else "degraded",
            "a2a_protocol": "enabled",
            "firestore_status": firestore_status
        }
        
        # Include diagnostics if there were any issues
        if agent_errors or diagnostic_info["initialization_errors"]:
            response["diagnostics"] = diagnostic_info
            response["warnings"] = f"{len(agent_errors)} agent(s) failed to initialize"
        
        logger.info(f"✅ ADK status check complete: {response['adk_system']}, {len(agents)}/{len(agent_classes)} agents available")
        return response
        
    except ImportError as e:
        error_msg = f"Failed to import ADK agents: {str(e)}"
        diagnostic_info["import_errors"].append(error_msg)
        logger.error(f"❌ Import error: {error_msg}")
        import traceback
        diagnostic_info["import_traceback"] = traceback.format_exc()
        
        return {
            "total_agents": 0,
            "agents": {},
            "adk_system": "unavailable",
            "a2a_protocol": "unknown",
            "diagnostics": diagnostic_info,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error checking agent status: {str(e)}"
        logger.error(f"❌ Unexpected error: {error_msg}")
        import traceback
        diagnostic_info["unexpected_error"] = error_msg
        diagnostic_info["traceback"] = traceback.format_exc()
        
        return {
            "total_agents": 0,
            "agents": {},
            "adk_system": "error",
            "diagnostics": diagnostic_info,
            "error": error_msg
        }


