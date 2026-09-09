"""Hybrid retrieval: indexing, semantic search, RRF fusion (fake embedder)."""

from __future__ import annotations

from chronicle.acquisition.retrieval import (
    hybrid_search,
    index_passages,
    reciprocal_rank_fusion,
    semantic_search,
)
from chronicle.acquisition.vector_store import PassageVectorStore
from chronicle.contracts.shared import Passage


class FakeEmbedder:
    """Deterministic 2-D embeddings keyed off two marker words, so nearest-neighbour
    results are predictable without a real model."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(text) for text in texts]

    def embed_one(self, text: str) -> list[float]:
        lower = text.lower()
        return [float(lower.count("alpha")), float(lower.count("beta"))]


def _passage(pid: str, text: str) -> Passage:
    return Passage(id=pid, documentId="doc-0", excerpt=text, locator="chars 0-10")


def test_index_and_semantic_search_finds_nearest():
    store = PassageVectorStore()
    passages = [
        _passage("p-alpha", "alpha alpha alpha"),
        _passage("p-beta", "beta beta beta"),
        _passage("p-mixed", "alpha beta"),
    ]
    assert index_passages(passages, FakeEmbedder(), store) == 3

    results = semantic_search("alpha topic", FakeEmbedder(), store, k=2)
    assert results[0][0] == "p-alpha"  # most alpha-aligned ranks first


def test_semantic_search_empty_store():
    assert semantic_search("alpha", FakeEmbedder(), PassageVectorStore(), k=3) == []


def test_reciprocal_rank_fusion_rewards_agreement():
    lexical = ["a", "b", "c"]
    semantic = ["b", "a", "d"]
    fused = reciprocal_rank_fusion([lexical, semantic])
    order = [item_id for item_id, _ in fused]
    # "a" (ranks 0,1) and "b" (ranks 1,0) appear in both and lead
    assert set(order[:2]) == {"a", "b"}
    assert set(order) == {"a", "b", "c", "d"}


def test_hybrid_search_merges_both_lanes():
    top = hybrid_search(lexical_ids=["a", "b", "c"], semantic_ids=["c", "b", "e"], k=3)
    assert set(top[:2]) == {"b", "c"}  # present in both lanes -> fused to the top
    assert len(top) == 3
