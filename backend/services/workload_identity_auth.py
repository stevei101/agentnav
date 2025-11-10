"""Workload Identity authentication helpers.

Provides FastAPI dependencies for verifying Google Cloud Run ID tokens that are
issued via Workload Identity (WI). This allows the Prompt Vault companion
service to call protected Agent Navigator endpoints using credential-less
service-to-service authentication.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

_AUTH_HEADER_PREFIX = "bearer "


def _strtobool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def require_workload_identity() -> bool:
    """Returns True when Workload Identity enforcement is required."""

    return _strtobool(os.getenv("REQUIRE_WI_AUTH", "false"))


@lru_cache(maxsize=1)
def _trusted_service_accounts() -> Optional[set[str]]:
    raw = os.getenv("TRUSTED_SERVICE_ACCOUNTS")
    if not raw:
        return None

    accounts = {item.strip().lower() for item in raw.split(",") if item.strip()}
    return accounts or None


def _expected_audience() -> Optional[str]:
    return os.getenv("EXPECTED_AUDIENCE") or os.getenv("WI_EXPECTED_AUDIENCE")


def _build_google_request() -> google_requests.Request:
    return google_requests.Request()


def _extract_bearer_token(request: Request) -> Optional[str]:
    header = request.headers.get("authorization")
    if not header:
        return None

    header_lower = header.lower()
    if not header_lower.startswith(_AUTH_HEADER_PREFIX):
        return None

    return header[len(_AUTH_HEADER_PREFIX) :].strip()


async def verify_workload_identity(request: Request) -> Dict[str, Any]:
    """FastAPI dependency that enforces Workload Identity authentication.

    When `REQUIRE_WI_AUTH` is set to true, this dependency checks for a Bearer
    token in the Authorization header, verifies it using Google's public keys,
    validates the audience, and ensures the calling service account is trusted.

    Returns a dictionary with token metadata so routes can inspect the caller's
    identity. If WI is not required, the dependency returns a dictionary with
    `authenticated=False`.
    """

    token = _extract_bearer_token(request)

    if not token:
        if require_workload_identity():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Bearer token for Workload Identity authentication",
            )
        return {"authenticated": False, "email": None, "audience": None}

    audience = _expected_audience()

    try:
        claims = id_token.verify_oauth2_token(
            token,
            _build_google_request(),
            audience=audience,
        )
    except Exception as exc:  # noqa: BLE001 - intentionally broad to map to 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Workload Identity token: {exc}",
        ) from exc

    email = claims.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Workload Identity token missing email claim",
        )

    trusted_accounts = _trusted_service_accounts()
    if trusted_accounts is not None and email.lower() not in trusted_accounts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Caller service account is not allowed",
        )

    return {
        "authenticated": True,
        "email": email,
        "audience": claims.get("aud"),
        "subject": claims.get("sub"),
        "claims": claims,
    }


WorkloadIdentityAuth = Depends(verify_workload_identity)
