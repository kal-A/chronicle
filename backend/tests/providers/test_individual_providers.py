"""One focused test per provider, checking the specific fields downstream
stages (and ultimately the composer) actually depend on — not full package
validation, which test_pipeline_end_to_end.py already covers."""

from chronicle.providers.mock.assessment import assess_sources
from chronicle.providers.mock.composition import compose_investigation
from chronicle.providers.mock.corpus import assemble_corpus
from chronicle.providers.mock.discovery import prepare_discovery_queries
from chronicle.providers.mock.extraction import extract_historical_model
from chronicle.providers.mock.geography import assemble_geography
from chronicle.providers.mock.relationships import propose_relationships
from chronicle.providers.mock.scope import propose_scope
from chronicle.providers.mock.source_candidates import discover_source_candidates
from chronicle.providers.mock.timeline import build_timeline
from chronicle.providers.verification import verify_investigation


def _build_up_to_corpus(topic: str) -> dict:
    data = {"topic": topic}
    data = propose_scope(data)
    data = prepare_discovery_queries(data)
    data = discover_source_candidates(data)
    data = assess_sources(data)
    data = assemble_corpus(data)
    return data


def _build_up_to_historical_model(topic: str) -> dict:
    data = _build_up_to_corpus(topic)
    data = extract_historical_model(data)
    data = build_timeline(data)
    data = propose_relationships(data)
    data = assemble_geography(data)
    return data


def test_scope_provider_produces_non_empty_required_arrays():
    data = propose_scope({"topic": "Test Topic"})
    scope = data["scope"]
    assert scope["geographicScope"]
    assert scope["approvalStatus"] == "proposed"
    assert data["slug"] == "test-topic"


def test_discovery_provider_references_the_scope_stage():
    data = propose_scope({"topic": "Test Topic"})
    data = prepare_discovery_queries(data)
    assert data["discoveryQueries"][0]["id"].startswith("query-test-topic")


def test_source_candidate_provider_references_a_discovery_query():
    data = propose_scope({"topic": "Test Topic"})
    data = prepare_discovery_queries(data)
    data = discover_source_candidates(data)
    candidate = data["sourceCandidates"][0]
    assert candidate["discoveryQueryId"] == data["discoveryQueries"][0]["id"]


def test_assessment_provider_accepts_every_candidate():
    data = propose_scope({"topic": "Test Topic"})
    data = prepare_discovery_queries(data)
    data = discover_source_candidates(data)
    data = assess_sources(data)
    assert all(a["status"] == "ACCEPTED_EVIDENCE" for a in data["sourceAssessments"])


def test_corpus_assembler_produces_a_source_document_passage_chain():
    data = _build_up_to_corpus("Test Topic")
    corpus = data["corpus"]
    assert len(corpus["sources"]) == 1
    assert corpus["documents"][0]["sourceId"] == corpus["sources"][0]["id"]
    assert corpus["passages"][0]["documentId"] == corpus["documents"][0]["id"]


def test_extraction_provider_gives_every_claim_a_supporting_evidence_link():
    data = _build_up_to_corpus("Test Topic")
    data = extract_historical_model(data)

    links_by_target = {link["targetId"]: link for link in data["evidenceLinks"] if link["targetType"] == "claim"}
    for claim in data["claims"]:
        assert claim["id"] in links_by_target
        assert links_by_target[claim["id"]]["role"] == "supporting"


def test_extraction_provider_events_reference_a_place_entity():
    data = _build_up_to_corpus("Test Topic")
    data = extract_historical_model(data)
    place_ids = {e["id"] for e in data["entities"] if e["entityType"] == "place"}
    assert data["events"][0]["placeId"] in place_ids


def test_timeline_provider_has_one_entry_per_event():
    data = _build_up_to_corpus("Test Topic")
    data = extract_historical_model(data)
    data = build_timeline(data)
    assert len(data["timeline"]) == len(data["events"])
    assert data["timeline"][0]["eventId"] == data["events"][0]["id"]


def test_relationship_provider_adds_a_supporting_link_for_directly_supported_classification():
    data = _build_up_to_corpus("Test Topic")
    data = extract_historical_model(data)
    data = build_timeline(data)
    before_link_count = len(data["evidenceLinks"])
    data = propose_relationships(data)

    relationship = data["relationships"][0]
    assert relationship["evidenceClassification"] == "directly_supported"
    assert len(data["evidenceLinks"]) == before_link_count + 1
    new_link = data["evidenceLinks"][-1]
    assert new_link["targetType"] == "relationship"
    assert new_link["targetId"] == relationship["id"]
    assert new_link["role"] == "supporting"


def test_geography_provider_honestly_produces_no_map_assets():
    data = _build_up_to_historical_model("Test Topic")
    assert data["mapAssets"] == []
    assert data["mapScenes"] == []
    assert data["geographyOmitted"] is True


def test_composer_builds_a_claim_ledger_with_a_supporting_link():
    data = _build_up_to_historical_model("Test Topic")
    data = compose_investigation(data)
    package = data["package"]

    ledger = package["claimLedgers"][0]
    assert ledger["claimId"] == package["claims"][0]["id"]
    assert ledger["evidenceLinkIds"]


def test_verification_stage_marks_the_check_as_passed():
    data = _build_up_to_historical_model("Test Topic")
    data = compose_investigation(data)

    verified = verify_investigation(data)
    checks = verified["generationReport"]["verificationChecks"]
    assert any(check["status"] == "passed" for check in checks)
