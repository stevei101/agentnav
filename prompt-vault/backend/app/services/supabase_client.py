"""Supabase client service for database operations."""
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self):
        """Initialize Supabase client."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            logger.warning("Supabase credentials not configured - client will be None")
            self.client: Optional[Client] = None
        else:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized")
    
    def is_available(self) -> bool:
        """Check if Supabase client is available."""
        return self.client is not None
    
    async def get_prompt(self, prompt_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a prompt by ID."""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            response = self.client.table("prompts").select("*").eq("id", prompt_id).eq("user_id", user_id).single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error fetching prompt {prompt_id}: {e}")
            raise
    
    async def get_prompt_versions(self, prompt_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a prompt."""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            response = self.client.table("prompt_versions").select("*").eq("prompt_id", prompt_id).eq("user_id", user_id).order("created_at", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching prompt versions for {prompt_id}: {e}")
            raise
    
    async def save_test_result(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save test result to database."""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            response = self.client.table("prompt_tests").insert(test_data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error saving test result: {e}")
            raise
    
    async def save_comparison(self, comparison_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save version comparison to database."""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            response = self.client.table("version_comparisons").insert(comparison_data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error saving comparison: {e}")
            raise
    
    async def save_suggestion(self, suggestion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save prompt suggestion to database."""
        if not self.client:
            raise RuntimeError("Supabase client not initialized")
        
        try:
            response = self.client.table("prompt_suggestions").insert(suggestion_data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error saving suggestion: {e}")
            raise


# Global instance
supabase_client = SupabaseClient()

