import httpx

from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.ai.models.ollama import (
    DEFAULT_OLLAMA_BASE_URL,
    OllamaModelProvider,
    resolve_base_url_from_env,
)
from chronicle.ai.models.protocol import ModelProvider


def _null_client() -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})))


def test_deterministic_provider_satisfies_the_protocol_structurally():
    assert isinstance(DeterministicModelProvider(), ModelProvider)


def test_ollama_provider_satisfies_the_protocol_structurally():
    provider = OllamaModelProvider(base_url="http://fake:11434", client=_null_client())
    assert isinstance(provider, ModelProvider)


def test_base_url_defaults_to_local_ollama_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("CHRONICLE_OLLAMA_BASE_URL", raising=False)
    assert resolve_base_url_from_env() == DEFAULT_OLLAMA_BASE_URL


def test_base_url_env_var_overrides_the_default(monkeypatch):
    monkeypatch.setenv("CHRONICLE_OLLAMA_BASE_URL", "http://example-ollama:1234")
    assert resolve_base_url_from_env() == "http://example-ollama:1234"
