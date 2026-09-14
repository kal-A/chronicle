"""Python mirror of the ControlState / TerritoryGeometry contract tests
(ADR-004 addendum, Slice T2a). Proves the additive time-indexed territory layer
validates the same way in both languages: the record shapes accept valid data,
reject malformed data, and — being optional/additive — leave every existing
package valid, defaulting to empty when omitted.

T2a adds only the SHAPES. The cross-record rules (geometryRef resolves, evidence
grounding, precision/fuzziness honesty, the territory facet flip) are Slice T2b.
"""

import copy

import pytest
from pydantic import ValidationError

from chronicle.contracts import (
    ControlState,
    TerritoryGeometry,
    validate_generated_investigation,
)

VALID_GEOMETRY = {
    "id": "geo-1",
    "type": "Polygon",
    "coordinates": [[[10.0, 36.0], [11.0, 36.0], [11.0, 37.0], [10.0, 36.0]]],
    "sourceDataset": "historical-basemaps",
    "attestedYear": -218,  # BC snapshot year the polygon actually came from
    "license": "CC0-1.0",
    "polity": "Carthage",
}

VALID_CONTROL_STATE = {
    "id": "cs-1",
    "polity": "Carthage",
    "kind": "controlled",
    "validFrom": {"precision": "range", "earliest": "1900-01-01", "latest": "1900-12-31"},
    "validTo": {"precision": "range", "earliest": "1901-01-01", "latest": "1901-12-31"},
    "geometryRef": "geo-1",
    "precision": "region",
    "evidenceLinkIds": ["el-1"],
    "reviewStatus": "proposed",
    "visibility": "public",
}


def test_record_shapes_accept_valid_data():
    geometry = TerritoryGeometry.model_validate(VALID_GEOMETRY)
    assert geometry.attestedYear == -218
    assert geometry.polity == "Carthage"

    control = ControlState.model_validate(VALID_CONTROL_STATE)
    assert control.kind.value == "controlled"
    assert control.evidenceLinkIds == ["el-1"]


def test_territory_geometry_polity_is_optional():
    without_polity = {k: v for k, v in VALID_GEOMETRY.items() if k != "polity"}
    assert TerritoryGeometry.model_validate(without_polity).polity is None


@pytest.mark.parametrize(
    "mutation",
    [
        {"evidenceLinkIds": []},  # a control assertion must cite ≥1 passage
        {"kind": "occupied"},  # not a ControlStateKind member
        {"geometryRef": ""},  # must reference a geometry
        {"precision": "street"},  # not a LocationPrecision member
    ],
)
def test_control_state_rejects_malformed(mutation):
    bad = {**VALID_CONTROL_STATE, **mutation}
    with pytest.raises(ValidationError):
        ControlState.model_validate(bad)


@pytest.mark.parametrize(
    "mutation",
    [
        {"coordinates": []},  # a polygon needs coordinates
        {"type": "Point"},  # only Polygon / MultiPolygon are territory geometry
        {"license": ""},  # provenance is mandatory
    ],
)
def test_territory_geometry_rejects_malformed(mutation):
    bad = {**VALID_GEOMETRY, **mutation}
    with pytest.raises(ValidationError):
        TerritoryGeometry.model_validate(bad)


def _package_with_grounded_territory(golden: dict) -> dict:
    """A copy of the golden package with a fully-grounded ControlState: a
    supporting EvidenceLink (targetType controlState) over an existing passage,
    listed bidirectionally, plus its sourced geometry."""
    package = copy.deepcopy(golden)
    passage_id = package["passages"][0]["id"]
    package["evidenceLinks"].append(
        {
            "id": "el-cs-1",
            "targetType": "controlState",
            "targetId": "cs-1",
            "passageId": passage_id,
            "role": "supporting",
        }
    )
    package["territoryGeometries"] = [copy.deepcopy(VALID_GEOMETRY)]
    package["controlStates"] = [{**copy.deepcopy(VALID_CONTROL_STATE), "evidenceLinkIds": ["el-cs-1"]}]
    return package


def test_existing_package_stays_valid_without_the_territory_layer(golden_investigation):
    result = validate_generated_investigation(golden_investigation)
    assert result.controlStates == []
    assert result.territoryGeometries == []


def test_package_accepts_a_grounded_territory_layer(golden_investigation):
    result = validate_generated_investigation(_package_with_grounded_territory(golden_investigation))
    assert [g.id for g in result.territoryGeometries] == ["geo-1"]
    assert [c.id for c in result.controlStates] == ["cs-1"]


def test_control_state_requires_a_supporting_evidence_link(golden_investigation):
    package = _package_with_grounded_territory(golden_investigation)
    package["evidenceLinks"][-1]["role"] = "context"  # resolves, but not supporting
    with pytest.raises(Exception, match="requires a supporting EvidenceLink"):
        validate_generated_investigation(package)


def test_control_state_geometry_ref_must_resolve(golden_investigation):
    package = _package_with_grounded_territory(golden_investigation)
    package["controlStates"][0]["geometryRef"] = "geo-missing"
    with pytest.raises(Exception, match="unknown TerritoryGeometry"):
        validate_generated_investigation(package)


def test_control_state_interval_must_be_ordered(golden_investigation):
    package = _package_with_grounded_territory(golden_investigation)
    package["controlStates"][0]["validFrom"] = {
        "precision": "range",
        "earliest": "1902-01-01",
        "latest": "1902-12-31",
    }  # after validTo (1901)
    with pytest.raises(Exception, match="validFrom after validTo"):
        validate_generated_investigation(package)


@pytest.mark.parametrize("kind", ["influence", "contested"])
def test_fuzzy_control_states_cannot_claim_city_precision(golden_investigation, kind):
    package = _package_with_grounded_territory(golden_investigation)
    package["controlStates"][0]["kind"] = kind
    package["controlStates"][0]["precision"] = "city"
    with pytest.raises(Exception, match="cannot claim"):
        validate_generated_investigation(package)


def test_territory_facet_requires_control_states(golden_investigation):
    package = copy.deepcopy(golden_investigation)
    package["interactionSpec"]["enabledFacets"] = [
        *package["interactionSpec"]["enabledFacets"],
        "territory",
    ]
    with pytest.raises(Exception, match="territory.*facet is enabled but no ControlState"):
        validate_generated_investigation(package)
