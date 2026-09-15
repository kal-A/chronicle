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
    _control_signal_score,
    _select_control_passages,
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


def _filler(index: int) -> Passage:
    # ~1200 chars, no control-signal vocabulary.
    return Passage(
        id=f"f-{index:02d}", documentId="d-1", excerpt="Neutral placeholder narrative. " * 40, locator=f"f#{index}"
    )


def _control_passage(passage_id: str) -> Passage:
    return Passage(
        id=passage_id,
        documentId="d-1",
        excerpt="The realm annexed and controlled the northern province after the war.",
        locator="c#1",
    )


def test_control_signal_score_ranks_control_prose_above_filler():
    assert _control_signal_score(_control_passage("c").excerpt) > 0
    assert _control_signal_score(_filler(0).excerpt) == 0


def test_control_signal_score_matches_morphology_but_not_substring_false_positives():
    # Word-boundary matching: stems catch inflections without spurious hits.
    assert _control_signal_score("the empire annexed and occupied the province") >= 3
    # "foreign" must NOT trigger "reign"; "conceded" must NOT trigger "cede".
    assert _control_signal_score("the foreign minister conceded a point") == 0


def test_selection_prefers_control_passages_over_filler_beyond_the_window():
    # A control-relevant passage buried past the char budget behind many filler
    # passages is still selected (the fix for the zero-yield Franco-Prussian run).
    passages = [_filler(i) for i in range(10)] + [_control_passage("deep")]
    selected = _select_control_passages(passages)
    assert [p.id for p in selected] == ["deep"]  # only the signalling passage is sent


def test_selection_falls_back_to_document_order_when_nothing_signals():
    passages = [_filler(i) for i in range(3)]
    selected = _select_control_passages(passages)
    assert [p.id for p in selected] == ["f-00", "f-01", "f-02"]  # unchanged head order


def test_extraction_grounds_a_state_citing_a_deep_control_passage():
    # End to end: the buried control passage is selected, so a state citing its id
    # is grounded (previously it fell outside the head window and would be dropped).
    passages = [_filler(i) for i in range(10)] + [_control_passage("deep")]
    provider = _provider([_state(passageIds=["deep"])])
    result = extract_control_states(passages, _period(), "A topic", provider)
    assert len(result) == 1 and result[0].passageIds == ["deep"]
