"""
Prompt Loader Service
Loads and caches agent prompts from Firestore
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional

from .firestore_client import get_firestore_client

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL_SECONDS = 300  # 5 minutes


class PromptCache:
    """In-memory cache for prompts with TTL (thread-safe)"""

    def __init__(self, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        """
        Get cached value if not expired (thread-safe)

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/not found
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if datetime.now() > entry["expires_at"]:
                # Cache expired
                del self._cache[key]
                logger.debug(f"Cache expired for: {key}")
                return None

            return entry["value"]

    def set(self, key: str, value: str):
        """
        Store value in cache with expiration (thread-safe)

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expires_at": datetime.now() + timedelta(seconds=self.ttl_seconds),
            }
        logger.debug(f"Cached prompt: {key} (TTL: {self.ttl_seconds}s)")

    def clear(self):
        """Clear all cached entries (thread-safe)"""
        with self._lock:
            self._cache.clear()
        logger.info("Prompt cache cleared")

    def invalidate(self, key: str):
        """
        Remove specific entry from cache (thread-safe)

        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Invalidated cache for: {key}")


class PromptLoaderService:
    """
    Service for loading agent prompts from Firestore with caching

    Provides high-performance prompt loading with in-memory caching
    to reduce Firestore read operations.
    """

    def __init__(self, cache_ttl_seconds: int = CACHE_TTL_SECONDS):
        """
        Initialize PromptLoaderService

        Args:
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.firestore_client = get_firestore_client()
        self.cache = PromptCache(ttl_seconds=cache_ttl_seconds)
        self.collection_name = "agent_prompts"

    def get_prompt(self, prompt_id: str) -> str:
        """
        Load a prompt by ID from Firestore (with caching)

        Args:
            prompt_id: Document ID in agent_prompts collection

        Returns:
            Prompt text

        Raises:
            Exception: If prompt not found or Firestore error

        Note:
            Results are cached for CACHE_TTL_SECONDS to reduce Firestore reads.
            If Firestore is unavailable, this will raise an exception.
        """
        # Check cache first
        cached_prompt = self.cache.get(prompt_id)
        if cached_prompt is not None:
            logger.debug(f"Cache hit for prompt: {prompt_id}")
            return cached_prompt

        # Cache miss - load from Firestore
        logger.info(f"Loading prompt from Firestore: {prompt_id}")
        try:
            doc_ref = self.firestore_client.get_document(
                self.collection_name, prompt_id
            )
            doc = doc_ref.get()

            if not doc.exists:
                error_msg = f"Prompt not found: {prompt_id}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Extract prompt text
            data = doc.to_dict()
            prompt_text = data.get("prompt_text", "")

            if not prompt_text:
                error_msg = f"Prompt has empty prompt_text: {prompt_id}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Cache the result
            self.cache.set(prompt_id, prompt_text)

            logger.info(f"Successfully loaded prompt: {prompt_id}")
            return prompt_text

        except Exception as e:
            logger.error(f"Error loading prompt {prompt_id}: {e}")
            raise

    def reload_prompt(self, prompt_id: str) -> str:
        """
        Force reload a prompt from Firestore (bypass cache)

        Args:
            prompt_id: Document ID in agent_prompts collection

        Returns:
            Prompt text
        """
        # Invalidate cache first
        self.cache.invalidate(prompt_id)

        # Load fresh from Firestore
        return self.get_prompt(prompt_id)

    def clear_cache(self):
        """Clear all cached prompts"""
        self.cache.clear()

    def invalidate_cache(self, prompt_id: str):
        """
        Invalidate cache for a specific prompt

        Args:
            prompt_id: Document ID to invalidate
        """
        self.cache.invalidate(prompt_id)


# Global service instance
_prompt_loader: Optional[PromptLoaderService] = None


def get_prompt_loader() -> PromptLoaderService:
    """
    Get or create the global PromptLoaderService singleton

    Returns:
        PromptLoaderService instance
    """
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoaderService()
    return _prompt_loader


def get_prompt(prompt_id: str) -> str:
    """
    Convenience function to load a prompt

    Args:
        prompt_id: Document ID in agent_prompts collection

    Returns:
        Prompt text
    """
    return get_prompt_loader().get_prompt(prompt_id)
