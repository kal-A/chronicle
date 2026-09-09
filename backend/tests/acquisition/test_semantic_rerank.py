"""SemanticReranker: reorder lexical candidate passage ids by fusing the lexical
ranking with a local-semantic ranking (RRF). Operates on ids only, so it is
independent of the large PassageSearchHit projection."""

from __future__ import annotations

from chronicle.acquisition.retrieval import SemanticReranker
from chronicle.acquisition.vector_store import PassageVectorStore


class _FakeEmbedder:
    """embed_one returns a fixed query vector; embed unused here."""

    def __init__(self, query_vector: list[float]) -> None:
        self._q = query_vector

    def embed(self, texts: list[str]) -> list[list[float]]:  # pragma: no cover - unused
        return [self._q for _ in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._q


def _store_with(vectors: dict[str, list[float]]) -> PassageVectorStore:
    store = PassageVectorStore()
    store.add_many(list(vectors.items()))
    return store


def test_order_returns_a_permutation_of_the_candidates():
    store = _store_with({"p1": [1, 0, 0], "p2": [0, 1, 0], "p3": [0, 0, 1]})
    reranker = SemanticReranker(_FakeEmbedder([0, 1, 0]), store)

    ordered = reranker.order("q", ["p1", "p2", "p3"])

    assert sorted(ordered) == ["p1", "p2", "p3"]


def test_semantically_closest_lexical_tail_passage_is_promoted():
    # Lexical ranks p3 last; semantically the query is closest to p3.
    store = _store_with({"p1": [1, 0, 0], "p2": [0, 1, 0], "p3": [0, 0, 1]})
    reranker = SemanticReranker(_FakeEmbedder([0, 0, 1]), store)

    ordered = reranker.order("q", ["p1", "p2", "p3"])

    # p3 improves on its pure-lexical position (was index 2).
    assert ordered.index("p3") < 2


def test_empty_store_leaves_lexical_order_unchanged():
    reranker = SemanticReranker(_FakeEmbedder([1, 0, 0]), PassageVectorStore())

    ordered = reranker.order("q", ["p1", "p2", "p3"])

    assert ordered == ["p1", "p2", "p3"]


def test_ids_absent_from_the_store_still_appear():
    # A candidate with no embedding must not be dropped from the ranking.
    store = _store_with({"p1": [1, 0, 0]})
    reranker = SemanticReranker(_FakeEmbedder([1, 0, 0]), store)

    ordered = reranker.order("q", ["p1", "p2"])

    assert sorted(ordered) == ["p1", "p2"]
