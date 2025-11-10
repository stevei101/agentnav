from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_event_emitter_manager(monkeypatch):
    """Provide a reusable mocked EventEmitterManager for stream route tests.

    Patches `backend.routes.stream_routes.get_event_emitter_manager` so tests
    can rely on a simple, predictable manager that returns a mock emitter.
    """
    mock_emitter = Mock()
    # These methods are synchronous in the actual implementation
    mock_emitter.register_client = Mock()
    mock_emitter.unregister_client = Mock()
    mock_emitter.emit_event = AsyncMock()  # This one is async

    mock_manager = Mock()
    mock_manager.create_emitter.return_value = mock_emitter

    # Patch the accessor used by stream routes to return our manager
    monkeypatch.setattr(
        "backend.routes.stream_routes.get_event_emitter_manager",
        lambda: mock_manager,
        raising=False,
    )

    return mock_manager


@pytest.fixture
def mock_websocket():
    """Factory-like fixture returning a simple mocked WebSocket.

    The mock implements async methods `accept`, `receive_json`, and `send_json`.
    Tests can override `receive_json.side_effect` or `return_value` as needed.
    """
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock(side_effect=Exception("Connection closed"))
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def simple_emitter(mock_event_emitter_manager):
    """Return the emitter object created by the patched manager for convenience."""
    return mock_event_emitter_manager.create_emitter()
