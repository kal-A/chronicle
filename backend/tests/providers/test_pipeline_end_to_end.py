"""Proves MOCK_STAGE_FNS produces an actual schema-valid GeneratedInvestigation
package for an arbitrary topic, and that its PARTIAL outcome is genuine
(map data honestly omitted), not contrived."""

import json

from chronicle.contracts.validation import validate_generated_investigation
from chronicle.providers.registry import MOCK_STAGE_FNS
from chronicle.storage.run_store import RunStore
from chronicle.workflow.engine import generate
from chronicle.workflow.stages import STAGE_ORDER, RunStatus


def test_generate_produces_a_schema_valid_package(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, "A generic test topic", MOCK_STAGE_FNS)

    assert run.completedStages == STAGE_ORDER
    assert run.outputPackagePath is not None
    package = json.loads(open(run.outputPackagePath, encoding="utf-8").read())

    # Re-validating through the same C0 boundary the CLI's `validate` command
    # and the frontend renderer use is the real proof, not just "no exception
    # was raised while building the dict."
    validated = validate_generated_investigation(package)
    assert validated.packageId == "generic-mock-a-generic-test-topic"


def test_partial_outcome_is_genuine_not_contrived(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, "Another topic", MOCK_STAGE_FNS)

    assert run.status == RunStatus.PARTIAL
    package = json.loads(open(run.outputPackagePath, encoding="utf-8").read())

    assert package["status"] == "partial"
    assert package["generationReport"]["outcome"] == "partial"
    assert package["mapAssets"] == []
    assert package["mapScenes"] == []
    assert any("geographic" in omission.lower() for omission in package["generationReport"]["omissions"])


def test_generation_report_discloses_synthetic_content(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, "Yet another topic", MOCK_STAGE_FNS)
    package = json.loads(open(run.outputPackagePath, encoding="utf-8").read())

    warnings = " ".join(package["generationReport"]["warnings"]).lower()
    assert "synthetic" in warnings
    assert "not real historical scholarship" in warnings


def test_generation_report_is_also_persisted_separately(tmp_path):
    store = RunStore(tmp_path)
    run = generate(store, "A third topic", MOCK_STAGE_FNS)

    assert run.generationReportPath is not None
    report = json.loads(open(run.generationReportPath, encoding="utf-8").read())
    assert report["outcome"] == "partial"
    assert any(check["status"] == "passed" for check in report["verificationChecks"])
