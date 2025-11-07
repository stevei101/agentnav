import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.services.workload_identity_auth import verify_workload_identity


def create_app(dep=Depends(verify_workload_identity)):
    app = FastAPI()

    @app.get("/protected")
    async def protected_route(auth=dep):  # type: ignore[no-redef]
        return auth

    return app


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv("REQUIRE_WI_AUTH", raising=False)
    monkeypatch.delenv("TRUSTED_SERVICE_ACCOUNTS", raising=False)
    monkeypatch.delenv("EXPECTED_AUDIENCE", raising=False)
    yield


def test_auth_not_required_when_disabled(monkeypatch):
    app = create_app()
    client = TestClient(app)

    response = client.get("/protected")

    assert response.status_code == 200
    assert response.json()["authenticated"] is False


def test_missing_token_rejected_when_required(monkeypatch):
    monkeypatch.setenv("REQUIRE_WI_AUTH", "true")
    app = create_app()
    client = TestClient(app)

    response = client.get("/protected")

    assert response.status_code == 401


def test_token_rejected_if_email_missing(monkeypatch):
    monkeypatch.setenv("REQUIRE_WI_AUTH", "true")

    app = create_app()
    client = TestClient(app)

    with patch(
        "backend.services.workload_identity_auth.id_token.verify_oauth2_token"
    ) as verify:
        verify.return_value = {"aud": "aud"}

        response = client.get("/protected", headers={"Authorization": "Bearer abc"})

    assert response.status_code == 401


def test_token_rejected_if_email_not_trusted(monkeypatch):
    monkeypatch.setenv("REQUIRE_WI_AUTH", "true")
    monkeypatch.setenv(
        "TRUSTED_SERVICE_ACCOUNTS", "trusted@project.iam.gserviceaccount.com"
    )

    app = create_app()
    client = TestClient(app)

    with patch(
        "backend.services.workload_identity_auth.id_token.verify_oauth2_token"
    ) as verify:
        verify.return_value = {
            "aud": "aud",
            "email": "intruder@project.iam.gserviceaccount.com",
        }

        response = client.get("/protected", headers={"Authorization": "Bearer abc"})

    assert response.status_code == 403


def test_token_allows_trusted_service_account(monkeypatch):
    monkeypatch.setenv("REQUIRE_WI_AUTH", "true")
    monkeypatch.setenv(
        "TRUSTED_SERVICE_ACCOUNTS", "trusted@project.iam.gserviceaccount.com"
    )
    monkeypatch.setenv("EXPECTED_AUDIENCE", "https://backend")

    app = create_app()
    client = TestClient(app)

    with patch(
        "backend.services.workload_identity_auth.id_token.verify_oauth2_token"
    ) as verify:
        verify.return_value = {
            "aud": "https://backend",
            "email": "trusted@project.iam.gserviceaccount.com",
        }

        response = client.get("/protected", headers={"Authorization": "Bearer abc"})

    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["email"] == "trusted@project.iam.gserviceaccount.com"
