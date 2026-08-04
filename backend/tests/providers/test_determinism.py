"""Every provider is a pure function of its input, so two independent
`generate()` calls with the same topic must produce byte-identical packages
(chronicle_phase_c_adjusted_plan.md §8's determinism requirement) even
though they get different run ids."""

import json

from chronicle.providers.registry import MOCK_STAGE_FNS
from chronicle.storage.run_store import RunStore
from chronicle.workflow.engine import generate


def test_identical_topic_produces_byte_identical_packages(tmp_path):
    store_a = RunStore(tmp_path / "a")
    store_b = RunStore(tmp_path / "b")

    run_a = generate(store_a, "Deterministic topic", MOCK_STAGE_FNS)
    run_b = generate(store_b, "Deterministic topic", MOCK_STAGE_FNS)

    assert run_a.runId != run_b.runId

    package_a = json.loads(open(run_a.outputPackagePath, encoding="utf-8").read())
    package_b = json.loads(open(run_b.outputPackagePath, encoding="utf-8").read())
    assert package_a == package_b


def test_different_topics_produce_different_package_ids(tmp_path):
    store = RunStore(tmp_path)
    run_a = generate(store, "Topic one", MOCK_STAGE_FNS)
    run_b = generate(store, "Topic two", MOCK_STAGE_FNS)

    package_a = json.loads(open(run_a.outputPackagePath, encoding="utf-8").read())
    package_b = json.loads(open(run_b.outputPackagePath, encoding="utf-8").read())
    assert package_a["packageId"] != package_b["packageId"]
