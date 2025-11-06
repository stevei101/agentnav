"""
Workload Identity (WI) Authentication Service (Feature Request #335)

Implements Cloud Run service-to-service authentication using Workload Identity ID Tokens.
This provides credential-less, cryptographically-verifiable authentication for Cloud Run services.

Key Features:
- ID Token verification using Google's public keys
- Audience (aud) claim validation
- Service Account (sub) claim validation
- FastAPI dependency injection support
- Support for both production (Cloud Run) and development environments

Usage:
    from fastapi import Depends
    from services.workload_identity_auth import verify_workload_identity
    
    @app.get("/secure-endpoint")
    async def secure_endpoint(auth_info: dict = Depends(verify_workload_identity)):
        # auth_info contains validated token claims
        return {"message": "Authenticated"}
"""
import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, Header, Depends
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if authentication is required (disabled for local development)
REQUIRE_AUTH = os.getenv("REQUIRE_WI_AUTH", os.getenv("REQUIRE_AUTH", "false")).lower() == "true"

# Trusted service accounts (comma-separated list)
# In production, this should be set via environment variable or Secret Manager
TRUSTED_SERVICE_ACCOUNTS_ENV = os.getenv("TRUSTED_SERVICE_ACCOUNTS", "")


class WorkloadIdentityAuth:
    """
    Workload Identity authentication service for Cloud Run
    
    Validates ID tokens from other Cloud Run services using Google's public keys.
    """
    
    def __init__(self):
        self.require_auth = REQUIRE_AUTH
        self.trusted_service_accounts = self._load_trusted_accounts()
        self.expected_audience = self._get_expected_audience()
        
        logger.info(f"🔐 Workload Identity Auth initialized")
        logger.info(f"   Authentication required: {self.require_auth}")
        logger.info(f"   Trusted service accounts: {len(self.trusted_service_accounts)}")
        logger.info(f"   Expected audience: {self.expected_audience}")
    
    def _load_trusted_accounts(self) -> List[str]:
        """
        Load list of trusted Service Account emails
        
        Returns:
            List of trusted Service Account emails
        """
        if TRUSTED_SERVICE_ACCOUNTS_ENV:
            accounts = [acc.strip() for acc in TRUSTED_SERVICE_ACCOUNTS_ENV.split(",")]
            logger.info(f"✅ Loaded {len(accounts)} trusted accounts from environment")
            return accounts
        
        # Development fallback - allow all service accounts in the same project
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID") or "development"
        
        default_accounts = [
            f"agentnav-backend@{project_id}.iam.gserviceaccount.com",
            f"agentnav-frontend@{project_id}.iam.gserviceaccount.com",
            f"agentnav-gemma@{project_id}.iam.gserviceaccount.com",
            f"prompt-vault@{project_id}.iam.gserviceaccount.com",  # Prompt Vault service account
        ]
        
        # Only add dev account in development environment
        if os.getenv("ENVIRONMENT", "production") == "development":
            default_accounts.append("dev-service-account@development.iam.gserviceaccount.com")
        
        logger.warning(f"⚠️  Using default trusted accounts (configure via TRUSTED_SERVICE_ACCOUNTS)")
        return default_accounts
    
    def _get_expected_audience(self) -> Optional[str]:
        """
        Get the expected audience claim for ID token validation
        
        In Cloud Run, the audience should be the service URL.
        For development, this can be disabled.
        
        Returns:
            Expected audience string or None for development
        """
        # Check explicit environment variable
        audience = os.getenv("EXPECTED_AUDIENCE")
        if audience:
            return audience
        
        # Try to construct from Cloud Run service URL
        service_url = os.getenv("K_SERVICE")
        if service_url:
            # In Cloud Run, construct the full URL
            region = os.getenv("CLOUD_RUN_REGION", "us-central1")
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if project_id:
                return f"https://{service_url}-{region}.run.app"
        
        # Development mode - no audience validation
        logger.warning("⚠️  No audience configured - running in development mode")
        return None
    
    async def verify_id_token(
        self, 
        authorization: Optional[str] = Header(None)
    ) -> Dict[str, Any]:
        """
        Verify ID token from Authorization header
        
        Args:
            authorization: Authorization header value (Bearer <token>)
            
        Returns:
            Dictionary with validated token claims:
            {
                "email": "service-account@project.iam.gserviceaccount.com",
                "sub": "service-account-id",
                "aud": "expected-audience",
                "iss": "https://accounts.google.com",
                "exp": timestamp,
                "iat": timestamp
            }
            
        Raises:
            HTTPException: If authentication fails
        """
        # Authentication bypass for local development
        if not self.require_auth:
            logger.debug("⚠️  WI authentication disabled - development mode")
            return {
                "email": "dev-user@development.iam.gserviceaccount.com",
                "sub": "dev-123",
                "aud": "development",
                "iss": "development",
                "exp": 9999999999,
                "iat": 0,
                "development_mode": True
            }
        
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
            from google.oauth2 import id_token
            from google.auth.transport import requests
            
            # Verify the ID token
            request = requests.Request()
            
            # Decode and verify the token
            # This validates signature, expiration, and issuer
            id_info = id_token.verify_oauth2_token(
                token,
                request,
                audience=self.expected_audience  # Can be None for development
            )
            
            # Extract claims
            service_account_email = id_info.get("email")
            subject = id_info.get("sub")
            audience = id_info.get("aud")
            issuer = id_info.get("iss")
            expiry = id_info.get("exp")
            issued_at = id_info.get("iat")
            
            logger.debug(f"✅ ID token verified successfully")
            logger.debug(f"   Service Account: {service_account_email}")
            logger.debug(f"   Subject: {subject}")
            logger.debug(f"   Audience: {audience}")
            
            # Validate service account is trusted
            if not self._is_trusted_service_account(service_account_email):
                logger.warning(f"❌ Untrusted service account: {service_account_email}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Service account not authorized: {service_account_email}"
                )
            
            # Validate audience if expected
            if self.expected_audience and audience != self.expected_audience:
                logger.warning(f"❌ Invalid audience: {audience} (expected: {self.expected_audience})")
                raise HTTPException(
                    status_code=403,
                    detail=f"Invalid token audience: {audience}"
                )
            
            logger.info(f"✅ Authenticated service account: {service_account_email}")
            
            return {
                "email": service_account_email,
                "sub": subject,
                "aud": audience,
                "iss": issuer,
                "exp": expiry,
                "iat": issued_at
            }
            
        except ImportError:
            logger.error("❌ google-auth not installed - required for WI authentication")
            if self.require_auth:
                raise HTTPException(
                    status_code=500,
                    detail="Authentication system not available. Install google-auth."
                )
            # Development fallback
            return {
                "email": "dev-user@development.iam.gserviceaccount.com",
                "sub": "dev-123",
                "development_mode": True
            }
            
        except ValueError as e:
            # Token validation failed
            logger.error(f"❌ ID token validation failed: {e}")
            raise HTTPException(
                status_code=401,
                detail=f"Invalid ID token: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"❌ Unexpected error during authentication: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Authentication error: {str(e)}"
            )
    
    def _is_trusted_service_account(self, email: Optional[str]) -> bool:
        """
        Check if a service account email is trusted
        
        Args:
            email: Service account email
            
        Returns:
            True if trusted, False otherwise
        """
        if not email:
            return False
        
        # Check against trusted list
        is_trusted = email in self.trusted_service_accounts
        
        if not is_trusted:
            logger.warning(f"⚠️  Service account not in trusted list: {email}")
            logger.debug(f"   Trusted accounts: {self.trusted_service_accounts}")
        
        return is_trusted


