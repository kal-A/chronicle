"""Proves the Python contract mirror accepts the same real package the
TypeScript renderer already accepts — the load-bearing test of Phase C0."""

from chronicle.contracts import validate_generated_investigation


def test_golden_fixture_is_accepted(golden_investigation):
    result = validate_generated_investigation(golden_investigation)
    assert result.packageId == "blank-cheque-golden"
    assert len(result.scenes) >= 1


def test_golden_fixture_round_trips_through_pydantic(golden_investigation):
    result = validate_generated_investigation(golden_investigation)
    # model_dump(mode="json") should reproduce every id present in the source
    # JSON — a cheap way to confirm no records were silently dropped.
    dumped = result.model_dump(mode="json")
    assert {c["id"] for c in dumped["claims"]} == {c["id"] for c in golden_investigation["claims"]}
    assert {r["id"] for r in dumped["relationships"]} == {
        r["id"] for r in golden_investigation["relationships"]
    }
    assert {s["id"] for s in dumped["sources"]} == {s["id"] for s in golden_investigation["sources"]}
