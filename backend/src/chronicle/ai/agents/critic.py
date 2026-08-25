"""Bounded Historical Critic with deterministic decision validation."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.analysis import AnalysisDraft, GroundingValidationReport
from ..contracts.critique import CriticDecision, CriticValidationReport
from ..contracts.plan import InvestigationPlan
from ..contracts.retrieval import RetrievalBundle
from ..contracts.run import PromptMeasurement
from ..models.metadata import ModelCallRecord, ModelGenerationSettings
from ..models.protocol import ModelProvider
from ..orchestration.policies import AgentExecutionPolicy
from .critic_prompt import CriticPrompt, build_critic_prompt
from .validation import validate_critic_decision

CRITIC_PROMPT_VERSION = "e4-historical-critic-v1"


class CriticError(RuntimeError):
    pass


class CriticBudgetError(CriticError):
    pass


class CriticValidationError(CriticError):
    def __init__(
        self,
        message: str,
        *,
        validation_report: CriticValidationReport | None = None,
        model_call: ModelCallRecord | None = None,
        prompt_measurement: PromptMeasurement | None = None,
    ) -> None:
        super().__init__(message)
        self.validationReport = validation_report
        self.modelCall = model_call
        self.promptMeasurement = prompt_measurement


@dataclass(frozen=True)
class CriticExecution:
    modelCall: ModelCallRecord
    promptMeasurement: PromptMeasurement
    validationReport: CriticValidationReport


class HistoricalCritic:
    def __init__(
        self,
        provider: ModelProvider,
        policy: AgentExecutionPolicy | None = None,
    ) -> None:
        self._provider = provider
        self._policy = policy or AgentExecutionPolicy()
        self.last_prompt: CriticPrompt | None = None
        self.last_execution: CriticExecution | None = None

    def review(
        self,
        user_question: str,
        plan: InvestigationPlan,
        retrieval_bundle: RetrievalBundle,
        analysis: AnalysisDraft,
        grounding: GroundingValidationReport,
    ) -> CriticDecision:
        self.last_prompt = None
        self.last_execution = None
        if not user_question or len(user_question) > 1_000:
            raise CriticValidationError("user question must contain 1 to 1,000 characters")
        if (
            plan.runId != retrieval_bundle.runId
            or plan.planId != retrieval_bundle.planId
            or plan.corpusId != retrieval_bundle.corpusId
        ):
            raise CriticValidationError("plan and retrieval bundle identities do not match")
        try:
            prompt = build_critic_prompt(
                user_question,
                plan,
                retrieval_bundle,
                analysis,
                grounding,
                self._policy,
            )
        except ValueError as exc:
            raise CriticBudgetError(str(exc)) from None
        self.last_prompt = prompt
        result = self._provider.generate_structured(
            system_prompt=prompt.systemPrompt,
            user_prompt=prompt.userPrompt,
            response_model=CriticDecision,
            prompt_version=CRITIC_PROMPT_VERSION,
            temperature=0.0,
            generation_settings=ModelGenerationSettings(
                temperature=0.0,
                contextTokens=self._policy.modelContextTokens,
                maxCompletionTokens=self._policy.criticMaxCompletionTokens,
            ),
        )
        report = validate_critic_decision(result.value, analysis, grounding, plan)
        if not report.valid:
            raise CriticValidationError(
                "critic decision failed deterministic validation",
                validation_report=report,
                model_call=result.modelCall,
                prompt_measurement=prompt.measurement,
            )
        self.last_execution = CriticExecution(
            modelCall=result.modelCall,
            promptMeasurement=prompt.measurement,
            validationReport=report,
        )
        return result.value
