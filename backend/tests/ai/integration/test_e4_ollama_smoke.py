"""Opt-in real-model smoke test for the E4 Critic and Guide contracts."""

from __future__ import annotations

import time

import pytest

from chronicle.ai.agents.critic import CriticValidationError, HistoricalCritic
from chronicle.ai.agents.guide import GuideValidationError, InvestigationGuide
from chronicle.ai.agents.validation import build_action_reference_index
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
from chronicle.ai.contracts.critique import CriticVerdict
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlannedToolCall,
    PlanDisposition,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.models.ollama import OllamaModelProvider
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import EvidenceLinkRole
from chronicle.corpus import CorpusRegistry

pytestmark = pytest.mark.local_ollama_integration


def test_real_ollama_critic_and_guide_nested_contracts():
    provider = OllamaModelProvider(timeout=120.0)
    health = provider.health_check()
    if not health.healthy:
        pytest.skip(f"Ollama not reachable: {health.detail}")

    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    plan = InvestigationPlan(
        planId="plan-e4-real-smoke",
        runId="run-e4-real-smoke",
        corpusId=corpus.corpus_id,
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What does the retrieved report record?",
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
    analysis = AnalysisDraft(
        analysisVersion="e3-analyst-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        statements=[statement],
    )
    grounding = GroundingValidationReport(valid=True)

    started = time.perf_counter()
    critic = HistoricalCritic(provider)
    try:
        decision = critic.review(
            "What does the retrieved report record?",
            plan,
            bundle,
            analysis,
            grounding,
        )
    except CriticValidationError as exc:
        print(f"\nE4 Critic validation failure: {exc.validationReport}")
        raise
    assert decision.verdict is not CriticVerdict.RETRIEVE_MORE

    guide = InvestigationGuide(provider)
    try:
        answer = guide.compose(
            "What does the retrieved report record?",
            analysis,
            decision,
            build_action_reference_index(corpus.get_investigation()),
        )
    except GuideValidationError as exc:
        print(f"\nE4 Guide validation failure: {exc.validationReport}")
        print(f"E4 rejected Guide proposal: {exc.proposedAnswer}")
        raise
    elapsed = time.perf_counter() - started

    if decision.verdict in {CriticVerdict.REJECT, CriticVerdict.ABSTAIN}:
        assert answer.status is AnswerStatus.ABSTAINED
        assert not answer.citations
    else:
        assert answer.status in {AnswerStatus.ANSWERED, AnswerStatus.PARTIAL}
        assert answer.citations
    assert guide.last_execution is not None
    assert guide.last_execution.validationReport.valid is True
    print(
        f"\nE4 real-model smoke: verdict={decision.verdict.value}, "
        f"status={answer.status.value}, seconds={elapsed:.2f}"
    )
