"""Utilities for calling other Cloud Run services with Workload Identity.

This module is primarily intended for the Prompt Vault companion application to
invoke Agent Navigator APIs without storing static credentials. It fetches ID
tokens from the metadata server and attaches them to outgoing HTTP requests.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Dict, Optional

import httpx
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

_CACHE_TTL_SECONDS = int(os.getenv("WI_TOKEN_CACHE_SECONDS", "3300"))
_TOKEN_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_LOCK = asyncio.Lock()


def _default_audience(target_url: str) -> str:
    explicit = os.getenv("PROMPT_VAULT_BACKEND_AUDIENCE") or os.getenv(
        "EXPECTED_AUDIENCE"
    )
    if explicit:
        return explicit
    return target_url


async def _cached_fetch_id_token(audience: str) -> str:
    async with _CACHE_LOCK:
        entry = _TOKEN_CACHE.get(audience)
        now = time.time()
        if entry and entry["expires_at"] > now:
            return entry["token"]

        request = google_requests.Request()
        token = id_token.fetch_id_token(request, audience)

        _TOKEN_CACHE[audience] = {
            "token": token,
            "expires_at": now + _CACHE_TTL_SECONDS,
        }

        return token


async def call_service(
    url: str,
    *,
    method: str = "GET",
    json: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
) -> httpx.Response:
    """Call a Cloud Run service using Workload Identity authentication."""

    audience = _default_audience(url)
    token = await _cached_fetch_id_token(audience)

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method.upper(), url, json=json, headers=headers)
        response.raise_for_status()
        return response


def reset_token_cache() -> None:
    """Utility for tests to clear the cached tokens."""

    _TOKEN_CACHE.clear()
