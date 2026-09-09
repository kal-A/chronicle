"""OllamaEmbedder: batch embed via mocked /api/embed (no real daemon)."""

from __future__ import annotations

import httpx
import pytest

from chronicle.acquisition.embeddings import EmbeddingError, OllamaEmbedder


def _embedder(handler, **kwargs) -> OllamaEmbedder:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://fake-ollama:11434")
    return OllamaEmbedder(client=client, **kwargs)


def test_embed_returns_vectors_and_sends_model_and_input():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    embedder = _embedder(handler, model="nomic-embed-text")
    vectors = embedder.embed(["a", "b"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert captured[0].url.path == "/api/embed"
    import json

    body = json.loads(captured[0].content)
    assert body["model"] == "nomic-embed-text"
    assert body["input"] == ["a", "b"]


def test_embed_empty_list_is_a_noop():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not be called
        raise AssertionError("should not hit the network for empty input")

    assert _embedder(handler).embed([]) == []


def test_embed_one_returns_single_vector():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[1.0, 2.0, 3.0]]})

    assert _embedder(handler).embed_one("x") == [1.0, 2.0, 3.0]


def test_http_error_raises_embedding_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="down")

    with pytest.raises(EmbeddingError):
        _embedder(handler).embed(["a"])


def test_count_mismatch_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2]]})  # 1 for 2 inputs

    with pytest.raises(EmbeddingError):
        _embedder(handler).embed(["a", "b"])