# Singleton instance
_auth_service: Optional[WorkloadIdentityAuth] = None


def get_auth_service() -> WorkloadIdentityAuth:
    """
    Get or create singleton WorkloadIdentityAuth instance
    
    Returns:
        WorkloadIdentityAuth instance
    """
    global _auth_service
    
    if _auth_service is None:
        _auth_service = WorkloadIdentityAuth()
    
    return _auth_service


# FastAPI dependency for route protection
async def verify_workload_identity(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency for Workload Identity authentication
    
    Usage:
        @router.get("/secure-endpoint")
        async def secure_endpoint(
            auth_info: dict = Depends(verify_workload_identity)
        ):
            service_account = auth_info["email"]
            return {"authenticated_as": service_account}
    
    Args:
        authorization: Authorization header (automatically injected by FastAPI)
        
    Returns:
        Dictionary with authenticated identity information
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_service = get_auth_service()
    return await auth_service.verify_id_token(authorization)


# Optional: Require specific service accounts
def require_service_account(allowed_accounts: List[str]):
    """
    Create a dependency that requires specific service accounts
    
    Usage:
        @router.get("/admin-endpoint")
        async def admin_endpoint(
            auth_info: dict = Depends(require_service_account([
                "admin@project.iam.gserviceaccount.com"
            ]))
        ):
            return {"message": "Admin access granted"}
    
    Args:
        allowed_accounts: List of allowed service account emails
        
    Returns:
        FastAPI dependency function
    """
    async def _verify(auth_info: Dict[str, Any] = Depends(verify_workload_identity)):
        email = auth_info.get("email")
        if email not in allowed_accounts:
            logger.warning(f"❌ Service account not authorized: {email}")
            raise HTTPException(
                status_code=403,
                detail=f"Service account not authorized for this endpoint: {email}"
            )
        return auth_info
    
    return _verify
