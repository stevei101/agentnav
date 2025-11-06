"""
Integration tests for Linker Agent with Gemma Service
Tests the enhanced semantic relationship mapping functionality
"""

import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.base_agent import A2AProtocol
from agents.linker_agent import LinkerAgent


@pytest.fixture
def mock_a2a_protocol():
    """Mock A2A Protocol"""
    protocol = Mock(spec=A2AProtocol)
    protocol.send_message = AsyncMock()
    protocol.get_shared_context = AsyncMock(return_value={})
    return protocol


@pytest.fixture
def linker_agent(mock_a2a_protocol):
    """Create a Linker Agent instance"""
    return LinkerAgent(a2a_protocol=mock_a2a_protocol)


@pytest.mark.asyncio
async def test_linker_agent_basic_processing(linker_agent):
    """Test basic Linker Agent processing"""
    context = {
        "document": "This is a simple test document.",
        "content_type": "document",
        "shared_context": {},
    }

    with patch(
        "services.gemma_service.reason_with_gemma", new_callable=AsyncMock
    ) as mock_reason:
        mock_reason.return_value = "Concept 1\nConcept 2\nConcept 3"

        with patch(
            "services.gemma_service.embed_with_gemma", new_callable=AsyncMock
        ) as mock_embed:
            # Mock embeddings for 3 concepts
            mock_embed.return_value = [
                [0.1, 0.2, 0.3],
                [0.2, 0.3, 0.4],
                [0.9, 0.8, 0.7],
            ]

            result = await linker_agent.process(context)

            assert result["agent"] == "linker"
            assert "entities" in result
            assert "relationships" in result
            assert "graph_data" in result
            assert result["processing_complete"] is True


@pytest.mark.asyncio
async def test_linker_agent_semantic_similarity(linker_agent):
    """Test semantic similarity calculation"""
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]

    # Same vectors should have similarity of 1.0
    sim1 = linker_agent._cosine_similarity(vec1, vec2)
    assert abs(sim1 - 1.0) < 0.01

    # Orthogonal vectors should have similarity of 0.0
    sim2 = linker_agent._cosine_similarity(vec1, vec3)
    assert abs(sim2 - 0.0) < 0.01


@pytest.mark.asyncio
async def test_linker_agent_with_embeddings(linker_agent):
    """Test relationship identification using embeddings"""
    document = "Machine learning is a subset of artificial intelligence. Deep learning is a type of machine learning."
    entities = [
        {
            "id": "concept_0",
            "label": "Machine Learning",
            "type": "concept",
            "group": "Concept",
        },
        {
            "id": "concept_1",
            "label": "Artificial Intelligence",
            "type": "concept",
            "group": "Concept",
        },
        {
            "id": "concept_2",
            "label": "Deep Learning",
            "type": "concept",
            "group": "Concept",
        },
    ]

    with patch(
        "services.gemma_service.embed_with_gemma", new_callable=AsyncMock
    ) as mock_embed:
        # Create embeddings with high similarity for ML and DL, lower for AI
        mock_embed.return_value = [
            [0.8, 0.6, 0.0],  # ML
            [0.5, 0.5, 0.7],  # AI
            [0.85, 0.55, 0.1],  # DL - very similar to ML
        ]

        with patch(
            "services.gemma_service.reason_with_gemma", new_callable=AsyncMock
        ) as mock_reason:
            mock_reason.return_value = (
                "Deep learning builds on machine learning concepts."
            )

            relationships = (
                await linker_agent._identify_document_relationships_with_embeddings(
                    document, entities
                )
            )

            # Should find relationships based on semantic similarity
            assert len(relationships) > 0

            # Check that high-similarity relationships were found
            high_sim_rels = [r for r in relationships if r.get("similarity", 0) > 0.9]
            assert len(high_sim_rels) > 0


