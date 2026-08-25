"""Deterministic traceability validation for corpus-blind Analyst output.

Passing this validator proves that the draft's structured assertions trace to
the bounded retrieval bundle. It deliberately does not prove historical truth
or semantic entailment of free-form statement text.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from chronicle.contracts.enums import (
    Awareness,
    EvidenceClassification,
    LocationPrecision,
)
from chronicle.corpus.contracts import EvidenceLinkProjection, PassageDateRole

from ..contracts.analysis import (
    AnalysisCitation,
    AnalysisDraft,
    AnalysisStatement,
    AnswerStatus,
    DirectnessAssessment,
    GroundingIssue,
    GroundingIssueCode,
    GroundingValidationReport,
    StatementForm,
    StatementKind,
)
from ..contracts.plan import InvestigationPlan
from ..contracts.retrieval import RetrievalBundle


def validate_grounding(
    draft: AnalysisDraft,
    plan: InvestigationPlan,
    bundle: RetrievalBundle,
) -> GroundingValidationReport:
    """Validate identities and exact structured references in an AnalysisDraft."""

    issues: list[GroundingIssue] = []
    if (draft.runId, draft.planId, draft.corpusId) != (
        plan.runId,
        plan.planId,
        plan.corpusId,
    ) or (bundle.runId, bundle.planId, bundle.corpusId) != (
        plan.runId,
        plan.planId,
        plan.corpusId,
    ):
        _add(issues, GroundingIssueCode.STATUS_MISMATCH, None, "draft, plan, and retrieval identities must match")

    catalog = _Catalog(bundle)
    statement_ids = [statement.statementId for statement in draft.statements]
    if len(statement_ids) != len(set(statement_ids)):
        _add(issues, GroundingIssueCode.STATUS_MISMATCH, None, "statement IDs must be unique")

    if bundle.totalResultCount == 0:
        if draft.statements or draft.status is AnswerStatus.ANSWERED:
            _add(
                issues,
                GroundingIssueCode.STATUS_MISMATCH,
                None,
                "zero retrieval cannot support statements or prove historical absence",
            )
    if bundle.partial and draft.status is AnswerStatus.ANSWERED:
        _add(
            issues,
            GroundingIssueCode.STATUS_MISMATCH,
            None,
            "a partial retrieval bundle cannot support an answered status",
        )
    if catalog.truncated and not _discloses_truncation(draft):
        _add(
            issues,
            GroundingIssueCode.STATUS_MISMATCH,
            None,
            "retrieval truncation must be disclosed in draft or statement limitations",
        )

    _validate_follow_up(draft, bundle, issues)
    for statement in draft.statements:
        _validate_statement(statement, catalog, issues)

    return GroundingValidationReport(valid=not issues, issues=issues)


def _validate_follow_up(
    draft: AnalysisDraft,
    bundle: RetrievalBundle,
    issues: list[GroundingIssue],
) -> None:
    call = draft.suggestedFollowUpToolCall
    if call is None:
        return
    if len(bundle.results) >= 4 or any(item.round == 1 for item in bundle.results):
        _add(
            issues,
            GroundingIssueCode.STATUS_MISMATCH,
            None,
            "the one permitted follow-up round or total tool-call budget is exhausted",
        )
    if call.callId in {item.plannedCallId for item in bundle.results}:
        _add(
            issues,
            GroundingIssueCode.STATUS_MISMATCH,
            None,
            "follow-up call ID must not duplicate an executed call",
        )


def _validate_statement(
    statement: AnalysisStatement,
    catalog: "_Catalog",
    issues: list[GroundingIssue],
) -> None:
    statement_id = statement.statementId
    if not statement.citations:
        _add(issues, GroundingIssueCode.MISSING_CITATION, statement_id, "every statement requires a retrieved citation")
        return

    for record_ref in statement.basisRecordRefs:
        if record_ref not in catalog.all_record_ids:
            _add(
                issues,
                GroundingIssueCode.UNKNOWN_RECORD,
                statement_id,
                f'basis record "{record_ref}" was not retrieved in this bundle',
            )

    cited_call_ids: set[str] = set()
    cited_record_ids: set[str] = set(statement.basisRecordRefs)
    cited_links: list[EvidenceLinkProjection] = []
    for citation in statement.citations:
        call = catalog.calls.get(citation.toolCallId)
        if call is None:
            _add(
                issues,
                GroundingIssueCode.UNKNOWN_TOOL_CALL,
                statement_id,
                f'tool call "{citation.toolCallId}" is not in this retrieval bundle',
            )
            continue
        cited_call_ids.add(citation.toolCallId)
        cited_record_ids.update(_citation_ids(citation))
        link = _validate_citation(citation, call, statement_id, issues)
        if link is not None:
            cited_links.append(link)

    _validate_directness(statement, cited_record_ids, cited_links, catalog, issues)
    _validate_classification(statement, cited_record_ids, catalog, issues)
    _validate_knowledge(statement, cited_record_ids, cited_call_ids, catalog, issues)
    _validate_geography(statement, cited_record_ids, cited_call_ids, catalog, issues)
    _validate_temporal_roles(statement, cited_call_ids, catalog, issues)


def _validate_citation(
    citation: AnalysisCitation,
    call: "_CallCatalog",
    statement_id: str,
    issues: list[GroundingIssue],
) -> EvidenceLinkProjection | None:
    if citation.evidenceLinkId is not None:
        link = call.evidence_links.get(citation.evidenceLinkId)
        if link is None:
            _add(
                issues,
                GroundingIssueCode.UNKNOWN_RECORD,
                statement_id,
                f'evidence link "{citation.evidenceLinkId}" was not returned by the cited tool call',
            )
            return None
        expected = (
            link.passageId,
            link.sourceId,
            link.targetType,
            link.targetId,
            link.role,
        )
        actual = (
            citation.passageId,
            citation.sourceId,
            citation.targetType,
            citation.targetId,
            citation.role.value if citation.role is not None else None,
        )
        if actual != expected:
            _add(
                issues,
                GroundingIssueCode.CITATION_MISMATCH,
                statement_id,
                "evidence-link citation must preserve its exact passage/source/target/role tuple",
            )
        return link

    if citation.role is not None:
        _add(
            issues,
            GroundingIssueCode.CITATION_MISMATCH,
            statement_id,
            "an evidence role requires an exact evidenceLinkId",
        )
    for value in _citation_ids(citation):
        if value not in call.record_ids:
            _add(
                issues,
                GroundingIssueCode.UNKNOWN_RECORD,
                statement_id,
                f'citation record "{value}" was not returned by the cited tool call',
            )
    return None


def _validate_directness(
    statement: AnalysisStatement,
    cited_ids: set[str],
    cited_links: list[EvidenceLinkProjection],
    catalog: "_Catalog",
    issues: list[GroundingIssue],
) -> None:
    if statement.statementForm is StatementForm.EVIDENCE_SYNTHESIS:
        # This is also enforced by the frozen Pydantic contract, retained here
        # so callers of this function have an explicit deterministic gate.
        if statement.directness is not DirectnessAssessment.INFERRED:
            _add(issues, GroundingIssueCode.INVALID_DIRECTNESS, statement.statementId, "multi-record synthesis must remain inferred")
        return

    recorded = {
        catalog.directness_by_record[record_id]
        for record_id in cited_ids
        if record_id in catalog.directness_by_record
    }
    if statement.directness is DirectnessAssessment.DIRECT and "inferred" in recorded:
        _add(
            issues,
            GroundingIssueCode.INVALID_DIRECTNESS,
            statement.statementId,
            "an inferred retrieved record cannot be upgraded to direct",
        )
    if statement.directness is DirectnessAssessment.NOT_RECORDED:
        availability = {
            catalog.directness_availability[record_id]
            for record_id in cited_ids
            if record_id in catalog.directness_availability
        }
        if "not-recorded" not in availability:
            _add(
                issues,
                GroundingIssueCode.INVALID_DIRECTNESS,
                statement.statementId,
                "not_recorded directness requires an explicit retrieved not-recorded marker",
            )
    elif not recorded and not cited_links:
        _add(
            issues,
            GroundingIssueCode.INVALID_DIRECTNESS,
            statement.statementId,
            "directness has no retrieved record or evidence-link basis",
        )


def _validate_classification(
    statement: AnalysisStatement,
    cited_ids: set[str],
    catalog: "_Catalog",
    issues: list[GroundingIssue],
) -> None:
    if statement.evidenceClassification is None:
        return
    retrieved = {
        catalog.classification_by_relationship[record_id]
        for record_id in cited_ids
        if record_id in catalog.classification_by_relationship
    }
    if not retrieved or statement.evidenceClassification.value not in retrieved:
        _add(
            issues,
            GroundingIssueCode.CITATION_MISMATCH,
            statement.statementId,
            "relationship evidence classification must exactly match a cited retrieved relationship",
        )


def _validate_knowledge(
    statement: AnalysisStatement,
    cited_ids: set[str],
    cited_call_ids: set[str],
    catalog: "_Catalog",
    issues: list[GroundingIssue],
) -> None:
    if statement.statementKind is not StatementKind.KNOWLEDGE:
        return
    retrieved = {
        catalog.awareness_by_knowledge_state[record_id]
        for record_id in cited_ids
        if record_id in catalog.awareness_by_knowledge_state
    }
    # A source/passsage's existence cannot substitute for a KnownAtTime record.
    if not retrieved:
        for call_id in cited_call_ids:
            retrieved.update(catalog.calls[call_id].awareness_values)
    if not retrieved:
        _add(
            issues,
            GroundingIssueCode.UNKNOWN_RECORD,
            statement.statementId,
            "knowledge statement requires a retrieved knowledge-state record",
        )
    elif statement.knowledgeAwareness is None or statement.knowledgeAwareness.value not in retrieved:
        _add(
            issues,
            GroundingIssueCode.CITATION_MISMATCH,
            statement.statementId,
            "knowledge awareness must exactly match a cited retrieved knowledge-state record",
        )


def _validate_geography(
    statement: AnalysisStatement,
    cited_ids: set[str],
    cited_call_ids: set[str],
    catalog: "_Catalog",
    issues: list[GroundingIssue],
) -> None:
    if statement.geographicPrecision is None:
        return
    retrieved: set[LocationPrecision] = set()
    for record_id in cited_ids:
        retrieved.update(catalog.precision_by_record.get(record_id, set()))
    if not retrieved:
        for call_id in cited_call_ids:
            retrieved.update(catalog.calls[call_id].precision_values)
    if not retrieved:
        _add(
            issues,
            GroundingIssueCode.UNKNOWN_RECORD,
            statement.statementId,
            "geographic precision requires a retrieved place or map record",
        )
        return
    # The statement may be more conservative than its sources, but never finer
    # than the least precise record on which it is based.
    source_ceiling = min(_PRECISION_RANK[value] for value in retrieved)
    if _PRECISION_RANK[statement.geographicPrecision] > source_ceiling:
        _add(
            issues,
            GroundingIssueCode.CITATION_MISMATCH,
            statement.statementId,
            "geographic precision is finer than the cited retrieved record permits",
        )


def _validate_temporal_roles(
    statement: AnalysisStatement,
    cited_call_ids: set[str],
    catalog: "_Catalog",
    issues: list[GroundingIssue],
) -> None:
    if not statement.temporalRoles:
        return
    retrieved: set[PassageDateRole] = set()
    for call_id in cited_call_ids:
        retrieved.update(catalog.calls[call_id].temporal_roles)
    if not set(statement.temporalRoles).issubset(retrieved):
        _add(
            issues,
            GroundingIssueCode.CITATION_MISMATCH,
            statement.statementId,
            "temporal roles must exactly name roles represented by the cited tool results",
        )


class _CallCatalog:
    def __init__(self, output: Any) -> None:
        data = output.model_dump(mode="json") if output is not None else {}
        nodes = list(_walk(data))
        self.record_ids = _record_ids(nodes)
        self.evidence_links: dict[str, EvidenceLinkProjection] = {}
        self.awareness_values: set[str] = set()
        self.precision_values: set[LocationPrecision] = set()
        self.temporal_roles: set[PassageDateRole] = set()
        for node in nodes:
            link = _evidence_link(node)
            if link is not None:
                self.evidence_links[link.evidenceLinkId] = link
            awareness = node.get("awareness")
            if awareness in {item.value for item in Awareness}:
                self.awareness_values.add(awareness)
            self.precision_values.update(_node_precisions(node))
            self.temporal_roles.update(_node_temporal_roles(node))


class _Catalog:
    def __init__(self, bundle: RetrievalBundle) -> None:
        self.calls = {
            item.plannedCallId: _CallCatalog(item.output) for item in bundle.results
        }
        self.all_record_ids = set().union(
            *(call.record_ids for call in self.calls.values()),
            _index_ids(bundle),
        )
        self.directness_by_record: dict[str, str] = {}
        self.directness_availability: dict[str, str] = {}
        self.classification_by_relationship: dict[str, str] = {}
        self.awareness_by_knowledge_state: dict[str, str] = {}
        self.precision_by_record: dict[str, set[LocationPrecision]] = defaultdict(set)
        self.truncated = bundle.truncated or any(item.truncated for item in bundle.results)
        for item in bundle.results:
            if item.output is None:
                continue
            for node in _walk(item.output.model_dump(mode="json")):
                self.truncated = self.truncated or any(
                    key.lower().endswith("truncated") and value is True
                    for key, value in node.items()
                )
                record_ids = _record_ids([node])
                directness = node.get("directOrInferred")
                if directness in {"direct", "inferred"}:
                    for record_id in record_ids:
                        self.directness_by_record[record_id] = directness
                availability = node.get("directOrInferredAvailability")
                if availability in {"recorded", "not-recorded"}:
                    for record_id in record_ids:
                        self.directness_availability[record_id] = availability
                relationship_id = node.get("relationshipId")
                classification = node.get("evidenceClassification")
                if (
                    isinstance(relationship_id, str)
                    and classification in {item.value for item in EvidenceClassification}
                ):
                    self.classification_by_relationship[relationship_id] = classification
                knowledge_id = node.get("knowledgeStateId")
                awareness = node.get("awareness")
                if (
                    isinstance(knowledge_id, str)
                    and awareness in {item.value for item in Awareness}
                ):
                    self.awareness_by_knowledge_state[knowledge_id] = awareness
                precisions = _node_precisions(node)
                for record_id in record_ids:
                    self.precision_by_record[record_id].update(precisions)


def _index_ids(bundle: RetrievalBundle) -> set[str]:
    index = bundle.referenceIndex
    return set().union(
        index.passageIds,
        index.sourceIds,
        index.documentIds,
        index.claimIds,
        index.relationshipIds,
        index.eventIds,
        index.knowledgeStateIds,
        index.placeIds,
        index.mapSceneIds,
        (link.evidenceLinkId for link in index.evidenceLinks),
        (link.targetId for link in index.evidenceLinks),
    )


def _record_ids(nodes: Iterable[dict[str, Any]]) -> set[str]:
    found: set[str] = set()
    excluded = {"corpusId", "packageId", "toolCallId"}
    for node in nodes:
        for key, value in node.items():
            if key in excluded:
                continue
            if key.endswith("Id") and isinstance(value, str):
                found.add(value)
            elif key.endswith("Ids") and isinstance(value, list):
                found.update(item for item in value if isinstance(item, str))
    return found


def _evidence_link(node: dict[str, Any]) -> EvidenceLinkProjection | None:
    required = {
        "evidenceLinkId",
        "targetType",
        "targetId",
        "role",
        "reviewStatus",
        "visibility",
        "passageId",
        "documentId",
        "sourceId",
    }
    if not required.issubset(node):
        return None
    try:
        return EvidenceLinkProjection.model_validate(node)
    except ValueError:
        return None


def _node_precisions(node: dict[str, Any]) -> set[LocationPrecision]:
    found: set[LocationPrecision] = set()
    for key in ("precision", "georeferencingPrecision"):
        value = node.get(key)
        try:
            if isinstance(value, str):
                found.add(LocationPrecision(value))
        except ValueError:
            pass
    return found


def _node_temporal_roles(node: dict[str, Any]) -> set[PassageDateRole]:
    found: set[PassageDateRole] = set()
    role = node.get("timeRole") or node.get("role")
    try:
        if isinstance(role, str):
            found.add(PassageDateRole(role))
    except ValueError:
        pass
    if node.get("sentTime") is not None:
        found.add(PassageDateRole.SENT_TIME)
    if node.get("receivedTime") is not None:
        found.add(PassageDateRole.RECEIVED_TIME)
    if node.get("sourceDate") is not None or node.get("dateOfSource") is not None:
        found.add(PassageDateRole.SOURCE_DATE)
    if node.get("eventTime") is not None:
        found.add(PassageDateRole.LINKED_EVENT_TIME)
    if node.get("asOfDate") is not None:
        found.add(PassageDateRole.LINKED_ACTOR_AWARENESS_TIME)
    return found


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def _citation_ids(citation: AnalysisCitation) -> set[str]:
    return {
        value
        for value in (
            citation.evidenceLinkId,
            citation.passageId,
            citation.sourceId,
            citation.targetId,
        )
        if value is not None
    }


def _discloses_truncation(draft: AnalysisDraft) -> bool:
    limitations = list(draft.limitations)
    limitations.extend(
        limitation
        for statement in draft.statements
        for limitation in statement.limitations
    )
    return any("truncat" in limitation.casefold() for limitation in limitations)


def _add(
    issues: list[GroundingIssue],
    code: GroundingIssueCode,
    statement_id: str | None,
    message: str,
) -> None:
    issue = GroundingIssue(code=code, statementId=statement_id, message=message)
    if issue not in issues and len(issues) < 50:
        issues.append(issue)


_PRECISION_RANK = {
    LocationPrecision.APPROXIMATE: 0,
    LocationPrecision.REGION: 1,
    LocationPrecision.CITY: 2,
    LocationPrecision.BUILDING: 3,
}


__all__ = ["validate_grounding"]
