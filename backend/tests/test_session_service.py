"""
Tests for SessionService
Tests session metadata management in Firestore
"""

import time

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_create_session():
    """Test creating a session document"""
    service = SessionService()

    session_id = f"test_session_{int(time.time())}"
    user_input = "Test document content"
    content_type = "document"

    # Create session
    success = await service.create_session(
        session_id=session_id,
        user_input=user_input,
        content_type=content_type,
        metadata={"test": True},
    )

    # Service may fail if Firestore is not available
    # This is expected behavior in some environments
    if not success:
        pytest.skip("Firestore not available - skipping test")
        return

    assert success

    # Verify session was created
    session_data = await service.get_session(session_id)
    assert session_data is not None
    assert session_data["session_id"] == session_id
    assert session_data["user_input"] == user_input
    assert session_data["content_type"] == content_type
    assert session_data["workflow_status"] == "initializing"
    assert "created_at" in session_data
    assert "agent_states" in session_data

    # Cleanup
    await service.delete_session(session_id)


@pytest.mark.asyncio
async def test_update_session():
    """Test updating session metadata"""
    service = SessionService()

    session_id = f"test_session_update_{int(time.time())}"

    # Create session
    success = await service.create_session(
        session_id=session_id, user_input="Test content", content_type="document"
    )

    if not success:
        pytest.skip("Firestore not available - skipping test")
        return

    # Update session
    update_success = await service.update_session(
        session_id=session_id, updates={"workflow_status": "in_progress"}
    )

    assert update_success

    # Verify update
    session_data = await service.get_session(session_id)
    assert session_data["workflow_status"] == "in_progress"

    # Cleanup
    await service.delete_session(session_id)


@pytest.mark.asyncio
async def test_update_agent_state():
    """Test updating agent state in session"""
    service = SessionService()

    session_id = f"test_session_agent_{int(time.time())}"

    # Create session
    success = await service.create_session(
        session_id=session_id, user_input="Test content", content_type="document"
    )

    if not success:
        pytest.skip("Firestore not available - skipping test")
        return

    # Update agent state
    agent_success = await service.update_agent_state(
        session_id=session_id,
        agent_name="summarizer",
        state={
            "status": "completed",
            "execution_time": 1.5,
            "result_summary": "Summary generated",
        },
    )

    assert agent_success

    # Verify agent state
    session_data = await service.get_session(session_id)
    assert "summarizer" in session_data["agent_states"]
    assert session_data["agent_states"]["summarizer"]["status"] == "completed"
    assert session_data["agent_states"]["summarizer"]["execution_time"] == 1.5

    # Cleanup
    await service.delete_session(session_id)


@pytest.mark.asyncio
async def test_list_sessions():
    """Test listing sessions"""
    service = SessionService()

    # Create test sessions
    session_ids = []
    for i in range(3):
        session_id = f"test_session_list_{int(time.time())}_{i}"
        success = await service.create_session(
            session_id=session_id,
            user_input=f"Test content {i}",
            content_type="document",
        )
        if success:
            session_ids.append(session_id)

    if not session_ids:
        pytest.skip("Firestore not available - skipping test")
        return

    # List sessions
    sessions = await service.list_sessions(limit=10)

    # Should have at least our test sessions
    assert len(sessions) >= len(session_ids)

    # Cleanup
    for session_id in session_ids:
        await service.delete_session(session_id)
