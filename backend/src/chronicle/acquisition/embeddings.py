"""Local text embeddings via Ollama (no API key, no cost).

Wraps Ollama's ``/api/embed`` batch endpoint behind an injected httpx.Client, so
unit tests drive it with MockTransport and the real call only happens against a
local daemon (mirrors ai/models/ollama.py). Default model is ``nomic-embed-text``.
"""

from __future__ import annotations

import os

import httpx

DEFAULT_OLLAMA_BASE_URL = os.environ.get("CHRONICLE_OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_TIMEOUT_SECONDS = 60.0


class EmbeddingError(RuntimeError):
    """The embedding provider could not return usable vectors."""


class OllamaEmbedder:
    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        model: str = DEFAULT_EMBEDDING_MODEL,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._model = model
        self._timeout = timeout
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)

    @property
    def model(self) -> str:
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self._client.post(
                "/api/embed",
                json={"model": self._model, "input": texts},
                timeout=self._timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"ollama embedding request failed: {exc}") from exc
        except ValueError as exc:
            raise EmbeddingError(f"ollama embedding returned invalid JSON: {exc}") from exc

        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingError(
                f"expected {len(texts)} embeddings, got {len(embeddings) if isinstance(embeddings, list) else 'none'}"
            )
        return embeddings

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
