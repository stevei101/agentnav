"""
Firestore Client Service
Singleton pattern for managing Firestore database connections
"""

import os
import logging
from typing import Optional
from google.cloud import firestore

logger = logging.getLogger(__name__)


class FirestoreClient:
    """
    Singleton Firestore client wrapper

    Handles connection initialization and provides access to Firestore database.
    Supports both production and emulator environments.
    """

    def __init__(self):
        """Initialize Firestore client (private, use get_client())"""
        self._client: Optional[firestore.Client] = None
        self._project_id: Optional[str] = None
        self._database_id: Optional[str] = None

    def _initialize(self):
        """
        Initialize Firestore client connection

        Automatically detects emulator or production environment based on
        FIRESTORE_EMULATOR_HOST environment variable.
        """
        if self._client is not None:
            return self._client

        try:
            # Get configuration from environment
            self._project_id = os.getenv("FIRESTORE_PROJECT_ID", "agentnav-dev")
            self._database_id = os.getenv("FIRESTORE_DATABASE_ID", "default")
            emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

            # Initialize client
            if emulator_host:
                # Use emulator for local development
                logger.info(f"🔧 Using Firestore emulator: {emulator_host}")
                logger.info(
                    f"   Project: {self._project_id}, Database: {self._database_id}"
                )

                # Note: Firestore client for emulator doesn't require explicit connection
                # The emulator_host environment variable is sufficient
                self._client = firestore.Client(
                    project=self._project_id, database=self._database_id
                )
            else:
                # Use production Firestore
                logger.info(f"☁️  Using production Firestore")
                logger.info(
                    f"   Project: {self._project_id}, Database: {self._database_id}"
                )

                self._client = firestore.Client(
                    project=self._project_id, database=self._database_id
                )

            logger.info("✅ Firestore client initialized successfully")
            return self._client

        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore client: {e}")
            raise

    @property
    def client(self) -> firestore.Client:
        """
        Get Firestore client instance (lazy initialization)

        Returns:
            Initialized Firestore client
        """
        if self._client is None:
            self._initialize()
        return self._client

    def get_collection(self, collection_name: str):
        """
        Get a Firestore collection reference

        Args:
            collection_name: Name of the collection

        Returns:
            Collection reference
        """
        return self.client.collection(collection_name)

    def get_document(self, collection_name: str, document_id: str):
        """
        Get a Firestore document reference

        Args:
            collection_name: Name of the collection
            document_id: Document ID

        Returns:
            Document reference
        """
        return self.client.collection(collection_name).document(document_id)


# Singleton instance
_firestore_singleton: Optional[FirestoreClient] = None


def get_firestore_client() -> FirestoreClient:
    """
    Get or create the global Firestore client singleton

    Returns:
        FirestoreClient instance
    """
    global _firestore_singleton
    if _firestore_singleton is None:
        _firestore_singleton = FirestoreClient()
    return _firestore_singleton


def get_client() -> firestore.Client:
    """
    Convenience function to get the raw Firestore client

    Returns:
        google.cloud.firestore.Client instance
    """
    return get_firestore_client().client
