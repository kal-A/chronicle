"""Local passage vector store: SQLite persistence + pure-Python cosine search.

A deliberately simple, dependency-free backend suitable for Chronicle's small
per-investigation corpora (a handful of sources, at most a few thousand passages).
Vectors are stored as JSON in SQLite so a built index survives across runs and
processes. The ``VectorStore`` interface hides this: a future swap to sqlite-vec /
FAISS / Chroma changes only the internals, not callers.

Semantic retrieval is the substrate for hybrid search (semantic + the existing
lexical corpus/search.py); wiring it into the agent retrieval tools is a later step.
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must share a dimension")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class PassageVectorStore:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS passage_vectors ("
            "  passage_id TEXT PRIMARY KEY,"
            "  dimension INTEGER NOT NULL,"
            "  vector TEXT NOT NULL"
            ")"
        )
        self._conn.commit()

    def add(self, passage_id: str, vector: list[float]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO passage_vectors (passage_id, dimension, vector) VALUES (?, ?, ?)",
            (passage_id, len(vector), json.dumps(vector)),
        )
        self._conn.commit()

    def add_many(self, items: list[tuple[str, list[float]]]) -> None:
        self._conn.executemany(
            "INSERT OR REPLACE INTO passage_vectors (passage_id, dimension, vector) VALUES (?, ?, ?)",
            [(pid, len(vec), json.dumps(vec)) for pid, vec in items],
        )
        self._conn.commit()

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM passage_vectors").fetchone()[0])

    def query(self, vector: list[float], k: int = 8) -> list[tuple[str, float]]:
        rows = self._conn.execute("SELECT passage_id, vector FROM passage_vectors").fetchall()
        scored: list[tuple[str, float]] = []
        for passage_id, vector_json in rows:
            stored = json.loads(vector_json)
            if len(stored) != len(vector):
                continue  # dimension mismatch (e.g. different embedding model) -> skip
            scored.append((passage_id, cosine_similarity(vector, stored)))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored[:k]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "PassageVectorStore":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
