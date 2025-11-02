"""
JWT Authentication for Gemma Service
Implements Workload Identity authentication for Cloud Run service-to-service calls
"""
import os
import logging
from typing import Optional
from fastapi import HTTPException, Header

logger = logging.getLogger(__name__)

# Check if authentication is required (disabled for local development)
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"

# For local development, authentication is disabled by default
# Set REQUIRE_AUTH=true in production to enable JWT verification


def verify_jwt_token(authorization: Optional[str] = Header(None)) -> bool:
    """
    Verify JWT token from Authorization header for Workload Identity authentication
    
    In Cloud Run, this uses google-auth to verify tokens from other Cloud Run services
    or Workload Identity Federation. For local development, authentication is bypassed.
    
    Args:
        authorization: Authorization header value (Bearer <token>)
        
    Returns:
        True if authentication passes or is disabled
        
    Raises:
        HTTPException: If authentication is required and token is invalid
    """
    # Authentication bypass for local development
    if not REQUIRE_AUTH:
        return True
    
    # Check if Authorization header is present
    if not authorization:
        logger.warning("❌ Missing Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Missing Authorization header."
        )
    
    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        logger.warning("❌ Invalid Authorization header format")
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'."
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    if not token:
        logger.warning("❌ Empty token in Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Empty token in Authorization header."
        )
    
    try:
        # Import google-auth for JWT verification
        from google.auth import jwt
        from google.auth.transport import requests
        
        # Verify JWT token
        # In production, this would verify against GCP project's expected audience
        # For Workload Identity, we verify the token issuer and audience
        try:
            # For Cloud Run service-to-service, verify the token
            # The audience should match the service URL
            request = requests.Request()
            
            # Verify token (this validates signature, expiration, issuer, etc.)
            # For Cloud Run service-to-service, verify against GCP project
            gcp_project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID")
            
            # Get expected audience from environment variable
            expected_audience = os.getenv("GEMMA_SERVICE_URL")
            if REQUIRE_AUTH and not expected_audience:
                logger.error("❌ GEMMA_SERVICE_URL environment variable not set; cannot verify JWT audience")
                raise HTTPException(
                    status_code=500,
                    detail="Server misconfiguration: GEMMA_SERVICE_URL not set for JWT audience validation."
                )
            
            # Verify JWT token with proper audience
            # For Workload Identity, the audience is the service URL
            # For Cloud Run, we verify the token issuer and audience
            verified_token = jwt.decode(
                token,
                request=request,
                verify=True,  # Enable verification in production
                audience=expected_audience,  # Validate against expected service URL
                issuer=f"https://accounts.google.com" if gcp_project_id else None
            )
            
            # Log authentication success (without sensitive token data)
            logger.debug(f"✅ JWT token verified for issuer: {verified_token.get('iss', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ JWT verification failed: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"JWT token verification failed: {str(e)}"
            )
            
    except ImportError:
        logger.warning("⚠️  google-auth not installed, skipping JWT verification")
        # If google-auth is not available, allow request but log warning
        # In production, ensure google-auth is installed
        return True
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )

