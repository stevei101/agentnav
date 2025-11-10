"""
Tests for KnowledgeCacheService
Tests knowledge cache management in Firestore
"""

import time

import pytest

from services.knowledge_cache_service import KnowledgeCacheService


@pytest.mark.asyncio
async def test_generate_content_hash():
    """Test content hash generation"""
    service = KnowledgeCacheService()

    content = "Test document content"
    content_type = "document"

    hash1 = service.generate_content_hash(content, content_type)
    hash2 = service.generate_content_hash(content, content_type)

    # Same content should generate same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex string

    # Different content type should generate different hash
    hash3 = service.generate_content_hash(content, "codebase")
    assert hash1 != hash3


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss scenario"""
    service = KnowledgeCacheService()

    content = f"Unique content {time.time()}"
    content_type = "document"

    # Check cache for content that doesn't exist
    cached_result = await service.check_cache(content, content_type)

    # Should return None for cache miss
    assert cached_result is None


@pytest.mark.asyncio
async def test_cache_hit():
    """Test cache hit scenario"""
    service = KnowledgeCacheService()

    content = f"Test content for caching {time.time()}"
    content_type = "document"
    summary = "Test summary"
    visualization = {"type": "MIND_MAP", "nodes": [], "edges": []}

    # Store in cache
    store_success = await service.store_cache(
        content=content,
        content_type=content_type,
        summary=summary,
        visualization_data=visualization,
        key_entities=["Entity1", "Entity2"],
        relationships=[{"source": "A", "target": "B", "type": "relates_to"}],
    )

    if not store_success:
        pytest.skip("Firestore not available - skipping test")
        return

    assert store_success

    # Check cache
    cached_result = await service.check_cache(content, content_type)

    assert cached_result is not None
    assert cached_result["summary"] == summary
    assert cached_result["visualization_data"] == visualization
    assert cached_result["key_entities"] == ["Entity1", "Entity2"]
    assert len(cached_result["relationships"]) == 1
    assert "created_at" in cached_result
    assert "expires_at" in cached_result

    # Cleanup
    content_hash = service.generate_content_hash(content, content_type)
    await service.delete_cache_entry(content_hash)


@pytest.mark.asyncio
async def test_cache_expiration():
    """Test cache entry expiration"""
    service = KnowledgeCacheService()

    content = f"Test content for expiration {time.time()}"
    content_type = "document"

    # Store with very short TTL (0.0003 hours = ~1 second)
    store_success = await service.store_cache(
        content=content,
        content_type=content_type,
        summary="Test summary",
        visualization_data={},
        ttl_hours=0.0003,
    )

    if not store_success:
        pytest.skip("Firestore not available - skipping test")
        return

    # Wait for expiration using async sleep (reduced from 4s to 1.5s)
    import asyncio

    await asyncio.sleep(1.5)

    # Check cache - should return None for expired entry
    cached_result = await service.check_cache(content, content_type)

    # Entry should be expired
    assert cached_result is None


@pytest.mark.asyncio
async def test_increment_hit_count():
    """Test incrementing cache hit count"""
    service = KnowledgeCacheService()

    content = f"Test content for hit count {time.time()}"
    content_type = "document"

    # Store in cache
    store_success = await service.store_cache(
        content=content,
        content_type=content_type,
        summary="Test summary",
        visualization_data={},
    )

    if not store_success:
        pytest.skip("Firestore not available - skipping test")
        return

    content_hash = service.generate_content_hash(content, content_type)

    # Increment hit count
    increment_success = await service.increment_hit_count(content_hash)
    assert increment_success

    # Check updated count
    cached_result = await service.check_cache(content, content_type)
    assert cached_result["hit_count"] == 1

    # Increment again
    await service.increment_hit_count(content_hash)
    cached_result = await service.check_cache(content, content_type)
    assert cached_result["hit_count"] == 2

    # Cleanup
    await service.delete_cache_entry(content_hash)


@pytest.mark.asyncio
async def test_get_cache_stats():
    """Test getting cache statistics"""
    service = KnowledgeCacheService()

    stats = await service.get_cache_stats()

    # Should return stats dictionary
    assert "total_entries" in stats
    assert "total_hits" in stats
    assert "expired_entries" in stats
    assert "active_entries" in stats

    # Values should be non-negative
    assert stats["total_entries"] >= 0
    assert stats["total_hits"] >= 0
