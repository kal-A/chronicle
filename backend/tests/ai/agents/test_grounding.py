from __future__ import annotations

from chronicle.ai.contracts.analysis import (
    AnalysisCitation,
    AnalysisDraft,
    AnalysisStatement,
    AnswerStatus,
    DirectnessAssessment,
    GroundingIssueCode,
    StatementForm,
    StatementKind,
)
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlannedToolCall,
    PlanDisposition,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.agents.grounding import validate_grounding
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import Awareness, EvidenceClassification, EvidenceLinkRole
from chronicle.corpus import CorpusRegistry


def _retrieved_claim(tmp_path):
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    plan = InvestigationPlan(
        planId="plan-1",
        runId="run-1",
        corpusId=corpus.corpus_id,
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What did the report say?",
        questionType=QuestionType.DIRECT_EVIDENCE,
        plannedToolCalls=[
            PlannedToolCall(
                callId="claim-call",
                toolName="get_claim_evidence",
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"claimId": "claim-c1-assurance-reported"},
            )
        ],
    )
    bundle = InvestigationRunner(build_default_registry()).execute_initial(plan, corpus).bundle
    link = bundle.referenceIndex.evidenceLinks[0]
    return plan, bundle, link


def _statement(link, **updates):
    values = dict(
        statementId="s1",
        text="The retrieved report records an assurance of full support.",
        statementKind=StatementKind.FACT,
        statementForm=StatementForm.EXTRACTED_RECORD,
        basisRecordRefs=[link.targetId],
        citations=[
            AnalysisCitation(
                toolCallId="claim-call",
                evidenceLinkId=link.evidenceLinkId,
                passageId=link.passageId,
                sourceId=link.sourceId,
                targetType=link.targetType,
                targetId=link.targetId,
                role=EvidenceLinkRole(link.role),
            )
        ],
        directness=DirectnessAssessment.DIRECT,
    )
    values.update(updates)
    return AnalysisStatement(**values)


def _draft(plan, statements, **updates):
    values = dict(
        analysisVersion="e3-analyst-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        statements=statements,
    )
    values.update(updates)
    return AnalysisDraft(**values)


def test_grounding_accepts_an_exact_call_local_evidence_tuple(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)

    report = validate_grounding(_draft(plan, [_statement(link)]), plan, bundle)

    assert report.valid is True
    assert report.issues == []


def test_grounding_rejects_unknown_tool_call_and_cross_call_record(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)
    unknown_call = _statement(
        link,
        citations=[
            AnalysisCitation(
                toolCallId="other-run-call",
                evidenceLinkId=link.evidenceLinkId,
                passageId=link.passageId,
                sourceId=link.sourceId,
                targetType=link.targetType,
                targetId=link.targetId,
                role=EvidenceLinkRole(link.role),
            )
        ],
    )

    report = validate_grounding(_draft(plan, [unknown_call]), plan, bundle)

    assert GroundingIssueCode.UNKNOWN_TOOL_CALL in {issue.code for issue in report.issues}


def test_grounding_rejects_passage_source_target_and_role_mismatch(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)
    bad_tuple = _statement(
        link,
        citations=[
            AnalysisCitation(
                toolCallId="claim-call",
                evidenceLinkId=link.evidenceLinkId,
                passageId=link.passageId,
                sourceId="invented-source",
                targetType=link.targetType,
                targetId=link.targetId,
                role=(
                    EvidenceLinkRole.COUNTEREVIDENCE
                    if link.role != EvidenceLinkRole.COUNTEREVIDENCE.value
                    else EvidenceLinkRole.SUPPORTING
                ),
            )
        ],
    )

    report = validate_grounding(_draft(plan, [bad_tuple]), plan, bundle)

    assert GroundingIssueCode.CITATION_MISMATCH in {issue.code for issue in report.issues}


def test_grounding_rejects_unknown_basis_record_even_with_a_valid_citation(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)
    statement = _statement(link, basisRecordRefs=["claim-from-another-run"])

    report = validate_grounding(_draft(plan, [statement]), plan, bundle)

    assert GroundingIssueCode.UNKNOWN_RECORD in {issue.code for issue in report.issues}


def test_grounding_requires_truncation_disclosure(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)
    truncated = bundle.model_copy(update={"truncated": True})

    report = validate_grounding(_draft(plan, [_statement(link)]), plan, truncated)

    assert GroundingIssueCode.STATUS_MISMATCH in {issue.code for issue in report.issues}
    disclosed = _draft(
        plan,
        [_statement(link)],
        limitations=["Retrieval was truncated, so this answer is incomplete."],
    )
    assert validate_grounding(disclosed, plan, truncated).valid is True


def test_zero_retrieval_never_proves_absence(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)
    empty = bundle.model_copy(
        update={
            "results": [],
            "referenceIndex": bundle.referenceIndex.__class__(),
            "totalResultCount": 0,
            "serializedCharacters": 0,
        }
    )

    report = validate_grounding(
        _draft(
            plan,
            [_statement(link, directness=DirectnessAssessment.NOT_RECORDED)],
        ),
        plan,
        empty,
    )

    assert report.valid is False
    assert GroundingIssueCode.STATUS_MISMATCH in {issue.code for issue in report.issues}


def test_relationship_classification_and_directness_cannot_be_upgraded(tmp_path):
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    plan = InvestigationPlan(
        planId="plan-rel",
        runId="run-rel",
        corpusId=corpus.corpus_id,
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What does the relationship evidence establish?",
        questionType=QuestionType.RELATIONSHIP_TRACE,
        plannedToolCalls=[
            PlannedToolCall(
                callId="rel-call",
                toolName="get_relationship_evidence",
                purposeCode=ToolPurpose.TRACE_RELATIONSHIP,
                arguments={"relationshipId": "rel-r1-assurance-enabled-posture"},
            )
        ],
    )
    bundle = InvestigationRunner(build_default_registry()).execute_initial(plan, corpus).bundle
    link = bundle.referenceIndex.evidenceLinks[0]
    statement = _statement(
        link,
        statementKind=StatementKind.RELATIONSHIP,
        basisRecordRefs=["rel-r1-assurance-enabled-posture"],
        citations=[
            AnalysisCitation(
                toolCallId="rel-call",
                evidenceLinkId=link.evidenceLinkId,
                passageId=link.passageId,
                sourceId=link.sourceId,
                targetType=link.targetType,
                targetId=link.targetId,
                role=EvidenceLinkRole(link.role),
            )
        ],
        directness=DirectnessAssessment.DIRECT,
        evidenceClassification=EvidenceClassification.DIRECTLY_SUPPORTED,
    )

    report = validate_grounding(_draft(plan, [statement]), plan, bundle)

    codes = {issue.code for issue in report.issues}
    assert GroundingIssueCode.INVALID_DIRECTNESS in codes
    assert GroundingIssueCode.CITATION_MISMATCH in codes


def test_knowledge_statement_requires_a_retrieved_knowledge_state(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)
    statement = _statement(
        link,
        statementKind=StatementKind.KNOWLEDGE,
        knowledgeAwareness=Awareness.KNOWN,
    )

    report = validate_grounding(_draft(plan, [statement]), plan, bundle)

    assert GroundingIssueCode.UNKNOWN_RECORD in {issue.code for issue in report.issues}


def test_grounding_does_not_claim_to_validate_historical_truth(tmp_path):
    plan, bundle, link = _retrieved_claim(tmp_path)

    report = validate_grounding(_draft(plan, [_statement(link)]), plan, bundle)

    assert not hasattr(report, "truthVerified")
