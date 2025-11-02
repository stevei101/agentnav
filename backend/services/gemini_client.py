"""
Gemini Client Service
Standardized client for Google Gemini model interaction using official google-genai SDK

This service implements FR#090: Standardize AI Model Interaction with Google GenAI Python SDK.
All direct calls to Gemini models should use this client for consistency and feature access.
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logger.warning("google-genai package not installed. Install with: pip install google-genai")

# Global client instance (lazy initialization)
if GENAI_AVAILABLE:
    _gemini_client: Optional[genai.GenerativeModel] = None
else:
    _gemini_client = None


def get_gemini_client(model_name: str = "gemini-1.5-flash"):
    """
    Get or create Gemini client instance
    
    This function initializes the Google GenAI client with proper authentication.
    It uses Workload Identity (WI) in deployed environments or API key for local development.
    
    Args:
        model_name: Name of the Gemini model to use (default: "gemini-1.5-flash")
        
    Returns:
        GenerativeModel instance configured for Gemini
        
    Raises:
        ValueError: If API key is missing in local development
        RuntimeError: If client initialization fails or package not installed
        
    Authentication Methods (in priority order):
    1. Workload Identity (WI) - Automatic in Cloud Run (GCP environment)
    2. GOOGLE_APPLICATION_CREDENTIALS - Service account JSON file path
    3. GEMINI_API_KEY - API key from environment variable (local development)
    
    Note:
        In Cloud Run, Workload Identity automatically provides credentials.
        No explicit API key needed when running in GCP environment.
    """
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-genai package is not installed. Install with: pip install google-genai")
    
    global _gemini_client
    
    # Reuse existing client if already initialized
    if _gemini_client is not None:
        return _gemini_client
    
    try:
        # Check if running in GCP environment (Cloud Run, GCE, etc.)
        # GCP environments automatically provide credentials via Application Default Credentials
        gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID")
        
        if gcp_project:
            # Running in GCP - use Application Default Credentials (Workload Identity)
            logger.info(f"🔐 Using Application Default Credentials (Workload Identity) for GCP project: {gcp_project}")
            # GenAI SDK automatically uses Application Default Credentials when available
            # No explicit API key needed
            genai.configure()
        else:
            # Local development - require API key
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                error_msg = (
                    "GEMINI_API_KEY environment variable is required for local development. "
                    "In Cloud Run, credentials are provided automatically via Workload Identity."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info("🔑 Using GEMINI_API_KEY for local development")
            genai.configure(api_key=api_key)
        
        # Initialize the GenerativeModel with safety settings
        _gemini_client = genai.GenerativeModel(
            model_name=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        logger.info(f"✅ Gemini client initialized successfully (model: {model_name})")
        return _gemini_client
        
    except Exception as e:
        error_msg = f"Failed to initialize Gemini client: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def generate_content(
    prompt: str,
    context: Optional[str] = None,
    model_name: str = "gemini-1.5-flash",
    temperature: float = 0.7,
    max_output_tokens: Optional[int] = None,
    **kwargs
) -> str:
    """
    Generate content using Gemini model
    
    This is the primary method for interacting with Gemini models. It handles
    prompt formatting, model configuration, and response parsing.
    
    Args:
        prompt: The main prompt text (can include template variables)
        context: Optional additional context to prepend to the prompt
        model_name: Gemini model to use (default: "gemini-1.5-flash")
        temperature: Sampling temperature (0.0-1.0, default: 0.7)
        max_output_tokens: Maximum tokens to generate (optional)
        **kwargs: Additional generation config parameters
        
    Returns:
        Generated text content
        
    Raises:
        RuntimeError: If generation fails
        ValueError: If prompt is empty
        
    Example:
        ```python
        response = await generate_content(
            prompt="Summarize this document: {content}",
            context="This is a technical document about...",
            temperature=0.3
        )
        ```
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    try:
        client = get_gemini_client(model_name=model_name)
        
        # Format full prompt with context if provided
        full_prompt = prompt
        if context:
            full_prompt = f"Context: {context}\n\n{prompt}"
        
        # Build generation config
        generation_config = {
            "temperature": temperature,
        }
        if max_output_tokens:
            generation_config["max_output_tokens"] = max_output_tokens
        
        # Merge additional kwargs into generation config
        generation_config.update(kwargs)
        
        logger.debug(f"Generating content with Gemini ({model_name})")
        logger.debug(f"Prompt length: {len(full_prompt)} chars")
        
        # Generate content (GenAI SDK is synchronous, so run in thread pool for async compatibility)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.generate_content(
                full_prompt,
                generation_config=generation_config
            )
        )
        
        # Extract text from response
        generated_text = response.text if response.text else ""
        
        logger.debug(f"Generated {len(generated_text)} characters")
        return generated_text
        
    except Exception as e:
        error_msg = f"Failed to generate content with Gemini: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


async def generate_content_with_prompt_template(
    prompt_template_id: str,
    template_variables: Dict[str, Any],
    context: Optional[str] = None,
    model_name: str = "gemini-1.5-flash",
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    Generate content using a prompt template from Firestore (FR#003 integration)
    
    This method integrates with FR#003 (Prompt Management) by:
    1. Loading the prompt template from Firestore
    2. Formatting it with runtime variables
    3. Submitting to Gemini via the official SDK
    
    Args:
        prompt_template_id: Document ID in agent_prompts Firestore collection
        template_variables: Dictionary of variables to format into template
        context: Optional additional context to prepend
        model_name: Gemini model to use
        temperature: Sampling temperature
        **kwargs: Additional generation config parameters
        
    Returns:
        Generated text content
        
    Raises:
        ValueError: If prompt template not found or template variables missing
        RuntimeError: If generation fails
        
    Example:
        ```python
        response = await generate_content_with_prompt_template(
            prompt_template_id="linker_system_instruction",
            template_variables={"content": document_text, "content_type": "document"},
            temperature=0.3
        )
        ```
    """
    try:
        from .prompt_loader import get_prompt
        
        # Load prompt template from Firestore (FR#003)
        prompt_template = get_prompt(prompt_template_id)
        
        # Format template with variables
        try:
            formatted_prompt = prompt_template.format(**template_variables)
        except KeyError as e:
            error_msg = f"Missing template variable in prompt {prompt_template_id}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        
        # Generate content using formatted prompt
        return await generate_content(
            prompt=formatted_prompt,
            context=context,
            model_name=model_name,
            temperature=temperature,
            **kwargs
        )
        
    except ImportError:
        # Fallback if prompt_loader not available
        logger.warning("Prompt loader not available, using direct prompt")
        return await generate_content(
            prompt=str(template_variables),
            context=context,
            model_name=model_name,
            temperature=temperature,
            **kwargs
        )
    except Exception as e:
        error_msg = f"Failed to generate content with prompt template: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def reset_client():
    """
    Reset the global client instance (useful for testing)
    
    This function clears the cached client, forcing re-initialization
    on the next call to get_gemini_client().
    """
    global _gemini_client
    _gemini_client = None
    logger.info("Gemini client reset")

