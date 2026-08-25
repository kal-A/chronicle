"""Model-free Phase E3 benchmark cases and fixture-reference validation.

This module deliberately contains no production prompt imports and no target
answers.  A benchmark case describes observable retrieval/grounding behavior;
it does not provide prose that a model could copy.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...contracts.enums import EvidenceLinkRole
from ...corpus.manifest import CorpusRegistry
from ..contracts.plan import QuestionType


class TemporalConstraintKind(str, Enum):
    EVENT_ORDER = "event_order"
    DATE_BOUND = "date_bound"


class TemporalConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: TemporalConstraintKind
    eventIds: tuple[str, ...] = Field(default=(), max_length=8)
    earliest: date | None = None
    latest: date | None = None

    @model_validator(mode="after")
    def _require_a_bound(self) -> "TemporalConstraint":
        if not self.eventIds and self.earliest is None and self.latest is None:
            raise ValueError("a temporal constraint requires event IDs or a date bound")
        if self.earliest and self.latest and self.earliest > self.latest:
            raise ValueError("earliest cannot be after latest")
        return self


class BenchmarkCase(BaseModel):
    """One answer-free, deterministic evaluation case."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str = Field(pattern=r"^(bc|coe)-\d{2}$")
    corpusId: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=1_000)
    category: QuestionType
    acceptableTools: tuple[str, ...] = Field(min_length=1, max_length=10)
    requiredEvidenceIds: tuple[str, ...] = Field(default=(), max_length=12)
    forbiddenEvidenceIds: tuple[str, ...] = Field(default=(), max_length=12)
    expectedCitationRoles: tuple[EvidenceLinkRole, ...] = Field(default=(), max_length=3)
    requiresCounterevidence: bool = False
    temporalConstraints: tuple[TemporalConstraint, ...] = Field(default=(), max_length=3)
    expectedAbstention: bool = False
    unacceptableClaims: tuple[str, ...] = Field(default=(), max_length=8)

    @model_validator(mode="after")
    def _validate_case(self) -> "BenchmarkCase":
        if set(self.requiredEvidenceIds) & set(self.forbiddenEvidenceIds):
            raise ValueError("required and forbidden evidence IDs must be disjoint")
        if self.requiresCounterevidence and EvidenceLinkRole.COUNTEREVIDENCE not in self.expectedCitationRoles:
            raise ValueError("counterevidence cases must expect the counterevidence citation role")
        return self


class BenchmarkReferenceIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    caseId: str
    recordId: str
    detail: str


class BenchmarkReferenceValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    valid: bool
    validatedCaseCount: int = Field(ge=0)
    validatedReferenceCount: int = Field(ge=0)
    issues: tuple[BenchmarkReferenceIssue, ...] = ()


class BenchmarkValidationError(ValueError):
    def __init__(self, issues: tuple[BenchmarkReferenceIssue, ...]) -> None:
        self.issues = issues
        rendered = "; ".join(f"{issue.caseId}: {issue.recordId} ({issue.detail})" for issue in issues)
        super().__init__(f"benchmark fixture reference validation failed: {rendered}")


BC = "blank-cheque-golden"
COE = "concert-of-europe-1814-1822"

SUPPORT = (EvidenceLinkRole.SUPPORTING,)
SUPPORT_AND_CONTEXT = (EvidenceLinkRole.SUPPORTING, EvidenceLinkRole.CONTEXT)
SUPPORT_AND_COUNTER = (EvidenceLinkRole.SUPPORTING, EvidenceLinkRole.COUNTEREVIDENCE)


def _case(
    case_id: str,
    corpus_id: str,
    question: str,
    category: QuestionType,
    tools: tuple[str, ...],
    required: tuple[str, ...] = (),
    forbidden: tuple[str, ...] = (),
    roles: tuple[EvidenceLinkRole, ...] = SUPPORT,
    *,
    counter: bool = False,
    temporal: tuple[TemporalConstraint, ...] = (),
    abstain: bool = False,
    unacceptable: tuple[str, ...] = (),
) -> BenchmarkCase:
    return BenchmarkCase(
        caseId=case_id,
        corpusId=corpus_id,
        question=question,
        category=category,
        acceptableTools=tools,
        requiredEvidenceIds=required,
        forbiddenEvidenceIds=forbidden,
        expectedCitationRoles=roles,
        requiresCounterevidence=counter,
        temporalConstraints=temporal,
        expectedAbstention=abstain,
        unacceptableClaims=unacceptable,
    )


