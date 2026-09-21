"""Deterministic metrics for Phase E3 plans, citations, and run budgets."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from typing import TYPE_CHECKING

from ...contracts.enums import EvidenceLinkRole
from ..contracts.analysis import AnalysisCitation, AnalysisDraft, AnswerStatus
from ..contracts.plan import InvestigationPlan, PlanDisposition
from ..contracts.retrieval import RetrievedReferenceIndex
from ..orchestration.policies import AgentExecutionPolicy
from .benchmark import BenchmarkCase
from .contracts import StrategyId

if TYPE_CHECKING:  # StrategyResult lives in strategies.py (heavy imports); only annotated here
    from .contracts import EvaluationCase
    from .strategies import StrategyResult


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str
    planValid: bool | None = None
    acceptableToolSelectionRate: float | None = Field(default=None, ge=0, le=1)
    unnecessaryToolCallCount: int | None = Field(default=None, ge=0)
    requiredEvidenceRecall: float | None = Field(default=None, ge=0, le=1)
    citationIdValidityRate: float | None = Field(default=None, ge=0, le=1)
    citationCoverageRate: float | None = Field(default=None, ge=0, le=1)
    roleCorrectnessRate: float | None = Field(default=None, ge=0, le=1)
    unsupportedStatementRate: float | None = Field(default=None, ge=0, le=1)
    abstentionCorrect: bool | None = None
    counterevidenceSatisfied: bool | None = None
    temporalConstraintCoverage: float | None = Field(default=None, ge=0, le=1)
    forbiddenEvidenceHits: tuple[str, ...] = ()
    unacceptableClaimHits: tuple[str, ...] = ()


def _citation_ids(citation: AnalysisCitation) -> set[str]:
    return {
        value for value in (
            citation.evidenceLinkId,
            citation.passageId,
            citation.sourceId,
            citation.targetId,
        ) if value
    }


def _citation_is_valid(citation: AnalysisCitation, references: RetrievedReferenceIndex) -> bool:
    links = {link.evidenceLinkId: link for link in references.evidenceLinks}
    if citation.evidenceLinkId:
        link = links.get(citation.evidenceLinkId)
        if link is None:
            return False
        expected = (
            (citation.passageId, link.passageId),
            (citation.sourceId, link.sourceId),
            (citation.targetType, link.targetType),
            (citation.targetId, link.targetId),
        )
        return all(given is None or given == actual for given, actual in expected)

    checks = (
        citation.passageId is None or citation.passageId in references.passageIds,
        citation.sourceId is None or citation.sourceId in references.sourceIds,
        citation.targetId is None or citation.targetId in _target_ids(references),
    )
    return all(checks)


def _target_ids(references: RetrievedReferenceIndex) -> set[str]:
    return set().union(
        references.claimIds,
        references.relationshipIds,
        references.eventIds,
        references.knowledgeStateIds,
        references.placeIds,
        references.mapSceneIds,
    )


def evaluate_case(
    case: BenchmarkCase,
    *,
    plan: InvestigationPlan | None = None,
    analysis: AnalysisDraft | None = None,
    references: RetrievedReferenceIndex | None = None,
) -> EvaluationResult:
    """Score only machine-checkable properties; never judge prose quality."""

    values: dict = {"caseId": case.caseId}
    if plan is not None:
        values["planValid"] = (
            plan.corpusId == case.corpusId
            and plan.questionType is case.category
            and ((plan.disposition is PlanDisposition.ABSTAIN) == (not plan.plannedToolCalls))
        )
        calls = plan.plannedToolCalls
        acceptable_count = sum(call.toolName in case.acceptableTools for call in calls)
        values["acceptableToolSelectionRate"] = acceptable_count / len(calls) if calls else None
        values["unnecessaryToolCallCount"] = len(calls) - acceptable_count

    observed_abstention: bool | None = None
    if analysis is not None:
        observed_abstention = analysis.status is AnswerStatus.ABSTAINED
    elif plan is not None:
        observed_abstention = plan.disposition is PlanDisposition.ABSTAIN
    if observed_abstention is not None:
        values["abstentionCorrect"] = observed_abstention == case.expectedAbstention

    if analysis is not None:
        normalized = "\n".join(statement.text.casefold() for statement in analysis.statements)
        values["unacceptableClaimHits"] = tuple(
            phrase for phrase in case.unacceptableClaims if phrase.casefold() in normalized
        )

    if analysis is not None and references is not None:
        citations = [citation for statement in analysis.statements for citation in statement.citations]
        valid_by_id = {id(citation): _citation_is_valid(citation, references) for citation in citations}
        values["citationIdValidityRate"] = (
            sum(valid_by_id.values()) / len(citations) if citations else 0.0
        )
        supported = sum(
            any(valid_by_id[id(citation)] for citation in statement.citations)
            for statement in analysis.statements
        )
        statement_count = len(analysis.statements)
        coverage = supported / statement_count if statement_count else 0.0
        values["citationCoverageRate"] = coverage
        values["unsupportedStatementRate"] = 1.0 - coverage

        valid_citations = [citation for citation in citations if valid_by_id[id(citation)]]
        if case.expectedCitationRoles:
            values["roleCorrectnessRate"] = (
                sum(citation.role in case.expectedCitationRoles for citation in valid_citations)
                / len(valid_citations)
                if valid_citations else 0.0
            )
        cited_ids = set().union(*(_citation_ids(citation) for citation in valid_citations)) if valid_citations else set()
        values["requiredEvidenceRecall"] = (
            len(cited_ids & set(case.requiredEvidenceIds)) / len(case.requiredEvidenceIds)
            if case.requiredEvidenceIds else None
        )
        values["forbiddenEvidenceHits"] = tuple(
            record_id for record_id in case.forbiddenEvidenceIds if record_id in cited_ids
        )
        values["counterevidenceSatisfied"] = (
            any(citation.role is EvidenceLinkRole.COUNTEREVIDENCE for citation in valid_citations)
            if case.requiresCounterevidence else None
        )

        required_events = {
            event_id for constraint in case.temporalConstraints for event_id in constraint.eventIds
        }
        if required_events:
            values["temporalConstraintCoverage"] = (
                len(required_events & set(references.eventIds)) / len(required_events)
            )

    return EvaluationResult(**values)


class StrategyScore(BaseModel):
    """Per-result deterministic metrics as raw numerator/denominator counts, so
    they aggregate exactly. Human-only dimensions (semantic entailment,
    usefulness) are never scored here -- they surface as ``incomplete`` gates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str
    strategyId: StrategyId
    repeat: int = Field(ge=0)
    corpusId: str
    answerStatus: AnswerStatus

    citationValidNumerator: int = Field(ge=0)
    citationValidDenominator: int = Field(ge=0)
    coverageNumerator: int = Field(ge=0)
    coverageDenominator: int = Field(ge=0)
    requiredRecallNumerator: int = Field(ge=0)
    requiredRecallDenominator: int = Field(ge=0)
    roleRecallNumerator: int = Field(ge=0)
    roleRecallDenominator: int = Field(ge=0)
    temporalNumerator: int = Field(ge=0)
    temporalDenominator: int = Field(ge=0)

    forbiddenHits: tuple[str, ...] = ()
    leakageHits: tuple[str, ...] = ()
    unacceptableClaimHits: tuple[str, ...] = ()

    abstentionExpected: bool = False
    abstained: bool = False
    abstentionCorrect: bool = True


