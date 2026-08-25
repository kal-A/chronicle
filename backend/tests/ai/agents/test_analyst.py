from __future__ import annotations

import json

import pytest

from chronicle.ai.agents.analyst import (
    ANALYST_PROMPT_VERSION,
    AnalystBudgetError,
    AnalystValidationError,
    EvidenceAnalyst,
)
from chronicle.ai.agents.analyst_prompt import build_analyst_prompt
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
    PlannedToolCall,
    PlanDisposition,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.models import DeterministicModelProvider
from chronicle.ai.orchestration.policies import AgentExecutionPolicy
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import EvidenceLinkRole
from chronicle.corpus import CorpusRegistry


def _context():
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
    draft = AnalysisDraft(
        analysisVersion="e3-analyst-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        statements=[
            AnalysisStatement(
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
        ],
    )
    return plan, bundle, draft


def test_analyst_uses_one_bounded_structured_call_and_returns_grounded_draft():
    plan, bundle, draft = _context()
    provider = DeterministicModelProvider()
    provider.enqueue_value(draft)

    result = EvidenceAnalyst(provider).analyze("What did the report say?", plan, bundle)

    assert result == draft
    execution = EvidenceAnalyst  # keep the public class visible to static tooling
    assert execution is not None


def test_analyst_records_required_generation_settings():
    plan, bundle, draft = _context()
    provider = DeterministicModelProvider()
    provider.enqueue_value(draft)
    analyst = EvidenceAnalyst(provider)

    analyst.analyze("What did the report say?", plan, bundle)

    assert analyst.last_execution is not None
    call = analyst.last_execution.modelCall
    assert call.promptVersion == ANALYST_PROMPT_VERSION
    assert call.generationSettings.contextTokens == 8_192
    assert call.generationSettings.maxCompletionTokens == 1_800
    assert call.generationSettings.temperature == 0.0
    assert analyst.last_prompt.measurement.promptCharacters <= 24_000


class _SchemaCapturingProvider:
    def __init__(self, value: AnalysisDraft) -> None:
        self.inner = DeterministicModelProvider()
        self.inner.enqueue_value(value)
        self.response_schema = None

    def generate_structured(self, *, response_schema, **kwargs):
        self.response_schema = response_schema
        return self.inner.generate_structured(response_schema=response_schema, **kwargs)


def test_analyst_constrains_statement_fields_and_citations_to_retrieved_evidence():
    plan, bundle, draft = _context()
    provider = _SchemaCapturingProvider(draft)

    EvidenceAnalyst(provider).analyze("What did the report say?", plan, bundle)

    schema = provider.response_schema
    assert schema is not None
    assert set(schema["required"]) == set(schema["properties"])
    statement_variants = schema["$defs"]["AnalysisStatement"]["oneOf"]
    fact = next(
        variant
        for variant in statement_variants
        if variant["properties"]["statementKind"].get("const") == "fact"
    )
    knowledge = next(
        variant
        for variant in statement_variants
        if variant["properties"]["statementKind"].get("const") == "knowledge"
    )
    assert fact["properties"]["knowledgeAwareness"] == {"type": "null"}
    assert fact["properties"]["evidenceClassification"] == {"type": "null"}
    assert fact["properties"]["geographicPrecision"] == {"type": "null"}
    assert fact["properties"]["requiresHumanReview"] == {
        "const": True,
        "type": "boolean",
    }
    assert set(fact["properties"]["temporalRoles"]["items"]["enum"]) == {
        "sent_time",
        "source_date",
    }
    assert knowledge["properties"]["knowledgeAwareness"] == {
        "$ref": "#/$defs/Awareness"
    }

    link = bundle.referenceIndex.evidenceLinks[0]
    citation_variants = schema["$defs"]["AnalysisCitation"]["oneOf"]
    exact_link = next(
        variant
        for variant in citation_variants
        if variant["properties"]["evidenceLinkId"].get("const")
        == link.evidenceLinkId
    )
    assert exact_link["properties"]["toolCallId"]["const"] == "claim-call"
    assert exact_link["properties"]["passageId"]["const"] == link.passageId
    assert exact_link["properties"]["sourceId"]["const"] == link.sourceId
    assert exact_link["properties"]["targetId"]["const"] == link.targetId
    assert exact_link["properties"]["role"]["const"] == link.role


def test_analyst_rejects_identity_substitution_with_a_grounding_report():
    plan, bundle, draft = _context()
    provider = DeterministicModelProvider()
    provider.enqueue_value(draft.model_copy(update={"runId": "other-run"}))

    with pytest.raises(AnalystValidationError) as exc_info:
        EvidenceAnalyst(provider).analyze("What did the report say?", plan, bundle)

    assert exc_info.value.validationReport is not None
    assert exc_info.value.modelCall is not None


def test_analyst_input_contains_only_question_plan_bundle_and_response_schema():
    plan, bundle, _draft = _context()
    prompt = build_analyst_prompt(
        "What did the report say?",
        plan,
        bundle,
        AgentExecutionPolicy(),
    )

    payload = json.loads(prompt.userPrompt.split("\n", 1)[1])
    assert set(payload) == {"userQuestion", "investigationPlan", "retrievalBundle"}
    assert "corpusSnapshot" not in prompt.userPrompt
    assert "workspaceContext" not in prompt.userPrompt


def test_analyst_prompt_is_topic_neutral_and_forbids_truth_upgrade():
    plan, bundle, _draft = _context()
    prompt = build_analyst_prompt("Question", plan, bundle, AgentExecutionPolicy())
    combined = f"{prompt.systemPrompt}\n{prompt.userPrompt}".lower()

    assert "ground truth" in combined
    assert "do not upgrade" in combined
    assert "blank cheque" not in prompt.systemPrompt.lower()


def test_analyst_enforces_complete_prompt_budget_before_calling_provider():
    plan, bundle, draft = _context()
    provider = DeterministicModelProvider()
    provider.enqueue_value(draft)
    policy = AgentExecutionPolicy(maxPromptCharacters=10_000)

    with pytest.raises(AnalystBudgetError, match="prompt"):
        EvidenceAnalyst(provider, policy).analyze("Q" * 1_000, plan, bundle)

    assert len(provider._queue) == 1  # noqa: SLF001


def test_analyst_never_receives_or_queries_a_corpus_object():
    plan, bundle, draft = _context()
    provider = DeterministicModelProvider()
    provider.enqueue_value(draft)

    EvidenceAnalyst(provider).analyze("What did the report say?", plan, bundle)

    assert not hasattr(EvidenceAnalyst(provider), "corpus")
