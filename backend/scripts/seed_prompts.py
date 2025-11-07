"""
Seed Prompts Script
Initializes agent_prompts collection in Firestore with default prompts

Usage:
    python backend/scripts/seed_prompts.py
"""

import logging
import os
import sys
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.firestore_client import get_firestore_client
from services.prompt_loader import get_prompt_loader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Default prompts
PROMPTS = {
    "visualizer_graph_generation": """Generate a {viz_type} visualization for the following content.

Content:
{content}

Return a JSON structure with:
- nodes: array of {{id, label, group}}
- edges: array of {{from, to, label}}

Focus on key concepts and their relationships.""",
    # Placeholder prompts for future agents
    "orchestrator_system_instruction": """You are the Orchestrator Agent for Agentic Navigator.

Your role is to coordinate the analysis process by:
1. Determining the content type (document or codebase)
2. Delegating tasks to specialized agents
3. Synthesizing results from all agents
4. Returning a comprehensive analysis

Always maintain context and ensure all agents work collaboratively.""",
    "summarizer_system_instruction": """You are the Summarizer Agent for Agentic Navigator.

Your role is to:
1. Read the entire content comprehensively
2. Identify key themes and concepts
3. Generate concise, accurate summaries
4. Highlight important points and insights

Focus on clarity and completeness in your summarization.""",
    "linker_system_instruction": """You are the Linker Agent for Agentic Navigator.

Your role is to:
1. Identify key entities (concepts, functions, classes, etc.)
2. Map relationships between entities
3. Categorize relationship types
4. Provide structured relationship data

Focus on accuracy and relevance in your relationship mapping.""",
}


def seed_prompts():
    """
    Seed agent_prompts collection with default prompts
    """
    logger.info("🌱 Starting prompt seeding...")

    try:
        collection = get_firestore_client().get_collection("agent_prompts")

        seeded_count = 0
        updated_count = 0

        for prompt_id, prompt_text in PROMPTS.items():
            try:
                # Check if document exists
                doc_ref = collection.document(prompt_id)
                doc = doc_ref.get()

                if doc.exists:
                    # Update existing document
                    logger.info(f"  ↻ Updating existing prompt: {prompt_id}")
                    current_version = doc.to_dict().get("version", 1)
                    doc_ref.update(
                        {
                            "prompt_text": prompt_text,
                            "updated_at": datetime.now(timezone.utc),
                            "version": current_version + 1,
                        }
                    )
                    updated_count += 1
                else:
                    # Create new document
                    logger.info(f"  ➕ Creating new prompt: {prompt_id}")
                    now = datetime.now(timezone.utc)
                    doc_ref.set(
                        {
                            "prompt_text": prompt_text,
                            "created_at": now,
                            "updated_at": now,
                            "version": 1,
                            "metadata": {
                                "agent_name": prompt_id.split("_")[0],
                                "prompt_type": "_".join(prompt_id.split("_")[1:]),
                            },
                        }
                    )
                    seeded_count += 1

            except Exception as e:
                logger.error(f"  ❌ Error processing {prompt_id}: {e}")
                continue

        logger.info("✅ Seeding complete!")
        logger.info(f"   Created: {seeded_count}")
        logger.info(f"   Updated: {updated_count}")

        # Verify the seed
        verify_seed()

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        sys.exit(1)


def verify_seed():
    """
    Verify that prompts were seeded successfully
    """
    logger.info("🔍 Verifying seed...")

    try:
        for prompt_id in PROMPTS.keys():
            try:
                get_prompt_loader().get_prompt(prompt_id)
                logger.info(f"  ✓ {prompt_id}: Loaded successfully")
            except Exception as e:
                logger.error(f"  ✗ {prompt_id}: Failed to load - {e}")

    except Exception as e:
        logger.error(f"Verification failed: {e}")


if __name__ == "__main__":
    seed_prompts()
