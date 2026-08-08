"""CorpusIndex: every derived index traces back to an explicit stored
field. No claims_by_entity index exists -- GeneratedClaim has no
entity-reference field anywhere in the contract (E2 plan decision 4)."""

from __future__ import annotations

from chronicle.corpus.indexing import CorpusIndex, build_index

EXPECTED_RECORD_COUNTS = {
    "blank-cheque-golden": {
        "sources_by_id": 4,
        "documents_by_id": 4,
        "passages_by_id": 6,
        "claims_by_id": 4,
        "relationships_by_id": 1,
        "events_by_id": 3,
        "entities_by_id": 8,
        "places_by_id": 2,
        "knowledge_states_by_id": 1,
        "evidence_links_by_id": 11,
    },
    "concert-of-europe-1814-1822": {
        "sources_by_id": 3,
        "documents_by_id": 3,
        "passages_by_id": 3,
        "claims_by_id": 5,
        "relationships_by_id": 3,
        "events_by_id": 5,
        "entities_by_id": 9,
        "places_by_id": 5,
        "knowledge_states_by_id": 0,
        "evidence_links_by_id": 14,
    },
}


def test_index_record_counts_match_the_known_fixture_counts(corpus, corpus_id):
    index = build_index(corpus.get_investigation())
    expected = EXPECTED_RECORD_COUNTS[corpus_id]
    for attribute_name, expected_count in expected.items():
        actual = len(getattr(index, attribute_name))
        assert actual == expected_count, f"{attribute_name}: expected {expected_count}, got {actual}"


def test_no_claims_by_entity_index_exists():
    """Guard against silently reintroducing an invented Claim<->Entity
    edge -- see indexing.py's module docstring."""
    assert not hasattr(CorpusIndex, "claims_by_entity")
    assert "claims_by_entity" not in CorpusIndex.__dataclass_fields__


def test_passages_by_document_matches_the_direct_field(corpus):
    index = build_index(corpus.get_investigation())
    for document_id, passage_ids in index.passages_by_document.items():
        for passage_id in passage_ids:
            assert index.passages_by_id[passage_id].documentId == document_id


def test_passages_by_source_derived_via_document_chain(corpus):
    index = build_index(corpus.get_investigation())
    for source_id, passage_ids in index.passages_by_source.items():
        for passage_id in passage_ids:
            passage = index.passages_by_id[passage_id]
            document = index.documents_by_id[passage.documentId]
            assert document.sourceId == source_id


def test_evidence_links_by_target_and_by_passage_are_consistent(corpus):
    index = build_index(corpus.get_investigation())
    for link in corpus.get_investigation().evidenceLinks:
        assert link in index.evidence_links_by_target[link.targetId]
        assert link in index.evidence_links_by_passage[link.passageId]


def test_events_use_explicit_timeline_order_then_honest_fallback(corpus):
    investigation = corpus.get_investigation()
    index = build_index(investigation)
    timeline_order = {entry.eventId: entry.order for entry in investigation.timeline}
    expected = sorted(
        index.events_by_id,
        key=lambda event_id: (
            0 if event_id in timeline_order else 1,
            timeline_order.get(event_id, index.events_by_id[event_id].eventTime.earliest),
            event_id,
        ),
    )
    assert index.events_sorted_by_date == expected


def test_relationships_by_node_includes_both_endpoints(corpus):
    index = build_index(corpus.get_investigation())
    for relationship in corpus.get_investigation().relationships:
        assert relationship.id in index.relationships_by_node[relationship.fromId]
        assert relationship.id in index.relationships_by_node[relationship.toId]


def test_all_ids_covers_every_typed_collection(corpus):
    index = build_index(corpus.get_investigation())
    assert set(index.sources_by_id) <= index.all_ids
    assert set(index.claims_by_id) <= index.all_ids
    assert set(index.events_by_id) <= index.all_ids