_CASES: tuple[BenchmarkCase, ...] = (
    _case(
        "coe-01", COE,
        "What principle of intervention did the Troppau Protocol state?",
        QuestionType.DIRECT_EVIDENCE,
        ("get_claim_evidence", "search_passages"),
        ("evidence-claim-troppau-doctrine-1", "passage-troppau-protocol-1"),
        ("passage-vienna-final-act-1",),
    ),
    _case(
        "coe-02", COE,
        "Does this corpus independently verify that every Troppau signatory applied the principle consistently?",
        QuestionType.MISSING_EVIDENCE,
        ("search_passages", "compare_sources"),
        (),
        ("evidence-claim-vienna-settlement-1",),
        abstain=True,
        unacceptable=("every signatory applied the principle consistently",),
    ),
    _case(
        "coe-03", COE,
        "How did Castlereagh's 1820 state paper differ from the Troppau Protocol?",
        QuestionType.SOURCE_COMPARISON,
        ("compare_sources", "get_source_metadata", "search_passages"),
        ("source-castlereagh-state-paper", "source-troppau-protocol"),
        ("source-vienna-final-act",),
    ),
    _case(
        "coe-04", COE,
        "What classified relationship connects the Troppau doctrine to intervention in Naples?",
        QuestionType.RELATIONSHIP_TRACE,
        ("get_relationship_evidence", "trace_relationships"),
        ("rel-troppau-supports-naples", "evidence-rel-troppau-naples-1"),
        ("rel-verona-extends-troppau",),
    ),
    _case(
        "coe-05", COE,
        "In what order did Troppau, Laibach, and the Naples intervention occur?",
        QuestionType.TIMELINE_ORDERING,
        ("get_timeline_context",),
        ("event-troppau-protocol", "event-laibach-authorization", "event-naples-intervention"),
        ("event-congress-of-verona",),
        temporal=(TemporalConstraint(
            kind=TemporalConstraintKind.EVENT_ORDER,
            eventIds=("event-troppau-protocol", "event-laibach-authorization", "event-naples-intervention"),
        ),),
    ),
    _case(
        "coe-06", COE,
        "What date is attached to Castlereagh's state paper in the corpus?",
        QuestionType.DIRECT_EVIDENCE,
        ("get_source_metadata", "search_passages"),
        ("source-castlereagh-state-paper",),
        ("source-troppau-protocol",),
        temporal=(TemporalConstraint(
            kind=TemporalConstraintKind.DATE_BOUND,
            earliest=date(1820, 5, 5), latest=date(1820, 5, 5),
        ),),
    ),
    _case(
        "coe-07", COE,
        "What evidence supports and limits treating Verona as an extension of the Troppau principle?",
        QuestionType.COUNTEREVIDENCE,
        ("get_relationship_evidence", "find_counterevidence", "search_passages"),
        ("rel-verona-extends-troppau", "evidence-rel-verona-troppau-1"),
        ("evidence-claim-vienna-settlement-1",),
        SUPPORT_AND_COUNTER,
        counter=True,
    ),
    _case(
        "coe-08", COE,
        "Why did Britain endorse the general intervention principle at Troppau?",
        QuestionType.INVALID_PREMISE,
        ("get_claim_evidence", "search_passages", "find_counterevidence"),
        ("claim-castlereagh-dissent", "passage-castlereagh-state-paper-1"),
        ("evidence-claim-troppau-doctrine-1",),
        SUPPORT_AND_COUNTER,
        abstain=True,
        unacceptable=("Britain endorsed the general intervention principle",),
    ),
    _case(
        "coe-09", COE,
        "What happened during the 1823 French invasion of Spain?",
        QuestionType.OUT_OF_CORPUS,
        ("get_timeline_context", "search_passages"),
        (),
        ("event-congress-of-verona",),
        abstain=True,
        unacceptable=("the corpus documents the 1823 invasion",),
    ),
    _case(
        "coe-10", COE,
        "What does the corpus establish that Metternich personally knew at Troppau?",
        QuestionType.ACTOR_KNOWLEDGE,
        ("get_actor_knowledge_state", "search_passages"),
        (),
        ("claim-troppau-doctrine",),
        abstain=True,
        unacceptable=("Metternich personally knew",),
    ),
    _case(
        "coe-11", COE,
        "Which passage records the Troppau intervention principle, and what is paraphrase rather than quotation?",
        QuestionType.DIRECT_EVIDENCE,
        ("search_passages", "get_claim_evidence"),
        ("passage-troppau-protocol-1", "evidence-claim-troppau-doctrine-1"),
        ("passage-castlereagh-state-paper-1",),
    ),
    _case(
        "coe-12", COE,
        "What perspectives on the Concert are absent from this corpus?",
        QuestionType.MISSING_EVIDENCE,
        ("get_source_metadata", "compare_sources", "search_passages"),
        ("source-vienna-final-act", "source-troppau-protocol", "source-castlereagh-state-paper"),
        ("evidence-event-naples-1",),
        abstain=True,
        unacceptable=("the corpus contains every relevant perspective",),
    ),
    _case(
        "bc-01", BC,
        "What did Szögyény report about Wilhelm II's assurance?",
        QuestionType.DIRECT_EVIDENCE,
        ("get_claim_evidence", "search_passages"),
        ("evidence-claim-c1-assurance-reported-1",),
        ("evidence-claim-c3-vienna-posture-1",),
    ),
    _case(
        "bc-02", BC,
        "In what order did the assurance and the 10 July Vienna reports occur?",
        QuestionType.TIMELINE_ORDERING,
        ("get_timeline_context",),
        ("event-1-assurance-given", "event-2-vienna-posture-reported", "event-3-wilhelm-marginal-reaction"),
        ("claim-c0-franz-joseph-letter",),
        temporal=(TemporalConstraint(
            kind=TemporalConstraintKind.EVENT_ORDER,
            eventIds=("event-1-assurance-given", "event-2-vienna-posture-reported", "event-3-wilhelm-marginal-reaction"),
        ),),
    ),
    _case(
        "bc-03", BC,
        "What does the corpus record Berchtold knew about the German assurance?",
        QuestionType.ACTOR_KNOWLEDGE,
        ("get_actor_knowledge_state", "get_claim_evidence"),
        ("kat-k1-vienna-informed-of-assurance", "evidence-kat-k1-vienna-informed-of-assurance-1"),
        ("evidence-claim-c2-wilhelm-marginal-reaction-1",),
    ),
    _case(
        "bc-04", BC,
        "What posture did the 10 July report attribute to Vienna?",
        QuestionType.DIRECT_EVIDENCE,
        ("get_claim_evidence", "search_passages"),
        ("claim-c3-vienna-posture", "jc-src-002-p1"),
        ("jc-src-002-p2",),
    ),
    _case(
        "bc-05", BC,
        "What marginal reaction by Wilhelm II is preserved in the evidence?",
        QuestionType.DIRECT_EVIDENCE,
        ("get_claim_evidence", "search_passages"),
        ("claim-c2-wilhelm-marginal-reaction", "jc-src-002-p2"),
        ("jc-src-002-p1",),
    ),
    _case(
        "bc-06", BC,
        "How strongly does the corpus connect the German assurance to Vienna's subsequent posture?",
        QuestionType.EXPLANATION,
        ("get_relationship_evidence", "find_counterevidence", "trace_relationships"),
        ("rel-r1-assurance-enabled-posture", "evidence-rel-r1-assurance-enabled-posture-1"),
        ("evidence-claim-c0-franz-joseph-letter-1",),
        SUPPORT_AND_COUNTER,
        counter=True,
        unacceptable=("the assurance certainly caused Vienna's posture",),
    ),
    _case(
        "bc-07", BC,
        "How do the Fischer and Clark interpretations disagree about the assurance's causal weight?",
        QuestionType.DISPUTED_INTERPRETATION,
        ("find_counterevidence", "get_relationship_evidence", "search_passages"),
        ("evidence-rel-r1-assurance-enabled-posture-1", "evidence-rel-r1-assurance-enabled-posture-2"),
        ("evidence-claim-c2-wilhelm-marginal-reaction-1",),
        SUPPORT_AND_COUNTER,
        counter=True,
    ),
    _case(
        "bc-08", BC,
        "What role does Franz Joseph's letter play in the documented assurance episode?",
        QuestionType.DIRECT_EVIDENCE,
        ("get_claim_evidence", "search_passages"),
        ("claim-c0-franz-joseph-letter", "evidence-event-1-assurance-given-2"),
        ("evidence-claim-c3-vienna-posture-1",),
        SUPPORT_AND_CONTEXT,
    ),
    _case(
        "bc-09", BC,
        "How do the primary diplomatic documents and later historiography differ in their limitations?",
        QuestionType.SOURCE_COMPARISON,
        ("compare_sources", "get_source_metadata"),
        ("jc-src-001", "jc-src-020"),
        ("jc-src-021",),
    ),
    _case(
        "bc-10", BC,
        "Did the blank cheque single-handedly cause the First World War?",
        QuestionType.INVALID_PREMISE,
        ("get_relationship_evidence", "find_counterevidence"),
        ("evidence-rel-r1-assurance-enabled-posture-1", "evidence-rel-r1-assurance-enabled-posture-2"),
        ("evidence-claim-c2-wilhelm-marginal-reaction-1",),
        SUPPORT_AND_COUNTER,
        counter=True,
        unacceptable=("single-handedly caused the First World War",),
    ),
    _case(
        "bc-11", BC,
        "What decisions did Vienna take after 10 July 1914?",
        QuestionType.OUT_OF_CORPUS,
        ("get_timeline_context", "search_passages"),
        (),
        ("event-2-vienna-posture-reported",),
        abstain=True,
        unacceptable=("the corpus records Vienna's decisions after 10 July",),
    ),
    _case(
        "bc-12", BC,
        "At exactly what hour did Berchtold receive the assurance?",
        QuestionType.MISSING_EVIDENCE,
        ("get_actor_knowledge_state", "search_passages"),
        ("kat-k1-vienna-informed-of-assurance",),
        ("event-3-wilhelm-marginal-reaction",),
        abstain=True,
        unacceptable=("Berchtold received the assurance at exactly",),
    ),
)


