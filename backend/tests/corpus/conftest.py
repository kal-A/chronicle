"""Shared fixtures for the Phase E2 corpus test suite. The `corpus`
fixture is parametrized over both real benchmark corpora -- any test
that requests it runs once per corpus automatically, satisfying "both
corpora pass the same shared tests" without hand-duplicating test
files."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chronicle.corpus import CorpusRegistry, PackageBackedCorpus
from chronicle.corpus.manifest import BUILTIN_CORPUS_SOURCES

REPO_ROOT = Path(__file__).resolve().parents[3]
INVALID_FIXTURES_DIR = REPO_ROOT / "fixtures" / "contracts" / "invalid"

CORPUS_IDS = [source.corpus_id for source in BUILTIN_CORPUS_SOURCES]


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def registry() -> CorpusRegistry:
    return CorpusRegistry()


@pytest.fixture(params=CORPUS_IDS, ids=CORPUS_IDS)
def corpus_id(request) -> str:
    return request.param


@pytest.fixture
def corpus(registry: CorpusRegistry, corpus_id: str) -> PackageBackedCorpus:
    return registry.get_corpus(corpus_id)


@pytest.fixture
def other_corpus_id(corpus_id: str) -> str:
    """The one CORPUS_IDS entry that is NOT the current corpus_id --
    used by cross-corpus isolation tests."""
    others = [cid for cid in CORPUS_IDS if cid != corpus_id]
    assert len(others) == 1
    return others[0]
