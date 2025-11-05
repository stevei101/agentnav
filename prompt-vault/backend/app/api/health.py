"""Health check endpoints."""
from fastapi import APIRouter
from app.config import settings
from app.services.supabase_client import supabase_client
from app.services.firestore_client import firestore_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
    }


@router.get("/healthz")
async def healthz():
    """Cloud Run health check endpoint (required for Cloud Run)."""
    return {
        "status": "ok",
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service dependencies."""
    checks = {
        "service": {
            "status": "healthy",
            "name": settings.APP_NAME,
            "version": settings.VERSION,
        },
        "supabase": {
            "status": "available" if supabase_client.is_available() else "unavailable",
        },
        "firestore": {
            "status": "available" if firestore_client.is_available() else "unavailable",
        },
    }
    
    # Determine overall status
    overall_status = "healthy"
    if not supabase_client.is_available() or not firestore_client.is_available():
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "checks": checks,
    }

