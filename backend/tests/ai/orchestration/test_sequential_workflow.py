from __future__ import annotations

from chronicle.ai.agents import (
    EvidenceAnalyst,
    HistoricalCritic,
    InvestigationGuide,
    InvestigationPlanner,
)
from chronicle.ai.contracts.analysis import (
    AnalysisCitation,
    AnalysisDraft,
    AnalysisStatement,
    AnswerStatus,
    DirectnessAssessment,
    GroundingValidationReport,
    StatementForm,
    StatementKind,
)
from chronicle.ai.contracts.answer import AgentAnswer, AnswerCitation, AnswerPoint
from chronicle.ai.contracts.critique import CriticDecision, CriticVerdict
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlannedToolCall,
    PlanDisposition,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.contracts.run import (
    AgentRunRecord,
    AgentStageStatus,
    CorpusSnapshot,
    InvestigationRequest,
    SelectedRecord,
    SelectedRecordType,
    WorkspaceContextSnapshot,
)
from chronicle.ai.models import DeterministicModelProvider
from chronicle.ai.models.metadata import ModelCallStatus
from chronicle.ai.orchestration.finalization import FinalizationRunner
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.orchestration.sequential import (
    SequentialAgentWorkflow,
    WorkflowSignalType,
)
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import EvidenceLinkRole
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore


def _context(run_id: str = "run-e5"):
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    registry = build_default_registry()
    plan = InvestigationPlan(
        planId=f"plan-{run_id}",
        runId=run_id,
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
    bundle = InvestigationRunner(registry).execute_initial(plan, corpus).bundle
    link = bundle.referenceIndex.evidenceLinks[0]
    statement = AnalysisStatement(
        statementId="statement-1",
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
    draft = AnalysisDraft(
        analysisVersion="e3-analyst-v1",
        runId=run_id,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        statements=[statement],
    )
    decision = CriticDecision(
        criticVersion="e4-critic-v1",
        runId=run_id,
        planId=plan.planId,
        corpusId=plan.corpusId,
        verdict=CriticVerdict.APPROVE,
        acceptedStatementIds=[statement.statementId],
        rationaleSummary="The statement is grounded and appropriately bounded.",
    )
    answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=run_id,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        directAnswer=statement.text,
        keyPoints=[AnswerPoint(statementId=statement.statementId, text=statement.text)],
        citations=[AnswerCitation(statementId=statement.statementId, citation=statement.citations[0])],
    )
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    record = AgentRunRecord(
        runId=run_id,
        request=InvestigationRequest(
            runId=run_id,
            corpusId=corpus.corpus_id,
            userQuestion="What did the report say?",
            workspaceContext=WorkspaceContextSnapshot(
                selectedRecords=(
                    SelectedRecord(
                        recordType=SelectedRecordType.CLAIM,
                        recordId="claim-c1-assurance-reported",
                    ),
                )
            ),
        ),
        corpusSnapshot=CorpusSnapshot(
            corpusId=corpus.corpus_id,
            packageId=investigation.packageId,
            packageHash=manifest.packageHash,
            packageRevision=investigation.packageRevision,
            schemaVersion=investigation.schemaVersion,
            capabilities=tuple(manifest.supportedCapabilities),
            knownOmissions=tuple(manifest.knownOmissions),
        ),
    )
    return corpus, registry, plan, bundle, draft, decision, answer, record


def _workflow(tmp_path, registry, provider):
    store = AgentRunStore(tmp_path)
    retrieval = InvestigationRunner(registry, store=store)
    return SequentialAgentWorkflow(
        planner=InvestigationPlanner(provider),
        retrieval_runner=retrieval,
        analyst=EvidenceAnalyst(provider),
        finalization_runner=FinalizationRunner(
            retrieval_runner=retrieval,
            analyst=EvidenceAnalyst(provider),
            critic=HistoricalCritic(provider),
            guide=InvestigationGuide(provider),
            store=store,
        ),
        store=store,
    ), store


def test_workflow_runs_and_persists_all_four_roles_in_strict_order(tmp_path):
    corpus, registry, plan, _bundle, draft, decision, answer, record = _context()
    provider = DeterministicModelProvider()
    for value in (plan, draft, decision, answer):
        provider.enqueue_value(value)
    workflow, store = _workflow(tmp_path, registry, provider)
    signals = []

    result = workflow.run(record, corpus, emit=signals.append)

    assert result.status is AgentRunStatus.ANSWER_READY
    assert [stage.stageName.value for stage in result.stages] == [
        "planner",
        "retrieval",
        "analyst",
        "critic",
        "guide",
    ]
    assert [signal.stage.value for signal in signals if signal.type is WorkflowSignalType.STAGE_STARTED] == [
        "planner",
        "retrieval",
        "analyst",
        "critic",
        "guide",
    ]
    assert len(result.modelCalls) == 4
    assert len(result.toolCalls) == 1
    assert result.finalAnswer.directAnswer == answer.directAnswer
    assert store.load_run(record.runId) == result


def test_workflow_cancellation_before_planning_makes_no_model_call(tmp_path):
    corpus, registry, _plan, _bundle, _draft, _decision, _answer, record = _context(
        "run-cancelled"
    )
    provider = DeterministicModelProvider()
    workflow, store = _workflow(tmp_path, registry, provider)
    signals = []

    result = workflow.run(
        record,
        corpus,
        emit=signals.append,
        should_cancel=lambda: True,
    )

    assert result.status is AgentRunStatus.CANCELLED
    assert result.modelCalls == []
    assert result.plan is None
    assert signals[-1].type is WorkflowSignalType.RUN_CANCELLED
    assert store.load_run(record.runId).status is AgentRunStatus.CANCELLED


def test_workflow_resume_reuses_persisted_analysis_and_only_runs_critic_and_guide(tmp_path):
    corpus, registry, plan, bundle, draft, decision, answer, record = _context("run-resume")
    record.status = AgentRunStatus.INTERRUPTED
    record.plan = plan
    record.retrievalBundle = bundle
    record.analysisDraft = draft
    record.groundingValidation = GroundingValidationReport(valid=True)
    provider = DeterministicModelProvider()
    provider.enqueue_value(decision)
    provider.enqueue_value(answer)
    workflow, store = _workflow(tmp_path, registry, provider)
    store.save_run(record)
    signals = []

    result = workflow.run(record, corpus, emit=signals.append)

    assert result.status is AgentRunStatus.ANSWER_READY
    assert [stage.stageName.value for stage in result.stages] == ["critic", "guide"]
    assert [signal.stage.value for signal in signals if signal.type is WorkflowSignalType.STAGE_STARTED] == [
        "critic",
        "guide",
    ]


def test_workflow_persists_failed_planner_call_and_specific_bounded_cause(tmp_path):
    corpus, registry, _plan, _bundle, _draft, _decision, _answer, record = _context(
        "run-planner-failure"
    )
    provider = DeterministicModelProvider()
    provider.enqueue_malformed("first malformed response")
    provider.enqueue_malformed("second malformed response")
    workflow, store = _workflow(tmp_path, registry, provider)

    result = workflow.run(record, corpus)

    assert result.status is AgentRunStatus.FAILED
    assert len(result.modelCalls) == 1
    assert result.modelCalls[0].status is ModelCallStatus.FAILED
    assert result.stages[-1].stageName.value == "planner"
    assert result.stages[-1].status is AgentStageStatus.FAILED
    assert "Configured malformed response" in result.errorMessage
    assert store.load_run(record.runId) == result
