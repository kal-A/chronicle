"""Explicit LangGraph state graph for Chronicle's four-role investigation flow.

P2(a) migrates the *control flow* of :class:`SequentialAgentWorkflow` onto a
compiled LangGraph ``StateGraph`` while preserving every observable behavior:
stage order, emitted :class:`WorkflowSignal`s, persisted record shape,
resume-skipping, cancellation at safe boundaries, and the bounded failure audit.
``tests/ai/orchestration/test_langgraph_workflow.py`` mirrors the sequential
behavior suite against this graph to hold that parity.

This is the deliberate first step of the orchestration migration (see the
approved plan): the graph runs *inside* the current ``AgentRunManager`` as a
drop-in ``_SequentialWorkflow`` -- same ``run(record, corpus, *, emit,
should_cancel)`` contract -- so the manager boundary can be converged onto
LangGraph's checkpointer + ``astream_events`` in P2(b) without any behavior
change. Aligns with ADR-003: an explicit state machine, not an autonomous swarm.

The graph currently models the four top-level phases (planner -> retrieval ->
analyst -> finalization) with conditional edges for the abstain-after-plan and
fail-after-retrieval branches. ``finalization`` still delegates to
:class:`FinalizationRunner`, whose internal critic -> single follow-up -> guide
cycle is unchanged; decomposing that cycle into first-class ``critic`` /
``acquire_more`` / ``guide`` nodes (turning the hardcoded follow-up into a real
loop-back edge) is the next step and is why the boundary lives here now.

The substantive stage/audit helpers are imported from :mod:`sequential` to avoid
duplication; they move here when ``sequential.py`` is retired.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ...corpus.protocol import InvestigationCorpus
from ...storage.agent_run_store import AgentRunStore
from ...workflow.hashing import stable_json_hash
from ..agents import EvidenceAnalyst, InvestigationPlanner
from ..agents.analyst import AnalystValidationError
from ..agents.critic import CriticValidationError
from ..agents.guide import GuideValidationError
from ..agents.planner import PlannerValidationError
from ..models.errors import ModelProviderError
from ..contracts.analysis import GroundingValidationReport
from ..contracts.plan import PlanDisposition
from ..contracts.run import AgentRunRecord, AgentStageName, AgentStageRecord, AgentStageStatus
from ..tools.contracts import ToolExecutionContext
from .finalization import FinalizationRunner
from .runner import InvestigationRunner
from .sequential import (
    CancellationCheck,
    SignalEmitter,
    WorkflowSignal,
    WorkflowSignalType,
    _WorkflowCancelled,
    _append_failure_audit,
    _bounded_error,
    _model_stage,
)
from .statuses import AgentRunStatus


class _GraphState(TypedDict, total=False):
    """LangGraph channel state.

    ``record`` and ``corpus`` are threaded through the graph so the nodes read
    the live objects they mutate; ``outcome`` carries a terminal branch marker
    (``"abstained"`` / ``"failed"``) that the conditional edges route on. The
    stage side effects themselves are performed via closures captured per run,
    not stored in channels -- P2(b) makes them checkpointer-native.
    """

    outcome: str


class LangGraphAgentWorkflow:
    """Drop-in for :class:`SequentialAgentWorkflow`, backed by a state graph."""

    def __init__(
        self,
        *,
        planner: InvestigationPlanner,
        retrieval_runner: InvestigationRunner,
        analyst: EvidenceAnalyst,
        finalization_runner: FinalizationRunner,
        store: AgentRunStore,
    ) -> None:
        self.planner = planner
        self.retrieval_runner = retrieval_runner
        self.analyst = analyst
        self.finalization_runner = finalization_runner
        self.store = store

    def run(
        self,
        record: AgentRunRecord,
        corpus: InvestigationCorpus,
        *,
        emit: SignalEmitter | None = None,
        should_cancel: CancellationCheck | None = None,
    ) -> AgentRunRecord:
        emitter = emit or (lambda _signal: None)
        cancellation = should_cancel or (lambda: False)
        if record.runId != record.request.runId or record.request.corpusId != corpus.corpus_id:
            raise ValueError("run record and corpus identities must match")
        if record.status in {AgentRunStatus.ANSWER_READY, AgentRunStatus.ABSTAINED}:
            return record

        record.status = AgentRunStatus.RUNNING
        record.errorMessage = None
        record.touch()
        self.store.save_run(record)
        emitter(WorkflowSignal(type=WorkflowSignalType.RUN_STARTED, message="Agent run started."))

        # Progress is tracked so an unexpected failure records the phase that was
        # active, exactly as the sequential implementation's ``active_stage`` did.
        progress: dict[str, object] = {"stage": None, "round": 0}
        graph = self._build_graph(record, corpus, emitter, cancellation, progress)
        try:
            graph.invoke({})
            return record
        except _WorkflowCancelled:
            return self._cancel(record, emitter)
        except Exception as exc:  # noqa: BLE001 - bounded, audited, re-surfaced
            record.status = AgentRunStatus.FAILED
            record.errorMessage = _bounded_error(exc)
            _append_failure_audit(
                record,
                exc,
                progress["stage"],  # type: ignore[arg-type]
                int(progress["round"]),  # type: ignore[arg-type]
            )
            self._save(record)
            emitter(
                WorkflowSignal(
                    type=WorkflowSignalType.RUN_FAILED,
                    message="The agent run failed. Inspect the run record for the bounded error.",
                )
            )
            return record

    def _build_graph(
        self,
        record: AgentRunRecord,
        corpus: InvestigationCorpus,
        emitter: SignalEmitter,
        cancellation: CancellationCheck,
        progress: dict[str, object],
    ):
        def checkpoint() -> None:
            if cancellation():
                raise _WorkflowCancelled("cancellation requested")

        def planner_node(_state: _GraphState) -> _GraphState:
            checkpoint()
            if record.plan is None:
                progress["stage"] = AgentStageName.PLANNER
                progress["round"] = 0
                _stage_started(emitter, AgentStageName.PLANNER)
                context = ToolExecutionContext(
                    corpusId=corpus.corpus_id,
                    agentRunId=record.runId,
                    requestedByRole="planner",
                    allowedToolNames=set(self.retrieval_runner.allowed_tool_names),
                    maximumResults=self.retrieval_runner.policy.maxResultsPerTool,
                    maximumOutputCharacters=self.retrieval_runner.policy.maxCharactersPerToolOutput,
                )
                specs = self.retrieval_runner.registry.list_specs(context, corpus)
                try:
                    record.plan = self.planner.plan(
                        record.request, record.corpusSnapshot, specs
                    )
                except PlannerValidationError as exc:
                    # A schema-valid plan that failed deterministic planner
                    # authorization (unauthorized tool, incoherent proceed-plan,
                    # a proceed-plan for an out-of-corpus question) is a
                    # model-capability outcome over this corpus, not a system
                    # error: abstain with an audited REJECTED stage rather than
                    # hard-fail. Genuine boundary errors (identity/budget) carry
                    # no model attempt and are re-raised to the failure path.
                    if exc.modelCall is None:
                        raise
                    record.modelCalls.append(exc.modelCall)
                    record.stages.append(_planner_rejected_stage(record.runId, exc))
                    _stage_completed(emitter, AgentStageName.PLANNER)
                    progress["stage"] = None
                    record.status = AgentRunStatus.ABSTAINED
                    record.abstentionReason = _planner_abstention_reason(exc)
                    self._save(record)
                    emitter(
                        WorkflowSignal(
                            type=WorkflowSignalType.RUN_ABSTAINED,
                            message=(
                                "Chronicle could not form a valid, authorized line of "
                                "inquiry over this corpus, and abstained rather than "
                                "proceed on an invalid plan."
                            ),
                        )
                    )
                    return {"outcome": "abstained"}
                if self.planner.last_execution is None:
                    raise RuntimeError("Planner returned without an execution record")
                execution = self.planner.last_execution
                record.modelCalls.append(execution.modelCall)
                record.stages.append(
                    _model_stage(
                        record.runId,
                        AgentStageName.PLANNER,
                        0,
                        execution.modelCall,
                        execution.promptMeasurement,
                        record.plan,
                    )
                )
                self._save(record)
                _stage_completed(emitter, AgentStageName.PLANNER)
                progress["stage"] = None
            if record.plan.disposition is PlanDisposition.ABSTAIN:
                record.status = AgentRunStatus.ABSTAINED
                record.abstentionReason = record.plan.unsupportedReason
                self._save(record)
                emitter(
                    WorkflowSignal(
                        type=WorkflowSignalType.RUN_ABSTAINED,
                        message="Planner abstained because the request is unsupported by this corpus.",
                    )
                )
                return {"outcome": "abstained"}
            return {}

        def retrieval_node(_state: _GraphState) -> _GraphState:
            checkpoint()
            if record.retrievalBundle is None:
                progress["stage"] = AgentStageName.RETRIEVAL
                progress["round"] = 0
                _stage_started(emitter, AgentStageName.RETRIEVAL)
                retrieval = self.retrieval_runner.execute_initial(record.plan, corpus)
                record.retrievalBundle = retrieval.bundle
                record.stages.append(retrieval.stageRecord)
                record.toolCalls = [item.callRecord for item in retrieval.bundle.results]
                self._save(record)
                _stage_completed(emitter, AgentStageName.RETRIEVAL)
                progress["stage"] = None
                retrieval_status = retrieval.stageRecord.status
                if retrieval_status is AgentStageStatus.REJECTED:
                    # The plan was structurally acceptable to the planner but its
                    # tool-call arguments failed the runner's deterministic input
                    # preflight -- the local model produced an unusable plan. That
                    # is a model-capability outcome, not a system error: abstain
                    # honestly rather than crash. (Genuine execution failures and
                    # deadline interruptions keep their FAILED/INTERRUPTED terminal
                    # below.)
                    record.status = AgentRunStatus.ABSTAINED
                    record.abstentionReason = _retrieval_rejected_reason(
                        retrieval.stageRecord
                    )
                    self._save(record)
                    emitter(
                        WorkflowSignal(
                            type=WorkflowSignalType.RUN_ABSTAINED,
                            stage=AgentStageName.RETRIEVAL,
                            message=(
                                "The planned retrieval was invalid; Chronicle "
                                "abstained rather than proceed on an unusable plan."
                            ),
                        )
                    )
                    return {"outcome": "abstained"}
                if retrieval_status in {
                    AgentStageStatus.FAILED,
                    AgentStageStatus.INTERRUPTED,
                }:
                    record.status = (
                        AgentRunStatus.INTERRUPTED
                        if retrieval_status is AgentStageStatus.INTERRUPTED
                        else AgentRunStatus.FAILED
                    )
                    record.errorMessage = (
                        retrieval.stageRecord.errors[0]
                        if retrieval.stageRecord.errors
                        else "Retrieval did not produce a usable result."
                    )
                    self._save(record)
                    emitter(
                        WorkflowSignal(
                            type=WorkflowSignalType.RUN_FAILED,
                            stage=AgentStageName.RETRIEVAL,
                            message="Retrieval did not produce a usable result.",
                        )
                    )
                    return {"outcome": "failed"}
            return {}

        def analyst_node(_state: _GraphState) -> _GraphState:
            checkpoint()
            if record.analysisDraft is None:
                progress["stage"] = AgentStageName.ANALYST
                progress["round"] = 0
                _stage_started(emitter, AgentStageName.ANALYST)
                try:
                    record.analysisDraft = self.analyst.analyze(
                        record.request.userQuestion,
                        record.plan,
                        record.retrievalBundle,
                    )
                except AnalystValidationError as exc:
                    # A schema-valid but ungroundable draft is an
                    # insufficient-evidence outcome (common over thin,
                    # auto-acquired corpora), not a system error: abstain with an
                    # audited rejected stage rather than hard-fail. Genuine
                    # boundary errors (bad identities/lengths) carry no model
                    # attempt and are re-raised to the failure path.
                    if exc.validationReport is None or exc.modelCall is None:
                        raise
                    record.groundingValidation = exc.validationReport
                    record.modelCalls.append(exc.modelCall)
                    record.stages.append(_grounding_rejected_stage(record.runId, exc))
                    _stage_completed(emitter, AgentStageName.ANALYST)
                    progress["stage"] = None
                    record.status = AgentRunStatus.ABSTAINED
                    record.abstentionReason = _grounding_abstention_reason(
                        exc.validationReport
                    )
                    self._save(record)
                    emitter(
                        WorkflowSignal(
                            type=WorkflowSignalType.RUN_ABSTAINED,
                            message=(
                                "The retrieved evidence could not ground an analysis; "
                                "Chronicle abstained rather than assert unsupported claims."
                            ),
                        )
                    )
                    return {"outcome": "abstained"}
                if self.analyst.last_execution is None:
                    raise RuntimeError("Analyst returned without an execution record")
                execution = self.analyst.last_execution
                record.groundingValidation = execution.validationReport
                record.modelCalls.append(execution.modelCall)
                record.stages.append(
                    _model_stage(
                        record.runId,
                        AgentStageName.ANALYST,
                        0,
                        execution.modelCall,
                        execution.promptMeasurement,
                        record.analysisDraft,
                    )
                )
                self._save(record)
                _stage_completed(emitter, AgentStageName.ANALYST)
                progress["stage"] = None
            return {}

        def finalization_node(_state: _GraphState) -> _GraphState:
            checkpoint()

            def final_stage(stage: AgentStageName, started: bool, round_number: int) -> None:
                if started:
                    checkpoint()
                    progress["stage"] = stage
                    progress["round"] = round_number
                    _stage_started(emitter, stage, round_number)
                else:
                    _stage_completed(emitter, stage, round_number)
                    progress["stage"] = None
                    progress["round"] = 0

            try:
                self.finalization_runner.finalize(
                    record.request.userQuestion,
                    record.plan,
                    corpus,
                    record.retrievalBundle,
                    record.analysisDraft,
                    record.groundingValidation,
                    run_record=record,
                    stage_callback=final_stage,
                )
            except ModelProviderError as exc:
                # The Critic/Guide model call could not produce a valid decision
                # or answer even after bounded retries -- finalization-stage
                # model brittleness, not a system error. The run has a grounded
                # analysis but no completed review: abstain rather than crash.
                return _abstain_at_finalization(
                    record, emitter, progress, self._save, _bounded_error(exc)
                )
            except (CriticValidationError, GuideValidationError) as exc:
                # A schema-valid critic decision / guide answer that failed
                # deterministic validation is likewise an insufficient-review
                # outcome. Genuine boundary errors (bad identities/lengths) carry
                # no model attempt and are re-raised to the failure path.
                if exc.modelCall is None:
                    raise
                record.modelCalls.append(exc.modelCall)
                return _abstain_at_finalization(
                    record, emitter, progress, self._save, str(exc)
                )
            signal_type = (
                WorkflowSignalType.RUN_ABSTAINED
                if record.status is AgentRunStatus.ABSTAINED
                else WorkflowSignalType.RUN_COMPLETED
            )
            emitter(
                WorkflowSignal(
                    type=signal_type,
                    message=(
                        "The evidence was insufficient for a reliable answer."
                        if signal_type is WorkflowSignalType.RUN_ABSTAINED
                        else "The cited answer is ready."
                    ),
                )
            )
            return {}

        graph = StateGraph(_GraphState)
        graph.add_node("planner", planner_node)
        graph.add_node("retrieval", retrieval_node)
        graph.add_node("analyst", analyst_node)
        graph.add_node("finalization", finalization_node)
        graph.add_edge(START, "planner")
        graph.add_conditional_edges(
            "planner",
            lambda state: "end" if state.get("outcome") == "abstained" else "retrieval",
            {"end": END, "retrieval": "retrieval"},
        )
        graph.add_conditional_edges(
            "retrieval",
            lambda state: "end"
            if state.get("outcome") in {"failed", "abstained"}
            else "analyst",
            {"end": END, "analyst": "analyst"},
        )
        graph.add_conditional_edges(
            "analyst",
            lambda state: "end" if state.get("outcome") == "abstained" else "finalization",
            {"end": END, "finalization": "finalization"},
        )
        graph.add_edge("finalization", END)
        return graph.compile()

    def _cancel(self, record: AgentRunRecord, emitter: SignalEmitter) -> AgentRunRecord:
        record.status = AgentRunStatus.CANCELLED
        record.errorMessage = None
        self._save(record)
        emitter(
            WorkflowSignal(
                type=WorkflowSignalType.RUN_CANCELLED,
                message="The run stopped at a safe stage boundary.",
            )
        )
        return record

    def _save(self, record: AgentRunRecord) -> None:
        record.touch()
        self.store.save_run(record)


def _grounding_rejected_stage(run_id: str, exc: AnalystValidationError) -> AgentStageRecord:
    """Audit the analyst attempt that produced an ungroundable draft."""

    model_call = exc.modelCall
    assert model_call is not None  # guarded by caller
    output_hash = (
        stable_json_hash(exc.proposedDraft.model_dump(mode="json"))
        if exc.proposedDraft is not None
        else None
    )
    return AgentStageRecord(
        runId=run_id,
        stageName=AgentStageName.ANALYST,
        round=0,
        status=AgentStageStatus.REJECTED,
        startedAt=model_call.startedAt,
        completedAt=model_call.completedAt,
        latencyMs=model_call.latencyMs,
        inputHash=model_call.inputHash,
        outputHash=output_hash,
        promptMeasurement=exc.promptMeasurement,
        modelCalls=[model_call],
        errors=[_grounding_abstention_reason(exc.validationReport)],
    )


def _planner_rejected_stage(run_id: str, exc: PlannerValidationError) -> AgentStageRecord:
    """Audit the planner attempt whose schema-valid plan Chronicle rejected."""

    model_call = exc.modelCall
    assert model_call is not None  # guarded by caller
    return AgentStageRecord(
        runId=run_id,
        stageName=AgentStageName.PLANNER,
        round=0,
        status=AgentStageStatus.REJECTED,
        startedAt=model_call.startedAt,
        completedAt=model_call.completedAt,
        latencyMs=model_call.latencyMs,
        inputHash=model_call.inputHash,
        outputHash=None,
        promptMeasurement=exc.promptMeasurement,
        modelCalls=[model_call],
        errors=[_planner_abstention_reason(exc)],
    )


def _planner_abstention_reason(exc: PlannerValidationError) -> str:
    detail = str(exc).strip() or "the proposed plan was not authorized"
    reason = (
        "Chronicle's planner could not form a valid, authorized investigation plan "
        f"over this corpus ({detail}); it abstained rather than proceed on an invalid plan."
    )
    return reason[:500]


def _abstain_at_finalization(
    record: AgentRunRecord,
    emitter: SignalEmitter,
    progress: dict[str, object],
    save: "Callable[[AgentRunRecord], None]",
    detail: str,
) -> dict[str, str]:
    """Terminate a run that reached finalization but whose critic/guide model
    call could not produce a usable result: a principled abstention, not a crash.
    A grounded analysis exists; the run simply has no completed review."""

    progress["stage"] = None
    progress["round"] = 0
    record.status = AgentRunStatus.ABSTAINED
    record.abstentionReason = _finalization_abstention_reason(detail)
    save(record)
    emitter(
        WorkflowSignal(
            type=WorkflowSignalType.RUN_ABSTAINED,
            message=(
                "Chronicle could not complete the critical review of the analysis "
                "and abstained rather than present an unreviewed answer."
            ),
        )
    )
    return {"outcome": "abstained"}


def _finalization_abstention_reason(detail: str) -> str:
    detail = detail.strip() or "the critical review could not be completed"
    reason = (
        "Chronicle produced a grounded analysis but could not complete the "
        f"critical review or answer composition ({detail}); it abstained rather "
        "than present an unreviewed answer."
    )
    return reason[:500]


def _retrieval_rejected_reason(stage: AgentStageRecord) -> str:
    detail = stage.errors[0] if stage.errors else "the planned retrieval was rejected"
    reason = (
        "The planned retrieval could not be executed "
        f"({detail}); Chronicle abstained rather than proceed on an unusable plan."
    )
    return reason[:500]


def _grounding_abstention_reason(report: GroundingValidationReport | None) -> str:
    messages = [issue.message for issue in report.issues][:3] if report is not None else []
    detail = "; ".join(messages) if messages else "no traceable grounding"
    reason = (
        "The analysis could not be grounded in the retrieved evidence "
        f"({detail}); Chronicle abstained rather than assert unsupported claims."
    )
    return reason[:500]


def _stage_started(emitter: SignalEmitter, stage: AgentStageName, round_number: int = 0) -> None:
    emitter(
        WorkflowSignal(
            type=WorkflowSignalType.STAGE_STARTED,
            stage=stage,
            round=round_number,
            message=f"{stage.value.capitalize()} started.",
        )
    )


def _stage_completed(emitter: SignalEmitter, stage: AgentStageName, round_number: int = 0) -> None:
    emitter(
        WorkflowSignal(
            type=WorkflowSignalType.STAGE_COMPLETED,
            stage=stage,
            round=round_number,
            message=f"{stage.value.capitalize()} completed.",
        )
    )


__all__ = ["LangGraphAgentWorkflow"]
