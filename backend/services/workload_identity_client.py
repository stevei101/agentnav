"""
Workload Identity Client for Cloud Run (Feature Request #335)

Client utility for fetching ID tokens and making authenticated service-to-service calls.
This is used by services (like Prompt Vault) that need to call other Cloud Run services
(like Agent Navigator Backend) with Workload Identity authentication.

Key Features:
- Automatic ID token fetching using Cloud Run metadata service
- Token caching with automatic refresh
- Helper methods for authenticated HTTP requests
- Support for both production (Cloud Run) and development environments

Usage:
    from services.workload_identity_client import get_id_token_for_audience, call_service
    
    # Get ID token for a service
    token = await get_id_token_for_audience("https://backend-service.run.app")
    
    # Make authenticated request
    response = await call_service(
        url="https://backend-service.run.app/api/prompts",
        method="GET"
    )
"""
import os
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)

# Token cache with expiry
_token_cache: Dict[str, Dict[str, Any]] = {}


class WorkloadIdentityClient:
    """
    Client for fetching ID tokens and making authenticated requests
    """
    
    def __init__(self):
        self.metadata_server = "http://metadata.google.internal/computeMetadata/v1"
        self.metadata_flavor = {"Metadata-Flavor": "Google"}
        self.is_cloud_run = bool(os.getenv("K_SERVICE"))
        
        logger.info(f"🔐 Workload Identity Client initialized")
        logger.info(f"   Running on Cloud Run: {self.is_cloud_run}")
    
    async def get_id_token(self, audience: str) -> str:
        """
        Get ID token for the specified audience
        
        In Cloud Run, this fetches an ID token from the metadata service.
        In development, this returns a mock token.
        
        Args:
            audience: Target service URL (e.g., "https://backend-service.run.app")
            
        Returns:
            ID token string
            
        Raises:
            RuntimeError: If token fetching fails
        """
        # Check cache first
        cached_token = self._get_cached_token(audience)
        if cached_token:
            logger.debug(f"✅ Using cached ID token for audience: {audience}")
            return cached_token
        
        # Development mode - return mock token
        if not self.is_cloud_run:
            logger.warning(f"⚠️  Development mode - using mock ID token")
            # Use hash of audience to avoid leaking service URLs in logs
            import hashlib
            audience_hash = hashlib.sha256(audience.encode()).hexdigest()[:16]
            mock_token = f"dev_token_{audience_hash}"
            self._cache_token(audience, mock_token, expires_in=3600)
            return mock_token
        
        try:
            # Fetch ID token from Cloud Run metadata service
            token_url = (
                f"{self.metadata_server}/instance/service-accounts/default/identity"
                f"?audience={audience}"
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    token_url,
                    headers=self.metadata_flavor,
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Failed to fetch ID token: {response.status_code} {response.text}"
                    )
                
                token = response.text.strip()
                
                # Cache token (tokens typically valid for 1 hour)
                # We cache for 55 minutes to ensure refresh before expiry
                self._cache_token(audience, token, expires_in=3300)
                
                logger.info(f"✅ Fetched ID token for audience: {audience}")
                return token
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch ID token: {e}")
            raise RuntimeError(f"Failed to fetch ID token: {e}")
    
    async def call_service(
        self,
        url: str,
        method: str = "GET",
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ) -> httpx.Response:
        """
        Make an authenticated request to another Cloud Run service
        
        Args:
            url: Target service URL
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            json: JSON payload for request body
            data: Form data for request body
            headers: Additional headers
            timeout: Request timeout in seconds
            
        Returns:
            httpx.Response object
            
        Raises:
            httpx.HTTPError: If request fails
        """
        # Extract base URL for audience
        # audience should be just the base URL without path
        from urllib.parse import urlparse
        parsed = urlparse(url)
        audience = f"{parsed.scheme}://{parsed.netloc}"
        
        # Get ID token for the service
        id_token = await self.get_id_token(audience)
        
        # Prepare headers
        request_headers = headers or {}
        request_headers["Authorization"] = f"Bearer {id_token}"
        
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                json=json,
                data=data,
                headers=request_headers,
                timeout=timeout
            )
            
            logger.info(f"📡 {method} {url} -> {response.status_code}")
            
            return response
    
    def _get_cached_token(self, audience: str) -> Optional[str]:
        """
        Get cached token if available and not expired
        
        Args:
            audience: Token audience
            
        Returns:
            Cached token or None
        """
        if audience not in _token_cache:
            return None
        
        cache_entry = _token_cache[audience]
        
        # Check if token is expired
        if time.time() > cache_entry["expires_at"]:
            logger.debug(f"🕐 Cached token expired for audience: {audience}")
            del _token_cache[audience]
            return None
        
        return cache_entry["token"]
    
    def _cache_token(self, audience: str, token: str, expires_in: int):
        """
        Cache token with expiry
        
        Args:
            audience: Token audience
            token: ID token
            expires_in: Seconds until expiry
        """
        _token_cache[audience] = {
            "token": token,
            "expires_at": time.time() + expires_in
        }
        logger.debug(f"💾 Cached ID token for audience: {audience} (expires in {expires_in}s)")


# Singleton instance
_client: Optional[WorkloadIdentityClient] = None


def get_wi_client() -> WorkloadIdentityClient:
    """
    Get or create singleton WorkloadIdentityClient instance
    
    Returns:
        WorkloadIdentityClient instance
    """
    global _client
    
    if _client is None:
        _client = WorkloadIdentityClient()
    
    return _client


# Convenience functions
async def get_id_token_for_audience(audience: str) -> str:
    """
    Get ID token for the specified audience
    
    Convenience function that uses the singleton client.
    
    Args:
        audience: Target service URL (e.g., "https://backend-service.run.app")
        
    Returns:
        ID token string
        
    Raises:
        RuntimeError: If token fetching fails
    """
    client = get_wi_client()
    return await client.get_id_token(audience)


async def call_service(
    url: str,
    method: str = "GET",
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> httpx.Response:
    """
    Make an authenticated request to another Cloud Run service
    
    Convenience function that uses the singleton client.
    
    Args:
        url: Target service URL
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        json: JSON payload for request body
        data: Form data for request body
        headers: Additional headers
        timeout: Request timeout in seconds
        
    Returns:
        httpx.Response object
        
    Raises:
        httpx.HTTPError: If request fails
    """
    client = get_wi_client()
    return await client.call_service(
        url=url,
        method=method,
        json=json,
        data=data,
        headers=headers,
        timeout=timeout
    )
