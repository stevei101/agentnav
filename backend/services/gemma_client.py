"""
Gemma Service Client
HTTP client for calling the Gemma GPU service with support for WI-based authentication
"""
import os
import logging
from typing import Optional, List
import httpx
import asyncio

logger = logging.getLogger(__name__)


async def get_cloud_run_id_token(audience: str) -> Optional[str]:
    """
    Fetch Cloud Run Workload Identity ID token for authenticating to other Cloud Run services
    
    This uses the Google Cloud metadata server to obtain an ID token that can be used
    to authenticate requests between Cloud Run services.
    
    Args:
        audience: The target service URL (e.g., https://gemma-service-xyz.run.app)
        
    Returns:
        ID token string, or None if not running on Cloud Run or if fetch fails
    """
    # Only attempt to fetch token if running on Cloud Run (GCP_PROJECT env is set)
    if not os.getenv("GCP_PROJECT") and not os.getenv("GOOGLE_CLOUD_PROJECT"):
        logger.debug("Not running on Cloud Run, skipping ID token fetch")
        return None
    
    metadata_server = "http://metadata.google.internal/computeMetadata/v1"
    token_url = f"{metadata_server}/instance/service-accounts/default/identity?audience={audience}"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                token_url,
                headers={"Metadata-Flavor": "Google"}
            )
            if response.status_code == 200:
                token = response.text
                logger.debug(f"Successfully fetched ID token (length: {len(token)})")
                return token
            else:
                logger.warning(f"Failed to fetch ID token: {response.status_code}")
                return None
    except Exception as e:
        logger.warning(f"Error fetching ID token: {e}")
        return None


class GemmaServiceClient:
    """Client for interacting with Gemma GPU service with Workload Identity authentication"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "GEMMA_SERVICE_URL",
            "http://localhost:8080"  # Default for local development
        )
        self.timeout = float(os.getenv("GEMMA_SERVICE_TIMEOUT", "60.0"))
        self._id_token_cache: Optional[str] = None
        self._id_token_expiry: float = 0
    
    async def _get_auth_headers(self) -> dict:
        """
        Get authentication headers with Workload Identity ID token
        
        Returns:
            Dictionary of headers to include in requests
        """
        headers = {}
        
        # Only fetch ID token if base_url is an HTTPS Cloud Run URL
        if self.base_url.startswith("https://") and ".run.app" in self.base_url:
            # Check if we need to refresh the token (tokens expire after ~1 hour)
            import time
            current_time = time.time()
            
            # Refresh if token is missing or expired (with 5 min buffer)
            if not self._id_token_cache or current_time >= (self._id_token_expiry - 300):
                token = await get_cloud_run_id_token(audience=self.base_url)
                if token:
                    self._id_token_cache = token
                    # Tokens typically expire after 1 hour
                    self._id_token_expiry = current_time + 3600
                    logger.debug("ID token refreshed")
            
            if self._id_token_cache:
                headers["Authorization"] = f"Bearer {self._id_token_cache}"
                logger.debug("Added Authorization header with ID token")
        else:
            logger.debug(f"Skipping ID token for non-Cloud-Run URL: {self.base_url}")
        
        return headers
    
    async def reason(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
    ) -> str:
        """
        Generate reasoning/text using Gemma service with optional context
        
        Args:
            prompt: Input prompt
            context: Optional additional context for reasoning
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling
            
        Returns:
            Generated text
        """
        url = f"{self.base_url}/reason"
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
        }
        if context is not None:
            payload["context"] = context
        
        # Get authentication headers
        auth_headers = await self._get_auth_headers()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=auth_headers)
                response.raise_for_status()
                result = response.json()
                return result["text"]
                
        except httpx.TimeoutException as e:
            logger.error("Gemma service timeout")
            raise Exception("Gemma service request timeout") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemma service error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Gemma service error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Error calling Gemma service: {e}")
            raise
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of text strings
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        url = f"{self.base_url}/embed"
        payload = {"texts": texts}
        
        # Get authentication headers
        auth_headers = await self._get_auth_headers()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=auth_headers)
                response.raise_for_status()
                result = response.json()
                return result["embeddings"]
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    # Legacy method names for backward compatibility
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
    ) -> str:
        """Generate text using Gemma service (legacy method, use reason() instead)"""
        return await self.reason(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
        )
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text (legacy method, use embed() instead)
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector (empty list if no embeddings)
        """
        embeddings_batch = await self.embed([text])
        return embeddings_batch[0] if embeddings_batch and len(embeddings_batch) > 0 else []
    
    async def health_check(self) -> dict:
        """
        Check Gemma service health
        
        Returns:
            Health status information
        """
        url = f"{self.base_url}/healthz"
        
        # Get authentication headers
        auth_headers = await self._get_auth_headers()
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=auth_headers)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.warning(f"Gemma service health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Global client instance (lazy initialization)
_gemma_client: Optional[GemmaServiceClient] = None


def get_gemma_client() -> GemmaServiceClient:
    """Get or create Gemma service client"""
    global _gemma_client
    if _gemma_client is None:
        _gemma_client = GemmaServiceClient()
    return _gemma_client


# Convenience functions
async def reason_with_gemma(
    prompt: str,
    context: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> str:
    """Generate reasoning text using Gemma (convenience function)"""
    client = get_gemma_client()
    return await client.reason(
        prompt=prompt,
        context=context,
        max_tokens=max_tokens,
        temperature=temperature,
    )


async def embed_with_gemma(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using Gemma (convenience function)"""
    client = get_gemma_client()
    return await client.embed(texts)


# Legacy function for backward compatibility
async def generate_with_gemma(
    prompt: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> str:
    """Generate text using Gemma (legacy function, use reason_with_gemma() instead)"""
    client = get_gemma_client()
    return await client.generate(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )

