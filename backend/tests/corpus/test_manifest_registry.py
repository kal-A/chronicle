"""CorpusRegistry: registration, lazy loading, caching, duplicate/unknown
handling. See E2 plan decision 6: importing chronicle.corpus.manifest
must never do file I/O -- only explicit registry.get_corpus() calls do."""

from __future__ import annotations

import pytest

from chronicle.corpus.errors import DuplicateCorpusIdError, UnknownCorpusError
from chronicle.corpus.manifest import CorpusRegistry, CorpusSource
from chronicle.corpus.package_corpus import PackageBackedCorpus

from .conftest import CORPUS_IDS


def test_registry_lists_both_builtin_corpora(registry):
    assert registry.list_corpus_ids() == sorted(CORPUS_IDS)


def test_registry_construction_does_not_load_any_package(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("PackageBackedCorpus.load() must not run during registry construction")

    monkeypatch.setattr(PackageBackedCorpus, "load", staticmethod(_boom))
    CorpusRegistry()  # must not raise


def test_get_corpus_returns_the_same_cached_instance(registry, corpus_id):
    first = registry.get_corpus(corpus_id)
    second = registry.get_corpus(corpus_id)
    assert first is second


def test_get_corpus_unknown_id_raises(registry):
    with pytest.raises(UnknownCorpusError):
        registry.get_corpus("no-such-corpus")


def test_get_manifest_unknown_id_raises(registry):
    with pytest.raises(UnknownCorpusError):
        registry.get_manifest("no-such-corpus")


def test_duplicate_registration_raises():
    registry = CorpusRegistry(sources=[])
    source = CorpusSource(
        corpus_id="dup",
        package_path=CORPUS_IDS[0],  # unused, never loaded in this test
        title="t",
        benchmark_role="r",
    )
    registry.register(source)
    with pytest.raises(DuplicateCorpusIdError):
        registry.register(source)


def test_list_manifests_returns_one_per_corpus(registry):
    manifests = registry.list_manifests()
    assert sorted(m.corpusId for m in manifests) == sorted(CORPUS_IDS)


def test_manifest_schema_version_matches_the_loaded_investigation(corpus):
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    assert manifest.schemaVersion == investigation.schemaVersion


def test_manifest_known_omissions_come_from_the_generation_report(corpus):
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    assert manifest.knownOmissions == list(investigation.generationReport.omissions)


def test_builtin_sources_pin_package_identity_and_hash():
    from chronicle.corpus.manifest import BUILTIN_CORPUS_SOURCES

    for source in BUILTIN_CORPUS_SOURCES:
        assert source.expected_package_id == source.corpus_id
        assert source.expected_package_hash
        assert source.expected_schema_version
        assert source.expected_package_revision is not None
