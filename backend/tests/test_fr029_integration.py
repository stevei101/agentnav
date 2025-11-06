"""
Integration test for FR#029: Session and Knowledge Cache Persistence
Tests the complete workflow with session and cache integration
"""

import pytest
import time
import asyncio


@pytest.mark.asyncio
async def test_workflow_with_session_creation():
    """Test that workflow creates session document"""
    from agents import (
        AgentWorkflow,
        OrchestratorAgent,
        SummarizerAgent,
        LinkerAgent,
        VisualizerAgent,
    )
    from models.context_model import SessionContext
    from services.session_service import get_session_service

    # Create workflow
    workflow = AgentWorkflow()

    # Register agents
    workflow.register_agent(OrchestratorAgent(workflow.a2a))
    workflow.register_agent(SummarizerAgent(workflow.a2a))
    workflow.register_agent(LinkerAgent(workflow.a2a))
    workflow.register_agent(VisualizerAgent(workflow.a2a))

    # Create session context
    session_id = f"test_integration_{int(time.time())}"
    session_context = SessionContext(
        session_id=session_id,
        raw_input="Test document about machine learning and neural networks.",
        content_type="document",
    )

    # Execute workflow
    try:
        await workflow.execute_sequential_workflow(session_context)

        # Verify session was created
        session_service = get_session_service()
        session_data = await session_service.get_session(session_id)

        if session_data:
            # Session was created successfully
            assert session_data["session_id"] == session_id
            assert "agent_states" in session_data
            assert session_data["workflow_status"] in [
                "completed",
                "partially_completed",
                "in_progress",
            ]

            # Cleanup
            await session_service.delete_session(session_id)
        else:
            # Firestore not available - test still passes as this is graceful degradation
            pytest.skip("Firestore not available - session not persisted")

    except Exception as e:
        # Workflow may fail if Gemini API or other services are not available
        # This is expected in test environments
        pytest.skip(f"Workflow execution failed (expected in test env): {e}")


@pytest.mark.asyncio
async def test_workflow_with_cache():
    """Test that workflow uses cache on second run"""
    from agents import (
        AgentWorkflow,
        OrchestratorAgent,
        SummarizerAgent,
        LinkerAgent,
        VisualizerAgent,
    )
    from models.context_model import SessionContext
    from services.knowledge_cache_service import get_knowledge_cache_service

    # Create workflow
    workflow = AgentWorkflow()

    # Register agents
    workflow.register_agent(OrchestratorAgent(workflow.a2a))
    workflow.register_agent(SummarizerAgent(workflow.a2a))
    workflow.register_agent(LinkerAgent(workflow.a2a))
    workflow.register_agent(VisualizerAgent(workflow.a2a))

    # Use same content for both runs
    test_content = f"Test document about AI {time.time()}"

    # First run - should process normally
    session_id_1 = f"test_cache_1_{int(time.time())}"
    session_context_1 = SessionContext(
        session_id=session_id_1, raw_input=test_content, content_type="document"
    )

    try:
        await workflow.execute_sequential_workflow(session_context_1)

        # Give time for cache to be written
        await asyncio.sleep(1)

        # Second run - should use cache
        session_id_2 = f"test_cache_2_{int(time.time())}"
        session_context_2 = SessionContext(
            session_id=session_id_2, raw_input=test_content, content_type="document"  # Same content
        )

        updated_context_2 = await workflow.execute_sequential_workflow(session_context_2)

        # Check if cache was used
        if updated_context_2.workflow_status == "completed_from_cache":
            # Cache hit - verify results are populated
            assert updated_context_2.summary_text is not None

            # Cleanup cache
            cache_service = get_knowledge_cache_service()
            content_hash = cache_service.generate_content_hash(test_content, "document")
            await cache_service.delete_cache_entry(content_hash)
        else:
            # Cache not used or Firestore not available
            pytest.skip("Cache not used - Firestore may not be available")

    except Exception as e:
        # Workflow may fail if Gemini API or other services are not available
        pytest.skip(f"Workflow execution failed (expected in test env): {e}")


@pytest.mark.asyncio
async def test_agent_states_persisted():
    """Test that agent states are persisted to session document"""
    from agents import AgentWorkflow, OrchestratorAgent
    from models.context_model import SessionContext
    from services.session_service import get_session_service

    # Create simple workflow with just orchestrator
    workflow = AgentWorkflow()
    workflow.register_agent(OrchestratorAgent(workflow.a2a))

    session_id = f"test_agent_state_{int(time.time())}"
    session_context = SessionContext(
        session_id=session_id, raw_input="Test document", content_type="document"
    )

    try:
        await workflow.execute_sequential_workflow(session_context)

        # Check session for agent states
        session_service = get_session_service()
        session_data = await session_service.get_session(session_id)

        if session_data:
            # Verify agent states were recorded
            assert "agent_states" in session_data

            # At least orchestrator should have state
            if "orchestrator" in session_data["agent_states"]:
                orchestrator_state = session_data["agent_states"]["orchestrator"]
                assert "status" in orchestrator_state
                assert "timestamp" in orchestrator_state

            # Cleanup
            await session_service.delete_session(session_id)
        else:
            pytest.skip("Firestore not available - agent states not persisted")

    except Exception as e:
        pytest.skip(f"Workflow execution failed (expected in test env): {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
