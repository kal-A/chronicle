"""corpus.search.search_passages: lexical scoring, filters, ranking,
bounds -- no embeddings, deterministic only. Parametrized over both real
corpora via the `corpus` fixture."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from chronicle.contracts.enums import EvidenceLinkRole, EvidenceTargetType
from chronicle.corpus.contracts import (
    MAX_EXCERPT_LENGTH,
    MAX_QUERY_LENGTH,
    MAX_RESULT_COUNT,
    DateRangeFilter,
    PassageDateRole,
    PassageSearchRequest,
)
from chronicle.corpus.errors import UnknownRecordError
from chronicle.corpus.bounds import CollectionBudget
from chronicle.corpus.search import _round_robin_allocate, _score, _truncate


def _search(corpus, **kwargs):
    request = PassageSearchRequest(corpusId=corpus.corpus_id, **kwargs)
    return corpus.search_passages(request)


def test_link_annotation_density_does_not_inflate_relevance_score():
    index = SimpleNamespace(
        claims_by_id={
            "claim-a": SimpleNamespace(statement="alpha"),
            "claim-b": SimpleNamespace(statement="alpha"),
        },
        relationships_by_id={},
    )
    passage = SimpleNamespace(excerpt="unrelated wording")
    source = SimpleNamespace(title="unrelated source")
    document = SimpleNamespace(editionCitation="unrelated document")

    one_link_score = sum(
        factor.contribution
        for factor in _score(index, passage, source, document, ["alpha"], {"claim-a"}, set())
    )
    duplicate_annotation_score = sum(
        factor.contribution
        for factor in _score(
            index,
            passage,
            source,
            document,
            ["alpha"],
            {"claim-a", "claim-b"},
            set(),
        )
    )

    assert duplicate_annotation_score == one_link_score


def test_edition_citation_score_factor_names_the_field_it_scores():
    index = SimpleNamespace(claims_by_id={}, relationships_by_id={})
    factors = _score(
        index,
        SimpleNamespace(excerpt="unrelated wording"),
        SimpleNamespace(title="unrelated source"),
        SimpleNamespace(editionCitation="Vienna settlement"),
        ["vienna", "settlement"],
        set(),
        set(),
    )

    assert [factor.factor for factor in factors] == ["exact_phrase_edition_citation"]


def test_round_robin_nested_budget_prevents_dense_first_hit_starvation():
    assert _round_robin_allocate(
        [["dense-a", "dense-b", "dense-c"], ["later-hit"]],
        CollectionBudget(2),
    ) == [["dense-a"], ["later-hit"]]


def test_empty_query_is_rejected_by_pydantic(corpus):
    with pytest.raises(ValidationError):
        PassageSearchRequest(corpusId=corpus.corpus_id, query="")


def test_query_over_max_length_is_rejected(corpus):
    with pytest.raises(ValidationError):
        PassageSearchRequest(corpusId=corpus.corpus_id, query="x" * (MAX_QUERY_LENGTH + 1))


def test_max_results_cannot_exceed_the_hard_cap(corpus):
    with pytest.raises(ValidationError):
        PassageSearchRequest(corpusId=corpus.corpus_id, query="test", maxResults=MAX_RESULT_COUNT + 1)


def test_no_matches_returns_an_empty_result(corpus):
    result = _search(corpus, query="zzznonexistentzzz")
    assert result.totalMatched == 0
    assert result.hits == []
    assert result.truncated is False
    assert result.returnedCount == 0


def test_case_and_punctuation_are_normalized(corpus):
    lower = _search(corpus, query="vienna", maxResults=MAX_RESULT_COUNT)
    upper = _search(corpus, query="VIENNA!!!", maxResults=MAX_RESULT_COUNT)
    assert {h.passageId for h in lower.hits} == {h.passageId for h in upper.hits}


def test_exact_phrase_from_a_real_passage_ranks_that_passage_first(corpus):
    passage = corpus.get_investigation().passages[0]
    words = passage.excerpt.split()
    if len(words) < 3:
        pytest.skip("passage too short for a meaningful phrase test")
    phrase = " ".join(words[:4])
    result = _search(corpus, query=phrase, maxResults=MAX_RESULT_COUNT)
    assert result.hits, "expected the source passage to match its own excerpt phrase"
    assert result.hits[0].passageId == passage.id
    phrase_factors = [factor for factor in result.hits[0].scoreFactors if factor.factor == "exact_phrase_excerpt"]
    assert phrase_factors
    assert set(phrase_factors[0].matchedTerms) == set(word.lower().strip(".,;:\"'") for word in words[:4])


def test_partial_word_is_not_treated_as_a_token_match(corpus):
    """A raw substring such as ``vien`` must not match the token ``Vienna``."""
    assert _search(corpus, query="vien", maxResults=MAX_RESULT_COUNT).hits == []


def test_all_hit_ids_belong_to_this_corpus(corpus):
    result = _search(corpus, query="the", maxResults=MAX_RESULT_COUNT)
    known_passage_ids = {p.id for p in corpus.get_investigation().passages}
    for hit in result.hits:
        assert hit.passageId in known_passage_ids


def test_hits_preserve_locator_visibility_curation_and_limitations(corpus):
    result = _search(corpus, query="the", maxResults=MAX_RESULT_COUNT)
    investigation = corpus.get_investigation()
    passages = {passage.id: passage for passage in investigation.passages}
    documents = {document.id: document for document in investigation.documents}
    sources = {source.id: source for source in investigation.sources}
    for hit in result.hits:
        passage = passages[hit.passageId]
        document = documents[hit.documentId]
        source = sources[hit.sourceId]
        assert hit.locator == passage.locator
        assert hit.gapNote == passage.gapNote
        assert hit.documentVisibility == document.visibility.value
        assert hit.sourceCurationStatus == source.curationStatus.value
        assert hit.sourceLimitations == source.knownLimitations
        assert hit.documentLimitations == document.knownLimitations


def test_source_filter_narrows_results_to_that_source(corpus):
    source = corpus.get_investigation().sources[0]
    result = _search(corpus, query="the", sourceIds=[source.id], maxResults=MAX_RESULT_COUNT)
    for hit in result.hits:
        assert hit.sourceId == source.id


def test_unknown_source_id_filter_raises(corpus):
    with pytest.raises(UnknownRecordError):
        _search(corpus, query="test", sourceIds=["no-such-source"])


def test_unknown_document_id_filter_raises(corpus):
    with pytest.raises(UnknownRecordError):
        _search(corpus, query="test", documentIds=["no-such-document"])


def test_unknown_claim_id_filter_raises(corpus):
    with pytest.raises(UnknownRecordError):
        _search(corpus, query="test", claimIds=["no-such-claim"])


def test_unknown_relationship_id_filter_raises(corpus):
    with pytest.raises(UnknownRecordError):
        _search(corpus, query="test", relationshipIds=["no-such-relationship"])


def test_unknown_entity_id_filter_raises(corpus):
    with pytest.raises(UnknownRecordError):
        _search(corpus, query="test", entityIds=["no-such-entity"])


def test_unknown_event_id_filter_raises(corpus):
    with pytest.raises(UnknownRecordError):
        _search(corpus, query="test", eventIds=["no-such-event"])


def test_unknown_evidence_role_is_rejected_by_the_typed_request(corpus):
    with pytest.raises(ValidationError):
        _search(corpus, query="test", evidenceRoles=["not-a-real-role"])


def test_unknown_source_classification_is_rejected_by_the_typed_request(corpus):
    with pytest.raises(ValidationError):
        _search(corpus, query="test", sourceClassifications=["not-a-real-type"])


def test_result_cap_is_respected(corpus):
    result = _search(corpus, query="the", maxResults=1)
    assert len(result.hits) <= 1


def test_truncated_flag_is_set_when_more_matches_exist_than_returned(corpus):
    full = _search(corpus, query="the", maxResults=MAX_RESULT_COUNT)
    if full.totalMatched < 2:
        pytest.skip("not enough matches in this fixture to exercise truncation")
    capped = _search(corpus, query="the", maxResults=1)
    assert capped.truncated is True
    assert capped.totalMatched == full.totalMatched


def test_hits_are_sorted_by_score_desc_then_passage_id_asc(corpus):
    result = _search(corpus, query="the", maxResults=MAX_RESULT_COUNT)
    scores_and_ids = [(-h.score, h.passageId) for h in result.hits]
    assert scores_and_ids == sorted(scores_and_ids)


def test_evidence_role_filter_returns_only_matching_passages(corpus):
    result = _search(corpus, query="the", evidenceRoles=["supporting"], maxResults=MAX_RESULT_COUNT)
    for hit in result.hits:
        assert any(link.role == "supporting" for link in hit.evidenceLinks)


def test_evidence_link_projection_keeps_each_role_attached_to_its_target(corpus):
    result = _search(corpus, query="the", maxResults=MAX_RESULT_COUNT)
    for hit in result.hits:
        for projection in hit.evidenceLinks:
            stored = next(
                link
                for link in corpus.get_investigation().evidenceLinks
                if link.id == projection.evidenceLinkId
            )
            assert (projection.targetType, projection.targetId, projection.role) == (
                stored.targetType.value,
                stored.targetId,
                stored.role.value,
            )


def test_entity_filter_is_a_text_match_every_hit_contains_the_name(corpus):
    """E2 plan decision 4: entity association in search is a text match,
    never a structural claim -- proven here by asserting every returned
    hit's excerpt actually contains the entity's canonical name."""
    entity = next(e for e in corpus.get_investigation().entities if e.entityType == "person")
    result = _search(corpus, query="the", entityIds=[entity.id], maxResults=MAX_RESULT_COUNT)
    for hit in result.hits:
        assert entity.canonicalName.lower() in hit.excerpt.lower()


def test_date_range_filter_excludes_passages_outside_the_range(corpus):
    far_future = date(2100, 1, 1)
    result = _search(
        corpus,
        query="the",
        dateRange=DateRangeFilter(earliest=far_future),
        dateRoles=[PassageDateRole.SOURCE_DATE],
        maxResults=MAX_RESULT_COUNT,
    )
    assert result.hits == []


def test_date_filter_uses_requested_role_and_reports_the_matching_role(corpus):
    timed = next((p for p in corpus.get_investigation().passages if p.sentTime is not None), None)
    if timed is None:
        pytest.skip("corpus has no passage sent time")
    token = timed.excerpt.split()[0]
    result = _search(
        corpus,
        query=token,
        documentIds=[timed.documentId],
        dateRange=DateRangeFilter(earliest=timed.sentTime.latest, latest=timed.sentTime.latest),
        dateRoles=[PassageDateRole.SENT_TIME],
    )
    assert result.hits
    assert [match.role for match in result.hits[0].matchedDates] == [PassageDateRole.SENT_TIME]


def test_date_filter_uses_interval_overlap_not_only_earliest(corpus):
    investigation = corpus.get_investigation()
    passage = investigation.passages[0]
    passage.sentTime = passage.sentTime.model_copy(
        update={"earliest": date(1914, 7, 1), "latest": date(1914, 7, 10), "precision": "range"}
    ) if passage.sentTime else None
    if passage.sentTime is None:
        pytest.skip("fixture passage has no sent time")
    from chronicle.corpus.indexing import build_index
    from chronicle.corpus.search import search_passages

    result = search_passages(
        build_index(investigation),
        PassageSearchRequest(
            corpusId=corpus.corpus_id,
            query=passage.excerpt.split()[0],
            documentIds=[passage.documentId],
            dateRange=DateRangeFilter(earliest=date(1914, 7, 10), latest=date(1914, 7, 10)),
            dateRoles=[PassageDateRole.SENT_TIME],
        ),
    )
    assert [hit.passageId for hit in result.hits] == [passage.id]


def test_received_time_is_distinct_from_sent_and_source_time(corpus):
    from chronicle.contracts.shared import HistoricalDate
    from chronicle.corpus.indexing import build_index
    from chronicle.corpus.search import search_passages

    investigation = corpus.get_investigation()
    passage = investigation.passages[0]
    received = HistoricalDate(
        precision="exact",
        earliest=date(1933, 4, 12),
        latest=date(1933, 4, 12),
        label="synthetic received-time regression",
    )
    passage.receivedTime = received
    result = search_passages(
        build_index(investigation),
        PassageSearchRequest(
            corpusId=corpus.corpus_id,
            query=passage.excerpt.split()[0],
            documentIds=[passage.documentId],
            dateRange=DateRangeFilter(earliest=received.earliest, latest=received.latest),
            dateRoles=[PassageDateRole.RECEIVED_TIME],
        ),
    )
    assert [hit.passageId for hit in result.hits] == [passage.id]
    assert result.hits[0].matchedDates[0].role == PassageDateRole.RECEIVED_TIME
    assert result.hits[0].matchedDates[0].linkedTargetId is None


def test_evidence_role_filter_is_conjoined_with_the_requested_target(corpus):
    from chronicle.corpus.indexing import build_index
    from chronicle.corpus.search import search_passages

    investigation = corpus.get_investigation()
    if len(investigation.claims) < 2:
        pytest.skip("corpus needs two claims for mixed-target regression")
    passage = investigation.passages[0]
    template = investigation.evidenceLinks[0]
    claim_a, claim_b = investigation.claims[:2]
    investigation.evidenceLinks = [
        template.model_copy(
            update={
                "id": "mixed-context-a",
                "targetType": EvidenceTargetType.CLAIM,
                "targetId": claim_a.id,
                "passageId": passage.id,
                "role": EvidenceLinkRole.CONTEXT,
            }
        ),
        template.model_copy(
            update={
                "id": "mixed-support-b",
                "targetType": EvidenceTargetType.CLAIM,
                "targetId": claim_b.id,
                "passageId": passage.id,
                "role": EvidenceLinkRole.SUPPORTING,
            }
        ),
    ]

    result = search_passages(
        build_index(investigation),
        PassageSearchRequest(
            corpusId=corpus.corpus_id,
            query=passage.excerpt.split()[0],
            documentIds=[passage.documentId],
            claimIds=[claim_a.id],
            evidenceRoles=["supporting"],
        ),
    )

    assert result.hits == []


def test_linked_event_date_filter_is_scoped_to_the_requested_event(corpus):
    from chronicle.contracts.shared import HistoricalDate
    from chronicle.corpus.indexing import build_index
    from chronicle.corpus.search import search_passages

    investigation = corpus.get_investigation()
    if len(investigation.events) < 2:
        pytest.skip("corpus needs two events for mixed-date regression")
    passage = investigation.passages[0]
    template = investigation.evidenceLinks[0]
    event_a, event_b = investigation.events[:2]
    event_a.eventTime = HistoricalDate(
        precision="exact",
        earliest=date(1900, 1, 1),
        latest=date(1900, 1, 1),
    )
    event_b.eventTime = HistoricalDate(
        precision="exact",
        earliest=date(1950, 1, 1),
        latest=date(1950, 1, 1),
    )
    investigation.evidenceLinks = [
        template.model_copy(
            update={
                "id": "mixed-event-a",
                "targetType": EvidenceTargetType.EVENT,
                "targetId": event_a.id,
                "passageId": passage.id,
                "role": EvidenceLinkRole.SUPPORTING,
            }
        ),
        template.model_copy(
            update={
                "id": "mixed-event-b",
                "targetType": EvidenceTargetType.EVENT,
                "targetId": event_b.id,
                "passageId": passage.id,
                "role": EvidenceLinkRole.SUPPORTING,
            }
        ),
    ]

    result = search_passages(
        build_index(investigation),
        PassageSearchRequest(
            corpusId=corpus.corpus_id,
            query=passage.excerpt.split()[0],
            documentIds=[passage.documentId],
            eventIds=[event_a.id],
            dateRange=DateRangeFilter(earliest=date(1950, 1, 1), latest=date(1950, 1, 1)),
            dateRoles=[PassageDateRole.LINKED_EVENT_TIME],
        ),
    )

    assert result.hits == []


@pytest.mark.parametrize(
    "target_type,role,collection_name,date_field",
    [
        ("event", PassageDateRole.LINKED_EVENT_TIME, "events", "eventTime"),
        (
            "knownAtTime",
            PassageDateRole.LINKED_ACTOR_AWARENESS_TIME,
            "knowledgeStates",
            "asOfDate",
        ),
    ],
)
def test_linked_target_date_roles_are_filtered_and_reported(
    corpus, target_type, role, collection_name, date_field
):
    investigation = corpus.get_investigation()
    target_ids = {record.id for record in getattr(investigation, collection_name)}
    link = next(
        (
            candidate
            for candidate in investigation.evidenceLinks
            if candidate.targetType.value == target_type and candidate.targetId in target_ids
        ),
        None,
    )
    if link is None:
        pytest.skip(f"corpus has no passage linked to {target_type}")
    passage = next(item for item in investigation.passages if item.id == link.passageId)
    target = next(item for item in getattr(investigation, collection_name) if item.id == link.targetId)
    historical = getattr(target, date_field)
    result = _search(
        corpus,
        query=passage.excerpt.split()[0],
        documentIds=[passage.documentId],
        dateRange=DateRangeFilter(earliest=historical.latest, latest=historical.latest),
        dateRoles=[role],
    )
    assert result.hits
    assert any(
        match.role == role and match.linkedTargetId == link.targetId
        for match in result.hits[0].matchedDates
    )


def test_truncate_respects_max_excerpt_length():
    long_text = "word " * 300
    truncated = _truncate(long_text)
    assert len(truncated) <= MAX_EXCERPT_LENGTH


def test_truncate_leaves_short_excerpts_unchanged():
    short_text = "A short excerpt."
    assert _truncate(short_text) == short_text
