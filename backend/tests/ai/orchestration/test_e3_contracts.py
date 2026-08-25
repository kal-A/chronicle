from __future__ import annotations

import pytest
from pydantic import ValidationError

from chronicle.ai.contracts.analysis import (
    AnalysisCitation,
    AnalysisDraft,
    AnalysisStatement,
    AnswerStatus,
    DirectnessAssessment,
    StatementForm,
    StatementKind,
    GroundingIssue,
    GroundingIssueCode,
    GroundingValidationReport,
)
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    RequiredEvidenceType,
    ToolPurpose,
)
from chronicle.ai.contracts.run import (
    AgentRunRecord,
    CorpusSnapshot,
    InvestigationRequest,
    SelectedRecord,
    SelectedRecordType,
    WorkspaceContextSnapshot,
)
from chronicle.ai.orchestration.policies import AgentExecutionPolicy
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.contracts.enums import Awareness, LocationPrecision
from chronicle.corpus.contracts import PassageDateRole


def _request() -> InvestigationRequest:
    return InvestigationRequest(
        runId="run-e3-1",
        corpusId="concert-of-europe",
        userQuestion="What evidence supports the Troppau principle?",
        workspaceContext=WorkspaceContextSnapshot(
            sceneId="scene-troppau",
            selectedRecords=[SelectedRecord(recordType=SelectedRecordType.CLAIM, recordId="claim-1")],
        ),
    )


def _plan() -> InvestigationPlan:
    return InvestigationPlan(
        planId="plan-1",
        runId="run-e3-1",
        corpusId="concert-of-europe",
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What evidence supports the Troppau principle?",
        questionType=QuestionType.DIRECT_EVIDENCE,
        requiredEvidenceTypes=[RequiredEvidenceType.CLAIM_EVIDENCE],
        plannedToolCalls=[
            PlannedToolCall(
                callId="call-1",
                toolName="get_claim_evidence",
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"claimId": "claim-1"},
            )
        ],
    )


def test_default_execution_policy_matches_the_approved_e3_budget():
    policy = AgentExecutionPolicy()
    assert policy.maxPlannerModelCalls == 1
    assert policy.maxInitialToolCalls == 3
    assert policy.maxFollowUpRounds == 1
    assert policy.maxFollowUpToolCalls == 1
    assert policy.maxTotalToolCalls == 4
    assert policy.maxResultsPerTool == 4
    assert policy.maxCharactersPerToolOutput == 6_000
    assert policy.maxAggregateRetrievalCharacters == 14_000
    assert policy.maxAggregateResults == 16
    assert policy.maxAnalystModelCalls == 2
    assert policy.maxStructuredAttempts == 2
    assert policy.maxPromptCharacters == 24_000
    assert policy.maxToolSpecCharacters == 18_000
    assert policy.maxStatements == 8
    assert policy.maxCitationsPerStatement == 6
    assert policy.deadlineSeconds == 300
    assert policy.modelContextTokens == 8_192
    assert policy.plannerMaxCompletionTokens == 900
    assert policy.analystMaxCompletionTokens == 1_800


def test_policy_and_snapshots_are_frozen():
    policy = AgentExecutionPolicy()
    request = _request()
    with pytest.raises(ValidationError):
        policy.maxTotalToolCalls = 99
    with pytest.raises(ValidationError):
        request.workspaceContext.sceneId = "other"


def test_plan_enforces_initial_call_budget_and_unique_ids():
    call = _plan().plannedToolCalls[0]
    with pytest.raises(ValidationError):
        InvestigationPlan(
            **{
                **_plan().model_dump(),
                "plannedToolCalls": [call.model_copy(update={"callId": f"call-{index}"}) for index in range(4)],
            }
        )
    with pytest.raises(ValidationError):
        InvestigationPlan(**{**_plan().model_dump(), "plannedToolCalls": [call, call]})


def test_abstention_requires_a_reason_and_forbids_tool_calls():
    with pytest.raises(ValidationError):
        InvestigationPlan(
            **{
                **_plan().model_dump(),
                "disposition": PlanDisposition.ABSTAIN,
                "unsupportedReason": None,
            }
        )


def test_analysis_contract_limits_statements_and_citations():
    citation = AnalysisCitation(toolCallId="tool-1", passageId="passage-1", sourceId="source-1")
    statement = AnalysisStatement(
        statementId="statement-1",
        text="The passage records support for the principle.",
        statementKind=StatementKind.FACT,
        statementForm=StatementForm.EXTRACTED_RECORD,
        citations=[citation],
        directness=DirectnessAssessment.DIRECT,
        geographicPrecision=LocationPrecision.CITY,
        temporalRoles=[PassageDateRole.SENT_TIME],
    )
    draft = AnalysisDraft(
        analysisVersion="e3-analysis-v1",
        runId="run-e3-1",
        planId="plan-1",
        corpusId="concert-of-europe",
        status=AnswerStatus.ANSWERED,
        statements=[statement],
    )
    assert draft.statements[0].citations[0].passageId == "passage-1"
    assert draft.statements[0].geographicPrecision is LocationPrecision.CITY
    assert draft.statements[0].temporalRoles == [PassageDateRole.SENT_TIME]
    with pytest.raises(ValidationError):
        AnalysisStatement(**{**statement.model_dump(), "citations": [citation] * 7})
    with pytest.raises(ValidationError):
        AnalysisDraft(**{**draft.model_dump(), "statements": [statement] * 9})
    with pytest.raises(ValidationError):
        AnalysisDraft(**{**draft.model_dump(), "statements": []})
    with pytest.raises(ValidationError):
        AnalysisDraft(
            **{
                **draft.model_dump(),
                "status": AnswerStatus.ABSTAINED,
                "abstentionReason": "No evidence in this corpus.",
            }
        )


def test_agent_run_record_snapshots_corpus_identity_and_reserves_ready_for_e4():
    record = AgentRunRecord(
        runId="run-e3-1",
        request=_request(),
        corpusSnapshot=CorpusSnapshot(
            corpusId="concert-of-europe",
            packageId="concert-of-europe",
            packageHash="a" * 64,
            packageRevision=1,
            schemaVersion="1.0.0",
        ),
    )
    assert record.status is AgentRunStatus.CREATED
    assert AgentRunStatus.ANALYSIS_READY.value == "analysis_ready"
    assert AgentRunStatus.INTERRUPTED.value == "interrupted"


def test_grounding_report_truthfully_matches_its_issues():
    with pytest.raises(ValidationError):
        GroundingValidationReport(
            valid=True,
            issues=[GroundingIssue(code=GroundingIssueCode.UNKNOWN_RECORD, message="missing")],
        )


def test_knowledge_statements_can_preserve_structured_awareness():
    statement = AnalysisStatement(
        statementId="knowledge-1",
        text="The actor is recorded as not yet knowing the information.",
        statementKind=StatementKind.KNOWLEDGE,
        statementForm=StatementForm.EXTRACTED_RECORD,
        citations=[AnalysisCitation(toolCallId="tool-1", targetId="knowledge-1")],
        directness=DirectnessAssessment.NOT_RECORDED,
        knowledgeAwareness=Awareness.NOT_YET_KNOWN,
    )
    assert statement.knowledgeAwareness is Awareness.NOT_YET_KNOWN
