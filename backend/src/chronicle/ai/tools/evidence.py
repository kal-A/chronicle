"""Evidence-ledger tools that preserve EvidenceLink scope and provenance."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from ...contracts.shared import HistoricalDate
from ...corpus.contracts import EvidenceLinkProjection, MAX_EXCERPT_LENGTH
from ...corpus.errors import UnknownRecordError
from ...corpus.projections import project_evidence_link
from ...corpus.protocol import InvestigationCorpus
from .contracts import MAX_TOOL_RESULT_LIMIT, ToolExecutionContext
from .registry import ToolDefinition

MAX_TOOL_ID_LENGTH = 200
ToolRecordId = Annotated[str, Field(min_length=1, max_length=MAX_TOOL_ID_LENGTH)]


class EvidenceEntry(BaseModel):
    """One stored EvidenceLink plus the passage/source chain it actually cites."""

    model_config = ConfigDict(extra="forbid")

    evidenceLink: EvidenceLinkProjection
    excerpt: str = Field(max_length=MAX_EXCERPT_LENGTH)
    excerptTruncated: bool
    passageLocator: str
    sentTime: HistoricalDate | None
    receivedTime: HistoricalDate | None
    passageGapNote: str | None
    editionCitation: str
    translationCredit: str | None
    documentVisibility: str
    documentLimitations: str
    sourceTitle: str
    sourceType: str
    sourceDate: HistoricalDate
    sourceLimitations: str


class EvidenceGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    entries: list[EvidenceEntry]
    truncated: bool


def _target_record(corpus: InvestigationCorpus, target_type: str, target_id: str):
    if target_type == "claim":
        return corpus.get_claim(target_id)
    if target_type == "relationship":
        return corpus.get_relationship(target_id)
    if target_type == "knownAtTime":
        return corpus.get_knowledge_state(target_id)
    if target_type == "event":
        return corpus.get_event(target_id)
    raise UnknownRecordError(f'Unknown EvidenceLink target type "{target_type}"')


def _evidence_projection(corpus: InvestigationCorpus, link) -> EvidenceLinkProjection:
    passage = corpus.get_passage(link.passageId)
    document = corpus.get_document(passage.documentId)
    target = _target_record(corpus, link.targetType.value, link.targetId)
    return project_evidence_link(
        link=link,
        passage=passage,
        document=document,
        source=corpus.get_source(document.sourceId),
        target=target,
    )


def _evidence_entry(corpus: InvestigationCorpus, link) -> EvidenceEntry:
    passage = corpus.get_passage(link.passageId)
    document = corpus.get_document(passage.documentId)
    source = corpus.get_source(document.sourceId)
    excerpt_truncated = len(passage.excerpt) > MAX_EXCERPT_LENGTH
    return EvidenceEntry(
        evidenceLink=_evidence_projection(corpus, link),
        excerpt=passage.excerpt[:MAX_EXCERPT_LENGTH],
        excerptTruncated=excerpt_truncated,
        passageLocator=passage.locator,
        sentTime=passage.sentTime,
        receivedTime=passage.receivedTime,
        passageGapNote=passage.gapNote,
        editionCitation=document.editionCitation,
        translationCredit=document.translationCredit,
        documentVisibility=document.visibility.value,
        documentLimitations=document.knownLimitations,
        sourceTitle=source.title,
        sourceType=source.sourceType.value,
        sourceDate=source.dateOfSource,
        sourceLimitations=source.knownLimitations,
    )


def _group(role: str, all_links: list, returned_links: list, corpus: InvestigationCorpus) -> EvidenceGroup:
    matching_all = [link for link in all_links if link.role.value == role]
    matching_returned = [link for link in returned_links if link.role.value == role]
    return EvidenceGroup(
        role=role,
        totalCount=len(matching_all),
        returnedCount=len(matching_returned),
        entries=[_evidence_entry(corpus, link) for link in matching_returned],
        truncated=len(matching_returned) < len(matching_all),
    )


class GetClaimEvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: ToolRecordId
    claimId: ToolRecordId


class GetClaimEvidenceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    claimId: str
    statement: str
    directOrInferred: str
    reviewStatus: str
    visibility: str
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    truncated: bool
    supportingEvidence: EvidenceGroup
    contradictingEvidence: EvidenceGroup
    contextualEvidence: EvidenceGroup
    ledgerConclusion: str | None
    ledgerLimitations: list[str]
    ledgerLimitationsTotalCount: int = Field(ge=0)
    ledgerLimitationsReturnedCount: int = Field(ge=0)
    ledgerLimitationsTruncated: bool


def _get_claim_evidence(
    tool_input: GetClaimEvidenceInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> GetClaimEvidenceOutput:
    claim = corpus.get_claim(tool_input.claimId)
    links = corpus.get_evidence_links_for(claim.id)
    returned_links = links[: context.maximumResults]
    ledger = next(
        (item for item in corpus.get_investigation().claimLedgers if item.claimId == claim.id),
        None,
    )
    limitations = list(ledger.limitations) if ledger else []
    returned_limitations = limitations[: context.maximumResults]
    return GetClaimEvidenceOutput(
        corpusId=tool_input.corpusId,
        claimId=claim.id,
        statement=claim.statement,
        directOrInferred=claim.directOrInferred.value,
        reviewStatus=claim.reviewStatus.value,
        visibility=claim.visibility.value,
        totalCount=len(links),
        returnedCount=len(returned_links),
        truncated=len(returned_links) < len(links),
        supportingEvidence=_group("supporting", links, returned_links, corpus),
        contradictingEvidence=_group("counterevidence", links, returned_links, corpus),
        contextualEvidence=_group("context", links, returned_links, corpus),
        ledgerConclusion=ledger.conclusion.value if ledger else None,
        ledgerLimitations=returned_limitations,
        ledgerLimitationsTotalCount=len(limitations),
        ledgerLimitationsReturnedCount=len(returned_limitations),
        ledgerLimitationsTruncated=len(returned_limitations) < len(limitations),
    )


GET_CLAIM_EVIDENCE_TOOL = ToolDefinition(
    name="get_claim_evidence",
    version="e2-get-claim-evidence-v2",
    description=(
        "Return stored EvidenceLinks for one claim, separated by their exact roles, "
        "with target review/visibility and passage-to-source provenance."
    ),
    input_model=GetClaimEvidenceInput,
    output_model=GetClaimEvidenceOutput,
    required_capabilities=frozenset({"claims"}),
    max_result_limit=MAX_TOOL_RESULT_LIMIT,
    execute=_get_claim_evidence,
    use_when="Use to inspect exactly what supports, contradicts, or contextualizes a known claim ID.",
    avoid_when="Avoid for source discovery, unsupported prose synthesis, or a record that is not a claim.",
    output_summary="Bounded role-separated EvidenceLinks with lossless target scope and citation provenance.",
)


class FindCounterevidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: ToolRecordId
    recordId: ToolRecordId


class FindCounterevidenceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    recordId: str
    recordType: str
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    truncated: bool
    contradictingEvidence: EvidenceGroup
    contextualEvidence: EvidenceGroup


def _find_counterevidence(
    tool_input: FindCounterevidenceInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> FindCounterevidenceOutput:
    try:
        corpus.get_claim(tool_input.recordId)
        record_type = "claim"
    except UnknownRecordError:
        corpus.get_relationship(tool_input.recordId)
        record_type = "relationship"

    relevant_links = [
        link
        for link in corpus.get_evidence_links_for(tool_input.recordId)
        if link.role.value in {"counterevidence", "context"}
    ]
    returned_links = relevant_links[: context.maximumResults]
    return FindCounterevidenceOutput(
        corpusId=tool_input.corpusId,
        recordId=tool_input.recordId,
        recordType=record_type,
        totalCount=len(relevant_links),
        returnedCount=len(returned_links),
        truncated=len(returned_links) < len(relevant_links),
        contradictingEvidence=_group("counterevidence", relevant_links, returned_links, corpus),
        contextualEvidence=_group("context", relevant_links, returned_links, corpus),
    )


FIND_COUNTEREVIDENCE_TOOL = ToolDefinition(
    name="find_counterevidence",
    version="e2-find-counterevidence-v2",
    description=(
        "Return only stored counterevidence and context links for one claim or relationship, "
        "preserving their distinct roles and full citation scope."
    ),
    input_model=FindCounterevidenceInput,
    output_model=FindCounterevidenceOutput,
    required_capabilities=frozenset(),
    max_result_limit=MAX_TOOL_RESULT_LIMIT,
    execute=_find_counterevidence,
    use_when="Use to test a known claim or relationship against recorded counterevidence and context.",
    avoid_when=(
        "Avoid when seeking supporting evidence or when absence of a link would be treated as proof of agreement."
    ),
    output_summary="Bounded counterevidence/context groups with totals and passage/source provenance.",
)
