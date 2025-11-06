"""
Workload Identity / Google ID Token verification utilities

This module exposes a FastAPI dependency that verifies Google-signed
ID tokens (Workload Identity) and validates that the token was issued
for the expected audience and optionally that it originates from a
trusted service account (subject/email).

Usage:
    from services.wi_auth import require_wi_token

    @app.post("/api/suggest")
    async def suggest(payload: SuggestRequest, claims=Depends(require_wi_token())):
        # claims contains the verified token payload
        ...
"""
from typing import List, Optional
import os
import logging

from fastapi import Depends, HTTPException, Request

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

logger = logging.getLogger(__name__)


def _get_trusted_callers() -> Optional[List[str]]:
    """Return list of trusted service account subjects/emails from env var.

    Set TRUSTED_CALLERS to a comma-separated list of service-account emails
    or principals that are allowed to call protected endpoints. For the
    Prompt Vault integration, set this to the Prompt Vault service account
    email (for example: prompt-vault-sa@PROJECT.iam.gserviceaccount.com).
    """
    var = os.getenv("TRUSTED_CALLERS")
    if not var:
        return None
    return [s.strip() for s in var.split(",") if s.strip()]


def require_wi_token(audience_env: str = "AGENTNAV_URL"):
    """FastAPI dependency factory that validates Google-signed ID tokens.

    Parameters:
    - audience_env: environment variable name containing the audience (service URL).

    Returns a dependency function suitable for FastAPI's Depends(). The
    dependency extracts the Authorization header, validates the ID token
    using Google's public keys, enforces the audience, and optionally
    checks that the `sub` or `email` claim is in TRUSTED_CALLERS.
    """

    async def _dependency(request: Request):
        auth: str = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth or not auth.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")

        token = auth.split(None, 1)[1]

        audience = os.getenv(audience_env)
        if not audience:
            logger.warning("Audience environment variable %s not set; token verification will fail", audience_env)
            raise HTTPException(status_code=500, detail="Server misconfiguration: audience not set")

        try:
            # Verify the token signature and (optionally) the audience.
            # google.oauth2.id_token.verify_oauth2_token will raise on failure.
            request_adapter = google_requests.Request()
            payload = id_token.verify_oauth2_token(token, request_adapter, audience)

        except Exception as e:
            logger.warning("ID token verification failed: %s", str(e))
            raise HTTPException(status_code=401, detail="Invalid or expired ID token")

        # If trust list is configured, enforce that the caller matches
        # Get trusted callers at request time to support dynamic configuration
        trusted_callers = _get_trusted_callers()
        if trusted_callers:
            # service account identity may appear in 'email' or 'sub'
            caller_identity = payload.get("email") or payload.get("sub")
            if not caller_identity or caller_identity not in trusted_callers:
                logger.warning("Token from untrusted caller: %s", caller_identity)
                raise HTTPException(status_code=403, detail="Unauthorized caller")

        # Token is valid; return the payload to the endpoint
        return payload

    return _dependency
