"""Spot-checks that the Concert of Europe package's content is real, in the
right historical range, and honestly discloses its gaps — proving this
provider set is genuinely researched content, not another mock, without
re-litigating the schema/cross-reference checks validation.py already
covers exhaustively."""

import json

from chronicle.providers.curated.concert_of_europe.registry import CONCERT_OF_EUROPE_STAGE_FNS
from chronicle.storage.run_store import RunStore
from chronicle.workflow.engine import generate

TOPIC = "The Concert of Europe and Revolutionary Intervention"


def _generate_package(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, TOPIC, CONCERT_OF_EUROPE_STAGE_FNS, "c3-concert-of-europe-v1")
    return json.loads(open(run.outputPackagePath, encoding="utf-8").read())


def test_events_fall_within_the_1814_to_1822_period(tmp_path):
    package = _generate_package(tmp_path)
    for event in package["events"]:
        assert "1814" <= event["eventTime"]["earliest"][:4] <= "1822"
        assert "1814" <= event["eventTime"]["latest"][:4] <= "1822"


def test_real_historical_figures_are_present(tmp_path):
    package = _generate_package(tmp_path)
    names = {e["canonicalName"] for e in package["entities"] if e["entityType"] == "person"}
    assert names == {
        "Klemens von Metternich",
        "Alexander I of Russia",
        "Robert Stewart, Viscount Castlereagh",
        "George Canning",
    }


def test_troppau_protocol_quotation_is_present_and_labelled_direct(tmp_path):
    package = _generate_package(tmp_path)
    passage = next(p for p in package["passages"] if p["id"] == "passage-troppau-protocol-1")
    assert "ipso facto cease to be members of the European Alliance" in passage["excerpt"]


def test_only_the_vienna_scene_has_a_map(tmp_path):
    package = _generate_package(tmp_path)
    assert len(package["mapAssets"]) == 1
    assert len(package["mapScenes"]) == 1
    scenes_by_id = {s["id"]: s for s in package["scenes"]}
    assert scenes_by_id["scene-congress-of-vienna"]["mapSceneId"] == "map-scene-vienna"
    # exclude_none in verification.py means an absent-optional field is
    # simply not present in the serialized package, not present-as-null.
    assert scenes_by_id["scene-principle-of-intervention"].get("mapSceneId") is None


def test_disputed_relationship_has_both_supporting_and_counterevidence(tmp_path):
    package = _generate_package(tmp_path)
    relationship = next(r for r in package["relationships"] if r["id"] == "rel-castlereagh-disputes-troppau")
    assert relationship["evidenceClassification"] == "disputed"

    links_by_id = {link["id"]: link for link in package["evidenceLinks"]}
    roles = {links_by_id[link_id]["role"] for link_id in relationship["evidenceLinkIds"]}
    assert roles == {"supporting", "counterevidence"}


def test_generation_report_discloses_the_real_researched_gaps(tmp_path):
    package = _generate_package(tmp_path)
    omissions = " ".join(package["generationReport"]["omissions"]).lower()
    assert "1820-1822 scene" in omissions or "1820-1822" in omissions
    assert "verona" in omissions
    assert package["generationReport"]["outcome"] == "partial"
    assert package["status"] == "partial"


def test_warnings_disclose_this_is_a_prototype_curation_pass_not_peer_reviewed(tmp_path):
    package = _generate_package(tmp_path)
    warnings = " ".join(package["generationReport"]["warnings"]).lower()
    assert "not independently peer-reviewed" in warnings