def score_result(
    case: "EvaluationCase",
    result: "StrategyResult",
    *,
    foreign_ids: frozenset[str] = frozenset(),
) -> StrategyScore:
    """Score one strategy result against a case's machine-checkable expectations.

    ``foreign_ids`` are record IDs known to belong to *other* corpora; citing one
    is cross-corpus leakage. Gold rubric fields are never consulted."""

    statements = result.statements
    citations = [citation for statement in statements for citation in statement.citations]
    references = result.references

    if references is not None:
        valid_by_id = {id(c): _citation_is_valid(c, references) for c in citations}
    else:
        valid_by_id = {id(c): False for c in citations}

    valid_citations = [c for c in citations if valid_by_id[id(c)]]
    supported = sum(
        any(valid_by_id[id(c)] for c in statement.citations) for statement in statements
    )
    valid_ids: set[str] = set().union(*(_citation_ids(c) for c in valid_citations)) if valid_citations else set()
    all_cited_ids: set[str] = set().union(*(_citation_ids(c) for c in citations)) if citations else set()

    required = set(case.requiredEvidenceIds)
    required_events = {eid for constraint in case.temporalConstraints for eid in constraint.eventIds}
    retrieved_events = set(references.eventIds) if references is not None else set()

    normalized = "\n".join(statement.text.casefold() for statement in statements)
    abstained = result.answerStatus is AnswerStatus.ABSTAINED

    return StrategyScore(
        caseId=case.caseId,
        strategyId=result.strategyId,
        repeat=result.repeat,
        corpusId=result.corpusId,
        answerStatus=result.answerStatus,
        citationValidNumerator=sum(valid_by_id.values()),
        citationValidDenominator=len(citations),
        coverageNumerator=supported,
        coverageDenominator=len(statements),
        requiredRecallNumerator=len(valid_ids & required),
        requiredRecallDenominator=len(required),
        roleRecallNumerator=sum(c.role in case.expectedCitationRoles for c in valid_citations),
        roleRecallDenominator=len(valid_citations) if case.expectedCitationRoles else 0,
        temporalNumerator=len(required_events & retrieved_events),
        temporalDenominator=len(required_events),
        forbiddenHits=tuple(rid for rid in case.forbiddenEvidenceIds if rid in all_cited_ids),
        leakageHits=tuple(sorted(all_cited_ids & foreign_ids)),
        unacceptableClaimHits=tuple(
            phrase for phrase in case.unacceptableClaims if phrase.casefold() in normalized
        ),
        abstentionExpected=case.expectedAbstention,
        abstained=abstained,
        abstentionCorrect=(abstained == case.expectedAbstention),
    )


