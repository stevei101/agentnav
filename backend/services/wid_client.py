"""
Workload Identity ID Token client helper

Provides a small helper to fetch a Google-signed ID token for the current
service's identity. This works both on GCP (metadata server) and in local
development when a service account JSON is available via
GOOGLE_APPLICATION_CREDENTIALS.

The returned token is suitable to send in Authorization: Bearer <token>
to other Cloud Run services which validate the token.
"""
import os
import requests
import logging

logger = logging.getLogger(__name__)


def fetch_id_token_for_audience(audience: str, timeout: int = 5) -> str:
    """Fetch an ID token for the given audience.

    Strategy:
    1. If running on GCP (metadata server reachable), call the metadata
       server identity endpoint for the default service account.
    2. Otherwise, if GOOGLE_APPLICATION_CREDENTIALS is set and points to a
       service account key file, use google-auth to create an ID token.

    Returns the raw JWT string or raises an exception on failure.
    """
    # Prefer the metadata server path (Cloud Run / GCE / GKE)
    metadata_url = (
        "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity"
    )
    params = {"audience": audience, "format": "full"}

    try:
        headers = {"Metadata-Flavor": "Google"}
        resp = requests.get(metadata_url, params=params, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            token = resp.text
            return token
        else:
            logger.debug("Metadata server returned %s: %s", resp.status_code, resp.text)
    except requests.RequestException:
        logger.debug("Metadata server not reachable; falling back to application credentials")

    # Fallback: use google-auth library with service account key file
    try:
        from google.oauth2 import service_account
        from google.auth.transport import requests as google_requests

        sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not sa_path:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set and metadata server unreachable")

        target_audience = audience
        credentials = service_account.IDTokenCredentials.from_service_account_file(
            sa_path, target_audience=target_audience
        )
        request_adapter = google_requests.Request()
        credentials.refresh(request_adapter)
        return credentials.token

    except Exception as e:
        logger.error("Failed to obtain ID token: %s", str(e))
        raise