@pytest.mark.asyncio
async def test_linker_agent_fallback_on_error(linker_agent):
    """Test fallback to simple method when embeddings fail"""
    document = "Test document with concepts."
    entities = [
        {"id": "concept_0", "label": "Test", "type": "concept", "group": "Concept"},
        {"id": "concept_1", "label": "Document", "type": "concept", "group": "Concept"},
    ]

    with patch(
        "services.gemma_service.embed_with_gemma", new_callable=AsyncMock
    ) as mock_embed:
        # Simulate embedding failure
        mock_embed.side_effect = Exception("Embedding service unavailable")

        # Should fall back to simple method without crashing
        relationships = (
            await linker_agent._identify_document_relationships_with_embeddings(
                document, entities
            )
        )

        # Should return some relationships even with fallback
        assert isinstance(relationships, list)


@pytest.mark.asyncio
async def test_linker_agent_code_entities(linker_agent):
    """Test entity extraction from code"""
    code = """
def calculate_sum(a, b):
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y

import numpy as np
"""

    entities = linker_agent._extract_code_entities(code)

    # Should find function, class, and import
    assert any(e["type"] == "function" for e in entities)
    assert any(e["type"] == "class" for e in entities)
    assert any(e["type"] == "import" for e in entities)

    # Check specific entities
    function_names = [e["label"] for e in entities if e["type"] == "function"]
    assert "calculate_sum" in function_names

    class_names = [e["label"] for e in entities if e["type"] == "class"]
    assert "Calculator" in class_names


@pytest.mark.asyncio
async def test_linker_agent_a2a_notification(linker_agent, mock_a2a_protocol):
    """Test A2A Protocol notification on completion"""
    entities = [{"id": "e1", "label": "Entity 1"}]
    relationships = [{"from": "e1", "to": "e2", "type": "related"}]
    graph_data = {"nodes": [], "edges": []}

    await linker_agent._notify_linking_complete(entities, relationships, graph_data)

    # Should have sent messages via A2A Protocol
    assert mock_a2a_protocol.send_message.call_count >= 2

    # Check that messages were sent to correct recipients
    calls = mock_a2a_protocol.send_message.call_args_list
    messages = [call[0][0] for call in calls]

    # Should have broadcast and visualizer-specific messages
    broadcast_msgs = [m for m in messages if m.to_agent == "*"]
    visualizer_msgs = [m for m in messages if m.to_agent == "visualizer"]

    assert len(broadcast_msgs) >= 1
    assert len(visualizer_msgs) >= 1


@pytest.mark.asyncio
async def test_linker_agent_graph_data_structure(linker_agent):
    """Test graph data structure creation"""
    entities = [
        {"id": "e1", "label": "Entity 1", "type": "concept", "group": "Concept"},
        {"id": "e2", "label": "Entity 2", "type": "concept", "group": "Concept"},
    ]
    relationships = [
        {"from": "e1", "to": "e2", "type": "related", "label": "related to"}
    ]

    graph_data = linker_agent._prepare_graph_data(entities, relationships, "document")

    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert "type" in graph_data
    assert graph_data["type"] == "MIND_MAP"

    # Check nodes
    assert len(graph_data["nodes"]) == 2
    assert graph_data["nodes"][0]["id"] == "e1"

    # Check edges
    assert len(graph_data["edges"]) == 1
    assert graph_data["edges"][0]["from"] == "e1"
    assert graph_data["edges"][0]["to"] == "e2"


@pytest.mark.asyncio
async def test_linker_agent_reasoning_enhancement(linker_agent):
    """Test relationship enhancement with reasoning"""
    document = "AI and ML are related fields."
    entities = [{"id": "e1", "label": "AI"}, {"id": "e2", "label": "ML"}]
    relationships = [{"from": "e1", "to": "e2", "type": "related", "similarity": 0.8}]

    with patch(
        "services.gemma_service.reason_with_gemma", new_callable=AsyncMock
    ) as mock_reason:
        mock_reason.return_value = "AI encompasses ML as a subfield."

        enhanced = await linker_agent._enhance_relationships_with_reasoning(
            document, entities, relationships
        )

        # Should have added reasoning context
        assert enhanced[0].get("reasoning_context") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
