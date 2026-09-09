"""HybridCorpus: transparently reorders search_passages results via a semantic
reranker, delegating every other InvestigationCorpus method to the inner corpus.
Uses a stub reranker (reverses candidate order) so the wiring is asserted
independently of RRF math."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus
from chronicle.acquisition.hybrid_corpus import HybridCorpus
from chronicle.contracts.enums import RightsStatus, SourceType
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import PackageBackedCorpus


class _ReverseReranker:
    """Deterministic stand-in: reverses the candidate order."""

    def order(self, query: str, candidate_ids: list[str]) -> list[str]:
        return list(reversed(candidate_ids))


def _inner_corpus(tmp_path) -> PackageBackedCorpus:
    candidate = SourceCandidate(
        candidateId="wikipedia:en:1",
        connector="wikipedia",
        title="Alpha Overview",
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url="https://example.org/1",
        language="en",
    )
    src = AcquiredSource(
        candidate=candidate,
        text="Alpha describes the zeppelin registry in detail. " * 40,
        contentType="text/plain",
        contentSha256="hash-1",
        charCount=2000,
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )
    investigation = build_corpus(
        topic="the zeppelin registry",
        interpreted_question="What happened?",
        geographic_scope=["Europe"],
        date_earliest=date(1900, 1, 1),
        date_latest=date(1910, 12, 31),
        acquired=[src],
        passages=chunk_source(src),
    )
    path = tmp_path / "pkg.json"
    path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")
    return PackageBackedCorpus.load(
        corpus_id="zep", package_path=path, title="Zep", benchmark_role="test"
    )


def _request(max_results: int = 2) -> PassageSearchRequest:
    return PassageSearchRequest(corpusId="zep", query="zeppelin", maxResults=max_results)


def test_no_reranker_is_identical_to_inner(tmp_path):
    inner = _inner_corpus(tmp_path)
    hybrid = HybridCorpus(inner, None)

    assert hybrid.search_passages(_request()) == inner.search_passages(_request())


def test_reranker_reorders_hits_and_respects_the_original_limit(tmp_path):
    inner = _inner_corpus(tmp_path)
    hybrid = HybridCorpus(inner, _ReverseReranker())

    # expanded lexical candidate set (what the reranker sees), in lexical order
    expanded = inner.search_passages(_request(2).model_copy(update={"maxResults": 8}))
    expected_first = list(reversed([h.passageId for h in expanded.hits]))[:2]

    result = hybrid.search_passages(_request(2))

    assert result.returnedCount == len(result.hits) <= 2
    assert [h.passageId for h in result.hits] == expected_first
    assert result.corpusId == "zep"


def test_delegates_other_methods_to_inner(tmp_path):
    inner = _inner_corpus(tmp_path)
    hybrid = HybridCorpus(inner, _ReverseReranker())

    assert hybrid.corpus_id == inner.corpus_id
    assert hybrid.get_investigation().packageId == inner.get_investigation().packageId
    assert hybrid.get_manifest().corpusId == inner.get_manifest().corpusId
