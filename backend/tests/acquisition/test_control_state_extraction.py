"""Control-state extraction unit tests (ADR-004 addendum, Slice T5).

Uses DeterministicModelProvider (no network, no live model) with neutral
placeholder polities — the stage is subject-agnostic. The deterministic provider
does not enforce the JSON schema, so these tests deliberately feed malformed
proposals to prove the post-generation grounding / period / Rule-22 guards.
"""

from __future__ import annotations

from datetime import date

from chronicle.acquisition.control_state import (
    ExtractedControlState,
    ExtractedControlStates,
    extract_control_states,
)
from chronicle.ai.models.deterministic import DeterministicModelProvider
from chronicle.contracts.enums import DatePrecision
from chronicle.contracts.shared import HistoricalDate, Passage


def _period() -> HistoricalDate:
    return HistoricalDate(
        precision=DatePrecision.RANGE,
        earliest=date(1900, 1, 1),
        latest=date(1920, 12, 31),
        label="1900-1920",
    )


def _passages() -> list[Passage]:
    return [
        Passage(id="p-1", documentId="d-1", excerpt="Placeholder account one.", locator="doc#1"),
        Passage(id="p-2", documentId="d-1", excerpt="Placeholder account two.", locator="doc#2"),
    ]


def _provider(states: list[ExtractedControlState]) -> DeterministicModelProvider:
    provider = DeterministicModelProvider()
    provider.enqueue_value(ExtractedControlStates(controlStates=states))
    return provider


def _state(**kwargs) -> ExtractedControlState:
    base = {
        "polity": "Northland",
        "kind": "controlled",
        "fromYear": 1905,
        "toYear": 1910,
        "passageIds": ["p-1"],
    }
    base.update(kwargs)
    return ExtractedControlState(**base)


def test_extracts_grounded_control_states():
    result = extract_control_states(_passages(), _period(), "A topic", _provider([_state()]))
    assert [s.polity for s in result] == ["Northland"]
    assert result[0].kind == "controlled"


def test_drops_unknown_kind():
    result = extract_control_states(_passages(), _period(), "A topic", _provider([_state(kind="annexed")]))
    assert result == []


def test_drops_anachronistic_interval():
    result = extract_control_states(
        _passages(), _period(), "A topic", _provider([_state(fromYear=1880, toYear=1890)])
    )
    assert result == []


def test_strips_fabricated_citations_and_drops_ungrounded():
    kept = extract_control_states(
        _passages(), _period(), "A topic", _provider([_state(passageIds=["p-1", "ghost"])])
    )
    assert kept[0].passageIds == ["p-1"]

    dropped = extract_control_states(
        _passages(), _period(), "A topic", _provider([_state(passageIds=["ghost"])])
    )
    assert dropped == []


def test_basis_is_honoured_only_for_controlled_territory():
    result = extract_control_states(
        _passages(), _period(), "A topic", _provider([_state(kind="influence", basis="occupied")])
    )
    assert result[0].basis is None  # basis stripped off a non-controlled state


def test_sovereign_polity_requires_a_non_sovereign_basis_and_a_different_polity():
    sovereign_basis = extract_control_states(
        _passages(), _period(), "A topic",
        _provider([_state(basis="sovereign", sovereignPolity="Southland")]),
    )
    assert sovereign_basis[0].sovereignPolity is None  # sovereign basis owns itself

    self_sovereign = extract_control_states(
        _passages(), _period(), "A topic",
        _provider([_state(basis="occupied", sovereignPolity="Northland")]),  # == controller
    )
    assert self_sovereign[0].sovereignPolity is None

    occupied = extract_control_states(
        _passages(), _period(), "A topic",
        _provider([_state(basis="occupied", sovereignPolity="Southland")]),
    )
    assert occupied[0].basis == "occupied"
    assert occupied[0].sovereignPolity == "Southland"


def test_no_passages_makes_no_model_call():
    provider = DeterministicModelProvider()  # nothing enqueued -> would raise if called
    assert extract_control_states([], _period(), "A topic", provider) == []
