"""Deterministic E4 gates for Critic decisions, answers, citations, and actions."""

from __future__ import annotations

from ...contracts.generated_investigation import GeneratedInvestigation
from ..contracts.analysis import AnalysisDraft, AnalysisStatement, GroundingValidationReport
from ..contracts.answer import (
    ActionReferenceIndex,
    ActivateLensAction,
    AgentAnswer,
    AnswerValidationIssue,
    AnswerValidationIssueCode,
    AnswerValidationReport,
    CompareActorsAction,
    FocusEventAction,
    FocusLocationAction,
    HighlightEventsAction,
    HighlightRelationshipAction,
    OpenEvidenceAction,
    OpenSourceAction,
    SetTimeAction,
    SetTimeRangeAction,
    ShowSystemPathAction,
)
from ..contracts.critique import (
    CriticDecision,
    CriticValidationIssue,
    CriticValidationIssueCode,
    CriticValidationReport,
    CriticVerdict,
)
from ..contracts.plan import InvestigationPlan


def validate_critic_decision(
    decision: CriticDecision,
    analysis: AnalysisDraft,
    grounding: GroundingValidationReport,
    plan: InvestigationPlan | None = None,
) -> CriticValidationReport:
    issues: list[CriticValidationIssue] = []
    if (
        decision.runId != analysis.runId
        or decision.planId != analysis.planId
        or decision.corpusId != analysis.corpusId
        or (
            plan is not None
            and (
                decision.runId != plan.runId
                or decision.planId != plan.planId
                or decision.corpusId != plan.corpusId
            )
        )
    ):
        issues.append(
            CriticValidationIssue(
                code=CriticValidationIssueCode.IDENTITY_MISMATCH,
                message="critic, analysis, and plan identities must match",
            )
        )
    if not grounding.valid and decision.verdict not in {
        CriticVerdict.RETRIEVE_MORE,
        CriticVerdict.ABSTAIN,
    }:
        issues.append(
            CriticValidationIssue(
                code=CriticValidationIssueCode.UNGROUNDED_ANALYSIS,
                message="an ungrounded analysis cannot be approved or exposed",
            )
        )

    known_ids = {statement.statementId for statement in analysis.statements}
    disposed_ids = (
        list(decision.acceptedStatementIds)
        + [item.statementId for item in decision.downgradedStatements]
        + [item.statementId for item in decision.rejectedStatements]
    )
    for statement_id in disposed_ids:
        if statement_id not in known_ids:
            issues.append(
                CriticValidationIssue(
                    code=CriticValidationIssueCode.UNKNOWN_STATEMENT,
                    statementId=statement_id,
                    message=f'critic referenced unknown statement "{statement_id}"',
                )
            )
    if decision.verdict not in {CriticVerdict.RETRIEVE_MORE, CriticVerdict.ABSTAIN}:
        missing = sorted(known_ids - set(disposed_ids))
        if missing:
            issues.append(
                CriticValidationIssue(
                    code=CriticValidationIssueCode.INCOMPLETE_REVIEW,
                    message=f"critic did not disposition statements: {', '.join(missing)}",
                )
            )

    if decision.verdict is CriticVerdict.RETRIEVE_MORE:
        call = decision.additionalToolCalls[0]
        existing_call_ids = {item.callId for item in plan.plannedToolCalls} if plan else set()
        if call.callId in existing_call_ids or "corpusId" in call.arguments:
            issues.append(
                CriticValidationIssue(
                    code=CriticValidationIssueCode.INVALID_TOOL_CALL,
                    message="critic follow-up call must be new and corpusId must remain runner-owned",
                )
            )
    return CriticValidationReport(valid=not issues, issues=issues)


