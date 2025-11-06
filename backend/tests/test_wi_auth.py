import os

import pytest
from fastapi.testclient import TestClient

# Set ALLOWED_HOSTS before importing app to allow testserver
os.environ["ALLOWED_HOSTS"] = "testserver,localhost"

from backend.main import app


client = TestClient(app)


def test_suggest_missing_token_returns_401():
    resp = client.post("/api/suggest", json={"document": "hello world"})
    assert resp.status_code == 401


def test_suggest_with_valid_token(monkeypatch):
    # Configure expected audience and trusted callers
    os.environ["AGENTNAV_URL"] = "https://agentnav.example"
    os.environ["TRUSTED_CALLERS"] = "prompt-vault@project.iam.gserviceaccount.com"

    # Monkeypatch the verify_oauth2_token to simulate a valid Google-signed token
    def fake_verify(token, request_adapter, audience=None):
        assert audience == os.environ["AGENTNAV_URL"]
        return {"email": "prompt-vault@project.iam.gserviceaccount.com", "aud": audience}

    monkeypatch.setattr("services.wi_auth.id_token.verify_oauth2_token", fake_verify)

    headers = {"Authorization": "Bearer faketoken"}
    resp = client.post("/api/suggest", json={"document": "This is a test document to suggest improvements."}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data
    assert data["caller"] == "prompt-vault@project.iam.gserviceaccount.com"
