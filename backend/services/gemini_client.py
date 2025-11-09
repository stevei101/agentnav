"""
Gemini client wrapper for Agentnav

Provides a small, flexible wrapper around the official Google GenAI Python SDK
so agents can consistently call Gemini models. The wrapper attempts to import
the installed SDK (several import paths are tolerated) and exposes an async
`generate` method and a convenience `reason_with_gemini` helper used by agents.

This module intentionally keeps initialization minimal so the SDK can pick up
credentials from the environment or Workload Identity (WI) when running on
Cloud Run.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Optional

logger = logging.getLogger(__name__)


# Flexible import: support multiple possible package layouts for the GenAI SDK.
genai = None

# Always honor a pre-inserted stub (used by unit tests)
if "genai" in sys.modules:
    genai = sys.modules["genai"]
else:
    try:
        import genai as _genai  # type: ignore

        genai = _genai
    except Exception:
        try:
            import google.genai as _genai  # type: ignore

            genai = _genai
        except Exception:
            genai = None


class GeminiClient:
    """Lightweight wrapper around the installed GenAI SDK client.

    The wrapper does not inject credentials; the SDK should use environment
    credentials or Workload Identity (WI) provided by Cloud Run.
    """

    def __init__(self, client: Optional[Any] = None):
        if client is not None:
            self._client = client
            return

        if genai is None:
            raise RuntimeError(
                "google-genai SDK is not installed. Install `google-genai` in requirements."
            )

        # Prefer an explicit Client() constructor if available
        ClientCtor = getattr(genai, "Client", None)
        if callable(ClientCtor):
            try:
                self._client = ClientCtor()
            except Exception:
                # Fall back to using module as client
                self._client = genai
        else:
            # Some SDK versions expose top-level helpers; use module directly
            self._client = genai

        logger.info("Initialized Gemini client wrapper")

    async def generate(
        self,
        model: Optional[str],
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
        **kwargs,
    ) -> Any:
        """Generate text from the specified model.

        This method attempts several common call signatures for different SDK
        versions. The call is run in a thread to avoid blocking if the SDK is
        synchronous.
        """

        def _sync_call():
            # Try client.models.generate(model=..., prompt=...)
            try:
                if hasattr(self._client, "models") and hasattr(
                    self._client.models, "generate"
                ):
                    # Newer SDKs (module.client.models.generate)
                    return self._client.models.generate(
                        model=model,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs,
                    )

                # genai.generate(...) or client.generate(...)
                if hasattr(self._client, "generate"):
                    return self._client.generate(
                        model=model,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs,
                    )

                # Older variants
                if hasattr(self._client, "generate_text"):
                    return self._client.generate_text(
                        model=model,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs,
                    )

            except Exception as e:
                # Surface SDK errors
                logger.exception("Error while calling GenAI SDK: %s", e)
                raise

            raise RuntimeError("Unsupported or unknown google-genai client interface")

        return await asyncio.to_thread(_sync_call)


async def reason_with_gemini(
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.0,
    model: Optional[str] = None,
) -> str:
    """Convenience helper used by agents for reasoning prompts.

    Uses cloud-based Gemini for all reasoning tasks.
    Agents should fetch prompt templates from prompt loader, format them,
    and call this helper.

    Args:
        prompt: The reasoning prompt to send.
        max_tokens: Maximum tokens in the response.
        temperature: Sampling temperature (0.0 = deterministic, higher = more creative).
        model: Optional explicit model name. Defaults to "gemini-1" or GEMINI_MODEL env var.

    Returns:
        The text response from Gemini.

    Raises:
        RuntimeError: If Gemini client fails to generate response.
    """
    # Use cloud Gemini via GenAI SDK
    model = model or os.environ.get("GEMINI_MODEL") or "gemini-1"
    client = GeminiClient()
    result = await client.generate(
        model=model, prompt=prompt, max_tokens=max_tokens, temperature=temperature
    )

    # Normalize a few common SDK return shapes
    # - Newer SDKs may return an object with .candidates or .output
    if isinstance(result, dict):
        # common pattern: {'candidates': [{'content': {'text': '...'}}]}
        candidates = result.get("candidates") or result.get("outputs")
        if isinstance(candidates, list) and len(candidates) > 0:
            first = candidates[0]
            # nested content
            content = first.get("content") or first.get("output") or first
            if isinstance(content, dict):
                text = content.get("text") or content.get("content")
                if text:
                    logger.info(
                        f"✅ Used Gemini service for reasoning (max_tokens={max_tokens})"
                    )
                    return text
            # fallback to string representation
            return str(first)

    # If result is a string-like return it
    if isinstance(result, str):
        logger.info(f"✅ Used Gemini service for reasoning (max_tokens={max_tokens})")
        return result

    # Last resort: return stringified result
    logger.info(f"✅ Used Gemini service for reasoning (max_tokens={max_tokens})")
    return str(result)
