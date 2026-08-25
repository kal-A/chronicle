"""Resumable, strictly sequential execution of Chronicle's four AI roles."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field

from ...corpus.protocol import InvestigationCorpus
from ...storage.agent_run_store import AgentRunStore
from ...workflow.hashing import stable_json_hash
from ..agents import EvidenceAnalyst, InvestigationPlanner
from ..contracts.plan import PlanDisposition
from ..contracts.run import (
    AgentRunRecord,
    AgentStageName,
    AgentStageRecord,
    AgentStageStatus,
    PromptMeasurement,
)
from ..models.metadata import ModelCallRecord
from ..tools.contracts import ToolExecutionContext
from .finalization import FinalizationRunner
from .runner import InvestigationRunner
from .statuses import AgentRunStatus


class WorkflowSignalType(str, Enum):
    RUN_STARTED = "run_started"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    RUN_COMPLETED = "run_completed"
    RUN_ABSTAINED = "run_abstained"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"


class WorkflowSignal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: WorkflowSignalType
    stage: AgentStageName | None = None
    round: int = Field(default=0, ge=0, le=1)
    message: str = Field(min_length=1, max_length=300)


SignalEmitter = Callable[[WorkflowSignal], None]
CancellationCheck = Callable[[], bool]


class _WorkflowCancelled(RuntimeError):
    pass


class SequentialAgentWorkflow:
    """Run one investigation request with no parallel role execution."""

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
        active_stage: AgentStageName | None = None
        active_round = 0

        try:
            self._checkpoint(cancellation)
            if record.plan is None:
                active_stage = AgentStageName.PLANNER
                self._stage_started(emitter, AgentStageName.PLANNER)
                context = ToolExecutionContext(
                    corpusId=corpus.corpus_id,
                    agentRunId=record.runId,
                    requestedByRole="planner",
                    allowedToolNames=set(self.retrieval_runner.allowed_tool_names),
                    maximumResults=self.retrieval_runner.policy.maxResultsPerTool,
                    maximumOutputCharacters=self.retrieval_runner.policy.maxCharactersPerToolOutput,
                )
                specs = self.retrieval_runner.registry.list_specs(context, corpus)
                record.plan = self.planner.plan(record.request, record.corpusSnapshot, specs)
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
                self._stage_completed(emitter, AgentStageName.PLANNER)
                active_stage = None
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
                return record

            self._checkpoint(cancellation)
            if record.retrievalBundle is None:
                active_stage = AgentStageName.RETRIEVAL
                self._stage_started(emitter, AgentStageName.RETRIEVAL)
                retrieval = self.retrieval_runner.execute_initial(record.plan, corpus)
                record.retrievalBundle = retrieval.bundle
                record.stages.append(retrieval.stageRecord)
                record.toolCalls = [item.callRecord for item in retrieval.bundle.results]
                self._save(record)
                self._stage_completed(emitter, AgentStageName.RETRIEVAL)
                active_stage = None
                if retrieval.stageRecord.status in {
                    AgentStageStatus.FAILED,
                    AgentStageStatus.REJECTED,
                    AgentStageStatus.INTERRUPTED,
                }:
                    record.status = (
                        AgentRunStatus.INTERRUPTED
                        if retrieval.stageRecord.status is AgentStageStatus.INTERRUPTED
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
                    return record

            self._checkpoint(cancellation)
            if record.analysisDraft is None:
                active_stage = AgentStageName.ANALYST
                self._stage_started(emitter, AgentStageName.ANALYST)
                record.analysisDraft = self.analyst.analyze(
                    record.request.userQuestion,
                    record.plan,
                    record.retrievalBundle,
                )
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
                self._stage_completed(emitter, AgentStageName.ANALYST)
                active_stage = None

            self._checkpoint(cancellation)

            def final_stage(stage: AgentStageName, started: bool, round_number: int) -> None:
                nonlocal active_stage, active_round
                if started:
                    self._checkpoint(cancellation)
                    active_stage = stage
                    active_round = round_number
                    self._stage_started(emitter, stage, round_number)
                else:
                    self._stage_completed(emitter, stage, round_number)
                    active_stage = None
                    active_round = 0

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
            return record
        except _WorkflowCancelled:
            return self._cancel(record, emitter)
        except Exception as exc:
            record.status = AgentRunStatus.FAILED
            record.errorMessage = _bounded_error(exc)
            _append_failure_audit(record, exc, active_stage, active_round)
            self._save(record)
            emitter(
                WorkflowSignal(
                    type=WorkflowSignalType.RUN_FAILED,
                    message="The agent run failed. Inspect the run record for the bounded error.",
                )
            )
            return record

    @staticmethod
    def _checkpoint(cancellation: CancellationCheck) -> None:
        if cancellation():
            raise _WorkflowCancelled("cancellation requested")

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

    @staticmethod
    def _stage_started(
        emitter: SignalEmitter,
        stage: AgentStageName,
        round_number: int = 0,
    ) -> None:
        emitter(
            WorkflowSignal(
                type=WorkflowSignalType.STAGE_STARTED,
                stage=stage,
                round=round_number,
                message=f"{stage.value.capitalize()} started.",
            )
        )

    @staticmethod
    def _stage_completed(
        emitter: SignalEmitter,
        stage: AgentStageName,
        round_number: int = 0,
    ) -> None:
        emitter(
            WorkflowSignal(
                type=WorkflowSignalType.STAGE_COMPLETED,
                stage=stage,
                round=round_number,
                message=f"{stage.value.capitalize()} completed.",
            )
        )


def _model_stage(
    run_id: str,
    stage_name: AgentStageName,
    round_number: int,
    model_call: ModelCallRecord,
    prompt_measurement: PromptMeasurement,
    output: BaseModel,
) -> AgentStageRecord:
    return AgentStageRecord(
        runId=run_id,
        stageName=stage_name,
        round=round_number,
        status=AgentStageStatus.SUCCEEDED,
        startedAt=model_call.startedAt,
        completedAt=model_call.completedAt,
        latencyMs=model_call.latencyMs,
        inputHash=model_call.inputHash,
        outputHash=stable_json_hash(output.model_dump(mode="json")),
        promptMeasurement=prompt_measurement,
        modelCalls=[model_call],
    )


def _bounded_error(error: Exception) -> str:
    parts = [str(error) or type(error).__name__]
    cause = error.__cause__
    if cause is not None:
        parts.append(f"{type(cause).__name__}: {cause}")
    rendered = " Caused by: ".join(parts).replace("\r", " ").replace("\n", " ")
    return rendered[:800]


def _append_failure_audit(
    record: AgentRunRecord,
    error: Exception,
    stage: AgentStageName | None,
    round_number: int,
) -> None:
    model_call = getattr(error, "callRecord", None) or getattr(error, "modelCall", None)
    if model_call is not None and model_call not in record.modelCalls:
        record.modelCalls.append(model_call)
    if stage is None:
        return
    now = datetime.now(timezone.utc)
    record.stages.append(
        AgentStageRecord(
            runId=record.runId,
            stageName=stage,
            round=round_number,
            status=AgentStageStatus.FAILED,
            startedAt=model_call.startedAt if model_call is not None else now,
            completedAt=model_call.completedAt if model_call is not None else now,
            latencyMs=model_call.latencyMs if model_call is not None else 0.0,
            inputHash=model_call.inputHash if model_call is not None else None,
            modelCalls=[model_call] if model_call is not None else [],
            errors=[_bounded_error(error)],
        )
    )


__all__ = ["SequentialAgentWorkflow", "WorkflowSignal", "WorkflowSignalType"]
