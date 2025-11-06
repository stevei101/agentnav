"""
Tests for Workload Identity Authentication (Feature Request #335)
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import HTTPException
from services.workload_identity_auth import (
    WorkloadIdentityAuth,
    verify_workload_identity,
    require_service_account,
    get_auth_service
)


class TestWorkloadIdentityAuth:
    """Test Workload Identity authentication for Cloud Run services"""
    
    def test_auth_bypass_when_disabled(self):
        """Test that authentication is bypassed when REQUIRE_WI_AUTH is False"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "false"}, clear=True):
            auth = WorkloadIdentityAuth()
            
            # Should return development mode token without requiring header
            import asyncio
            result = asyncio.run(auth.verify_id_token(None))
            
            assert result is not None
            assert result.get("development_mode") is True
            assert "email" in result
    
    @pytest.mark.asyncio
    async def test_auth_required_when_enabled_no_header(self):
        """Test that authentication fails when required but no header provided"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "true"}, clear=True):
            # Import after setting env var to pick it up
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            with pytest.raises(HTTPException) as exc_info:
                await auth.verify_id_token(None)
            
            assert exc_info.value.status_code == 401
            assert "Missing Authorization header" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_auth_invalid_header_format(self):
        """Test that invalid Authorization header format is rejected"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "true"}, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            with pytest.raises(HTTPException) as exc_info:
                await auth.verify_id_token("InvalidFormat token123")
            
            assert exc_info.value.status_code == 401
            assert "Invalid Authorization header format" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_auth_empty_token(self):
        """Test that empty token is rejected"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "true"}, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            with pytest.raises(HTTPException) as exc_info:
                await auth.verify_id_token("Bearer ")
            
            assert exc_info.value.status_code == 401
            assert "Empty token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_auth_valid_token(self):
        """Test that valid ID token passes authentication"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "test@project.iam.gserviceaccount.com",
            "EXPECTED_AUDIENCE": "https://backend-service.run.app"
        }, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            # Mock google.oauth2.id_token.verify_oauth2_token
            with patch('google.oauth2.id_token.verify_oauth2_token') as mock_verify:
                mock_verify.return_value = {
                    "email": "test@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                result = await auth.verify_id_token("Bearer valid_token_123")
                
                assert result is not None
                assert result["email"] == "test@project.iam.gserviceaccount.com"
                assert result["sub"] == "123456789"
                assert result["aud"] == "https://backend-service.run.app"
                mock_verify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auth_invalid_token_signature(self):
        """Test that invalid token signature fails authentication"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "true"}, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            # Mock google.oauth2.id_token to raise ValueError
            with patch('google.oauth2.id_token.verify_oauth2_token') as mock_verify:
                mock_verify.side_effect = ValueError("Invalid token signature")
                
                with pytest.raises(HTTPException) as exc_info:
                    await auth.verify_id_token("Bearer invalid_token")
                
                assert exc_info.value.status_code == 401
                assert "Invalid ID token" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_auth_untrusted_service_account(self):
        """Test that untrusted service account is rejected"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "trusted@project.iam.gserviceaccount.com"
        }, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            # Mock token verification to return untrusted account
            with patch('google.oauth2.id_token.verify_oauth2_token') as mock_verify:
                mock_verify.return_value = {
                    "email": "untrusted@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://backend-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                with pytest.raises(HTTPException) as exc_info:
                    await auth.verify_id_token("Bearer valid_token_untrusted")
                
                assert exc_info.value.status_code == 403
                assert "not authorized" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_auth_invalid_audience(self):
        """Test that invalid audience is rejected"""
        with patch.dict(os.environ, {
            "REQUIRE_WI_AUTH": "true",
            "TRUSTED_SERVICE_ACCOUNTS": "test@project.iam.gserviceaccount.com",
            "EXPECTED_AUDIENCE": "https://backend-service.run.app"
        }, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            # Mock token with wrong audience
            with patch('google.oauth2.id_token.verify_oauth2_token') as mock_verify:
                mock_verify.return_value = {
                    "email": "test@project.iam.gserviceaccount.com",
                    "sub": "123456789",
                    "aud": "https://wrong-service.run.app",
                    "iss": "https://accounts.google.com",
                    "exp": 9999999999,
                    "iat": 1234567890
                }
                
                with pytest.raises(HTTPException) as exc_info:
                    await auth.verify_id_token("Bearer token_wrong_audience")
                
                assert exc_info.value.status_code == 403
                assert "Invalid token audience" in str(exc_info.value.detail)
    
    def test_trusted_service_accounts_from_env(self):
        """Test loading trusted service accounts from environment"""
        with patch.dict(os.environ, {
            "TRUSTED_SERVICE_ACCOUNTS": "sa1@project.iam.gserviceaccount.com,sa2@project.iam.gserviceaccount.com"
        }, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            # Should have exactly the two from environment (no defaults added)
            assert len(auth.trusted_service_accounts) == 2
            assert "sa1@project.iam.gserviceaccount.com" in auth.trusted_service_accounts
            assert "sa2@project.iam.gserviceaccount.com" in auth.trusted_service_accounts
    
    def test_default_trusted_service_accounts(self):
        """Test default trusted service accounts when none configured"""
        with patch.dict(os.environ, {
            "GCP_PROJECT_ID": "test-project",
            "ENVIRONMENT": "production"
        }, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            # Should include default service accounts for the project
            assert any("agentnav-backend" in sa for sa in auth.trusted_service_accounts)
            assert any("prompt-vault" in sa for sa in auth.trusted_service_accounts)
            
            # Should NOT include dev account in production
            assert not any("dev-service-account" in sa for sa in auth.trusted_service_accounts)
    
    def test_development_mode_includes_dev_account(self):
        """Test that development mode includes dev service account"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development"
        }, clear=True):
            import importlib
            import services.workload_identity_auth
            importlib.reload(services.workload_identity_auth)
            
            auth = services.workload_identity_auth.WorkloadIdentityAuth()
            
            # Should include dev account in development
            assert any("dev-service-account" in sa for sa in auth.trusted_service_accounts)
    
    def test_expected_audience_from_env(self):
        """Test expected audience is loaded from environment"""
        with patch.dict(os.environ, {
            "EXPECTED_AUDIENCE": "https://my-service.run.app"
        }, clear=True):
            auth = WorkloadIdentityAuth()
            
            assert auth.expected_audience == "https://my-service.run.app"
    
    def test_expected_audience_from_cloud_run_metadata(self):
        """Test expected audience constructed from Cloud Run metadata"""
        with patch.dict(os.environ, {
            "K_SERVICE": "backend-service",
            "CLOUD_RUN_REGION": "us-central1",
            "GOOGLE_CLOUD_PROJECT": "test-project"
        }, clear=True):
            auth = WorkloadIdentityAuth()
            
            # Should construct audience from Cloud Run metadata
            assert auth.expected_audience == "https://backend-service-us-central1.run.app"
    
    @pytest.mark.asyncio
    async def test_require_service_account_dependency(self):
        """Test require_service_account dependency helper"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "false"}, clear=True):
            # Create dependency that requires specific account
            allowed_accounts = ["admin@project.iam.gserviceaccount.com"]
            dependency = require_service_account(allowed_accounts)
            
            # Test with allowed account
            auth_info = {
                "email": "admin@project.iam.gserviceaccount.com",
                "sub": "123"
            }
            
            # Should pass (mock the Depends injection)
            with patch('services.workload_identity_auth.verify_workload_identity', return_value=auth_info):
                result = await dependency(auth_info=auth_info)
                assert result == auth_info
            
            # Test with disallowed account
            auth_info_wrong = {
                "email": "user@project.iam.gserviceaccount.com",
                "sub": "456"
            }
            
            with pytest.raises(HTTPException) as exc_info:
                await dependency(auth_info=auth_info_wrong)
            
            assert exc_info.value.status_code == 403
            assert "not authorized" in str(exc_info.value.detail)


class TestWorkloadIdentityIntegration:
    """Integration tests for WI authentication with FastAPI"""
    
    @pytest.mark.asyncio
    async def test_verify_workload_identity_dependency(self):
        """Test the FastAPI dependency function"""
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "false"}, clear=True):
            # Call the dependency directly
            result = await verify_workload_identity(None)
            
            assert result is not None
            assert "email" in result
            assert result.get("development_mode") is True
    
    @pytest.mark.asyncio
    async def test_fastapi_route_protection(self):
        """Test WI authentication in FastAPI route context"""
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        @app.get("/secure")
        async def secure_endpoint(auth_info: dict = Depends(verify_workload_identity)):
            return {"authenticated_as": auth_info["email"]}
        
        # Test in development mode (auth disabled)
        with patch.dict(os.environ, {"REQUIRE_WI_AUTH": "false"}, clear=True):
            client = TestClient(app)
            response = client.get("/secure")
            
            assert response.status_code == 200
            data = response.json()
            assert "authenticated_as" in data


# Coverage target: >= 70%
# These tests cover:
# - Authentication bypass in development mode
# - Missing/invalid/empty Authorization headers
# - Valid token verification
# - Invalid token signature handling
# - Untrusted service account rejection
# - Invalid audience rejection
# - Trusted service accounts loading (env and defaults)
# - Development vs production mode behavior
# - Expected audience configuration
# - require_service_account dependency helper
# - FastAPI integration
