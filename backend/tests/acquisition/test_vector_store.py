"""PassageVectorStore: cosine ranking + SQLite persistence."""

from __future__ import annotations

from chronicle.acquisition.vector_store import PassageVectorStore, cosine_similarity


def test_cosine_similarity_basic():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0  # zero vector guard


def test_query_ranks_by_cosine_similarity():
    store = PassageVectorStore()
    store.add_many([
        ("p-near", [1.0, 0.1, 0.0]),
        ("p-far", [0.0, 0.0, 1.0]),
        ("p-mid", [0.7, 0.7, 0.0]),
    ])
    results = store.query([1.0, 0.0, 0.0], k=2)
    assert [pid for pid, _ in results] == ["p-near", "p-mid"]
    assert results[0][1] >= results[1][1]


def test_query_skips_dimension_mismatches():
    store = PassageVectorStore()
    store.add("ok", [1.0, 0.0])
    store.add("wrong-dim", [1.0, 0.0, 0.0])
    results = store.query([1.0, 0.0], k=5)
    assert [pid for pid, _ in results] == ["ok"]


def test_empty_store_returns_no_results():
    assert PassageVectorStore().query([1.0, 0.0], k=5) == []


def test_persists_across_connections(tmp_path):
    db_path = tmp_path / "vectors.db"
    with PassageVectorStore(db_path) as store:
        store.add("p1", [1.0, 2.0, 3.0])
        assert store.count() == 1

    reopened = PassageVectorStore(db_path)
    assert reopened.count() == 1
    assert reopened.query([1.0, 2.0, 3.0], k=1)[0][0] == "p1"
