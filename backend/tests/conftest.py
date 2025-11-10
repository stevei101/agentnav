from __future__ import annotations

from collections.abc import Callable
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest

from backend.services.event_emitter import EventEmitter, EventEmitterManager


@pytest.fixture
def event_emitter_manager(monkeypatch: pytest.MonkeyPatch) -> EventEmitterManager:
    """Provide a real EventEmitterManager wired into the stream routes module.

    Using the real manager keeps the tests close to the production behaviour
    while still allowing us to observe and assert on emitted events.
    """

    manager = EventEmitterManager()
    monkeypatch.setattr(
        "backend.routes.stream_routes.get_event_emitter_manager",
        lambda: manager,
        raising=False,
    )
    yield manager
    manager.emitters.clear()


@pytest.fixture
def emitter_factory(
    event_emitter_manager: EventEmitterManager,
) -> Callable[[str], EventEmitter]:
    """Return a factory that produces emitters for ad-hoc session IDs."""

    def _create(session_id: str = "test-session") -> EventEmitter:
        return event_emitter_manager.create_emitter(session_id)

    return _create


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """Factory-like fixture returning a simple mocked WebSocket.

    The mock implements the async methods used by the route handler so tests
    can tailor behaviour via `return_value` or `side_effect`.
    """

    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def stub_external_services(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    """Stub external I/O services (Gemini + Firestore) for agent tests."""

    async def _fake_reason_with_gemini(*_: Any, **__: Any) -> str:
        return "Stubbed summary content."

    gemini_mock = AsyncMock(side_effect=_fake_reason_with_gemini)
    monkeypatch.setattr(
        "backend.services.gemini_client.reason_with_gemini",
        gemini_mock,
        raising=False,
    )

    firestore_doc = Mock()
    firestore_client = Mock()
    firestore_client.get_document.return_value = firestore_doc
    monkeypatch.setattr(
        "backend.services.firestore_client.get_firestore_client",
        lambda: firestore_client,
        raising=False,
    )

    return {
        "gemini": gemini_mock,
        "firestore": firestore_client,
        "document": firestore_doc,
    }
