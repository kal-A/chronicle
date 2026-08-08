"""Proves the Python contract mirror rejects the same broken packages the
TypeScript renderer rejects, and for the expected reason — see
fixtures/contracts/invalid/*.json and validation.py's rule numbering."""

import pytest

from chronicle.contracts import (
    GeneratedInvestigationValidationError,
    validate_generated_investigation,
)

from .conftest import INVALID_FIXTURES_DIR, load_json

EXPECTED_MESSAGE_FRAGMENTS = {
    "unsupported-version": "Unsupported GeneratedInvestigation schema version",
    "missing-evidence-reference": "references unknown Passage",
    "claim-without-supporting-evidence": "requires a supporting EvidenceLink",
    "disputed-relationship-missing-counterevidence": "requires supporting and counterevidence links",
    "overprecise-map-marker": "exceeds Place",
    "experience-plan-unknown-location": "unknown Place",
    "experience-plan-unknown-initial-lens": "unknown InvestigationLens",
}


@pytest.mark.parametrize("fixture_name", sorted(EXPECTED_MESSAGE_FRAGMENTS))
def test_invalid_fixture_is_rejected(fixture_name):
    data = load_json(INVALID_FIXTURES_DIR / f"{fixture_name}.json")
    with pytest.raises(GeneratedInvestigationValidationError) as excinfo:
        validate_generated_investigation(data)
    assert EXPECTED_MESSAGE_FRAGMENTS[fixture_name] in str(excinfo.value)


def test_all_invalid_fixtures_are_covered_by_a_case():
    on_disk = {p.stem for p in INVALID_FIXTURES_DIR.glob("*.json")}
    assert on_disk == set(EXPECTED_MESSAGE_FRAGMENTS)


def test_top_level_evidence_link_must_be_listed_by_its_target_record(golden_investigation):
    original = golden_investigation["evidenceLinks"][0]
    orphaned_from_target = {
        **original,
        "id": "evidence-link-not-listed-by-target",
    }
    golden_investigation["evidenceLinks"].append(orphaned_from_target)

    with pytest.raises(GeneratedInvestigationValidationError) as excinfo:
        validate_generated_investigation(golden_investigation)

    assert "is not listed by its target record" in str(excinfo.value)


def test_target_evidence_link_ids_must_not_contain_duplicates(golden_investigation):
    claim = golden_investigation["claims"][0]
    claim["evidenceLinkIds"].append(claim["evidenceLinkIds"][0])

    with pytest.raises(GeneratedInvestigationValidationError, match="duplicate EvidenceLink"):
        validate_generated_investigation(golden_investigation)
