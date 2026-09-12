from __future__ import annotations

from chronicle.ai.agents.analyst import EvidenceAnalyst
from chronicle.ai.agents.critic import HistoricalCritic
from chronicle.ai.agents.guide import InvestigationGuide
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
from chronicle.ai.models import DeterministicModelProvider
from chronicle.ai.contracts.run import AgentRunRecord, CorpusSnapshot, InvestigationRequest
from chronicle.ai.orchestration.finalization import FinalizationRunner
from chronicle.ai.orchestration.statuses import AgentRunStatus
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import EvidenceLinkRole
from chronicle.corpus import CorpusRegistry
from chronicle.storage.agent_run_store import AgentRunStore


def _workflow_context():
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    plan = InvestigationPlan(
        planId="plan-finalize",
        runId="run-finalize",
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
    retrieval_runner = InvestigationRunner(build_default_registry())
    bundle = retrieval_runner.execute_initial(plan, corpus).bundle
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
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        statements=[statement],
    )
    return corpus, plan, retrieval_runner, bundle, draft


def test_finalization_allows_one_critic_retrieval_then_guides_the_reanalysis():
    corpus, plan, retrieval_runner, bundle, initial_draft = _workflow_context()
    follow_up = PlannedToolCall(
        callId="critic-counterevidence",
        toolName="find_counterevidence",
        purposeCode=ToolPurpose.FIND_COUNTEREVIDENCE,
        arguments={"recordId": "claim-c1-assurance-reported"},
    )
    critic_provider = DeterministicModelProvider()
    critic_provider.enqueue_value(
        CriticDecision(
            criticVersion="e4-critic-v1",
            runId=plan.runId,
            planId=plan.planId,
            corpusId=plan.corpusId,
            verdict=CriticVerdict.RETRIEVE_MORE,
            additionalToolCalls=[follow_up],
            rationaleSummary="Check the recorded counterevidence before answering.",
        )
    )
    critic_provider.enqueue_value(
        CriticDecision(
            criticVersion="e4-critic-v1",
            runId=plan.runId,
            planId=plan.planId,
            corpusId=plan.corpusId,
            verdict=CriticVerdict.APPROVE,
            acceptedStatementIds=[initial_draft.statements[0].statementId],
            rationaleSummary="The reanalysis is sufficiently supported.",
        )
    )
    analyst_provider = DeterministicModelProvider()
    analyst_provider.enqueue_value(initial_draft)
    answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        directAnswer=initial_draft.statements[0].text,
        keyPoints=[
            AnswerPoint(
                statementId=initial_draft.statements[0].statementId,
                text=initial_draft.statements[0].text,
            )
        ],
        citations=[
            AnswerCitation(
                statementId=initial_draft.statements[0].statementId,
                citation=initial_draft.statements[0].citations[0],
            )
        ],
    )
    guide_provider = DeterministicModelProvider()
    guide_provider.enqueue_value(answer)

    result = FinalizationRunner(
        retrieval_runner=retrieval_runner,
        analyst=EvidenceAnalyst(analyst_provider),
        critic=HistoricalCritic(critic_provider),
        guide=InvestigationGuide(guide_provider),
    ).finalize(
        "What did the report say?",
        plan,
        corpus,
        bundle,
        initial_draft,
        GroundingValidationReport(valid=True),
    )

    assert [decision.verdict for decision in result.criticDecisions] == [
        CriticVerdict.RETRIEVE_MORE,
        CriticVerdict.APPROVE,
    ]
    assert sum(item.round == 1 for item in result.retrievalBundle.results) == 1
    assert result.answer == answer
    assert result.answerValidation.valid is True


