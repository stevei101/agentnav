"""Tests for configuration."""
import pytest
from app.config import Settings, settings


def test_settings_instance():
    """Test that settings instance exists."""
    assert settings is not None
    assert isinstance(settings, Settings)


def test_settings_defaults():
    """Test default settings values."""
    assert settings.APP_NAME == "Prompt Vault Backend"
    assert settings.VERSION == "0.1.0"
    assert settings.PORT == 8080
    assert settings.A2A_PROTOCOL_ENABLED is True


def test_is_development():
    """Test development mode detection."""
    # Default should be production
    assert settings.is_development is False


def test_cors_origins():
    """Test CORS origins configuration."""
    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0

