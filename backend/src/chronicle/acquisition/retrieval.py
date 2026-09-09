"""Hybrid retrieval helper: fuse lexical and local-semantic passage rankings.

The existing ``corpus/search.py`` gives strong lexical retrieval; this adds a
semantic lane over locally-embedded passages and fuses the two rankings with
Reciprocal Rank Fusion (RRF) — a simple, robust combiner that needs no score
normalization between the two very different scoring schemes.

This is the retrieval substrate. Wiring it into the agents' typed retrieval tools
(so the Planner/Analyst can request hybrid search over a built corpus) is a P2 step;
kept here, decoupled and unit-tested, so that wiring is mechanical.

The embedder is duck-typed (anything with ``embed(list[str]) -> list[list[float]]``
and ``embed_one(str) -> list[float]``), so tests inject a deterministic fake and the
real ``OllamaEmbedder`` drops in unchanged.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from ..contracts.shared import Passage
from .vector_store import PassageVectorStore

DEFAULT_RRF_K = 60


class SupportsEmbedding(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...


def index_passages(
    passages: list[Passage],
    embedder: SupportsEmbedding,
    store: PassageVectorStore,
    *,
    batch_size: int = 32,
) -> int:
    """Embed passage excerpts and add them to the vector store. Returns the count."""
    ids = [p.id for p in passages]
    texts = [p.excerpt for p in passages]
    added = 0
    for start in range(0, len(texts), batch_size):
        chunk_ids = ids[start : start + batch_size]
        vectors = embedder.embed(texts[start : start + batch_size])
        store.add_many(list(zip(chunk_ids, vectors)))
        added += len(chunk_ids)
    return added


def semantic_search(
    query: str,
    embedder: SupportsEmbedding,
    store: PassageVectorStore,
    *,
    k: int = 8,
) -> list[tuple[str, float]]:
    if store.count() == 0:
        return []
    return store.query(embedder.embed_one(query), k=k)


def reciprocal_rank_fusion(
    rankings: list[list[str]],
    *,
    k: int = DEFAULT_RRF_K,
) -> list[tuple[str, float]]:
    """Fuse ranked id lists into one ranking. Each list contributes 1/(k+rank)."""
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, item_id in enumerate(ranking):
            scores[item_id] += 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def hybrid_search(
    *,
    lexical_ids: list[str],
    semantic_ids: list[str],
    k: int = 8,
    rrf_k: int = DEFAULT_RRF_K,
) -> list[str]:
    """Fuse a lexical ranking and a semantic ranking into the top-k passage ids."""
    fused = reciprocal_rank_fusion([lexical_ids, semantic_ids], k=rrf_k)
    return [item_id for item_id, _ in fused[:k]]
