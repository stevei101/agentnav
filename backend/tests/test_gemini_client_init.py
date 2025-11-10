import os
import sys
import types
from importlib.util import module_from_spec, spec_from_file_location


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

    fake_genai = types.ModuleType("google.genai")
    fake_genai.Client = FakeClient

    monkeypatch.setitem(sys.modules, "genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    existing_google = sys.modules.get("google")
    if existing_google is None:
        fake_google_pkg = types.ModuleType("google")
        monkeypatch.setitem(sys.modules, "google", fake_google_pkg)
        existing_google = fake_google_pkg

    monkeypatch.setattr(existing_google, "genai", fake_genai, raising=False)

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

    # Fake genai module for Gemini tests
    class FakeModels:
        def generate(self, *args, **kwargs):
            return {"candidates": [{"content": {"text": "gemini_response"}}]}

    class FakeClient:
        def __init__(self):
            self.models = FakeModels()

    fake_genai = types.ModuleType("google.genai")
    fake_genai.Client = FakeClient

    monkeypatch.setitem(sys.modules, "genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    existing_google = sys.modules.get("google")
    if existing_google is None:
        fake_google_pkg = types.ModuleType("google")
        monkeypatch.setitem(sys.modules, "google", fake_google_pkg)
        existing_google = fake_google_pkg

    monkeypatch.setattr(existing_google, "genai", fake_genai, raising=False)

    # Import gemini_client
    base = os.path.dirname(os.path.dirname(__file__))
    gemini_path = os.path.join(base, "services", "gemini_client.py")
    spec = spec_from_file_location("services.gemini_client_model_test", gemini_path)
    module = module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    loader.exec_module(module)

    reason_with_gemini = getattr(module, "reason_with_gemini")

    # Test: Gemini service (cloud-based)
    async def test_gemini():
        result = await reason_with_gemini(
            prompt="Test prompt", max_tokens=100, temperature=0.5
        )
        assert result == "gemini_response"

    asyncio.run(test_gemini())