def load_e3_benchmark() -> tuple[BenchmarkCase, ...]:
    """Return immutable copies so an evaluator cannot contaminate later runs."""

    return tuple(case.model_copy(deep=True) for case in _CASES)


def _investigation_ids(investigation) -> set[str]:
    names = (
        "entities", "events", "decisions", "communications", "knowledgeStates",
        "claims", "relationships", "perspectives", "conflicts", "uncertainties",
        "researchGaps", "sources", "documents", "passages", "evidenceLinks",
        "claimLedgers", "timeline", "mapAssets", "mapScenes", "scenes",
    )
    return {
        item.id
        for name in names
        for item in getattr(investigation, name, ())
        if getattr(item, "id", None)
    }


def validate_benchmark_references(
    cases: Iterable[BenchmarkCase], registry: CorpusRegistry
) -> BenchmarkReferenceValidationReport:
    """Fail closed when a benchmark expectation is absent from its corpus."""

    materialized = tuple(cases)
    ids_by_corpus: dict[str, set[str]] = {}
    issues: list[BenchmarkReferenceIssue] = []
    count = 0
    for case in materialized:
        if case.corpusId not in ids_by_corpus:
            ids_by_corpus[case.corpusId] = _investigation_ids(
                registry.get_corpus(case.corpusId).get_investigation()
            )
        local_ids = ids_by_corpus[case.corpusId]
        references = (
            case.requiredEvidenceIds
            + case.forbiddenEvidenceIds
            + tuple(event_id for constraint in case.temporalConstraints for event_id in constraint.eventIds)
        )
        count += len(references)
        for record_id in references:
            if record_id not in local_ids:
                issues.append(BenchmarkReferenceIssue(
                    caseId=case.caseId,
                    recordId=record_id,
                    detail=f'not present in corpus "{case.corpusId}"',
                ))
    if issues:
        raise BenchmarkValidationError(tuple(issues))
    return BenchmarkReferenceValidationReport(
        valid=True,
        validatedCaseCount=len(materialized),
        validatedReferenceCount=count,
    )
