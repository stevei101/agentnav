"""
Knowledge Cache Service
Manages knowledge cache in Firestore 'knowledge_cache/' collection
Implements content hash-based caching to avoid redundant processing
"""

import hashlib
import logging
import time
from typing import Optional, Dict, Any
from google.cloud.firestore import Increment

logger = logging.getLogger(__name__)


class KnowledgeCacheService:
    """
    Service for managing knowledge cache in Firestore

    Stores cached analysis results in the 'knowledge_cache/' collection.
    Uses content hash (SHA256) as document ID to enable fast cache lookups.
    Implements TTL-based expiration to manage storage costs.
    """

    def __init__(self, firestore_client=None, default_ttl_hours: int = 168):
        """
        Initialize knowledge cache service

        Args:
            firestore_client: Optional Firestore client (will get default if not provided)
            default_ttl_hours: Default time-to-live in hours (default: 168 = 1 week)
        """
        self.firestore_client = firestore_client
        self._collection_name = "knowledge_cache"
        self.default_ttl_hours = default_ttl_hours

    def _get_client(self):
        """Get Firestore client (lazy initialization)"""
        if self.firestore_client is None:
            from services.firestore_client import get_firestore_client

            self.firestore_client = get_firestore_client()
        return self.firestore_client

    def generate_content_hash(
        self, content: str, content_type: str = "document"
    ) -> str:
        """
        Generate SHA256 hash for content

        Args:
            content: Content to hash
            content_type: Type of content (included in hash for differentiation)

        Returns:
            Hexadecimal hash string
        """
        # Combine content and type for hash to differentiate same text analyzed differently
        hash_input = f"{content_type}:{content}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    async def check_cache(
        self, content: str, content_type: str = "document"
    ) -> Optional[Dict[str, Any]]:
        """
        Check if cached result exists for content

        Args:
            content: Content to check
            content_type: Type of content

        Returns:
            Cached result dictionary if found and not expired, None otherwise
        """
        try:
            content_hash = self.generate_content_hash(content, content_type)

            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, content_hash)
            doc = doc_ref.get()

            if not doc.exists:
                logger.info(f"🔍 Cache MISS: {content_hash[:16]}...")
                return None

            cached_data = doc.to_dict()

            # Check if cache entry has expired
            expires_at = cached_data.get("expires_at")
            if expires_at and expires_at < time.time():
                logger.info(f"⏰ Cache EXPIRED: {content_hash[:16]}...")
                # Delete expired entry
                await self.delete_cache_entry(content_hash)
                return None

            logger.info(f"✅ Cache HIT: {content_hash[:16]}...")
            logger.debug(f"   Cached at: {cached_data.get('created_at')}")

            return cached_data

        except Exception as e:
            logger.error(f"❌ Failed to check cache: {e}")
            return None

    async def store_cache(
        self,
        content: str,
        content_type: str,
        summary: str,
        visualization_data: Dict[str, Any],
        key_entities: list = None,
        relationships: list = None,
        ttl_hours: Optional[int] = None,
    ) -> bool:
        """
        Store analysis results in cache

        Args:
            content: Original content
            content_type: Type of content
            summary: Generated summary
            visualization_data: Visualization graph JSON
            key_entities: Optional list of key entities
            relationships: Optional list of relationships
            ttl_hours: Time-to-live in hours (uses default if not specified)

        Returns:
            True if successful, False otherwise
        """
        try:
            content_hash = self.generate_content_hash(content, content_type)
            ttl = ttl_hours or self.default_ttl_hours

            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, content_hash)

            # Calculate expiration time
            current_time = time.time()
            expires_at = current_time + (ttl * 3600)  # Convert hours to seconds

            cache_data = {
                "content_hash": content_hash,
                "content_type": content_type,
                "summary": summary,
                "visualization_data": visualization_data,
                "key_entities": key_entities or [],
                "relationships": relationships or [],
                "created_at": current_time,
                "expires_at": expires_at,
                "ttl_hours": ttl,
                "hit_count": 0,  # Track cache hits
            }

            doc_ref.set(cache_data)

            logger.info(f"💾 Stored in cache: {content_hash[:16]}...")
            logger.debug(f"   TTL: {ttl} hours")
            logger.debug(f"   Expires at: {expires_at}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to store in cache: {e}")
            logger.warning("⚠️  Continuing without caching")
            return False

    async def increment_hit_count(self, content_hash: str) -> bool:
        """
        Increment hit count for cache entry

        Args:
            content_hash: Hash of the cached content

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, content_hash)

            # Increment hit count atomically
            doc_ref.update({"hit_count": Increment(1)})

            logger.debug(f"📊 Incremented hit count for {content_hash[:16]}...")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to increment hit count: {e}")
            return False

    async def delete_cache_entry(self, content_hash: str) -> bool:
        """
        Delete cache entry from Firestore

        Args:
            content_hash: Hash of the content to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            client = self._get_client()
            doc_ref = client.get_document(self._collection_name, content_hash)
            doc_ref.delete()

            logger.info(f"🗑️  Deleted cache entry: {content_hash[:16]}...")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete cache entry: {e}")
            return False

    async def cleanup_expired_entries(self, batch_size: int = 100) -> int:
        """
        Clean up expired cache entries

        Args:
            batch_size: Maximum number of entries to delete in one batch

        Returns:
            Number of entries deleted
        """
        try:
            client = self._get_client()
            collection = client.get_collection(self._collection_name)

            # Query for expired entries
            current_time = time.time()
            expired_docs = (
                collection.where("expires_at", "<", current_time)
                .limit(batch_size)
                .stream()
            )

            deleted_count = 0
            for doc in expired_docs:
                doc.reference.delete()
                deleted_count += 1

            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} expired cache entries")

            return deleted_count

        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired entries: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        try:
            client = self._get_client()
            collection = client.get_collection(self._collection_name)

            # Get all cache entries (limited for performance)
            # Limit can be made configurable via constructor parameter if needed
            docs = collection.limit(1000).stream()

            total_entries = 0
            total_hits = 0
            expired_entries = 0
            current_time = time.time()

            for doc in docs:
                total_entries += 1
                data = doc.to_dict()
                total_hits += data.get("hit_count", 0)

                expires_at = data.get("expires_at")
                if expires_at and expires_at < current_time:
                    expired_entries += 1

            return {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
            }

        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {
                "total_entries": 0,
                "total_hits": 0,
                "expired_entries": 0,
                "active_entries": 0,
                "error": str(e),
            }


# Global singleton instance
_cache_service: Optional[KnowledgeCacheService] = None


def get_knowledge_cache_service() -> KnowledgeCacheService:
    """
    Get or create global KnowledgeCacheService singleton

    Returns:
        KnowledgeCacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = KnowledgeCacheService()
    return _cache_service
