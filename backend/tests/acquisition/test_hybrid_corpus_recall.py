"""Recall-additive HybridCorpus: the semantic lane surfaces relevant passages the
lexical lane drops entirely (zero query-token overlap), bounded by a reserve so a
strong lexical hit is never fully displaced.

A deterministic fake embedder gives the semantic geometry (no Ollama, no network):
passages about the *concept* embed onto one axis, lexical-only decoys onto another,
so the test asserts recall behaviour independently of any real embedding model.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus
from chronicle.acquisition.hybrid_corpus import HybridCorpus
from chronicle.acquisition.retrieval import SemanticReranker, index_passages
from chronicle.acquisition.vector_store import PassageVectorStore
from chronicle.contracts.enums import RightsStatus, SourceType
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import PackageBackedCorpus

# The query shares tokens ONLY with the lexical-decoy source, so lexical search
# never returns the concept source; the concept source is reachable only
# semantically. "interdiction" is the concept marker the fake embedder keys on.
_QUERY = "alpha"


class _ConceptEmbedder:
    """Deterministic 2-D embedder. Text about the concept (contains 'interdiction')
    embeds to the concept axis; everything else -- including the lexical query
    'alpha' -- is judged by whether it is *about* the concept. The query is treated
    as a concept query so it retrieves the concept passages the lexical lane misses."""

    _CONCEPT = [1.0, 0.0]
    _OTHER = [0.0, 1.0]

    def _vec(self, text: str) -> list[float]:
        return self._CONCEPT if ("interdiction" in text or text.strip() == _QUERY) else self._OTHER

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return self._vec(text)


def _source(candidate_id: str, title: str, text: str) -> AcquiredSource:
    candidate = SourceCandidate(
        candidateId=candidate_id,
        connector="wikipedia",
        title=title,
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url=f"https://example.org/{candidate_id}",
        language="en",
    )
    return AcquiredSource(
        candidate=candidate,
        text=text,
        contentType="text/plain",
        contentSha256=f"hash-{candidate_id}",
        charCount=len(text),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def _hybrid(tmp_path, *, empty_index: bool = False) -> tuple[HybridCorpus, PackageBackedCorpus]:
    # Lexical-decoy source: contains the query token "alpha" but is off-concept.
    decoy = _source("wikipedia:en:decoy", "Alpha Notes", "alpha alpha padding padding padding. " * 30)
    # Concept source: relevant, but shares NO token with the query -> lexical drops it.
    concept = _source(
        "wikipedia:en:concept",
        "Naval Interdiction",
        "Naval interdiction throttled coastal supply lines and shifted the campaign. " * 20,
    )
    investigation = build_corpus(
        topic="a coastal campaign",
        interpreted_question="What shaped the campaign?",
        geographic_scope=["Region"],
        date_earliest=date(1860, 1, 1),
        date_latest=date(1865, 12, 31),
        acquired=[decoy, concept],
        passages=_chunk_all([decoy, concept]),
    )
    path = tmp_path / "pkg.json"
    path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")
    inner = PackageBackedCorpus.load(
        corpus_id="camp", package_path=path, title="Camp", benchmark_role="test"
    )

    store = PassageVectorStore(":memory:")
    if not empty_index:
        index_passages(list(inner.get_investigation().passages), _ConceptEmbedder(), store)
    return HybridCorpus(inner, SemanticReranker(_ConceptEmbedder(), store)), inner


def _chunk_all(sources):
    from chronicle.acquisition.chunking import chunk_source

    passages = []
    for src in sources:
        passages.extend(chunk_source(src))
    return passages


_CONCEPT_TITLE = "Naval Interdiction"
_DECOY_TITLE = "Alpha Notes"


def _title_of(inner: PackageBackedCorpus, passage_id: str) -> str:
    passage = inner.get_passage(passage_id)
    source_id = inner.get_document(passage.documentId).sourceId
    return inner.get_source(source_id).title


def _request(max_results: int) -> PassageSearchRequest:
    return PassageSearchRequest(corpusId="camp", query=_QUERY, maxResults=max_results)


def test_lexical_alone_misses_the_concept_source(tmp_path):
    # Precondition: the lexical lane genuinely cannot see the concept source, so any
    # concept passage in the hybrid result is a real recall gain, not a re-rank.
    _, inner = _hybrid(tmp_path)
    lexical = inner.search_passages(_request(20))
    titles = {_title_of(inner, h.passageId) for h in lexical.hits}
    assert _CONCEPT_TITLE not in titles, "lexical must not reach the concept source"
    assert _DECOY_TITLE in titles, "the decoy source should still match lexically"


def test_recall_additive_surfaces_a_semantically_relevant_passage(tmp_path):
    hybrid, inner = _hybrid(tmp_path)
    result = hybrid.search_passages(_request(2))

    titles = {_title_of(inner, h.passageId) for h in result.hits}
    assert _CONCEPT_TITLE in titles, "semantic recall should surface the source lexical missed"
    assert _DECOY_TITLE in titles, "the reserve should keep a lexical hit (never fully displaced)"
    assert result.returnedCount == len(result.hits) <= 2


def test_reserve_caps_semantic_only_passages(tmp_path):
    # With maxResults=2, at most floor(2/2)=1 slot may be semantic-only.
    hybrid, inner = _hybrid(tmp_path)
    result = hybrid.search_passages(_request(2))

    semantic_only = [h for h in result.hits if _title_of(inner, h.passageId) == _CONCEPT_TITLE]
    assert len(semantic_only) <= 1


def test_semantic_only_hit_is_well_formed(tmp_path):
    hybrid, inner = _hybrid(tmp_path)
    result = hybrid.search_passages(_request(2))

    concept_hits = [h for h in result.hits if _title_of(inner, h.passageId) == _CONCEPT_TITLE]
    assert concept_hits
    hit = concept_hits[0]
    assert hit.excerpt and hit.locator
    assert hit.sourceTitle == "Naval Interdiction"
    assert hit.evidenceLinks == [] and hit.matchedDates == []
    # The materialised hit must round-trip the corpus's own stored passage.
    assert hit.passageId in {p.id for p in inner.get_investigation().passages}


def test_empty_index_degrades_to_lexical(tmp_path):
    hybrid, inner = _hybrid(tmp_path, empty_index=True)
    hybrid_result = hybrid.search_passages(_request(2))
    lexical = inner.search_passages(_request(2))
    assert [h.passageId for h in hybrid_result.hits] == [h.passageId for h in lexical.hits]
