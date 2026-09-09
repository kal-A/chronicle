"""Behavior parity: the LangGraph workflow must be a drop-in for the
hand-rolled SequentialAgentWorkflow.

These scenarios mirror ``test_sequential_workflow.py`` exactly -- same fixtures,
same deterministic provider, same assertions -- but drive
``LangGraphAgentWorkflow``. P2(a) migrates *control flow* to an explicit
LangGraph state graph while every observable outcome (stage order, emitted
signals, persisted record, resume-skipping, cancellation, failure audit) stays
identical. If these pass alongside the sequential suite, the graph is a proven
drop-in and the manager boundary can be converged in P2(b).
"""

from __future__ import annotations

from chronicle.ai.agents import (
    EvidenceAnalyst,
    HistoricalCritic,
    InvestigationGuide,
    InvestigationPlanner,
)
from chronicle.ai.contracts.analysis import GroundingValidationReport
from chronicle.ai.contracts.plan import PlannedToolCall, ToolPurpose
from chronicle.ai.models import DeterministicModelProvider
from chronicle.ai.models.metadata import ModelCallStatus
from chronicle.ai.orchestration.finalization import FinalizationRunner
from chronicle.ai.orchestration.graph import LangGraphAgentWorkflow
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.orchestration.sequential import WorkflowSignalType
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.ai.contracts.run import AgentStageStatus
from chronicle.storage.agent_run_store import AgentRunStore

from .test_sequential_workflow import _context


def _workflow(tmp_path, registry, provider):
    store = AgentRunStore(tmp_path)
    retrieval = InvestigationRunner(registry, store=store)
    return (
        LangGraphAgentWorkflow(
            planner=InvestigationPlanner(provider),
            retrieval_runner=retrieval,
            analyst=EvidenceAnalyst(provider),
            finalization_runner=FinalizationRunner(
                retrieval_runner=retrieval,
                analyst=EvidenceAnalyst(provider),
                critic=HistoricalCritic(provider),
                guide=InvestigationGuide(provider),
                store=store,
            ),
            store=store,
        ),
        store,
    )


def test_graph_runs_and_persists_all_four_roles_in_strict_order(tmp_path):
    corpus, registry, plan, _bundle, draft, decision, answer, record = _context()
    provider = DeterministicModelProvider()
    for value in (plan, draft, decision, answer):
        provider.enqueue_value(value)
    workflow, store = _workflow(tmp_path, registry, provider)
    signals = []

    result = workflow.run(record, corpus, emit=signals.append)

    assert result.status is AgentRunStatus.ANSWER_READY
    assert [stage.stageName.value for stage in result.stages] == [
        "planner",
        "retrieval",
        "analyst",
        "critic",
        "guide",
    ]
    assert [
        signal.stage.value
        for signal in signals
        if signal.type is WorkflowSignalType.STAGE_STARTED
    ] == ["planner", "retrieval", "analyst", "critic", "guide"]
    assert signals[0].type is WorkflowSignalType.RUN_STARTED
    assert signals[-1].type is WorkflowSignalType.RUN_COMPLETED
    assert len(result.modelCalls) == 4
    assert len(result.toolCalls) == 1
    assert result.finalAnswer.directAnswer == answer.directAnswer
    assert store.load_run(record.runId) == result


def test_graph_cancellation_before_planning_makes_no_model_call(tmp_path):
    corpus, registry, _plan, _bundle, _draft, _decision, _answer, record = _context(
        "run-cancelled"
    )
    provider = DeterministicModelProvider()
    workflow, store = _workflow(tmp_path, registry, provider)
    signals = []

    result = workflow.run(
        record,
        corpus,
        emit=signals.append,
        should_cancel=lambda: True,
    )

    assert result.status is AgentRunStatus.CANCELLED
    assert result.modelCalls == []
    assert result.plan is None
    assert signals[-1].type is WorkflowSignalType.RUN_CANCELLED
    assert store.load_run(record.runId).status is AgentRunStatus.CANCELLED


def test_graph_resume_reuses_persisted_analysis_and_only_runs_critic_and_guide(tmp_path):
    corpus, registry, plan, bundle, draft, decision, answer, record = _context("run-resume")
    record.status = AgentRunStatus.INTERRUPTED
    record.plan = plan
    record.retrievalBundle = bundle
    record.analysisDraft = draft
    record.groundingValidation = GroundingValidationReport(valid=True)
    provider = DeterministicModelProvider()
    provider.enqueue_value(decision)
    provider.enqueue_value(answer)
    workflow, store = _workflow(tmp_path, registry, provider)
    store.save_run(record)
    signals = []

    result = workflow.run(record, corpus, emit=signals.append)

    assert result.status is AgentRunStatus.ANSWER_READY
    assert [stage.stageName.value for stage in result.stages] == ["critic", "guide"]
    assert [
        signal.stage.value
        for signal in signals
        if signal.type is WorkflowSignalType.STAGE_STARTED
    ] == ["critic", "guide"]


