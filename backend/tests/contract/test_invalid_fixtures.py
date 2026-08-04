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
