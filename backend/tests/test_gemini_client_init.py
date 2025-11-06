import sys
import types
import os
from importlib.util import spec_from_file_location, module_from_spec


def test_gemini_client_initializes(monkeypatch):
    """Verify GeminiClient can be initialized without hardcoded credentials.

    This test fakes a minimal `genai` module in sys.modules so the wrapper
    initializes the client without reaching out to external credentials.
    It imports the `gemini_client.py` file directly to avoid executing
    `backend/services/__init__.py` which pulls in Firestore and other heavy deps.
    """

    # Create a fake genai module with a Client class
    class FakeModels:
        def generate(self, *args, **kwargs):
            return {"candidates": [{"content": {"text": "ok"}}]}

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    fake_genai = types.SimpleNamespace(Client=FakeClient)

    monkeypatch.setitem(sys.modules, "genai", fake_genai)

    # Import gemini_client directly from file to avoid package side-effects
    base = os.path.dirname(os.path.dirname(__file__))
    gemini_path = os.path.join(base, "services", "gemini_client.py")
    spec = spec_from_file_location("services.gemini_client", gemini_path)
    module = module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)

    GeminiClient = getattr(module, "GeminiClient")

    client = GeminiClient()
    assert client is not None
    # Ensure the wrapped client has models.generate available
    assert hasattr(client._client, "models") or hasattr(client._client, "generate")


def test_reason_with_gemini_basic(monkeypatch):
    """Verify reason_with_gemini works with Gemini cloud service.

    This test verifies that reason_with_gemini successfully calls
    the Gemini cloud service for reasoning tasks.
    """
    import asyncio

    # Fake genai module for Gemini tests - must match the expected interface
    # The client needs to support models.generate() pattern (first check in _sync_call)
    # The code checks: hasattr(self._client, "models") and hasattr(self._client.models, "generate")
    class FakeModels:
        def generate(self, model=None, prompt=None, max_tokens=None, temperature=None, **kwargs):
            # Return response matching expected format
            return {"candidates": [{"content": {"text": "gemini_response"}}]}

    class FakeClient:
        def __init__(self):
            # Must have models attribute with generate method (this is the first check in _sync_call)
            self.models = FakeModels()
        
        # Also provide direct generate method as fallback (second check in _sync_call)
        def generate(self, model=None, prompt=None, max_tokens=None, temperature=None, **kwargs):
            # Direct generate method - return full response
            return {"candidates": [{"content": {"text": "gemini_response"}}]}

    fake_genai = types.SimpleNamespace(Client=FakeClient)
    
    # Clear any existing genai modules and gemini_client from cache
    # This must happen BEFORE setting up the fake to ensure clean state
    modules_to_clear = []
    for module_name in list(sys.modules.keys()):
        if (module_name in ["genai", "google.genai", "services.gemini_client", "backend.services.gemini_client"] or 
            module_name.startswith("google.genai.") or 
            module_name.startswith("services.gemini_client")):
            modules_to_clear.append(module_name)
    
    for module_name in modules_to_clear:
        del sys.modules[module_name]
    
    # Set up fake modules BEFORE importing gemini_client
    # gemini_client.py tries google.genai first, then genai
    # Use monkeypatch.delitem to ensure clean removal, then setitem to add fake
    if "google.genai" in sys.modules:
        monkeypatch.delitem(sys.modules, "google.genai", raising=False)
    if "genai" in sys.modules:
        monkeypatch.delitem(sys.modules, "genai", raising=False)
    
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "genai", fake_genai)

    # Import gemini_client directly from file to avoid package side-effects
    # This will use our fake modules since they're already in sys.modules
    base = os.path.dirname(os.path.dirname(__file__))
    gemini_path = os.path.join(base, "services", "gemini_client.py")
    spec = spec_from_file_location("services.gemini_client_model_test", gemini_path)
    module = module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)

    reason_with_gemini = getattr(module, "reason_with_gemini")

    # Test: Gemini service (cloud-based)
    # reason_with_gemini() creates its own GeminiClient() internally
    # which will call ClientCtor() (FakeClient) to create the client instance
    async def test_gemini():
        # Test reason_with_gemini helper - it creates GeminiClient() internally
        # which will use our FakeClient via ClientCtor()
        result = await reason_with_gemini(
            prompt="Test prompt", max_tokens=100, temperature=0.5
        )
        assert result == "gemini_response"

    asyncio.run(test_gemini())
