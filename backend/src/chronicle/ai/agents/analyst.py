"""Bounded, corpus-blind Evidence Analyst with deterministic grounding gates."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.analysis import AnalysisDraft, GroundingValidationReport
from ..contracts.plan import InvestigationPlan
from ..contracts.retrieval import RetrievalBundle
from ..contracts.run import PromptMeasurement
from ..models.metadata import ModelCallRecord, ModelGenerationSettings
from ..models.protocol import ModelProvider
from ..orchestration.policies import AgentExecutionPolicy
from .analyst_prompt import AnalystPrompt, build_analyst_prompt
from .analyst_schema import build_analyst_response_schema
from .grounding import validate_grounding

ANALYST_PROMPT_VERSION = "e3-evidence-analyst-v1"


class AnalystError(RuntimeError):
    """Base class for deterministic Analyst boundary failures."""


class AnalystBudgetError(AnalystError):
    """The complete logical Analyst input exceeds an approved budget."""


class AnalystValidationError(AnalystError):
    """A schema-valid model proposal failed deterministic grounding."""

    def __init__(
        self,
        message: str,
        *,
        validation_report: GroundingValidationReport | None = None,
        proposed_draft: AnalysisDraft | None = None,
        model_call: ModelCallRecord | None = None,
        prompt_measurement: PromptMeasurement | None = None,
    ) -> None:
        super().__init__(message)
        self.validationReport = validation_report
        self.proposedDraft = proposed_draft
        self.modelCall = model_call
        self.promptMeasurement = prompt_measurement


@dataclass(frozen=True)
class AnalystExecution:
    modelCall: ModelCallRecord
    promptMeasurement: PromptMeasurement
    validationReport: GroundingValidationReport


class EvidenceAnalyst:
    """Generate and ground one AnalysisDraft without access to a corpus."""

    def __init__(
        self,
        provider: ModelProvider,
        policy: AgentExecutionPolicy | None = None,
    ) -> None:
        self._provider = provider
        self._policy = policy or AgentExecutionPolicy()
        self.last_prompt: AnalystPrompt | None = None
        self.last_execution: AnalystExecution | None = None

    def analyze(
        self,
        user_question: str,
        plan: InvestigationPlan,
        retrieval_bundle: RetrievalBundle,
    ) -> AnalysisDraft:
        self.last_prompt = None
        self.last_execution = None
        if not user_question or len(user_question) > 1_000:
            raise AnalystValidationError("user question must contain 1 to 1,000 characters")
        if (
            plan.runId != retrieval_bundle.runId
            or plan.planId != retrieval_bundle.planId
            or plan.corpusId != retrieval_bundle.corpusId
        ):
            raise AnalystValidationError(
                "plan and retrieval bundle identities do not match"
            )
        try:
            response_schema = build_analyst_response_schema(retrieval_bundle)
            prompt = build_analyst_prompt(
                user_question,
                plan,
                retrieval_bundle,
                self._policy,
                response_schema=response_schema,
            )
        except ValueError as exc:
            raise AnalystBudgetError(str(exc)) from None
        self.last_prompt = prompt

        result = self._provider.generate_structured(
            system_prompt=prompt.systemPrompt,
            user_prompt=prompt.userPrompt,
            response_model=AnalysisDraft,
            response_schema=response_schema,
            prompt_version=ANALYST_PROMPT_VERSION,
            temperature=0.0,
            generation_settings=ModelGenerationSettings(
                temperature=0.0,
                contextTokens=self._policy.modelContextTokens,
                maxCompletionTokens=self._policy.analystMaxCompletionTokens,
            ),
        )
        report = validate_grounding(result.value, plan, retrieval_bundle)
        if not report.valid:
            raise AnalystValidationError(
                "analysis draft failed deterministic grounding validation",
                validation_report=report,
                proposed_draft=result.value,
                model_call=result.modelCall,
                prompt_measurement=prompt.measurement,
            )
        self.last_execution = AnalystExecution(
            modelCall=result.modelCall,
            promptMeasurement=prompt.measurement,
            validationReport=report,
        )
        return result.value
