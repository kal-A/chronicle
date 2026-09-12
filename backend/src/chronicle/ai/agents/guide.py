"""Investigation Guide over only Critic-approved statements.

The Guide's answer is fully determined by the Critic-approved statements: its
key points are exactly those statements (whose text ``validate_agent_answer``
requires verbatim), its ``directAnswer`` is their concatenation, and its
citations are re-attached mechanically from each statement's grounded evidence.
The response schema (``build_guide_response_schema``) const-locks every one of
those fields, so a model call only echoes values Chronicle already holds -- and
a small model routinely fails to echo them (e.g. emitting a ``directAnswer``
with no key point), turning a grounded, approved analysis into a false
abstention.

So the Guide composes the answer deterministically from the approved statements
instead of calling the model, then runs the same ``validate_agent_answer`` gate.
This makes a grounded, approved analysis reach the user as a real cited answer
by construction (no model hiccup can drop it), and cannot fabricate: every key
point is an approved statement, every citation traces to that statement's
evidence, and no map action or disagreement is invented. The Critic remains the
sole honesty gate upstream; the Guide only renders its approved verdict.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from ..contracts.analysis import AnalysisDraft, AnswerStatus
from ..contracts.answer import (
    ActionReferenceIndex,
    AgentAnswer,
    AnswerCitation,
    AnswerPoint,
    AnswerValidationReport,
)
from ..contracts.critique import CriticDecision
from ..contracts.run import PromptMeasurement
from ..models.metadata import ModelCallRecord
from ..models.protocol import ModelProvider
from ..orchestration.policies import AgentExecutionPolicy
from .validation import approved_statements, validate_agent_answer

GUIDE_PROMPT_VERSION = "e4-investigation-guide-v1"
GUIDE_ANSWER_VERSION = "e4-guide-v1"
_ABSTENTION_TEXT = (
    "The available evidence did not support a grounded answer to this question."
)


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
    """Auditable metadata. ``modelCall`` is None because the constrained answer
    is composed deterministically -- the audit trail records no model call
    rather than a fabricated one."""

    modelCall: ModelCallRecord | None
    promptMeasurement: PromptMeasurement | None
    validationReport: AnswerValidationReport
    answer: AgentAnswer
    deterministic: bool


class InvestigationGuide:
    def __init__(
        self,
        provider: ModelProvider,
        policy: AgentExecutionPolicy | None = None,
    ) -> None:
        # The provider is retained for interface compatibility with the other
        # agents; the Guide's constrained answer needs no model call.
        self._provider = provider
        self._policy = policy or AgentExecutionPolicy()
        self.last_execution: GuideExecution | None = None

    def compose(
        self,
        user_question: str,
        analysis: AnalysisDraft,
        decision: CriticDecision,
        action_index: ActionReferenceIndex,
    ) -> AgentAnswer:
        self.last_execution = None
        if not user_question or len(user_question) > 1_000:
            raise GuideValidationError("user question must contain 1 to 1,000 characters")

        answer = self._compose_answer(analysis, decision)
        report = validate_agent_answer(answer, analysis, decision, action_index)
        if not report.valid:
            raise GuideValidationError(
                "deterministically composed answer failed validation",
                validation_report=report,
                proposed_answer=answer,
            )
        self.last_execution = GuideExecution(
            modelCall=None,
            promptMeasurement=None,
            validationReport=report,
            answer=answer,
            deterministic=True,
        )
        return answer

    def _compose_answer(
        self,
        analysis: AnalysisDraft,
        decision: CriticDecision,
    ) -> AgentAnswer:
        approved = approved_statements(analysis, decision)
        identity = {
            "answerVersion": GUIDE_ANSWER_VERSION,
            "runId": analysis.runId,
            "planId": analysis.planId,
            "corpusId": analysis.corpusId,
        }
        if not approved:
            # A rejected/abstained critique yields an abstained answer: no claims,
            # citations, or actions (validate_agent_answer enforces this shape).
            return AgentAnswer(
                **identity,
                status=AnswerStatus.ABSTAINED,
                directAnswer=_ABSTENTION_TEXT,
            )

        # One key point per approved statement, in approved order (accepted then
        # downgraded), with the exact approved text; directAnswer is their join
        # (validate_agent_answer forbids any paraphrase). Status mirrors the
        # analyst's own assessment, never abstained (the critique approved it).
        key_points = [
            AnswerPoint(statementId=statement_id, text=text)
            for statement_id, (text, _statement) in approved.items()
        ]
        direct_answer = " ".join(point.text for point in key_points)
        status = (
            analysis.status
            if analysis.status in {AnswerStatus.ANSWERED, AnswerStatus.PARTIAL}
            else AnswerStatus.PARTIAL
        )
        try:
            answer = AgentAnswer(
                **identity,
                status=status,
                directAnswer=direct_answer,
                keyPoints=key_points,
            )
        except ValidationError as exc:
            # The only realistic failure is the approved text exceeding the
            # directAnswer/key-point length ceilings -- surface it as a graceful
            # abstention (finalization converts it) rather than a crash.
            raise GuideValidationError(
                "approved statements do not fit a valid answer shape",
                proposed_answer=None,
            ) from exc
        return _attach_canonical_citations(answer, analysis, decision)


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
