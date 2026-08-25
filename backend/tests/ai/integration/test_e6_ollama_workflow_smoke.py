"""Opt-in real-Qwen smoke tests for Chronicle's complete E6 agent path."""

from __future__ import annotations

import time

import pytest

from chronicle.ai.agents import (
    EvidenceAnalyst,
    HistoricalCritic,
    InvestigationGuide,
    InvestigationPlanner,
)
from chronicle.ai.agents.analyst import AnalystValidationError
from chronicle.ai.agents.planner_prompt import ToolSpecRepresentation
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.contracts.run import (
    AgentRunRecord,
    CorpusSnapshot,
    InvestigationRequest,
    SelectedRecord,
    SelectedRecordType,
    WorkspaceContextSnapshot,
)
from chronicle.ai.models.ollama import OllamaModelProvider
from chronicle.ai.orchestration.finalization import FinalizationRunner
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.orchestration.sequential import SequentialAgentWorkflow
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.ai.tools import build_default_registry
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore

pytestmark = pytest.mark.local_ollama_integration


def _context(run_id: str) -> tuple[object, AgentRunRecord]:
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    record = AgentRunRecord(
        runId=run_id,
        request=InvestigationRequest(
            runId=run_id,
            corpusId=corpus.corpus_id,
            userQuestion="What does the selected report say about German support?",
            workspaceContext=WorkspaceContextSnapshot(
                selectedRecords=(
                    SelectedRecord(
                        recordType=SelectedRecordType.CLAIM,
                        recordId="claim-c1-assurance-reported",
                    ),
                )
            ),
        ),
        corpusSnapshot=CorpusSnapshot(
            corpusId=corpus.corpus_id,
            packageId=investigation.packageId,
            packageHash=manifest.packageHash,
            packageRevision=investigation.packageRevision,
            schemaVersion=investigation.schemaVersion,
            capabilities=tuple(manifest.supportedCapabilities),
            knownOmissions=tuple(manifest.knownOmissions),
        ),
    )
    return corpus, record


def _provider() -> OllamaModelProvider:
    provider = OllamaModelProvider(timeout=180.0)
    health = provider.health_check()
    if not health.healthy:
        pytest.skip(f"Ollama not reachable: {health.detail}")
    return provider


def test_real_qwen_returns_a_valid_context_constrained_plan():
    corpus, record = _context("run-e6-real-planner")
    provider = _provider()
    registry = build_default_registry()
    retrieval = InvestigationRunner(registry)
    specs = registry.list_specs()

    started = time.perf_counter()
    planner = InvestigationPlanner(
        provider,
        representation=ToolSpecRepresentation.COMPACT,
    )
    plan = planner.plan(record.request, record.corpusSnapshot, specs)

    assert plan.plannedToolCalls
    assert planner.last_execution is not None
    assert all(call.toolName in retrieval.allowed_tool_names for call in plan.plannedToolCalls)
    print(
        f"\nE6 real Planner smoke: tools="
        f"{[call.toolName for call in plan.plannedToolCalls]}, "
        f"seconds={time.perf_counter() - started:.2f}"
    )


def test_real_qwen_returns_a_grounded_analysis():
    corpus, record = _context("run-e6-real-analyst")
    provider = _provider()
    plan = InvestigationPlan(
        planId="plan-e6-real-analyst",
        runId=record.runId,
        corpusId=corpus.corpus_id,
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion=record.request.userQuestion,
        questionType=QuestionType.DIRECT_EVIDENCE,
        plannedToolCalls=[
            PlannedToolCall(
                callId="claim-call",
                toolName="get_claim_evidence",
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"claimId": "claim-c1-assurance-reported"},
            )
        ],
    )
    bundle = InvestigationRunner(build_default_registry()).execute_initial(plan, corpus).bundle

    try:
        draft = EvidenceAnalyst(provider).analyze(
            record.request.userQuestion,
            plan,
            bundle,
        )
    except AnalystValidationError as exc:
        print(f"\nE6 Analyst validation failure: {exc.validationReport}")
        print(f"E6 rejected Analyst draft: {exc.proposedDraft}")
        raise

    assert draft.statements
    assert draft.statements[0].citations


def test_real_qwen_completes_a_cited_investigation(tmp_path):
    corpus, record = _context("run-e6-real-workflow")
    provider = _provider()
    store = AgentRunStore(tmp_path)
    retrieval = InvestigationRunner(build_default_registry(), store=store)
    analyst = EvidenceAnalyst(provider)
    workflow = SequentialAgentWorkflow(
        planner=InvestigationPlanner(
            provider,
            representation=ToolSpecRepresentation.COMPACT,
        ),
        retrieval_runner=retrieval,
        analyst=analyst,
        finalization_runner=FinalizationRunner(
            retrieval_runner=retrieval,
            analyst=analyst,
            critic=HistoricalCritic(provider),
            guide=InvestigationGuide(provider),
            store=store,
        ),
        store=store,
    )

    started = time.perf_counter()
    result = workflow.run(record, corpus)

    assert result.status is AgentRunStatus.ANSWER_READY, result.errorMessage
    assert result.finalAnswer is not None
    assert result.finalAnswer.citations
    print(
        f"\nE6 real workflow smoke: status={result.status.value}, "
        f"citations={len(result.finalAnswer.citations)}, "
        f"seconds={time.perf_counter() - started:.2f}"
    )