def build_action_reference_index(
    investigation: GeneratedInvestigation,
) -> ActionReferenceIndex:
    locations = sorted(
        entity.id for entity in investigation.entities if entity.entityType == "place"
    )
    actors = sorted(
        entity.id for entity in investigation.entities if entity.entityType != "place"
    )
    lenses: list[str] = []
    paths: list[str] = []
    if investigation.experiencePlan is not None:
        lenses = sorted(item.id for item in investigation.experiencePlan.lenses)
        paths = sorted(item.id for item in investigation.experiencePlan.systemPaths)
    evidence_ids = sorted(
        {
            *(item.id for item in investigation.claims),
            *(item.id for item in investigation.relationships),
            *(item.id for item in investigation.events),
            *(item.id for item in investigation.knowledgeStates),
            *(item.id for item in investigation.evidenceLinks),
            *(item.id for item in investigation.passages),
            *(item.id for item in investigation.documents),
        }
    )
    return ActionReferenceIndex(
        locationIds=tuple(locations),
        eventIds=tuple(sorted(item.id for item in investigation.events)),
        lensIds=tuple(lenses),
        relationshipIds=tuple(sorted(item.id for item in investigation.relationships)),
        pathIds=tuple(paths),
        actorIds=tuple(actors),
        evidenceRecordIds=tuple(evidence_ids),
        sourceIds=tuple(sorted(item.id for item in investigation.sources)),
        earliestKey=investigation.scope.dateRange.lower_key,
        latestKey=investigation.scope.dateRange.upper_key,
    )


def approved_statements(
    analysis: AnalysisDraft,
    decision: CriticDecision,
) -> dict[str, tuple[str, AnalysisStatement]]:
    """Return exact exposable text plus its original, grounded statement."""

    source = {statement.statementId: statement for statement in analysis.statements}
    approved: dict[str, tuple[str, AnalysisStatement]] = {}
    for statement_id in decision.acceptedStatementIds:
        if statement_id in source:
            approved[statement_id] = (source[statement_id].text, source[statement_id])
    for downgrade in decision.downgradedStatements:
        if downgrade.statementId in source:
            approved[downgrade.statementId] = (
                downgrade.revisedText,
                source[downgrade.statementId],
            )
    return approved


