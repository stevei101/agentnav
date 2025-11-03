"""
Gemma Service Client
HTTP client for calling the Gemma GPU service with support for WI-based authentication
Implements Workload Identity ID token fetching for Cloud Run service-to-service calls
"""

import os
import logging
from typing import Optional, List
import httpx

logger = logging.getLogger(__name__)


def _fetch_id_token(target_url: str) -> Optional[str]:
    """
    Fetch ID token from Cloud Run metadata server for Workload Identity authentication

    This function retrieves an ID token for service-to-service authentication
    in Cloud Run. In local development, this returns None (auth is disabled).

    Args:
        target_url: The URL of the target service (used as audience for the token)

    Returns:
        ID token string if available, None otherwise

    Raises:
        Exception: If token fetch fails in production (GCP environment)
    """
    # Check if running in GCP environment
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID")

    if not gcp_project:
        # Local development - no token needed
        logger.debug("Not in GCP environment, skipping ID token fetch")
        return None

    try:
        import requests

        # Fetch ID token from Cloud Run metadata server
        # The audience is the target service URL
        metadata_server = "http://metadata.google.internal/computeMetadata/v1"
        metadata_flavor = {"Metadata-Flavor": "Google"}

        # Construct token endpoint with target URL as audience
        token_url = f"{metadata_server}/instance/service-accounts/default/identity"
        params = {"audience": target_url}

        response = requests.get(
            token_url, headers=metadata_flavor, params=params, timeout=5.0
        )

        if response.status_code == 200:
            id_token = response.text
            logger.debug(f"✅ Successfully fetched ID token for {target_url}")
            return id_token
        else:
            error_msg = (
                f"Failed to fetch ID token: {response.status_code} {response.text}"
            )
            logger.warning(f"⚠️  {error_msg}")
            # In production, this is a critical failure
            # In development, allow graceful fallback
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise Exception(error_msg)
            return None

    except ImportError:
        logger.warning("⚠️  requests library not available, cannot fetch ID token")
        return None
    except Exception as e:
        error_msg = f"Error fetching ID token: {e}"
        logger.warning(f"⚠️  {error_msg}")
        # In production, fail if we can't get a token
        if os.getenv("ENVIRONMENT", "development") == "production":
            raise Exception(error_msg) from e
        return None


class GemmaServiceClient:
    """
    Client for interacting with Gemma GPU service

    Automatically handles Workload Identity authentication in Cloud Run environments
    by fetching and attaching ID tokens to requests.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "GEMMA_SERVICE_URL",
            "http://localhost:8080",  # Default for local development
        )
        self.timeout = float(os.getenv("GEMMA_SERVICE_TIMEOUT", "60.0"))
        self._id_token_cache: Optional[str] = None
        self._token_expiry: Optional[float] = None

    def _get_authorization_header(self) -> Optional[str]:
        """
        Get Authorization header with ID token for Cloud Run service-to-service auth

        Returns:
            Authorization header value (Bearer <token>) or None if not needed
        """
        # Check if authentication is required
        require_auth = os.getenv("REQUIRE_AUTH", "false").lower() == "true"

        if not require_auth:
            # Authentication disabled (local development)
            return None

        # Check if token is cached and still valid
        import time

        if self._id_token_cache and self._token_expiry:
            if time.time() < self._token_expiry:
                return f"Bearer {self._id_token_cache}"

        # Fetch new token
        id_token = _fetch_id_token(self.base_url)

        if id_token:
            self._id_token_cache = id_token
            # Cache for 55 minutes (tokens are valid for 1 hour)
            self._token_expiry = time.time() + (55 * 60)
            return f"Bearer {id_token}"

        return None

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

        try:
            # Get authorization header for Workload Identity
            auth_header = self._get_authorization_header()
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result["text"]

        except httpx.TimeoutException as e:
            logger.error("Gemma service timeout")
            raise Exception("Gemma service request timeout") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemma service error: {e.response.status_code}")
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

        try:
            # Get authorization header for Workload Identity
            auth_header = self._get_authorization_header()
            headers = {}
            if auth_header:
                headers["Authorization"] = auth_header

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
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
        return (
            embeddings_batch[0]
            if embeddings_batch and len(embeddings_batch) > 0
            else []
        )

    async def health_check(self) -> dict:
        """
        Check Gemma service health

        Returns:
            Health status information
        """
        url = f"{self.base_url}/healthz"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
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
