from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from backend.routes import prompt_routes
from backend.routes.prompt_routes import router


def create_app():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[prompt_routes.verify_workload_identity] = lambda: {
        "authenticated": True,
        "email": "prompt-vault@project.iam.gserviceaccount.com",
    }
    return app


def test_suggest_prompt_requires_body():
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/prompt-assistant/suggest", json={"prompt": "  "})

    assert response.status_code == 400


def test_suggest_prompt_returns_suggestions():
    app = create_app()
    client = TestClient(app)

    fake_response = "- Improved prompt\n- Another prompt"

    with patch("backend.services.gemini_client.reason_with_gemini", new=AsyncMock(return_value=fake_response)):
        response = client.post(
            "/api/prompt-assistant/suggest",
            json={"prompt": "Test prompt", "max_suggestions": 2},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["suggestions"] == ["Improved prompt", "Another prompt"]

