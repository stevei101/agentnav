"""
Unit tests for Gemini Client Service (FR#090)

Tests verify that the Gemini client and reason_with_gemini work
with the current API (no legacy functions).
"""

import os
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_gemini_client_can_be_imported():
    """Verify GeminiClient and reason_with_gemini can be imported"""
    # Import gemini_client directly from file to avoid package side-effects
    base = os.path.dirname(os.path.dirname(__file__))
    gemini_path = os.path.join(base, "services", "gemini_client.py")
    spec = spec_from_file_location("services.gemini_client_test", gemini_path)
    module = module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)

    # Verify exports exist
    assert hasattr(module, "GeminiClient")
    assert hasattr(module, "reason_with_gemini")

    # Verify they are callable
    assert callable(getattr(module, "GeminiClient"))
    assert callable(getattr(module, "reason_with_gemini"))


def test_gemini_client_initialization_with_fake_genai(monkeypatch):
    """Test GeminiClient can be initialized with a fake genai module"""

    # Create a fake genai module
    class FakeModels:
        def generate(self, *args, **kwargs):
            return {"candidates": [{"content": {"text": "test response"}}]}

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    fake_genai = types.SimpleNamespace(Client=FakeClient)
    monkeypatch.setitem(sys.modules, "genai", fake_genai)

    # Import and test
    base = os.path.dirname(os.path.dirname(__file__))
    gemini_path = os.path.join(base, "services", "gemini_client.py")
    spec = spec_from_file_location("services.gemini_client_fake_test", gemini_path)
    module = module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)

    GeminiClient = getattr(module, "GeminiClient")
    client = GeminiClient()
    assert client is not None
