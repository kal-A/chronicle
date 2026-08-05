"""Phase D0.4: proves the curated pipeline itself generates a valid
InvestigationExperiencePlan for the Concert of Europe package — replacing
what D0.3 had only hand-authored as a frontend fixture
(src/content/investigationFixtures.ts)."""

import json

from chronicle.providers.curated.concert_of_europe.registry import (
    CONCERT_OF_EUROPE_PROVIDER_SET_VERSION,
    CONCERT_OF_EUROPE_STAGE_FNS,
)
from chronicle.storage.run_store import RunStore
from chronicle.workflow.engine import generate

TOPIC = "The Concert of Europe and Revolutionary Intervention"


def _generate_package(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, TOPIC, CONCERT_OF_EUROPE_STAGE_FNS, CONCERT_OF_EUROPE_PROVIDER_SET_VERSION)
    return json.loads(open(run.outputPackagePath, encoding="utf-8").read())


def test_package_has_an_experience_plan_with_three_lenses(tmp_path):
    package = _generate_package(tmp_path)
    plan = package["experiencePlan"]
    lens_ids = {lens["id"] for lens in plan["lenses"]}
    assert lens_ids == {"lens-sequence", "lens-systems", "lens-uncertainty"}


def test_systems_lens_references_all_three_curated_relationships(tmp_path):
    package = _generate_package(tmp_path)
    plan = package["experiencePlan"]
    systems_lens = next(lens for lens in plan["lenses"] if lens["id"] == "lens-systems")
    assert set(systems_lens["visibleRelationships"]) == {
        "rel-troppau-supports-naples",
        "rel-castlereagh-disputes-troppau",
        "rel-verona-extends-troppau",
    }
    assert systems_lens["visualizationType"] == "graph"


def test_uncertainty_lens_discloses_the_same_gaps_as_the_generation_report(tmp_path):
    package = _generate_package(tmp_path)
    uncertainty_lens = next(
        lens for lens in package["experiencePlan"]["lenses"] if lens["id"] == "lens-uncertainty"
    )
    limitations = " ".join(uncertainty_lens["limitations"]).lower()
    assert "verona" in limitations
    assert "map" in limitations


def test_system_path_and_perspective_comparison_reference_real_curated_ids(tmp_path):
    package = _generate_package(tmp_path)
    plan = package["experiencePlan"]

    claim_ids = {claim["id"] for claim in package["claims"]}
    relationship_ids = {rel["id"] for rel in package["relationships"]}
    entity_ids = {entity["id"] for entity in package["entities"]}

    path = plan["systemPaths"][0]
    assert path["lensId"] == "lens-systems"
    assert set(path["nodeIds"]) <= claim_ids
    assert set(path["relationshipIds"]) <= relationship_ids

    comparison = plan["perspectiveComparisons"][0]
    assert set(comparison["entityIds"]) <= entity_ids


def test_experience_plan_is_deterministic_across_independent_runs(tmp_path):
    package_a = _generate_package(tmp_path / "a")
    package_b = _generate_package(tmp_path / "b")
    assert package_a["experiencePlan"] == package_b["experiencePlan"]
