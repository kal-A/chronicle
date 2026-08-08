"""Shared fixtures for the Phase E2 tool-layer test suite. Mirrors
tests/corpus/conftest.py's parametrize-over-both-corpora pattern."""

from __future__ import annotations

import pytest

from chronicle.ai.tools import ToolExecutionContext, ToolRegistry, build_default_registry
from chronicle.corpus import CorpusRegistry, PackageBackedCorpus
from chronicle.corpus.manifest import BUILTIN_CORPUS_SOURCES

CORPUS_IDS = [source.corpus_id for source in BUILTIN_CORPUS_SOURCES]


@pytest.fixture
def corpus_registry() -> CorpusRegistry:
    return CorpusRegistry()


@pytest.fixture(params=CORPUS_IDS, ids=CORPUS_IDS)
def corpus_id(request) -> str:
    return request.param


@pytest.fixture
def corpus(corpus_registry: CorpusRegistry, corpus_id: str) -> PackageBackedCorpus:
    return corpus_registry.get_corpus(corpus_id)


@pytest.fixture
def other_corpus_id(corpus_id: str) -> str:
    others = [cid for cid in CORPUS_IDS if cid != corpus_id]
    assert len(others) == 1
    return others[0]


@pytest.fixture
def tool_registry() -> ToolRegistry:
    return build_default_registry()


@pytest.fixture
def context(corpus_id: str) -> ToolExecutionContext:
    return ToolExecutionContext(corpusId=corpus_id)
