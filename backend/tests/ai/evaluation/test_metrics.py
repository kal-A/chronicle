from __future__ import annotations

from chronicle.ai.contracts.analysis import (
    AnalysisCitation,
    AnalysisDraft,
    AnalysisStatement,
    AnswerStatus,
    DirectnessAssessment,
    StatementForm,
    StatementKind,
)
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.contracts.retrieval import RetrievedReferenceIndex
from chronicle.ai.evaluation import (
    ExecutionMeasurements,
    ObservationAvailability,
    evaluate_case,
    observe_execution_budgets,
)
from chronicle.ai.orchestration.policies import AgentExecutionPolicy
from chronicle.contracts.enums import EvidenceLinkRole
from chronicle.corpus.contracts import EvidenceLinkProjection


def _case(case_id: str):
    from chronicle.ai.evaluation import load_e3_benchmark

    return next(case for case in load_e3_benchmark() if case.caseId == case_id)


def _plan(*tool_names: str, disposition: PlanDisposition = PlanDisposition.PROCEED) -> InvestigationPlan:
    return InvestigationPlan(
        planId="plan-1",
        runId="run-1",
        corpusId="blank-cheque-golden",
        disposition=disposition,
        normalizedQuestion="What evidence supports the reported assurance?",
        questionType=QuestionType.DIRECT_EVIDENCE,
        plannedToolCalls=[
            PlannedToolCall(
                callId=f"call-{index}",
                toolName=name,
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"claimId": "claim-c1-assurance-reported"},
            )
            for index, name in enumerate(tool_names)
        ],
        unsupportedReason="Outside the corpus" if disposition is PlanDisposition.ABSTAIN else None,
    )


def _references() -> RetrievedReferenceIndex:
    return RetrievedReferenceIndex(
        evidenceLinks=[
            EvidenceLinkProjection(
                evidenceLinkId="evidence-claim-c1-assurance-reported-1",
                targetType="claim",
                targetId="claim-c1-assurance-reported",
                role="supporting",
                reviewStatus="reviewed",
                visibility="public",
                passageId="jc-src-001-p1",
                documentId="doc-jc-src-001",
                sourceId="jc-src-001",
            )
        ],
        passageIds=("jc-src-001-p1",),
        sourceIds=("jc-src-001",),
        documentIds=("doc-jc-src-001",),
        claimIds=("claim-c1-assurance-reported",),
    )


def _draft(*citations: AnalysisCitation, text: str = "Szögyény reported the assurance.") -> AnalysisDraft:
    return AnalysisDraft(
        analysisVersion="e3-v1",
        runId="run-1",
        planId="plan-1",
        corpusId="blank-cheque-golden",
        status=AnswerStatus.ANSWERED,
        statements=[
            AnalysisStatement(
                statementId="statement-1",
                text=text,
                statementKind=StatementKind.FACT,
                statementForm=StatementForm.EXTRACTED_RECORD,
                citations=list(citations),
                directness=DirectnessAssessment.DIRECT,
            )
        ],
    )


def test_plan_metrics_flag_unnecessary_tool_calls_without_invalidating_the_plan() -> None:
    result = evaluate_case(
        _case("bc-01"),
        plan=_plan("get_claim_evidence", "get_map_context"),
    )

    assert result.planValid is True
    assert result.acceptableToolSelectionRate == 0.5
    assert result.unnecessaryToolCallCount == 1


def test_citation_metrics_require_ids_to_match_one_retrieved_reference() -> None:
    valid = AnalysisCitation(
        toolCallId="call-0",
        evidenceLinkId="evidence-claim-c1-assurance-reported-1",
        passageId="jc-src-001-p1",
        sourceId="jc-src-001",
        targetType="claim",
        targetId="claim-c1-assurance-reported",
        role=EvidenceLinkRole.SUPPORTING,
    )
    invalid = AnalysisCitation(
        toolCallId="call-0",
        passageId="jc-src-002-p2",
        sourceId="jc-src-001",
        role=EvidenceLinkRole.SUPPORTING,
    )

    valid_result = evaluate_case(_case("bc-01"), analysis=_draft(valid), references=_references())
    invalid_result = evaluate_case(_case("bc-01"), analysis=_draft(invalid), references=_references())

    assert valid_result.citationIdValidityRate == 1.0
    assert valid_result.citationCoverageRate == 1.0
    assert valid_result.unsupportedStatementRate == 0.0
    assert invalid_result.citationIdValidityRate == 0.0
    assert invalid_result.citationCoverageRate == 0.0
    assert invalid_result.unsupportedStatementRate == 1.0


def test_role_correctness_and_required_evidence_recall_are_scored_deterministically() -> None:
    correct = AnalysisCitation(
        toolCallId="call-0",
        evidenceLinkId="evidence-claim-c1-assurance-reported-1",
        role=EvidenceLinkRole.SUPPORTING,
    )
    wrong_role = correct.model_copy(update={"role": EvidenceLinkRole.CONTEXT})

    correct_result = evaluate_case(_case("bc-01"), analysis=_draft(correct), references=_references())
    wrong_result = evaluate_case(_case("bc-01"), analysis=_draft(wrong_role), references=_references())

    assert correct_result.roleCorrectnessRate == 1.0
    assert correct_result.requiredEvidenceRecall == 1.0
    assert wrong_result.roleCorrectnessRate == 0.0


def test_abstention_accuracy_distinguishes_expected_and_unexpected_abstention() -> None:
    expected = evaluate_case(_case("bc-11"), plan=_plan(disposition=PlanDisposition.ABSTAIN))
    unexpected = evaluate_case(_case("bc-01"), plan=_plan(disposition=PlanDisposition.ABSTAIN))

    assert expected.abstentionCorrect is True
    assert unexpected.abstentionCorrect is False


def test_unacceptable_claims_are_reported_as_case_insensitive_substring_hits() -> None:
    citation = AnalysisCitation(
        toolCallId="call-0",
        evidenceLinkId="evidence-claim-c1-assurance-reported-1",
        role=EvidenceLinkRole.SUPPORTING,
    )
    result = evaluate_case(
        _case("bc-10"),
        analysis=_draft(citation, text="The BLANK CHEQUE single-handedly caused the First World War."),
        references=_references(),
    )

    assert result.unacceptableClaimHits == ("single-handedly caused the First World War",)


def test_budget_observations_preserve_unavailable_values_and_detect_excesses() -> None:
    observations = observe_execution_budgets(
        ExecutionMeasurements(
            plannerModelCalls=1,
            totalToolCalls=5,
            elapsedSeconds=301.0,
            plannerPromptCharacters=23_000,
        ),
        AgentExecutionPolicy(),
    )
    by_name = {observation.name: observation for observation in observations}

    assert by_name["planner_model_calls"].availability is ObservationAvailability.AVAILABLE
    assert by_name["planner_model_calls"].withinLimit is True
    assert by_name["total_tool_calls"].withinLimit is False
    assert by_name["deadline_seconds"].withinLimit is False
    assert by_name["analyst_model_calls"].availability is ObservationAvailability.UNAVAILABLE
    assert by_name["analyst_model_calls"].withinLimit is None
    assert by_name["planner_prompt_characters"].withinLimit is True
