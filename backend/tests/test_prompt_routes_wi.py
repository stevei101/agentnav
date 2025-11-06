"""
Integration Tests for Prompt Routes with Workload Identity (Feature Request #335)
"""
import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from main import app


class TestPromptRoutesWIAuthentication:
    """Test prompt routes with Workload Identity authentication"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_list_prompts_no_auth_development_mode(self):
        """Test listing prompts in development mode (auth disabled)"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "false"}, clear=True):
            # Mock the prompt service to return empty list
            with patch('routes.prompt_routes.get_prompt_service') as mock_service:
                mock_service.return_value.list_prompts.return_value = []
                
                response = self.client.get("/api/prompts/")
                
                assert response.status_code == 200
                assert response.json() == []
    
    def test_list_prompts_requires_auth_production_mode(self):
        """Test that listing prompts requires auth in production mode"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "true"}, clear=True):
            # No Authorization header
            response = self.client.get("/api/prompts/")
            
            assert response.status_code == 401
            assert "Missing Authorization header" in response.text
    
    def test_list_prompts_with_valid_token(self):
        """Test listing prompts with valid WI token"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "prompt-vault@project.iam.gserviceaccount.com"
        }, clear=True):
            # Mock ID token verification
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    "email": "prompt-vault@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                # Mock prompt service
                with patch('routes.prompt_routes.get_prompt_service') as mock_service:
                    mock_service.return_value.list_prompts.return_value = []
                    
                    response = self.client.get(
                        "/api/prompts/",
                        headers={"Authorization": "Bearer valid_token"}
                    )
                    
                    assert response.status_code == 200
                    assert response.json() == []
    
    def test_list_prompts_with_invalid_token(self):
        """Test that invalid token is rejected"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "true"}, clear=True):
            # Mock ID token verification to fail
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.side_effect = ValueError("Invalid token")
                
                response = self.client.get(
                    "/api/prompts/",
                    headers={"Authorization": "Bearer invalid_token"}
                )
                
                assert response.status_code == 401
                assert "Invalid ID token" in response.text
    
    def test_create_prompt_with_valid_token(self):
        """Test creating prompt with valid WI token"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "prompt-vault@project.iam.gserviceaccount.com"
        }, clear=True):
            # Mock ID token verification
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    "email": "prompt-vault@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                # Mock prompt service
                mock_prompt = {
                    "id": "test-123",
                    "title": "Test Prompt",
                    "content": "Test content",
                    "tags": [],
                    "createdAt": "2024-01-01T00:00:00",
                    "updatedAt": "2024-01-01T00:00:00",
                    "userId": "prompt-vault@project.iam.gserviceaccount.com",
                    "userName": "prompt-vault",
                    "version": 1,
                    "testResults": []
                }
                
                with patch('routes.prompt_routes.get_prompt_service') as mock_service:
                    mock_service.return_value.create_prompt.return_value = type('Prompt', (), mock_prompt)()
                    
                    response = self.client.post(
                        "/api/prompts/",
                        json={
                            "title": "Test Prompt",
                            "content": "Test content",
                            "tags": []
                        },
                        headers={"Authorization": "Bearer valid_token"}
                    )
                    
                    assert response.status_code == 201
    
    def test_get_prompt_with_valid_token(self):
        """Test getting prompt by ID with valid WI token"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "prompt-vault@project.iam.gserviceaccount.com"
        }, clear=True):
            # Mock ID token verification
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    "email": "prompt-vault@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                # Mock prompt service
                mock_prompt = {
                    "id": "test-123",
                    "title": "Test Prompt",
                    "content": "Test content",
                    "tags": [],
                    "createdAt": "2024-01-01T00:00:00",
                    "updatedAt": "2024-01-01T00:00:00",
                    "userId": "prompt-vault@project.iam.gserviceaccount.com",
                    "userName": "prompt-vault",
                    "version": 1,
                    "testResults": []
                }
                
                with patch('routes.prompt_routes.get_prompt_service') as mock_service:
                    mock_service.return_value.get_prompt.return_value = type('Prompt', (), mock_prompt)()
                    
                    response = self.client.get(
                        "/api/prompts/test-123",
                        headers={"Authorization": "Bearer valid_token"}
                    )
                    
                    assert response.status_code == 200
    
    def test_update_prompt_with_valid_token(self):
        """Test updating prompt with valid WI token"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "prompt-vault@project.iam.gserviceaccount.com"
        }, clear=True):
            # Mock ID token verification
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    "email": "prompt-vault@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                # Mock prompt service
                mock_prompt = {
                    "id": "test-123",
                    "title": "Updated Prompt",
                    "content": "Updated content",
                    "tags": [],
                    "createdAt": "2024-01-01T00:00:00",
                    "updatedAt": "2024-01-02T00:00:00",
                    "userId": "prompt-vault@project.iam.gserviceaccount.com",
                    "userName": "prompt-vault",
                    "version": 2,
                    "testResults": []
                }
                
                with patch('routes.prompt_routes.get_prompt_service') as mock_service:
                    mock_service.return_value.update_prompt.return_value = type('Prompt', (), mock_prompt)()
                    
                    response = self.client.put(
                        "/api/prompts/test-123",
                        json={"title": "Updated Prompt"},
                        headers={"Authorization": "Bearer valid_token"}
                    )
                    
                    assert response.status_code == 200
    
    def test_delete_prompt_with_valid_token(self):
        """Test deleting prompt with valid WI token"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "prompt-vault@project.iam.gserviceaccount.com"
        }, clear=True):
            # Mock ID token verification
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    "email": "prompt-vault@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                # Mock prompt service
                with patch('routes.prompt_routes.get_prompt_service') as mock_service:
                    mock_service.return_value.delete_prompt.return_value = True
                    
                    response = self.client.delete(
                        "/api/prompts/test-123",
                        headers={"Authorization": "Bearer valid_token"}
                    )
                    
                    assert response.status_code == 204
    
    def test_get_user_info_with_valid_token(self):
        """Test getting user info with valid WI token"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "prompt-vault@project.iam.gserviceaccount.com"
        }, clear=True):
            # Mock ID token verification
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    "email": "prompt-vault@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                response = self.client.get(
                    "/api/prompts/user/info",
                    headers={"Authorization": "Bearer valid_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["email"] == "prompt-vault@project.iam.gserviceaccount.com"
                assert data["name"] == "prompt-vault"
    
    def test_untrusted_service_account_rejected(self):
        """Test that untrusted service account is rejected"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "trusted@project.iam.gserviceaccount.com"
        }, clear=True):
            # Mock ID token verification with untrusted account
            with patch('services.workload_identity_auth.id_token') as mock_id_token:
                mock_id_token.verify_oauth2_token.return_value = {
                    "email": "untrusted@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                response = self.client.get(
                    "/api/prompts/",
                    headers={"Authorization": "Bearer valid_token_untrusted"}
                )
                
                assert response.status_code == 403
                assert "not authorized" in response.text


# Coverage target: >= 70%
# These tests cover:
# - Development mode (auth disabled)
# - Production mode requiring auth
# - Valid token authentication
# - Invalid token rejection
# - All CRUD operations with WI auth (list, create, get, update, delete)
# - User info endpoint
# - Untrusted service account rejection
