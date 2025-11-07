import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.services.workload_identity_client import (
    call_service,
    reset_token_cache,
)


@pytest.fixture(autouse=True)
def clear_cache():
    reset_token_cache()
    yield
    reset_token_cache()


@pytest.mark.asyncio
async def test_call_service_attaches_bearer_token(monkeypatch):
    async def mock_request(method, url, json=None, headers=None, timeout=None):
        class Response:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return {}

        assert headers["Authorization"].startswith("Bearer ")
        return Response()

    mock_client = AsyncMock()
    mock_client.request.side_effect = mock_request
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = False

    with (
        patch(
            "backend.services.workload_identity_client.httpx.AsyncClient",
            return_value=mock_context,
        ),
        patch(
            "backend.services.workload_identity_client.id_token.fetch_id_token",
            return_value="token123",
        ),
    ):
        await call_service(
            "https://backend.example.com/api", method="POST", json={"key": "value"}
        )

    mock_client.request.assert_awaited()


@pytest.mark.asyncio
async def test_token_cache(monkeypatch):
    class _Response:
        status_code = 200

        def raise_for_status(self):
            return None

    mock_client = AsyncMock()
    mock_client.request.return_value = _Response()

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_client
    mock_context.__aexit__.return_value = False

    with (
        patch(
            "backend.services.workload_identity_client.id_token.fetch_id_token",
            return_value="token123",
        ) as fetch,
        patch(
            "backend.services.workload_identity_client.httpx.AsyncClient",
            return_value=mock_context,
        ),
    ):
        await call_service("https://backend.example.com/api")
        await call_service("https://backend.example.com/api")

    fetch.assert_called_once()
