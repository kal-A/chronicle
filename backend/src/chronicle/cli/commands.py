"""Thin, testable command implementations — no argparse here, so tests can
call these directly with an injected RunStore/output stream instead of
going through subprocess."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TextIO

from ..ai.tools import ToolError, ToolExecutionContext, build_default_registry
from ..contracts.validation import GeneratedInvestigationValidationError, validate_generated_investigation
from ..corpus.errors import CorpusError
from ..corpus.manifest import CorpusRegistry
from ..providers.curated.concert_of_europe.registry import (
    CONCERT_OF_EUROPE_PROVIDER_SET_VERSION,
    CONCERT_OF_EUROPE_STAGE_FNS,
)
from ..providers.registry import MOCK_PROVIDER_SET_VERSION, MOCK_STAGE_FNS
from ..storage.run_store import RunNotFoundError, RunStore
from ..workflow.engine import generate, make_failing_stage, resume
from ..workflow.stages import STAGE_ORDER, RunStatus, StageName

_NON_FAILURE_STATUSES = {RunStatus.READY, RunStatus.PARTIAL, RunStatus.ABSTAINED}

PROVIDER_SETS = {
    "mock": (MOCK_STAGE_FNS, MOCK_PROVIDER_SET_VERSION),
    "concert-of-europe": (CONCERT_OF_EUROPE_STAGE_FNS, CONCERT_OF_EUROPE_PROVIDER_SET_VERSION),
}


def _print_run_summary(run, out: TextIO) -> None:
    print(f"Run {run.runId}", file=out)
    print(f"  status: {run.status.value}", file=out)
    print(f"  completed stages: {[s.value for s in run.completedStages]}", file=out)
    if run.failedStage:
        print(f"  failed stage: {run.failedStage.value}", file=out)
    if run.outputPackagePath:
        print(f"  package: {run.outputPackagePath}", file=out)


def cmd_generate(
    store: RunStore,
    topic: str,
    fail_at: str | None = None,
    provider_set: str = "mock",
    out: TextIO = sys.stdout,
) -> int:
    base_stage_fns, provider_set_version = PROVIDER_SETS[provider_set]
    stage_fns = dict(base_stage_fns)
    if fail_at:
        try:
            stage_name = StageName(fail_at)
        except ValueError:
            valid = ", ".join(s.value for s in STAGE_ORDER)
            print(f'Unknown stage "{fail_at}". Valid stages: {valid}', file=out)
            return 2
        stage_fns[stage_name] = make_failing_stage(stage_name)

    run = generate(store, topic, stage_fns, provider_set_version)
    _print_run_summary(run, out)
    return 0 if run.status in _NON_FAILURE_STATUSES else 1


def cmd_resume(store: RunStore, run_id: str, provider_set: str = "mock", out: TextIO = sys.stdout) -> int:
    stage_fns, provider_set_version = PROVIDER_SETS[provider_set]
    try:
        run = resume(store, run_id, stage_fns, provider_set_version)
    except RunNotFoundError as error:
        print(str(error), file=out)
        return 2
    _print_run_summary(run, out)
    return 0 if run.status in _NON_FAILURE_STATUSES else 1


def cmd_inspect(store: RunStore, run_id: str, out: TextIO = sys.stdout) -> int:
    try:
        run = store.load_run(run_id)
    except RunNotFoundError as error:
        print(str(error), file=out)
        return 2

    print(f"Run {run.runId}", file=out)
    print(f"  status: {run.status.value}", file=out)
    print(f"  topic: {run.request.topic}", file=out)
    print(f"  workflow version: {run.workflowVersion}", file=out)
    print(f"  provider set version: {run.providerSetVersion}", file=out)
    print(f"  completed stages: {[s.value for s in run.completedStages]}", file=out)
    if run.failedStage:
        print(f"  failed stage: {run.failedStage.value}", file=out)
        failed_record = store.load_stage(run.runId, run.failedStage)
        if failed_record is not None:
            print(f"    error: {failed_record.errorType}: {failed_record.errorMessage}", file=out)
            print(f"    attempt count: {failed_record.attemptCount}", file=out)
    if run.warnings:
        print(f"  warnings: {run.warnings}", file=out)
    return 0


def cmd_validate(package_path: str, out: TextIO = sys.stdout) -> int:
    path = Path(package_path)
    if not path.exists():
        print(f'No file found at "{package_path}"', file=out)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print(f'"{package_path}" is not valid JSON: {error}', file=out)
        return 2

    try:
        investigation = validate_generated_investigation(data)
    except GeneratedInvestigationValidationError as error:
        print(f"INVALID: {error}", file=out)
        return 1

    print(
        f'VALID: packageId="{investigation.packageId}", '
        f"status={investigation.status.value}, scenes={len(investigation.scenes)}",
        file=out,
    )
    return 0


def cmd_corpus_list(out: TextIO = sys.stdout) -> int:
    registry = CorpusRegistry()
    for manifest in registry.list_manifests():
        print(manifest.corpusId, file=out)
        print(f"  title: {manifest.title}", file=out)
        print(f"  benchmark role: {manifest.benchmarkRole}", file=out)
        print(f"  schema version: {manifest.schemaVersion}", file=out)
        print(f"  capabilities: {sorted(manifest.supportedCapabilities)}", file=out)
    return 0


def cmd_corpus_inspect(corpus_id: str, out: TextIO = sys.stdout) -> int:
    registry = CorpusRegistry()
    try:
        corpus = registry.get_corpus(corpus_id)
    except CorpusError as error:
        print(str(error), file=out)
        return 2

    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    print(f"Corpus {manifest.corpusId}", file=out)
    print(f"  title: {manifest.title}", file=out)
    print(f"  package hash: {manifest.packageHash}", file=out)
    print(f"  schema version: {manifest.schemaVersion}", file=out)
    print(f"  capabilities: {sorted(manifest.supportedCapabilities)}", file=out)
    print(f"  sources: {len(investigation.sources)}", file=out)
    print(f"  documents: {len(investigation.documents)}", file=out)
    print(f"  passages: {len(investigation.passages)}", file=out)
    print(f"  claims: {len(investigation.claims)}", file=out)
    print(f"  relationships: {len(investigation.relationships)}", file=out)
    print(f"  events: {len(investigation.events)}", file=out)
    print(f"  entities: {len(investigation.entities)}", file=out)
    print(f"  knowledge states: {len(investigation.knowledgeStates)}", file=out)
    if manifest.knownOmissions:
        print("  known omissions:", file=out)
        for omission in manifest.knownOmissions:
            print(f"    - {omission}", file=out)
    return 0


def cmd_corpus_search(corpus_id: str, query: str, out: TextIO = sys.stdout) -> int:
    registry = CorpusRegistry()
    try:
        corpus = registry.get_corpus(corpus_id)
    except CorpusError as error:
        print(str(error), file=out)
        return 2

    tool_registry = build_default_registry()
    context = ToolExecutionContext(corpusId=corpus_id)
    try:
        result, _record = tool_registry.invoke(
            "search_passages", {"corpusId": corpus_id, "query": query}, context, corpus
        )
    except ToolError as error:
        print(f"Search failed: {error}", file=out)
        return 1

    print(
        f'Search "{query}" in {corpus_id}: {result.totalMatched} matched (showing {len(result.hits)})',
        file=out,
    )
    for hit in result.hits:
        factors = [factor.factor for factor in hit.scoreFactors]
        print(f"  {hit.passageId}  score={hit.score:.1f}  factors={factors}", file=out)
        print(f"    {hit.excerpt}", file=out)
    return 0


def cmd_tools_list(out: TextIO = sys.stdout) -> int:
    registry = build_default_registry()
    for spec in registry.list_specs():
        print(f"{spec.name} ({spec.version})", file=out)
        print(f"  {spec.description}", file=out)
        print(f"  use when: {spec.useWhen}", file=out)
        print(f"  avoid when: {spec.avoidWhen}", file=out)
        print(f"  required capabilities: {spec.requiredCapabilities}", file=out)
        print(f"  maximum result limit: {spec.maxResultLimit}", file=out)
        print(f"  maximum output characters: {spec.maxOutputCharacters}", file=out)
        print(f"  input schema: {json.dumps(spec.inputSchema, sort_keys=True)}", file=out)
        print(f"  output: {spec.outputSummary}", file=out)
    return 0


def cmd_tools_invoke(tool_name: str, corpus_id: str, input_json: str, out: TextIO = sys.stdout) -> int:
    try:
        raw_input = json.loads(input_json)
    except json.JSONDecodeError as error:
        print(f"--input is not valid JSON: {error}", file=out)
        return 2
    if not isinstance(raw_input, dict):
        print("--input must be a JSON object", file=out)
        return 2
    raw_input.setdefault("corpusId", corpus_id)

    corpus_registry = CorpusRegistry()
    try:
        corpus = corpus_registry.get_corpus(corpus_id)
    except CorpusError as error:
        print(str(error), file=out)
        return 2

    tool_registry = build_default_registry()
    context = ToolExecutionContext(corpusId=corpus_id)
    try:
        result, _record = tool_registry.invoke(tool_name, raw_input, context, corpus)
    except ToolError as error:
        print(f"{type(error).__name__}: {error}", file=out)
        return 1

    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True), file=out)
    return 0