def validate_agent_answer(
    answer: AgentAnswer,
    analysis: AnalysisDraft,
    decision: CriticDecision,
    action_index: ActionReferenceIndex,
) -> AnswerValidationReport:
    issues: list[AnswerValidationIssue] = []
    if (
        answer.runId != analysis.runId
        or answer.planId != analysis.planId
        or answer.corpusId != analysis.corpusId
        or answer.runId != decision.runId
        or answer.planId != decision.planId
        or answer.corpusId != decision.corpusId
    ):
        issues.append(
            AnswerValidationIssue(
                code=AnswerValidationIssueCode.IDENTITY_MISMATCH,
                message="answer, critic, and analysis identities must match",
            )
        )

    approved = approved_statements(analysis, decision)
    if decision.verdict in {CriticVerdict.REJECT, CriticVerdict.ABSTAIN}:
        if answer.status.value != "abstained":
            issues.append(
                AnswerValidationIssue(
                    code=AnswerValidationIssueCode.UNAPPROVED_ANSWER_TEXT,
                    message="a rejected or abstained critique can only produce an abstained answer",
                )
            )
    elif answer.status.value == "abstained":
        issues.append(
            AnswerValidationIssue(
                code=AnswerValidationIssueCode.UNAPPROVED_ANSWER_TEXT,
                message="an approved critique cannot be silently converted to abstention",
            )
        )
    points = answer.keyPoints + answer.disagreements
    for point in points:
        expected = approved.get(point.statementId)
        if expected is None:
            issues.append(
                AnswerValidationIssue(
                    code=AnswerValidationIssueCode.UNKNOWN_STATEMENT,
                    message=f'answer referenced unapproved statement "{point.statementId}"',
                )
            )
        elif point.text != expected[0]:
            issues.append(
                AnswerValidationIssue(
                    code=AnswerValidationIssueCode.UNAPPROVED_ANSWER_TEXT,
                    message=f'answer changed approved text for "{point.statementId}"',
                )
            )
    if answer.status.value != "abstained":
        expected_direct = " ".join(point.text for point in answer.keyPoints)
        if answer.directAnswer != expected_direct:
            issues.append(
                AnswerValidationIssue(
                    code=AnswerValidationIssueCode.UNAPPROVED_ANSWER_TEXT,
                    message="directAnswer must be composed only from exact approved key-point text",
                )
            )

    point_ids = {point.statementId for point in points}
    cited_statement_ids: set[str] = set()
    for item in answer.citations:
        expected = approved.get(item.statementId)
        if expected is None or item.statementId not in point_ids:
            issues.append(
                AnswerValidationIssue(
                    code=AnswerValidationIssueCode.INVALID_CITATION,
                    message=f'citation is not attached to an exposed approved statement "{item.statementId}"',
                )
            )
            continue
        original_citations = {
            citation.model_dump_json() for citation in expected[1].citations
        }
        if item.citation.model_dump_json() not in original_citations:
            issues.append(
                AnswerValidationIssue(
                    code=AnswerValidationIssueCode.INVALID_CITATION,
                    message=f'citation for "{item.statementId}" was not present on the grounded statement',
                )
            )
        else:
            cited_statement_ids.add(item.statementId)
    for statement_id in point_ids - cited_statement_ids:
        issues.append(
            AnswerValidationIssue(
                code=AnswerValidationIssueCode.INVALID_CITATION,
                message=f'exposed statement "{statement_id}" has no preserved citation',
            )
        )

    allowed_limitations = set(analysis.limitations) | set(decision.limitationsToSurface)
    for statement in analysis.statements:
        allowed_limitations.update(statement.limitations)
    for downgrade in decision.downgradedStatements:
        allowed_limitations.update(downgrade.limitations)
    unknown_limitations = [item for item in answer.limitations if item not in allowed_limitations]
    if unknown_limitations:
        issues.append(
            AnswerValidationIssue(
                code=AnswerValidationIssueCode.INVALID_LIMITATION,
                message="answer introduced a limitation absent from Analyst or Critic material",
            )
        )

    for action in answer.actions:
        message = _action_error(action, action_index)
        if message:
            code = (
                AnswerValidationIssueCode.UNSUPPORTED_TIME
                if isinstance(action, (SetTimeAction, SetTimeRangeAction))
                else AnswerValidationIssueCode.UNKNOWN_ACTION_REFERENCE
            )
            issues.append(AnswerValidationIssue(code=code, message=message))
    return AnswerValidationReport(valid=not issues, issues=issues)


def _action_error(action, index: ActionReferenceIndex) -> str | None:
    checks: list[tuple[list[str], tuple[str, ...], str]] = []
    if isinstance(action, FocusLocationAction):
        checks.append(([action.locationId], index.locationIds, "location"))
    elif isinstance(action, FocusEventAction):
        checks.append(([action.eventId], index.eventIds, "event"))
    elif isinstance(action, ActivateLensAction):
        checks.append(([action.lensId], index.lensIds, "lens"))
    elif isinstance(action, HighlightEventsAction):
        checks.append((action.eventIds, index.eventIds, "event"))
    elif isinstance(action, HighlightRelationshipAction):
        checks.append(([action.relationshipId], index.relationshipIds, "relationship"))
    elif isinstance(action, ShowSystemPathAction):
        checks.append(([action.pathId], index.pathIds, "system path"))
    elif isinstance(action, CompareActorsAction):
        checks.append((action.actorIds, index.actorIds, "actor"))
    elif isinstance(action, OpenEvidenceAction):
        checks.append(([action.recordId], index.evidenceRecordIds, "evidence record"))
    elif isinstance(action, OpenSourceAction):
        checks.append(([action.sourceId], index.sourceIds, "source"))
    elif isinstance(action, (SetTimeAction, SetTimeRangeAction)):
        value = action.date if isinstance(action, SetTimeAction) else action.range
        if value.lower_key < index.earliestKey or value.upper_key > index.latestKey:
            return "time action falls outside the current investigation scope"
    for values, known, kind in checks:
        unknown = sorted(set(values) - set(known))
        if unknown:
            return f"unknown {kind} reference(s): {', '.join(unknown)}"
    return None


__all__ = [
    "approved_statements",
    "build_action_reference_index",
    "validate_agent_answer",
    "validate_critic_decision",
]