def test_graph_abstains_when_analyst_draft_cannot_be_grounded(tmp_path):
    # An acquired/thin corpus often yields a schema-valid but ungroundable
    # analysis. That is an insufficient-evidence outcome, not a system error:
    # the run must ABSTAIN (audited), never hard-fail, and never run Critic/Guide.
    corpus, registry, plan, _bundle, draft, _decision, _answer, record = _context(
        "run-ungrounded"
    )
    bad_citation = draft.statements[0].citations[0].model_copy(
        update={"toolCallId": "no-such-call"}
    )
    bad_statement = draft.statements[0].model_copy(update={"citations": [bad_citation]})
    ungroundable = draft.model_copy(update={"statements": [bad_statement]})
    provider = DeterministicModelProvider()
    provider.enqueue_value(plan)
    provider.enqueue_value(ungroundable)
    workflow, store = _workflow(tmp_path, registry, provider)
    signals = []

    result = workflow.run(record, corpus, emit=signals.append)

    assert result.status is AgentRunStatus.ABSTAINED
    assert result.abstentionReason
    assert result.groundingValidation is not None
    assert result.groundingValidation.valid is False
    assert result.finalAnswer is None
    assert [stage.stageName.value for stage in result.stages] == [
        "planner",
        "retrieval",
        "analyst",
    ]
    assert result.stages[-1].status is AgentStageStatus.REJECTED
    assert signals[-1].type is WorkflowSignalType.RUN_ABSTAINED
    assert store.load_run(record.runId).status is AgentRunStatus.ABSTAINED


def test_graph_abstains_when_planner_proposes_an_invalid_plan(tmp_path):
    # A local model can return a schema-valid plan that fails Chronicle's
    # deterministic planner authorization (e.g. proposing an unauthorized tool,
    # or a proceed-plan for an out-of-corpus question). That is a model-capability
    # outcome over this corpus, not a Chronicle system error: the run must ABSTAIN
    # with an audited REJECTED planner stage, never hard-fail. Reproduces the live
    # P3 "1918 influenza" failure where the planner emitted an invalid plan.
    corpus, registry, plan, *_rest, record = _context("run-bad-plan")
    invalid_plan = plan.model_copy(
        update={
            "plannedToolCalls": [
                PlannedToolCall(
                    callId="unauthorized-call",
                    toolName="totally_unauthorized_tool",
                    purposeCode=ToolPurpose.FIND_SUPPORT,
                    arguments={},
                )
            ]
        }
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(invalid_plan)
    workflow, store = _workflow(tmp_path, registry, provider)
    signals = []

    result = workflow.run(record, corpus, emit=signals.append)

    assert result.status is AgentRunStatus.ABSTAINED
    assert result.abstentionReason
    assert result.finalAnswer is None
    # the rejected planner attempt is audited (one model call, a REJECTED stage)
    assert result.stages[-1].stageName.value == "planner"
    assert result.stages[-1].status is AgentStageStatus.REJECTED
    assert len(result.modelCalls) == 1
    assert signals[-1].type is WorkflowSignalType.RUN_ABSTAINED
    assert store.load_run(record.runId).status is AgentRunStatus.ABSTAINED


def test_graph_abstains_when_planned_tool_call_arguments_are_invalid(tmp_path):
    # A schema-valid plan can still carry tool-call arguments that fail the
    # runner's deterministic input preflight (here: search_passages with a
    # dateRange but no dateRoles -- a Pydantic cross-field rule the planner's
    # shape check does not enforce). The initial retrieval is REJECTED; that is a
    # model-produced-unusable-plan outcome and must ABSTAIN, not FAIL. Reproduces
    # the live P3 "Great Fire of London" failure.
    corpus, registry, plan, *_rest, record = _context("run-bad-toolargs")
    bad_args_plan = plan.model_copy(
        update={
            "plannedToolCalls": [
                PlannedToolCall(
                    callId="bad-search",
                    toolName="search_passages",
                    purposeCode=ToolPurpose.FIND_SUPPORT,
                    arguments={
                        "query": "the report",
                        "dateRange": {"earliest": "1914-06-01", "latest": "1914-08-01"},
                    },
                )
            ]
        }
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(bad_args_plan)
    workflow, store = _workflow(tmp_path, registry, provider)
    signals = []

    result = workflow.run(record, corpus, emit=signals.append)

    assert result.status is AgentRunStatus.ABSTAINED
    assert result.abstentionReason
    assert result.finalAnswer is None
    # reached and was rejected at retrieval preflight, not the planner
    assert any(
        stage.stageName.value == "retrieval" and stage.status is AgentStageStatus.REJECTED
        for stage in result.stages
    )
    assert signals[-1].type is WorkflowSignalType.RUN_ABSTAINED
    assert store.load_run(record.runId).status is AgentRunStatus.ABSTAINED


def test_graph_persists_failed_planner_call_and_specific_bounded_cause(tmp_path):
    corpus, registry, _plan, _bundle, _draft, _decision, _answer, record = _context(
        "run-planner-failure"
    )
    provider = DeterministicModelProvider()
    provider.enqueue_malformed("first malformed response")
    provider.enqueue_malformed("second malformed response")
    workflow, store = _workflow(tmp_path, registry, provider)

    result = workflow.run(record, corpus)

    assert result.status is AgentRunStatus.FAILED
    assert len(result.modelCalls) == 1
    assert result.modelCalls[0].status is ModelCallStatus.FAILED
    assert result.stages[-1].stageName.value == "planner"
    assert result.stages[-1].status is AgentStageStatus.FAILED
    assert "Configured malformed response" in result.errorMessage
    assert store.load_run(record.runId) == result
