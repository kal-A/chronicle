"""Investigation Guide over only Critic-approved statements."""

from __future__ import annotations

from dataclasses import dataclass

from ..contracts.analysis import AnalysisDraft
from ..contracts.answer import (
    ActionReferenceIndex,
    AgentAnswer,
    AnswerCitation,
    AnswerValidationReport,
)
from ..contracts.critique import CriticDecision
from ..contracts.run import PromptMeasurement
from ..models.metadata import ModelCallRecord, ModelGenerationSettings
from ..models.protocol import ModelProvider
from ..orchestration.policies import AgentExecutionPolicy
from .guide_prompt import GuidePrompt, build_guide_prompt
from .guide_schema import build_guide_response_schema
from .validation import approved_statements, validate_agent_answer

GUIDE_PROMPT_VERSION = "e4-investigation-guide-v1"


class GuideError(RuntimeError):
    pass


class GuideBudgetError(GuideError):
    pass


class GuideValidationError(GuideError):
    def __init__(
        self,
        message: str,
        *,
        validation_report: AnswerValidationReport | None = None,
        model_call: ModelCallRecord | None = None,
        prompt_measurement: PromptMeasurement | None = None,
        proposed_answer: AgentAnswer | None = None,
    ) -> None:
        super().__init__(message)
        self.validationReport = validation_report
        self.modelCall = model_call
        self.promptMeasurement = prompt_measurement
        self.proposedAnswer = proposed_answer


@dataclass(frozen=True)
class GuideExecution:
    modelCall: ModelCallRecord
    promptMeasurement: PromptMeasurement
    validationReport: AnswerValidationReport
    modelAnswer: AgentAnswer
    citationsNormalized: bool


class InvestigationGuide:
    def __init__(
        self,
        provider: ModelProvider,
        policy: AgentExecutionPolicy | None = None,
    ) -> None:
        self._provider = provider
        self._policy = policy or AgentExecutionPolicy()
        self.last_prompt: GuidePrompt | None = None
        self.last_execution: GuideExecution | None = None

    def compose(
        self,
        user_question: str,
        analysis: AnalysisDraft,
        decision: CriticDecision,
        action_index: ActionReferenceIndex,
    ) -> AgentAnswer:
        self.last_prompt = None
        self.last_execution = None
        if not user_question or len(user_question) > 1_000:
            raise GuideValidationError("user question must contain 1 to 1,000 characters")
        response_schema = build_guide_response_schema(analysis, decision)
        try:
            prompt = build_guide_prompt(
                user_question,
                analysis,
                decision,
                action_index,
                self._policy,
                response_schema=response_schema,
            )
        except ValueError as exc:
            raise GuideBudgetError(str(exc)) from None
        self.last_prompt = prompt
        result = self._provider.generate_structured(
            system_prompt=prompt.systemPrompt,
            user_prompt=prompt.userPrompt,
            response_model=AgentAnswer,
            response_schema=response_schema,
            prompt_version=GUIDE_PROMPT_VERSION,
            temperature=0.0,
            generation_settings=ModelGenerationSettings(
                temperature=0.0,
                contextTokens=self._policy.modelContextTokens,
                maxCompletionTokens=self._policy.guideMaxCompletionTokens,
            ),
        )
        normalized_answer = _attach_canonical_citations(
            result.value, analysis, decision
        )
        report = validate_agent_answer(
            normalized_answer, analysis, decision, action_index
        )
        if not report.valid:
            raise GuideValidationError(
                "agent answer failed deterministic validation",
                validation_report=report,
                model_call=result.modelCall,
                prompt_measurement=prompt.measurement,
                proposed_answer=result.value,
            )
        self.last_execution = GuideExecution(
            modelCall=result.modelCall,
            promptMeasurement=prompt.measurement,
            validationReport=report,
            modelAnswer=result.value,
            citationsNormalized=normalized_answer.citations != result.value.citations,
        )
        return normalized_answer


def _attach_canonical_citations(
    answer: AgentAnswer,
    analysis: AnalysisDraft,
    decision: CriticDecision,
) -> AgentAnswer:
    approved = approved_statements(analysis, decision)
    citations: list[AnswerCitation] = []
    seen: set[tuple[str, str]] = set()
    for point in [*answer.keyPoints, *answer.disagreements]:
        item = approved.get(point.statementId)
        if item is None:
            continue
        for citation in item[1].citations:
            identity = (point.statementId, citation.model_dump_json())
            if identity in seen:
                continue
            seen.add(identity)
            citations.append(
                AnswerCitation(statementId=point.statementId, citation=citation)
            )
    return answer.model_copy(update={"citations": citations})