def test_second_retrieve_more_is_converted_to_bounded_abstention():
    corpus, plan, retrieval_runner, bundle, initial_draft = _workflow_context()
    follow_up = PlannedToolCall(
        callId="critic-counterevidence",
        toolName="find_counterevidence",
        purposeCode=ToolPurpose.FIND_COUNTEREVIDENCE,
        arguments={"recordId": "claim-c1-assurance-reported"},
    )
    critic_provider = DeterministicModelProvider()
    for call_id in ("critic-counterevidence", "forbidden-second-retry"):
        critic_provider.enqueue_value(
            CriticDecision(
                criticVersion="e4-critic-v1",
                runId=plan.runId,
                planId=plan.planId,
                corpusId=plan.corpusId,
                verdict=CriticVerdict.RETRIEVE_MORE,
                additionalToolCalls=[
                    follow_up.model_copy(update={"callId": call_id})
                ],
                rationaleSummary="More retrieval would be needed.",
            )
        )
    analyst_provider = DeterministicModelProvider()
    analyst_provider.enqueue_value(initial_draft)
    abstention = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ABSTAINED,
        directAnswer="The bounded evidence check did not support a reliable answer.",
        limitations=["The single permitted follow-up retrieval was exhausted."],
    )
    guide_provider = DeterministicModelProvider()
    guide_provider.enqueue_value(abstention)

    result = FinalizationRunner(
        retrieval_runner=retrieval_runner,
        analyst=EvidenceAnalyst(analyst_provider),
        critic=HistoricalCritic(critic_provider),
        guide=InvestigationGuide(guide_provider),
    ).finalize(
        "What did the report say?",
        plan,
        corpus,
        bundle,
        initial_draft,
        GroundingValidationReport(valid=True),
    )

    assert len(result.criticDecisions) == 3
    assert result.criticDecisions[-1].verdict is CriticVerdict.ABSTAIN
    assert sum(item.round == 1 for item in result.retrievalBundle.results) == 1
    assert result.answer.status is AnswerStatus.ABSTAINED


def test_finalization_persists_auditable_critic_and_guide_stages(tmp_path):
    corpus, plan, retrieval_runner, bundle, draft = _workflow_context()
    critic_provider = DeterministicModelProvider()
    critic_provider.enqueue_value(
        CriticDecision(
            criticVersion="e4-critic-v1",
            runId=plan.runId,
            planId=plan.planId,
            corpusId=plan.corpusId,
            verdict=CriticVerdict.APPROVE,
            acceptedStatementIds=[draft.statements[0].statementId],
            rationaleSummary="The statement is grounded and properly bounded.",
        )
    )
    answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        directAnswer=draft.statements[0].text,
        keyPoints=[
            AnswerPoint(statementId=draft.statements[0].statementId, text=draft.statements[0].text)
        ],
        citations=[
            AnswerCitation(
                statementId=draft.statements[0].statementId,
                citation=draft.statements[0].citations[0],
            )
        ],
    )
    guide_provider = DeterministicModelProvider()
    guide_provider.enqueue_value(answer)
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    record = AgentRunRecord(
        runId=plan.runId,
        request=InvestigationRequest(
            runId=plan.runId,
            corpusId=plan.corpusId,
            userQuestion="What did the report say?",
        ),
        corpusSnapshot=CorpusSnapshot(
            corpusId=plan.corpusId,
            packageId=investigation.packageId,
            packageHash=manifest.packageHash,
            packageRevision=investigation.packageRevision,
            schemaVersion=investigation.schemaVersion,
            capabilities=tuple(manifest.supportedCapabilities),
            knownOmissions=tuple(manifest.knownOmissions),
        ),
        plan=plan,
        retrievalBundle=bundle,
        analysisDraft=draft,
        groundingValidation=GroundingValidationReport(valid=True),
    )
    store = AgentRunStore(tmp_path)

    FinalizationRunner(
        retrieval_runner=retrieval_runner,
        analyst=EvidenceAnalyst(DeterministicModelProvider()),
        critic=HistoricalCritic(critic_provider),
        guide=InvestigationGuide(guide_provider),
        store=store,
    ).finalize(
        "What did the report say?",
        plan,
        corpus,
        bundle,
        draft,
        GroundingValidationReport(valid=True),
        run_record=record,
    )

    persisted = store.load_run(plan.runId)
    assert persisted.status is AgentRunStatus.ANSWER_READY
    assert [stage.stageName.value for stage in persisted.stages] == ["critic", "guide"]
    # Only the Critic makes a model call now; the Guide composes deterministically,
    # so its stage records no model call (the audit trail states that plainly).
    assert len(persisted.modelCalls) == 1
    guide_stage = next(s for s in persisted.stages if s.stageName.value == "guide")
    assert guide_stage.modelCalls == []
    assert persisted.finalAnswer == answer
