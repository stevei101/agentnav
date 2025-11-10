"""
Focused tests for the WebSocket streaming routes (FR#020).

The suite keeps each test narrow in scope so failures point directly to the
behaviour that regressed, which aligns with the SRP expectations in
https://github.com/stevei101/agentnav/issues/285.
"""

from __future__ import annotations

import asyncio
from typing import Dict
from unittest.mock import AsyncMock

import pytest

from backend.models.stream_event_model import (
    AgentStatusEnum,
    ErrorType,
    EventPayload,
    WorkflowStreamRequest,
)


@pytest.fixture
def stubbed_workflow(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Patch the internal workflow executor so route tests remain fast."""

    executed = AsyncMock()
    monkeypatch.setattr(
        "backend.routes.stream_routes._execute_stream_workflow",
        executed,
        raising=False,
    )
    return executed


@pytest.fixture
def fixed_session_id(monkeypatch: pytest.MonkeyPatch) -> str:
    """Force a deterministic session identifier for assertions."""

    class _DeterministicUUID:
        hex = "feedfacecafe123456789abc"

    session_id = "session_feedfacecafe"
    monkeypatch.setattr(
        "backend.routes.stream_routes.uuid.uuid4",
        lambda: _DeterministicUUID(),
        raising=False,
    )
    return session_id


@pytest.fixture
def workflow_request_payload() -> Dict[str, str]:
    return {
        "document": "Stream request payload",
        "content_type": "document",
    }


class TestWebSocketConnectionLifecycle:
    """WebSocket connection establishment and teardown."""

    def test_websocket_endpoint_exists(self) -> None:
        from backend.main import app

        routes = {route.path for route in app.routes}
        assert "/api/v1/navigate/stream" in routes

    @pytest.mark.asyncio
    async def test_websocket_connection_acceptance(
        self,
        event_emitter_manager,
        mock_websocket,
        stubbed_workflow,
        fixed_session_id,
        workflow_request_payload,
    ) -> None:
        from backend.routes.stream_routes import stream_workflow

        mock_websocket.receive_json = AsyncMock(return_value=workflow_request_payload)

        await stream_workflow(mock_websocket)

        mock_websocket.accept.assert_awaited_once()
        assert stubbed_workflow.await_count == 1

        call_args = stubbed_workflow.await_args.args
        assert call_args[0] == fixed_session_id
        assert call_args[1] == workflow_request_payload["document"]
        assert call_args[2] == workflow_request_payload["content_type"]

        workflow_emitter = call_args[3]
        assert workflow_emitter is not None
        assert workflow_emitter.session_id == fixed_session_id
        mock_websocket.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_disconnection_cleanup(
        self,
        event_emitter_manager,
        mock_websocket,
        stubbed_workflow,
        fixed_session_id,
        workflow_request_payload,
    ) -> None:
        from backend.routes.stream_routes import stream_workflow

        mock_websocket.receive_json = AsyncMock(return_value=workflow_request_payload)
        stubbed_workflow.side_effect = RuntimeError("workflow failed")

        await stream_workflow(mock_websocket)

        assert stubbed_workflow.await_count == 1
        mock_websocket.accept.assert_awaited_once()
        mock_websocket.send_json.assert_called()
        assert event_emitter_manager.get_emitter(fixed_session_id) is None


class TestEventModelValidation:
    """Pydantic model validation."""

    def test_workflow_stream_request_validation(self) -> None:
        request = WorkflowStreamRequest(
            document="Test document content",
            content_type="document",
            include_metadata=True,
            include_partial_results=True,
        )
        assert request.document == "Test document content"
        assert request.content_type == "document"

    @pytest.mark.parametrize("content_type", ["document", "codebase"])
    def test_workflow_stream_request_content_type_validation(
        self, content_type: str
    ) -> None:
        request = WorkflowStreamRequest(document="content", content_type=content_type)
        assert request.content_type == content_type

    def test_event_payload_with_metrics(self) -> None:
        payload = EventPayload(
            summary="Test summary",
            metrics={
                "processingTime": 1500,
                "tokensProcessed": 250,
                "entitiesFound": 5,
            },
        )
        assert payload.summary == "Test summary"
        assert payload.metrics["processingTime"] == 1500

    def test_event_payload_with_error(self) -> None:
        payload = EventPayload(
            error_message="Workflow execution failed",
            error_type="workflow_error",
            recoverable=False,
        )

        assert payload.error is not None
        assert payload.error.error == "Workflow execution failed"
        assert payload.error.error_type is ErrorType.WORKFLOW_ERROR
        assert payload.error.recoverable is False


class TestEventStreaming:
    """Event emitter behaviour."""

    def test_event_emitter_creation(self, event_emitter_manager) -> None:
        session_id = "test-session-123"
        emitter = event_emitter_manager.create_emitter(session_id)
        assert emitter.session_id == session_id

    @pytest.mark.asyncio
    async def test_event_emission_to_client_queue(self, emitter_factory) -> None:
        emitter = emitter_factory("test-session-stream")
        client_queue: asyncio.Queue = asyncio.Queue()
        emitter.register_client(client_queue)

        await emitter.emit_event(
            {
                "id": "evt-001",
                "agent": "summarizer",
                "status": "processing",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        )

        queued_event = await asyncio.wait_for(client_queue.get(), timeout=1.0)
        assert queued_event["id"] == "evt-001"
        assert queued_event["agent"] == "summarizer"

    @pytest.mark.asyncio
    async def test_multiple_clients_receive_events(self, emitter_factory) -> None:
        emitter = emitter_factory("test-session-multi")
        queue1: asyncio.Queue = asyncio.Queue()
        queue2: asyncio.Queue = asyncio.Queue()
        emitter.register_client(queue1)
        emitter.register_client(queue2)

        await emitter.emit_event(
            {
                "id": "evt-002",
                "agent": "linker",
                "status": "complete",
                "timestamp": "2024-01-01T00:00:01Z",
            }
        )

        event1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        event2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
        assert event1["id"] == event2["id"] == "evt-002"

    @pytest.mark.asyncio
    async def test_client_unregistration(self, emitter_factory) -> None:
        emitter = emitter_factory("test-session-unregister")
        queue1: asyncio.Queue = asyncio.Queue()
        queue2: asyncio.Queue = asyncio.Queue()
        emitter.register_client(queue1)
        emitter.register_client(queue2)

        emitter.unregister_client(queue1)
        await emitter.emit_event(
            {
                "id": "evt-003",
                "agent": "visualizer",
                "status": "processing",
                "timestamp": "2024-01-01T00:00:02Z",
            }
        )

        event2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
        assert event2["id"] == "evt-003"

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(queue1.get(), timeout=0.25)


class TestAgentEventEmission:
    """Agent-level streaming hooks."""

    @pytest.mark.asyncio
    async def test_summarizer_process_emits_stream_events(
        self, stub_external_services, emitter_factory
    ) -> None:
        from backend.agents.summarizer_agent import SummarizerAgent

        emitter = emitter_factory("agent-session")
        agent = SummarizerAgent(event_emitter=emitter)

        context = {
            "document": "Test content for summarization",
            "content_type": "document",
        }
        result = await agent.process(context)

        assert result["summary"] == "Stubbed summary content."
        stub_external_services["gemini"].assert_awaited()
        stub_external_services["firestore"].get_document.assert_called()

        statuses = {event.status for event in emitter.events_emitted}
        assert AgentStatusEnum.PROCESSING in statuses
        assert AgentStatusEnum.COMPLETE in statuses

    @pytest.mark.asyncio
    async def test_summarizer_process_raises_for_missing_document(
        self, emitter_factory
    ) -> None:
        from backend.agents.summarizer_agent import SummarizerAgent

        emitter = emitter_factory("agent-missing-doc")
        agent = SummarizerAgent(event_emitter=emitter)

        with pytest.raises(ValueError):
            await agent.process({"content_type": "document"})

        assert emitter.events_emitted == []


class TestErrorHandling:
    """Route error handling."""

    @pytest.mark.asyncio
    async def test_invalid_request_format_error(
        self,
        event_emitter_manager,
        mock_websocket,
    ) -> None:
        from backend.routes.stream_routes import stream_workflow

        # Missing required fields
        mock_websocket.receive_json = AsyncMock(return_value={})

        await stream_workflow(mock_websocket)

        mock_websocket.send_json.assert_called()
        # No emitter should be created because the workflow never started.
        assert not event_emitter_manager.emitters

    @pytest.mark.skip(
        reason="Timeout scenarios require live WebSocket integration testing."
    )
    def test_websocket_timeout_handling(
        self,
    ) -> None:  # pragma: no cover - documented expectation
        pass


class TestPayloadParsing:
    """Payload parsing helpers."""

    def test_parse_agent_stream_event(self) -> None:
        from backend.models.stream_event_model import AgentStreamEvent

        raw_event = {
            "id": "evt-100",
            "agent": "summarizer",
            "status": "complete",
            "timestamp": "2024-01-01T00:00:10Z",
            "payload": {
                "summary": "Key findings",
                "metrics": {
                    "processingTime": 2000,
                    "tokensProcessed": 500,
                },
            },
        }

        event = AgentStreamEvent(**raw_event)
        assert event.id == "evt-100"
        assert event.payload.summary == "Key findings"
        assert event.payload.metrics["processingTime"] == 2000

    @pytest.mark.parametrize("status", ["queued", "processing", "complete", "error"])
    def test_parse_multiple_event_types(self, status: str) -> None:
        from backend.models.stream_event_model import AgentStreamEvent

        event = AgentStreamEvent(
            id=f"evt-{status}",
            agent="visualizer",
            status=status,
            timestamp="2024-01-01T00:00:00Z",
        )
        assert event.status == status


class TestStreamingStateManagement:
    """Session context helpers."""

    def test_session_context_creation(self) -> None:
        from backend.models.context_model import SessionContext

        session = SessionContext(
            session_id="test-session-001",
            raw_input="Test document",
            content_type="document",
        )

        assert session.session_id == "test-session-001"
        assert session.document == "Test document"

    def test_session_state_updates_during_stream(self) -> None:
        from backend.models.context_model import SessionContext

        session = SessionContext(
            session_id="test-session-002",
            raw_input="Content",
            content_type="codebase",
        )

        session.agent_states["summarizer"] = {"status": "processing"}
        session.agent_states["linker"] = {"status": "queued"}

        assert len(session.agent_states) == 2
        assert session.agent_states["summarizer"]["status"] == "processing"


class TestWebSocketIntegration:
    """Placeholder integration tests."""

    @pytest.mark.skip(reason="Requires live WebSocket client and full agent graph.")
    async def test_end_to_end_event_stream(
        self,
    ) -> None:  # pragma: no cover - documented expectation
        ...

    @pytest.mark.skip(reason="Requires multi-session orchestration with real agents.")
    async def test_concurrent_sessions(
        self,
    ) -> None:  # pragma: no cover - documented expectation
        ...
