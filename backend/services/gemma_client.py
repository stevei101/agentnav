"""
Gemma Service Client
HTTP client for calling the Gemma GPU service with support for WI-based authentication
"""
import os
import logging
from typing import Optional, List
import httpx

logger = logging.getLogger(__name__)


class GemmaServiceClient:
    """Client for interacting with Gemma GPU service"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv(
            "GEMMA_SERVICE_URL",
            "http://localhost:8080"  # Default for local development
        )
        self.timeout = float(os.getenv("GEMMA_SERVICE_TIMEOUT", "60.0"))
    
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
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
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
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
            Embedding vector
        """
        embeddings_batch = await self.embed([text])
        return embeddings_batch[0] if embeddings_batch else []
    
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

