"""Proves CONCERT_OF_EUROPE_STAGE_FNS produces an actual schema-valid
GeneratedInvestigation package, and that it is deterministic — mirrors
backend/tests/providers/test_pipeline_end_to_end.py and test_determinism.py
for the real, curated (not mock) provider set."""

import json

from chronicle.contracts.validation import validate_generated_investigation
from chronicle.providers.curated.concert_of_europe.registry import CONCERT_OF_EUROPE_STAGE_FNS
from chronicle.storage.run_store import RunStore
from chronicle.workflow.engine import generate
from chronicle.workflow.stages import STAGE_ORDER

TOPIC = "The Concert of Europe and Revolutionary Intervention"


def test_generate_produces_a_schema_valid_package(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, TOPIC, CONCERT_OF_EUROPE_STAGE_FNS, "c3-concert-of-europe-v1")

    assert run.completedStages == STAGE_ORDER
    assert run.outputPackagePath is not None
    package = json.loads(open(run.outputPackagePath, encoding="utf-8").read())

    validated = validate_generated_investigation(package)
    assert validated.packageId == "concert-of-europe-1814-1822"
    assert len(validated.scenes) == 2


def test_identical_topic_produces_byte_identical_packages(tmp_path):
    store_a = RunStore(tmp_path / "a")
    store_b = RunStore(tmp_path / "b")

    run_a = generate(store_a, TOPIC, CONCERT_OF_EUROPE_STAGE_FNS, "c3-concert-of-europe-v1")
    run_b = generate(store_b, TOPIC, CONCERT_OF_EUROPE_STAGE_FNS, "c3-concert-of-europe-v1")

    assert run_a.runId != run_b.runId
    package_a = json.loads(open(run_a.outputPackagePath, encoding="utf-8").read())
    package_b = json.loads(open(run_b.outputPackagePath, encoding="utf-8").read())
    assert package_a == package_b
