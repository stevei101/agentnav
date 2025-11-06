"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings for Prompt Vault Backend."""
    
    # Application
    APP_NAME: str = "Prompt Vault Backend"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode should be enabled."""
        return self.DEBUG or self.is_development
    
    # Server (Cloud Run sets PORT automatically)
    HOST: str = "0.0.0.0"
    PORT: int = 8001  # Changed to 8001 to avoid conflict with other services (cursor-ide uses 8080, agentnav uses 8080)
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # cursor-ide
        "http://localhost:5176",  # prompt-vault frontend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5176",
    ]
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Firestore Configuration
    FIRESTORE_PROJECT_ID: Optional[str] = None
    FIRESTORE_DATABASE_ID: Optional[str] = "(default)"
    
    # Gemini API
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Default model (stable), can be overridden
    
    # ADK Configuration
    ADK_AGENT_CONFIG_PATH: str = "/app/config/agents.yaml"
    A2A_PROTOCOL_ENABLED: bool = True
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",  # Ignore extra environment variables
    }


# Global settings instance
settings = Settings()

