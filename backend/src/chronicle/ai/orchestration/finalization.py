"""One bounded E4 critique/retrieval/reanalysis/guide finalization cycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel

from ...corpus.protocol import InvestigationCorpus
from ...storage.agent_run_store import AgentRunStore
from ...workflow.hashing import stable_json_hash
from ..agents.analyst import EvidenceAnalyst
from ..agents.critic import HistoricalCritic
from ..agents.guide import InvestigationGuide
from ..agents.validation import build_action_reference_index, validate_critic_decision
from ..contracts.analysis import AnalysisDraft, GroundingValidationReport
from ..contracts.answer import AgentAnswer, AnswerValidationReport
from ..contracts.critique import CriticDecision, CriticValidationReport, CriticVerdict
from ..contracts.plan import InvestigationPlan
from ..contracts.retrieval import RetrievalBundle
from ..contracts.run import (
    AgentRunRecord,
    AgentStageName,
    AgentStageRecord,
    AgentStageStatus,
    PromptMeasurement,
)
from ..models.metadata import ModelCallRecord
from .policies import AgentExecutionPolicy
from .runner import InvestigationRunner
from .statuses import AgentRunStatus

StageCallback = Callable[[AgentStageName, bool, int], None]


@dataclass(frozen=True)
class FinalizationExecution:
    retrievalBundle: RetrievalBundle
    analysisDraft: AnalysisDraft
    groundingValidation: GroundingValidationReport
    criticDecisions: tuple[CriticDecision, ...]
    answer: AgentAnswer
    answerValidation: AnswerValidationReport


class FinalizationRunner:
    """Run Critic, at most one follow-up retrieval, then Guide."""

    def __init__(
        self,
        *,
        retrieval_runner: InvestigationRunner,
        analyst: EvidenceAnalyst,
        critic: HistoricalCritic,
        guide: InvestigationGuide,
        store: AgentRunStore | None = None,
        policy: AgentExecutionPolicy | None = None,
    ) -> None:
        self.retrieval_runner = retrieval_runner
        self.analyst = analyst
        self.critic = critic
        self.guide = guide
        self.store = store
        self.policy = policy or AgentExecutionPolicy()

    def finalize(
        self,
        user_question: str,
        plan: InvestigationPlan,
        corpus: InvestigationCorpus,
        retrieval_bundle: RetrievalBundle,
        analysis: AnalysisDraft,
        grounding: GroundingValidationReport,
        *,
        run_record: AgentRunRecord | None = None,
        stage_callback: StageCallback | None = None,
    ) -> FinalizationExecution:
        decisions: list[CriticDecision] = []
        critic_validations: list[CriticValidationReport] = []
        stage_records: list[AgentStageRecord] = []
        model_calls: list[ModelCallRecord] = []
        current_bundle = retrieval_bundle
        current_analysis = analysis
        current_grounding = grounding

        _notify(stage_callback, AgentStageName.CRITIC, True, 0)
        decision = self.critic.review(
            user_question,
            plan,
            current_bundle,
            current_analysis,
            current_grounding,
        )
        _notify(stage_callback, AgentStageName.CRITIC, False, 0)
        decisions.append(decision)
        if self.critic.last_execution is None:
            raise RuntimeError("Critic returned without an execution record")
        critic_validations.append(self.critic.last_execution.validationReport)
        model_calls.append(self.critic.last_execution.modelCall)
        stage_records.append(
            _model_stage(
                plan.runId,
                AgentStageName.CRITIC,
                0,
                self.critic.last_execution.modelCall,
                self.critic.last_execution.promptMeasurement,
                decision,
            )
        )
        if decision.verdict is CriticVerdict.RETRIEVE_MORE:
            _notify(stage_callback, AgentStageName.RETRIEVAL, True, 1)
            follow_up = self.retrieval_runner.execute_follow_up(
                plan,
                decision.additionalToolCalls[0],
                corpus,
                current_bundle,
            )
            _notify(stage_callback, AgentStageName.RETRIEVAL, False, 1)
            stage_records.append(follow_up.stageRecord)
            if follow_up.stageRecord.status.value not in {"succeeded", "partial"}:
                decision = _bounded_abstention(
                    plan,
                    "The permitted follow-up retrieval could not be completed.",
                )
                decisions.append(decision)
                critic_validations.append(
                    validate_critic_decision(decision, current_analysis, current_grounding, plan)
                )
            else:
                current_bundle = follow_up.bundle
                _notify(stage_callback, AgentStageName.ANALYST, True, 1)
                current_analysis = self.analyst.analyze(
                    user_question,
                    plan,
                    current_bundle,
                )
                _notify(stage_callback, AgentStageName.ANALYST, False, 1)
                if self.analyst.last_execution is None:
                    raise RuntimeError("Analyst returned without an execution record")
                current_grounding = self.analyst.last_execution.validationReport
                model_calls.append(self.analyst.last_execution.modelCall)
                stage_records.append(
                    _model_stage(
                        plan.runId,
                        AgentStageName.ANALYST,
                        1,
                        self.analyst.last_execution.modelCall,
                        self.analyst.last_execution.promptMeasurement,
                        current_analysis,
                    )
                )
                _notify(stage_callback, AgentStageName.CRITIC, True, 1)
                decision = self.critic.review(
                    user_question,
                    plan,
                    current_bundle,
                    current_analysis,
                    current_grounding,
                )
                _notify(stage_callback, AgentStageName.CRITIC, False, 1)
                decisions.append(decision)
                if self.critic.last_execution is None:
                    raise RuntimeError("Critic returned without an execution record")
                critic_validations.append(self.critic.last_execution.validationReport)
                model_calls.append(self.critic.last_execution.modelCall)
                stage_records.append(
                    _model_stage(
                        plan.runId,
                        AgentStageName.CRITIC,
                        1,
                        self.critic.last_execution.modelCall,
                        self.critic.last_execution.promptMeasurement,
                        decision,
                    )
                )
                if decision.verdict is CriticVerdict.RETRIEVE_MORE:
                    decision = _bounded_abstention(
                        plan,
                        "The single permitted follow-up retrieval was exhausted.",
                    )
                    decisions.append(decision)
                    critic_validations.append(
                        validate_critic_decision(
                            decision, current_analysis, current_grounding, plan
                        )
                    )

        action_index = build_action_reference_index(corpus.get_investigation())
        _notify(stage_callback, AgentStageName.GUIDE, True, 0)
        answer = self.guide.compose(
            user_question,
            current_analysis,
            decision,
            action_index,
        )
        _notify(stage_callback, AgentStageName.GUIDE, False, 0)
        if self.guide.last_execution is None:
            raise RuntimeError("Guide returned without an execution record")
        guide_call = self.guide.last_execution.modelCall
        if guide_call is not None:
            model_calls.append(guide_call)
            stage_records.append(
                _model_stage(
                    plan.runId,
                    AgentStageName.GUIDE,
                    0,
                    guide_call,
                    self.guide.last_execution.promptMeasurement,
                    answer,
                )
            )
        else:
            # The Guide composed the answer deterministically (no model call);
            # record a model-free stage, mirroring the deterministic retrieval
            # stage, so the audit trail states plainly that no model was invoked.
            stage_records.append(_deterministic_guide_stage(plan.runId, answer))
        execution = FinalizationExecution(
            retrievalBundle=current_bundle,
            analysisDraft=current_analysis,
            groundingValidation=current_grounding,
            criticDecisions=tuple(decisions),
            answer=answer,
            answerValidation=self.guide.last_execution.validationReport,
        )
        if run_record is not None:
            self._persist(
                run_record,
                execution,
                critic_validations,
                stage_records,
                model_calls,
            )
        return execution

    def _persist(
        self,
        run_record: AgentRunRecord,
        execution: FinalizationExecution,
        critic_validations: list[CriticValidationReport],
        stages: list[AgentStageRecord],
        model_calls: list[ModelCallRecord],
    ) -> None:
        if self.store is None:
            raise ValueError("run_record persistence requires an AgentRunStore")
        if run_record.runId != execution.analysisDraft.runId:
            raise ValueError("run_record identity does not match finalization")
        run_record.retrievalBundle = execution.retrievalBundle
        run_record.analysisDraft = execution.analysisDraft
        run_record.groundingValidation = execution.groundingValidation
        run_record.criticDecisions = list(execution.criticDecisions)
        run_record.criticValidations = critic_validations
        run_record.finalAnswer = execution.answer
        run_record.answerValidation = execution.answerValidation
        run_record.stages = [*run_record.stages, *stages]
        run_record.modelCalls = [*run_record.modelCalls, *model_calls]
        run_record.toolCalls = [
            item.callRecord for item in execution.retrievalBundle.results
        ]
        run_record.status = (
            AgentRunStatus.ABSTAINED
            if execution.answer.status.value == "abstained"
            else AgentRunStatus.ANSWER_READY
        )
        run_record.abstentionReason = (
            _abstention_reason(execution)
            if execution.answer.status.value == "abstained"
            else None
        )
        run_record.touch()
        self.store.save_run(run_record)


def _abstention_reason(execution: FinalizationExecution) -> str:
    direct = execution.answer.directAnswer.strip()
    if direct.casefold() not in {"abstain", "abstained", "insufficient evidence"}:
        return direct
    if execution.criticDecisions:
        return execution.criticDecisions[-1].rationaleSummary
    return "The retrieved evidence did not support a reliable answer."


def _bounded_abstention(plan: InvestigationPlan, limitation: str) -> CriticDecision:
    return CriticDecision(
        criticVersion="e4-deterministic-bound-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        verdict=CriticVerdict.ABSTAIN,
        limitationsToSurface=[limitation],
        rationaleSummary=(
            "Chronicle stopped after the one allowed evidence follow-up rather than "
            "continuing an unbounded retrieval loop."
        ),
    )


def _notify(
    callback: StageCallback | None,
    stage: AgentStageName,
    started: bool,
    round_number: int,
) -> None:
    if callback is not None:
        callback(stage, started, round_number)


def _deterministic_guide_stage(run_id: str, answer: BaseModel) -> AgentStageRecord:
    """A Guide stage that ran with no model call (deterministic composition)."""

    return AgentStageRecord(
        runId=run_id,
        stageName=AgentStageName.GUIDE,
        round=0,
        status=AgentStageStatus.SUCCEEDED,
        outputHash=stable_json_hash(answer.model_dump(mode="json")),
        modelCalls=[],
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


__all__ = ["FinalizationExecution", "FinalizationRunner"]