class ObservationAvailability(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class ExecutionMeasurements(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    plannerModelCalls: int | None = Field(default=None, ge=0)
    initialToolCalls: int | None = Field(default=None, ge=0)
    followUpRounds: int | None = Field(default=None, ge=0)
    followUpToolCalls: int | None = Field(default=None, ge=0)
    totalToolCalls: int | None = Field(default=None, ge=0)
    maxResultsPerTool: int | None = Field(default=None, ge=0)
    maxCharactersPerToolOutput: int | None = Field(default=None, ge=0)
    aggregateRetrievalCharacters: int | None = Field(default=None, ge=0)
    aggregateResults: int | None = Field(default=None, ge=0)
    analystModelCalls: int | None = Field(default=None, ge=0)
    maxStructuredAttempts: int | None = Field(default=None, ge=0)
    plannerPromptCharacters: int | None = Field(default=None, ge=0)
    analystPromptCharacters: int | None = Field(default=None, ge=0)
    toolSpecCharacters: int | None = Field(default=None, ge=0)
    statementCount: int | None = Field(default=None, ge=0)
    maxCitationsPerStatement: int | None = Field(default=None, ge=0)
    elapsedSeconds: float | None = Field(default=None, ge=0)
    modelContextTokens: int | None = Field(default=None, ge=0)
    plannerCompletionTokens: int | None = Field(default=None, ge=0)
    analystCompletionTokens: int | None = Field(default=None, ge=0)


class BudgetObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    availability: ObservationAvailability
    observed: float | None = None
    limit: float
    withinLimit: bool | None = None


_MEASUREMENT_LIMITS = (
    ("planner_model_calls", "plannerModelCalls", "maxPlannerModelCalls"),
    ("initial_tool_calls", "initialToolCalls", "maxInitialToolCalls"),
    ("follow_up_rounds", "followUpRounds", "maxFollowUpRounds"),
    ("follow_up_tool_calls", "followUpToolCalls", "maxFollowUpToolCalls"),
    ("total_tool_calls", "totalToolCalls", "maxTotalToolCalls"),
    ("results_per_tool", "maxResultsPerTool", "maxResultsPerTool"),
    ("characters_per_tool_output", "maxCharactersPerToolOutput", "maxCharactersPerToolOutput"),
    ("aggregate_retrieval_characters", "aggregateRetrievalCharacters", "maxAggregateRetrievalCharacters"),
    ("aggregate_results", "aggregateResults", "maxAggregateResults"),
    ("analyst_model_calls", "analystModelCalls", "maxAnalystModelCalls"),
    ("structured_attempts", "maxStructuredAttempts", "maxStructuredAttempts"),
    ("planner_prompt_characters", "plannerPromptCharacters", "maxPromptCharacters"),
    ("analyst_prompt_characters", "analystPromptCharacters", "maxPromptCharacters"),
    ("tool_spec_characters", "toolSpecCharacters", "maxToolSpecCharacters"),
    ("statements", "statementCount", "maxStatements"),
    ("citations_per_statement", "maxCitationsPerStatement", "maxCitationsPerStatement"),
    ("deadline_seconds", "elapsedSeconds", "deadlineSeconds"),
    ("context_tokens", "modelContextTokens", "modelContextTokens"),
    ("planner_completion_tokens", "plannerCompletionTokens", "plannerMaxCompletionTokens"),
    ("analyst_completion_tokens", "analystCompletionTokens", "analystMaxCompletionTokens"),
)


def observe_execution_budgets(
    measurements: ExecutionMeasurements,
    policy: AgentExecutionPolicy,
) -> tuple[BudgetObservation, ...]:
    observations = []
    for name, measurement_field, policy_field in _MEASUREMENT_LIMITS:
        observed = getattr(measurements, measurement_field)
        limit = getattr(policy, policy_field)
        observations.append(BudgetObservation(
            name=name,
            availability=(
                ObservationAvailability.AVAILABLE
                if observed is not None
                else ObservationAvailability.UNAVAILABLE
            ),
            observed=observed,
            limit=limit,
            withinLimit=observed <= limit if observed is not None else None,
        ))
    return tuple(observations)
