"""Deterministic source metadata and role-aware source comparison tools."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...contracts.shared import HistoricalDate
from ...corpus.contracts import EvidenceLinkProjection
from ...corpus.protocol import InvestigationCorpus
from .contracts import MAX_TOOL_RESULT_LIMIT, ToolExecutionContext
from .evidence import ToolRecordId, _evidence_projection
from .registry import ToolDefinition


def _primary_secondary(source_type: str) -> str:
    if source_type.startswith("primary"):
        return "primary"
    if source_type.startswith("secondary"):
        return "secondary"
    return "tertiary"


def _document_ids_for_source(investigation, source_id: str) -> list[str]:
    return [document.id for document in investigation.documents if document.sourceId == source_id]


def _passage_ids_for_source(investigation, source_id: str) -> list[str]:
    document_ids = set(_document_ids_for_source(investigation, source_id))
    return [passage.id for passage in investigation.passages if passage.documentId in document_ids]


@dataclass
class _ResultBudget:
    remaining: int

    def take(self, values: list):
        returned = values[: self.remaining]
        self.remaining -= len(returned)
        return returned


class GetSourceMetadataInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: ToolRecordId
    sourceId: ToolRecordId


class GetSourceMetadataOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    sourceId: str
    title: str
    creator: str
    date: HistoricalDate
    sourceType: str
    primarySecondaryStatus: str
    rightsStatus: str
    curationStatus: str
    knownLimitations: str
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    truncated: bool
    relatedDocumentIds: list[str]
    relatedDocumentTotalCount: int = Field(ge=0)
    relatedDocumentReturnedCount: int = Field(ge=0)
    relatedDocumentTruncated: bool
    relatedPassageIds: list[str]
    relatedPassageTotalCount: int = Field(ge=0)
    relatedPassageReturnedCount: int = Field(ge=0)
    relatedPassageTruncated: bool
    canonicalSourceReference: str


def _get_source_metadata(
    tool_input: GetSourceMetadataInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> GetSourceMetadataOutput:
    source = corpus.get_source(tool_input.sourceId)
    investigation = corpus.get_investigation()
    all_document_ids = _document_ids_for_source(investigation, source.id)
    all_passage_ids = _passage_ids_for_source(investigation, source.id)
    related_id_budget = _ResultBudget(context.maximumResults)
    document_ids = related_id_budget.take(all_document_ids)
    passage_ids = related_id_budget.take(all_passage_ids)
    total_count = len(all_document_ids) + len(all_passage_ids)
    returned_count = len(document_ids) + len(passage_ids)
    return GetSourceMetadataOutput(
        corpusId=tool_input.corpusId,
        sourceId=source.id,
        title=source.title,
        creator=source.authorOrOrigin,
        date=source.dateOfSource,
        sourceType=source.sourceType.value,
        primarySecondaryStatus=_primary_secondary(source.sourceType.value),
        rightsStatus=source.rightsStatus.value,
        curationStatus=source.curationStatus.value,
        knownLimitations=source.knownLimitations,
        totalCount=total_count,
        returnedCount=returned_count,
        truncated=returned_count < total_count,
        relatedDocumentIds=document_ids,
        relatedDocumentTotalCount=len(all_document_ids),
        relatedDocumentReturnedCount=len(document_ids),
        relatedDocumentTruncated=len(document_ids) < len(all_document_ids),
        relatedPassageIds=passage_ids,
        relatedPassageTotalCount=len(all_passage_ids),
        relatedPassageReturnedCount=len(passage_ids),
        relatedPassageTruncated=len(passage_ids) < len(all_passage_ids),
        canonicalSourceReference=source.linkOrLocation,
    )


GET_SOURCE_METADATA_TOOL = ToolDefinition(
    name="get_source_metadata",
    version="e2-get-source-metadata-v2",
    description=(
        "Return recorded provenance, rights, curation state, limitations, and bounded related IDs "
        "for one source; it does not judge reliability."
    ),
    input_model=GetSourceMetadataInput,
    output_model=GetSourceMetadataOutput,
    required_capabilities=frozenset(),
    max_result_limit=MAX_TOOL_RESULT_LIMIT,
    execute=_get_source_metadata,
    use_when="Use when a known source ID needs provenance, rights, limitations, or related record IDs.",
    avoid_when="Avoid for evaluating truth, reliability, or evidence support; those are not source metadata.",
    output_summary="Source metadata plus separately bounded document and passage IDs with truthful totals.",
)


class CompareSourcesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: ToolRecordId
    sourceIds: list[ToolRecordId] = Field(min_length=2, max_length=MAX_TOOL_RESULT_LIMIT)

    @field_validator("sourceIds")
    @classmethod
    def _source_ids_must_be_unique(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError("sourceIds must not contain duplicates")
        return value


class EvidenceRoleCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    targetTotalCount: int = Field(ge=0)
    targetReturnedCount: int = Field(ge=0)
    targetIds: list[str]
    targetIdsTruncated: bool
    evidenceLinkTotalCount: int = Field(ge=0)
    evidenceLinkReturnedCount: int = Field(ge=0)
    evidenceLinks: list[EvidenceLinkProjection]
    evidenceLinksTruncated: bool


class EvidenceRoleBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supporting: EvidenceRoleCoverage
    counterevidence: EvidenceRoleCoverage
    context: EvidenceRoleCoverage


class SourceComparisonEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sourceId: str
    title: str
    sourceType: str
    primarySecondaryStatus: str
    dateOfSource: HistoricalDate
    rightsStatus: str
    curationStatus: str
    knownLimitations: str
    passageCount: int
    claimsSupportedCount: int
    relationshipsSupportedCount: int
    claimEvidenceByRole: EvidenceRoleBreakdown
    relationshipEvidenceByRole: EvidenceRoleBreakdown


class CompareSourcesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpusId: str
    totalCount: int = Field(ge=0)
    returnedCount: int = Field(ge=0)
    entries: list[SourceComparisonEntry]
    truncated: bool
    sameSourceType: bool
    samePrimarySecondaryStatus: bool


def _coverage(
    corpus: InvestigationCorpus,
    links: list,
    role: str,
    target_budget: _ResultBudget,
    evidence_budget: _ResultBudget,
) -> EvidenceRoleCoverage:
    role_links = [link for link in links if link.role.value == role]
    target_ids = list(dict.fromkeys(link.targetId for link in role_links))
    returned_targets = target_budget.take(target_ids)
    returned_links = evidence_budget.take(role_links)
    return EvidenceRoleCoverage(
        role=role,
        targetTotalCount=len(target_ids),
        targetReturnedCount=len(returned_targets),
        targetIds=returned_targets,
        targetIdsTruncated=len(returned_targets) < len(target_ids),
        evidenceLinkTotalCount=len(role_links),
        evidenceLinkReturnedCount=len(returned_links),
        evidenceLinks=[_evidence_projection(corpus, link) for link in returned_links],
        evidenceLinksTruncated=len(returned_links) < len(role_links),
    )


def _breakdown(
    corpus: InvestigationCorpus,
    links: list,
    target_budget: _ResultBudget,
    evidence_budget: _ResultBudget,
) -> EvidenceRoleBreakdown:
    return EvidenceRoleBreakdown(
        supporting=_coverage(corpus, links, "supporting", target_budget, evidence_budget),
        counterevidence=_coverage(corpus, links, "counterevidence", target_budget, evidence_budget),
        context=_coverage(corpus, links, "context", target_budget, evidence_budget),
    )


def _comparison_entry(
    corpus: InvestigationCorpus,
    investigation,
    source,
    target_budget: _ResultBudget,
    evidence_budget: _ResultBudget,
) -> SourceComparisonEntry:
    passage_ids = set(_passage_ids_for_source(investigation, source.id))
    source_links = [link for link in investigation.evidenceLinks if link.passageId in passage_ids]
    claim_links = [link for link in source_links if link.targetType.value == "claim"]
    relationship_links = [link for link in source_links if link.targetType.value == "relationship"]
    claim_breakdown = _breakdown(corpus, claim_links, target_budget, evidence_budget)
    relationship_breakdown = _breakdown(corpus, relationship_links, target_budget, evidence_budget)
    return SourceComparisonEntry(
        sourceId=source.id,
        title=source.title,
        sourceType=source.sourceType.value,
        primarySecondaryStatus=_primary_secondary(source.sourceType.value),
        dateOfSource=source.dateOfSource,
        rightsStatus=source.rightsStatus.value,
        curationStatus=source.curationStatus.value,
        knownLimitations=source.knownLimitations,
        passageCount=len(passage_ids),
        claimsSupportedCount=claim_breakdown.supporting.targetTotalCount,
        relationshipsSupportedCount=relationship_breakdown.supporting.targetTotalCount,
        claimEvidenceByRole=claim_breakdown,
        relationshipEvidenceByRole=relationship_breakdown,
    )


def _compare_sources(
    tool_input: CompareSourcesInput,
    context: ToolExecutionContext,
    corpus: InvestigationCorpus,
) -> CompareSourcesOutput:
    all_sources = [corpus.get_source(source_id) for source_id in tool_input.sourceIds]
    returned_sources = all_sources[: context.maximumResults]
    investigation = corpus.get_investigation()
    target_budget = _ResultBudget(context.maximumResults)
    evidence_budget = _ResultBudget(context.maximumResults)
    entries = [
        _comparison_entry(corpus, investigation, source, target_budget, evidence_budget)
        for source in returned_sources
    ]
    source_types = {source.sourceType.value for source in all_sources}
    primary_secondary = {_primary_secondary(source.sourceType.value) for source in all_sources}
    return CompareSourcesOutput(
        corpusId=tool_input.corpusId,
        totalCount=len(all_sources),
        returnedCount=len(entries),
        entries=entries,
        truncated=len(entries) < len(all_sources),
        sameSourceType=len(source_types) == 1,
        samePrimarySecondaryStatus=len(primary_secondary) == 1,
    )


COMPARE_SOURCES_TOOL = ToolDefinition(
    name="compare_sources",
    version="e2-compare-sources-v2",
    description=(
        "Compare recorded source metadata and role-specific claim/relationship coverage. "
        "Only links whose role is supporting count as support."
    ),
    input_model=CompareSourcesInput,
    output_model=CompareSourcesOutput,
    required_capabilities=frozenset({"source_comparison"}),
    max_result_limit=MAX_TOOL_RESULT_LIMIT,
    execute=_compare_sources,
    use_when="Use to compare known sources by metadata and explicitly recorded evidence-link roles.",
    avoid_when="Avoid for ranking source reliability or treating counterevidence/context as support.",
    output_summary="Bounded source entries with supporting, counterevidence, and context coverage kept separate.",
)
