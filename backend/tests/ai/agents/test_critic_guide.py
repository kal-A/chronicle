from __future__ import annotations

import pytest

from chronicle.ai.agents.critic import CriticValidationError, HistoricalCritic
from chronicle.ai.agents.critic_prompt import build_critic_prompt
from chronicle.ai.agents.guide import GuideValidationError, InvestigationGuide
from chronicle.ai.agents.guide_prompt import build_guide_prompt
from chronicle.ai.agents.validation import (
    build_action_reference_index,
    validate_agent_answer,
    validate_critic_decision,
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
from chronicle.ai.contracts.answer import (
    AgentAnswer,
    AnswerCitation,
    AnswerPoint,
    FocusEventAction,
)
from chronicle.ai.contracts.critique import (
    CriticDecision,
    CriticVerdict,
    StatementRejection,
)
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlannedToolCall,
    PlanDisposition,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.models import DeterministicModelProvider
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.orchestration.policies import AgentExecutionPolicy
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import EvidenceLinkRole
from chronicle.corpus import CorpusRegistry


def _context():
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    plan = InvestigationPlan(
        planId="plan-e4",
        runId="run-e4",
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
    citation = AnalysisCitation(
        toolCallId="claim-call",
        evidenceLinkId=link.evidenceLinkId,
        passageId=link.passageId,
        sourceId=link.sourceId,
        targetType=link.targetType,
        targetId=link.targetId,
        role=EvidenceLinkRole(link.role),
    )
    statement = AnalysisStatement(
        statementId="statement-1",
        text="The retrieved report records an assurance of full support.",
        statementKind=StatementKind.FACT,
        statementForm=StatementForm.EXTRACTED_RECORD,
        basisRecordRefs=[link.targetId],
        citations=[citation],
        directness=DirectnessAssessment.DIRECT,
    )
    draft = AnalysisDraft(
        analysisVersion="e3-analyst-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        statements=[statement],
        limitations=["This corpus contains a bounded selection of records."],
    )
    grounding = GroundingValidationReport(valid=True)
    decision = CriticDecision(
        criticVersion="e4-critic-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        verdict=CriticVerdict.APPROVE,
        acceptedStatementIds=[statement.statementId],
        rationaleSummary="The statement is traceable and properly qualified.",
    )
    return corpus, plan, bundle, draft, grounding, decision


def test_critic_validation_requires_complete_non_overlapping_review():
    _corpus, _plan, _bundle, draft, grounding, decision = _context()

    assert validate_critic_decision(decision, draft, grounding).valid is True

    invalid = decision.model_copy(update={"acceptedStatementIds": ["invented-statement"]})
    report = validate_critic_decision(invalid, draft, grounding)
    assert report.valid is False
    assert {issue.code.value for issue in report.issues} >= {
        "unknown_statement",
        "incomplete_review",
    }


def test_critic_agent_rejects_a_schema_valid_but_untrusted_decision():
    _corpus, plan, bundle, draft, grounding, decision = _context()
    provider = DeterministicModelProvider()
    provider.enqueue_value(
        decision.model_copy(update={"acceptedStatementIds": ["invented-statement"]})
    )

    with pytest.raises(CriticValidationError) as exc_info:
        HistoricalCritic(provider).review(
            "What did the report say?", plan, bundle, draft, grounding
        )

    assert exc_info.value.validationReport is not None
    assert exc_info.value.modelCall is not None


def test_critic_prompt_names_every_statement_that_requires_disposition():
    _corpus, plan, bundle, draft, grounding, _decision = _context()

    prompt = build_critic_prompt(
        "What did the report say?",
        plan,
        bundle,
        draft,
        grounding,
        AgentExecutionPolicy(),
    )

    assert '"statementIdsRequiringDisposition":["statement-1"]' in prompt.userPrompt
    normalized_system = " ".join(prompt.systemPrompt.split())
    assert "Never use approve with an empty acceptedStatementIds" in normalized_system


def test_retrieve_more_requires_exactly_one_bounded_tool_call():
    _corpus, plan, _bundle, _draft, _grounding, decision = _context()
    follow_up = PlannedToolCall(
        callId="critic-counterevidence",
        toolName="find_counterevidence",
        purposeCode=ToolPurpose.FIND_COUNTEREVIDENCE,
        arguments={"recordId": "claim-c1-assurance-reported"},
    )
    retrieval = decision.model_copy(
        update={
            "verdict": CriticVerdict.RETRIEVE_MORE,
            "acceptedStatementIds": [],
            "additionalToolCalls": [follow_up],
        }
    )
    assert retrieval.additionalToolCalls == [follow_up]

    with pytest.raises(ValueError):
        CriticDecision(
            criticVersion="e4-critic-v1",
            runId=plan.runId,
            planId=plan.planId,
            corpusId=plan.corpusId,
            verdict=CriticVerdict.RETRIEVE_MORE,
            rationaleSummary="More evidence is required.",
        )

    with pytest.raises(ValueError, match="accepted statement"):
        CriticDecision.model_validate(
            {**decision.model_dump(), "acceptedStatementIds": []}
        )


def test_answer_validator_rejects_new_facts_citations_and_action_ids():
    corpus, plan, _bundle, draft, _grounding, decision = _context()
    statement = draft.statements[0]
    event_id = corpus.get_investigation().events[0].id
    answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        directAnswer=statement.text,
        keyPoints=[AnswerPoint(statementId=statement.statementId, text=statement.text)],
        limitations=list(draft.limitations),
        citations=[
            AnswerCitation(statementId=statement.statementId, citation=statement.citations[0])
        ],
        suggestedQuestions=["What counterevidence is recorded?"],
        actions=[FocusEventAction(eventId=event_id)],
    )
    action_index = build_action_reference_index(corpus.get_investigation())

    assert validate_agent_answer(answer, draft, decision, action_index).valid is True

    invented = answer.model_copy(
        update={
            "directAnswer": "An uncited new historical claim.",
            "actions": [FocusEventAction(eventId="invented-event")],
        }
    )
    report = validate_agent_answer(invented, draft, decision, action_index)
    assert report.valid is False
    assert {issue.code.value for issue in report.issues} >= {
        "unapproved_answer_text",
        "unknown_action_reference",
    }


def test_guide_receives_only_critic_approved_statements_and_valid_action_ids():
    corpus, plan, _bundle, draft, _grounding, decision = _context()
    rejected_statement = draft.statements[0].model_copy(
        update={"statementId": "statement-rejected", "text": "Rejected material."}
    )
    expanded_draft = draft.model_copy(
        update={"statements": [draft.statements[0], rejected_statement]}
    )
    expanded_decision = decision.model_copy(
        update={
            "rejectedStatements": [
                StatementRejection(
                    statementId=rejected_statement.statementId,
                    reason="Insufficient evidence.",
                )
            ]
        }
    )
    event_id = corpus.get_investigation().events[0].id
    answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        directAnswer=draft.statements[0].text,
        keyPoints=[
            AnswerPoint(
                statementId=draft.statements[0].statementId,
                text=draft.statements[0].text,
            )
        ],
        limitations=list(draft.limitations),
        citations=[
            AnswerCitation(
                statementId=draft.statements[0].statementId,
                citation=draft.statements[0].citations[0],
            )
        ],
        actions=[FocusEventAction(eventId=event_id)],
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(answer)
    guide = InvestigationGuide(provider)

    assert guide.compose(
        "What did the report say?",
        expanded_draft,
        expanded_decision,
        build_action_reference_index(corpus.get_investigation()),
    ) == answer
    assert guide.last_prompt is not None
    assert rejected_statement.text not in guide.last_prompt.userPrompt


def test_guide_prompt_names_required_key_points_for_an_approved_answer():
    corpus, _plan, _bundle, draft, _grounding, decision = _context()

    prompt = build_guide_prompt(
        "What did the report say?",
        draft,
        decision,
        build_action_reference_index(corpus.get_investigation()),
        AgentExecutionPolicy(),
    )

    assert '"requiredKeyPointIds":["statement-1"]' in prompt.userPrompt
    normalized_system = " ".join(prompt.systemPrompt.split())
    assert "Never return answered or partial with an empty keyPoints list" in normalized_system


def test_guide_rejects_a_schema_valid_answer_with_an_unknown_action():
    corpus, _plan, _bundle, draft, _grounding, decision = _context()
    statement = draft.statements[0]
    bad_answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=draft.runId,
        planId=draft.planId,
        corpusId=draft.corpusId,
        status=AnswerStatus.ANSWERED,
        directAnswer=statement.text,
        keyPoints=[AnswerPoint(statementId=statement.statementId, text=statement.text)],
        citations=[
            AnswerCitation(statementId=statement.statementId, citation=statement.citations[0])
        ],
        actions=[FocusEventAction(eventId="invented-event")],
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(bad_answer)

    with pytest.raises(GuideValidationError) as exc_info:
        InvestigationGuide(provider).compose(
            "What did the report say?",
            draft,
            decision,
            build_action_reference_index(corpus.get_investigation()),
        )

    assert exc_info.value.validationReport is not None
    assert exc_info.value.modelCall is not None
    assert exc_info.value.proposedAnswer == bad_answer


def test_guide_mechanically_reattaches_canonical_grounded_citations():
    corpus, _plan, _bundle, draft, _grounding, decision = _context()
    statement = draft.statements[0]
    lossy_model_answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId=draft.runId,
        planId=draft.planId,
        corpusId=draft.corpusId,
        status=AnswerStatus.ANSWERED,
        directAnswer=statement.text,
        keyPoints=[AnswerPoint(statementId=statement.statementId, text=statement.text)],
        citations=[
            AnswerCitation(
                statementId=statement.statementId,
                citation=AnalysisCitation(
                    toolCallId=statement.citations[0].toolCallId,
                    evidenceLinkId=statement.citations[0].evidenceLinkId,
                    passageId=statement.citations[0].passageId,
                ),
            )
        ],
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(lossy_model_answer)
    guide = InvestigationGuide(provider)

    answer = guide.compose(
        "What did the report say?",
        draft,
        decision,
        build_action_reference_index(corpus.get_investigation()),
    )

    assert answer.citations == [
        AnswerCitation(statementId=statement.statementId, citation=statement.citations[0])
    ]
    assert guide.last_execution is not None
    assert guide.last_execution.citationsNormalized is True
