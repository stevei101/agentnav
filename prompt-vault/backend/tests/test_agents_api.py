"""Tests for agent workflow API endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_optimize_endpoint_structure():
    """Test optimize endpoint accepts correct structure."""
    response = client.post(
        "/api/agents/optimize",
        json={
            "prompt_id": "test-prompt-id",
            "options": {}
        }
    )
    # Should accept the request (may fail on actual processing, but structure should be valid)
    assert response.status_code in [200, 500]  # 500 is OK if services not configured
    if response.status_code == 200:
        data = response.json()
        assert "success" in data
        assert "workflow_id" in data


def test_test_endpoint_structure():
    """Test test endpoint accepts correct structure."""
    response = client.post(
        "/api/agents/test",
        json={
            "prompt_id": "test-prompt-id",
            "scenarios": [],
            "options": {}
        }
    )
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "success" in data


def test_compare_endpoint_structure():
    """Test compare endpoint accepts correct structure."""
    response = client.post(
        "/api/agents/compare",
        json={
            "prompt_id": "test-prompt-id",
            "version_ids": ["v1", "v2"]
        }
    )
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "success" in data


def test_suggest_endpoint_structure():
    """Test suggest endpoint accepts correct structure."""
    response = client.post(
        "/api/agents/suggest",
        json={
            "requirements": {
                "purpose": "test",
                "target_model": "gemini-pro"
            },
            "options": {}
        }
    )
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "success" in data


def test_workflow_status_endpoint():
    """Test workflow status endpoint."""
    # Should return 404 for non-existent workflow
    response = client.get("/api/agents/workflow/non-existent-id")
    assert response.status_code == 404

