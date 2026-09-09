"""corpus_builder tests, including the round-trip through the real
PackageBackedCorpus the four agents use — proving an acquired corpus is
loadable and searchable exactly like a curated fixture."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus, deterministic_package_id
from chronicle.contracts.enums import PackageStatus, RightsStatus, SourceType
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import (
    CAPABILITY_PASSAGES,
    CAPABILITY_SOURCE_COMPARISON,
    PackageBackedCorpus,
)


def _acquired(candidate_id: str, title: str, body: str, connector: str = "wikipedia") -> AcquiredSource:
    candidate = SourceCandidate(
        candidateId=candidate_id,
        connector=connector,
        title=title,
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url=f"https://example.org/{candidate_id}",
        language="en",
    )
    return AcquiredSource(
        candidate=candidate,
        text=body,
        contentType="text/plain",
        contentSha256=f"hash-{candidate_id}",
        charCount=len(body),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def _sample_inputs():
    src_a = _acquired("wikipedia:en:1", "Alpha Overview", "Alpha describes the zeppelin registry in detail. " * 20)
    src_b = _acquired("wikipedia:en:2", "Beta Overview", "Beta covers maritime signalling conventions. " * 20)
    passages = chunk_source(src_a) + chunk_source(src_b)
    return [src_a, src_b], passages


def test_build_corpus_produces_a_valid_partial_evidence_package():
    acquired, passages = _sample_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened in the placeholder subject?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        acquired=acquired,
        passages=passages,
    )

    assert investigation.status is PackageStatus.PARTIAL
    assert investigation.generationReport.outcome.value == "partial"
    assert len(investigation.sources) == 2
    assert len(investigation.documents) == 2
    assert len(investigation.passages) == len(passages)
    # no fabricated historical records
    assert investigation.claims == []
    assert investigation.relationships == []
    assert investigation.events == []
    assert investigation.knowledgeStates == []
    # one scope placeholder place, clearly proposed/unreviewed
    assert len(investigation.entities) == 1
    place = investigation.entities[0]
    assert place.entityType == "place"
    assert place.reviewStatus.value == "proposed"
    # every scene reference resolves (validator already enforced this on build)
    assert investigation.scenes[0].placeIds == [place.id]


def test_acquired_corpus_loads_and_searches_through_package_backed_corpus(tmp_path):
    acquired, passages = _sample_inputs()
    investigation = build_corpus(
        topic="a placeholder subject",
        interpreted_question="What happened?",
        geographic_scope=["Somewhere"],
        date_earliest=date(1800, 1, 1),
        date_latest=date(1850, 12, 31),
        acquired=acquired,
        passages=passages,
    )

    package_path = tmp_path / "acquired.json"
    package_path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")

    corpus = PackageBackedCorpus.load(
        corpus_id="acquired-test",
        package_path=package_path,
        title="Acquired Test Corpus",
        benchmark_role="acquisition round-trip test",
    )

    manifest = corpus.get_manifest()
    assert CAPABILITY_PASSAGES in manifest.supportedCapabilities
    assert CAPABILITY_SOURCE_COMPARISON in manifest.supportedCapabilities  # two sources

    result = corpus.search_passages(
        PassageSearchRequest(corpusId="acquired-test", query="zeppelin")
    )
    assert result.totalMatched >= 1
    assert any("zeppelin" in hit.excerpt.lower() for hit in result.hits)


def test_package_id_is_deterministic_for_same_topic_and_content():
    acquired, _ = _sample_inputs()
    first = deterministic_package_id("a placeholder subject", acquired)
    second = deterministic_package_id("a placeholder subject", acquired)
    assert first == second
    assert first.startswith("acq-")


def test_empty_geographic_scope_is_rejected():
    acquired, passages = _sample_inputs()
    with pytest.raises(ValueError):
        build_corpus(
            topic="x",
            interpreted_question="x?",
            geographic_scope=[],
            date_earliest=date(1800, 1, 1),
            date_latest=date(1850, 12, 31),
            acquired=acquired,
            passages=passages,
        )
