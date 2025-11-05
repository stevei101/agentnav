"""
Prompt Management Service
Firestore-based service for prompt CRUD operations
"""
import os
import logging
from typing import List, Optional
from datetime import datetime
from google.cloud import firestore
from models.prompt_models import Prompt, PromptVersion, TestResult
from services.firestore_client import get_firestore_client

logger = logging.getLogger(__name__)


class PromptService:
    """Service for managing prompts in Firestore"""
    
    def __init__(self):
        self.db = get_firestore_client().client
        self.prompts_collection = "prompts"
        self.versions_collection = "versions"
    
    def create_prompt(
        self, 
        prompt_data: dict, 
        user_id: str, 
        user_name: str
    ) -> Prompt:
        """Create a new prompt"""
        prompt_id = prompt_data.get("id") or self._generate_id()
        now = datetime.utcnow().isoformat()
        
        prompt = Prompt(
            id=prompt_id,
            title=prompt_data.get("title", "Untitled Prompt"),
            content=prompt_data.get("content", ""),
            tags=prompt_data.get("tags", []),
            createdAt=now,
            updatedAt=now,
            userId=user_id,
            userName=user_name,
            version=1,
            testResults=[]
        )
        
        # Save to Firestore
        doc_ref = self.db.collection(self.prompts_collection).document(prompt_id)
        doc_ref.set(prompt.dict())
        
        # Save initial version
        self._save_version(prompt_id, prompt, user_id, user_name, 1)
        
        logger.info(f"✅ Created prompt: {prompt_id}")
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID"""
        doc_ref = self.db.collection(self.prompts_collection).document(prompt_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        return Prompt(**doc.to_dict())
    
    def list_prompts(self, user_id: Optional[str] = None) -> List[Prompt]:
        """List all prompts, optionally filtered by user"""
        query = self.db.collection(self.prompts_collection)
        
        if user_id:
            query = query.where("userId", "==", user_id)
        
        # Order by updatedAt descending
        query = query.order_by("updatedAt", direction=firestore.Query.DESCENDING)
        
        docs = query.stream()
        prompts = []
        
        for doc in docs:
            try:
                prompts.append(Prompt(**doc.to_dict()))
            except Exception as e:
                logger.error(f"Error parsing prompt {doc.id}: {e}")
        
        return prompts
    
    def update_prompt(
        self, 
        prompt_id: str, 
        updates: dict, 
        user_id: str, 
        user_name: str
    ) -> Optional[Prompt]:
        """Update a prompt and save version history"""
        doc_ref = self.db.collection(self.prompts_collection).document(prompt_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        existing = Prompt(**doc.to_dict())
        now = datetime.utcnow().isoformat()
        new_version = existing.version + 1
        
        # Build updated prompt
        updated_dict = existing.dict()
        updated_dict.update({
            **updates,
            "updatedAt": now,
            "version": new_version,
            "lastEditedBy": user_name,
            "createdAt": existing.createdAt,  # Preserve original
            "userId": existing.userId,  # Preserve original creator
            "userName": existing.userName,
        })
        
        updated = Prompt(**updated_dict)
        
        # Save updated prompt
        doc_ref.set(updated.dict())
        
        # Save version history
        self._save_version(prompt_id, updated, user_id, user_name, new_version)
        
        logger.info(f"✅ Updated prompt: {prompt_id} to version {new_version}")
        return updated
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt"""
        doc_ref = self.db.collection(self.prompts_collection).document(prompt_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return False
        
        # Delete the prompt
        doc_ref.delete()
        
        # Delete all versions (optional - you might want to keep versions)
        versions_query = self.db.collection(self.versions_collection).where("promptId", "==", prompt_id)
        for version_doc in versions_query.stream():
            version_doc.reference.delete()
        
        logger.info(f"✅ Deleted prompt: {prompt_id}")
        return True
    
    def get_versions(self, prompt_id: str) -> List[PromptVersion]:
        """Get version history for a prompt"""
        query = self.db.collection(self.versions_collection)\
            .where("promptId", "==", prompt_id)\
            .order_by("version", direction=firestore.Query.DESCENDING)
        
        docs = query.stream()
        versions = []
        
        for doc in docs:
            try:
                versions.append(PromptVersion(**doc.to_dict()))
            except Exception as e:
                logger.error(f"Error parsing version {doc.id}: {e}")
        
        return versions
    
    def add_test_result(
        self, 
        prompt_id: str, 
        test_data: dict, 
        user_id: str, 
        user_name: str
    ) -> Optional[Prompt]:
        """Add a test result to a prompt"""
        doc_ref = self.db.collection(self.prompts_collection).document(prompt_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        prompt = Prompt(**doc.to_dict())
        
        # Create test result
        test_result = TestResult(
            id=self._generate_id(),
            result=test_data.get("result", "success"),
            notes=test_data.get("notes", ""),
            model=test_data.get("model", "gemini-pro"),
            createdAt=datetime.utcnow().isoformat(),
            userId=user_id,
            userName=user_name
        )
        
        # Add to prompt's test results (keep last 10)
        test_results = prompt.testResults or []
        test_results.insert(0, test_result)
        prompt.testResults = test_results[:10]  # Keep last 10
        
        # Update prompt
        prompt.updatedAt = datetime.utcnow().isoformat()
        doc_ref.set(prompt.dict())
        
        logger.info(f"✅ Added test result to prompt: {prompt_id}")
        return prompt
    
    def _save_version(
        self, 
        prompt_id: str, 
        prompt: Prompt, 
        user_id: str, 
        user_name: str, 
        version: int
    ):
        """Save a version to version history"""
        version_id = self._generate_id()
        version_data = PromptVersion(
            id=version_id,
            promptId=prompt_id,
            version=version,
            title=prompt.title,
            content=prompt.content,
            tags=prompt.tags,
            createdAt=prompt.updatedAt,
            userId=user_id,
            userName=user_name
        )
        
        self.db.collection(self.versions_collection).document(version_id).set(version_data.dict())
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        import uuid
        return str(uuid.uuid4())


# Singleton instance
_prompt_service: Optional[PromptService] = None


def get_prompt_service() -> PromptService:
    """Get or create the global PromptService singleton"""
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service

