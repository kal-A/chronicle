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
from chronicle.ai.agents.analyst_schema import build_analyst_response_schema
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


def _passage_only_context(tmp_path):
    """A retrieval bundle over an auto-acquired corpus: passages + sources, but
    no evidence-links and no directness metadata (no claims/relationships). Over
    such a bundle only inferred synthesis can ground (see
    grounding._validate_directness), which is what the schema must enforce. Built
    from the real acquisition builder so the passage-only shape is faithful, not
    hand-crafted.
    """

    import json
    from datetime import date, datetime, timezone

    from chronicle.acquisition.chunking import chunk_source
    from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
    from chronicle.acquisition.corpus_builder import build_corpus
    from chronicle.contracts.enums import RightsStatus, SourceType
    from chronicle.corpus.manifest import CorpusRegistry as _Registry, CorpusSource

    body = (
        "War broke out in the summer of 1914 after the assurance of support was "
        "extended to Austria-Hungary during the July crisis. "
    ) * 12
    candidate = SourceCandidate(
        candidateId="wikipedia:en:1",
        connector="wikipedia",
        title="Origins of the war",
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url="https://example.org/origins",
        language="en",
    )
    acquired = AcquiredSource(
        candidate=candidate,
        text=body,
        contentType="text/plain",
        contentSha256="hash-1",
        charCount=len(body),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )
    passages = chunk_source(acquired)
    investigation = build_corpus(
        topic="the outbreak of war",
        interpreted_question="How did the war break out?",
        geographic_scope=["Europe"],
        date_earliest=date(1914, 1, 1),
        date_latest=date(1914, 12, 31),
        acquired=[acquired],
        passages=passages,
    )
    package_path = tmp_path / f"{investigation.packageId}.json"
    package_path.write_text(
        json.dumps(investigation.model_dump(mode="json")), encoding="utf-8"
    )
    registry = _Registry()
    registry.register(
        CorpusSource(
            corpus_id=investigation.packageId,
            package_path=package_path,
            title="Acquired passage-only corpus",
            benchmark_role="test-only auto-acquired corpus",
            expected_package_id=investigation.packageId,
        )
    )
    corpus = registry.get_corpus(investigation.packageId)
    plan = InvestigationPlan(
        planId="plan-passages",
        runId="run-passages",
        corpusId=corpus.corpus_id,
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="How did the war break out?",
        questionType=QuestionType.DIRECT_EVIDENCE,
        plannedToolCalls=[
            PlannedToolCall(
                callId="search-call",
                toolName="search_passages",
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"query": "war", "maxResults": 1},
            )
        ],
    )
    bundle = InvestigationRunner(build_default_registry()).execute_initial(plan, corpus).bundle
    return plan, bundle


def test_analyst_schema_forces_inferred_synthesis_over_passage_only_evidence(tmp_path):
    # The DIRECT-grounding gap: over passage-only evidence the model must not be
    # allowed to claim EXTRACTED_RECORD/DIRECT (which cannot ground and forces an
    # abstention). Constrain every statement variant to evidence_synthesis +
    # inferred so the model is guided into a groundable, review-flagged synthesis.
    _plan, bundle = _passage_only_context(tmp_path)
    assert bundle.totalResultCount > 0  # passages were actually retrieved
    assert not bundle.referenceIndex.evidenceLinks  # and there are no evidence-links

    schema = build_analyst_response_schema(bundle)

    variants = schema["$defs"]["AnalysisStatement"]["oneOf"]
    assert variants
    for variant in variants:
        assert variant["properties"]["statementForm"] == {
            "const": "evidence_synthesis",
            "type": "string",
        }
        assert variant["properties"]["directness"] == {
            "const": "inferred",
            "type": "string",
        }


def test_analyst_schema_requires_a_synthesis_when_passages_were_retrieved(tmp_path):
    # Kamal's feedback: a simple factual question whose retrieval returned relevant
    # passages must yield a cited synthesis (the factors from the sources), not a
    # "not found" abstention. When citations exist the status cannot be abstained
    # and at least one statement is required. Genuine no-evidence still abstains
    # (covered by the citations-empty path / other tests).
    _plan, bundle = _passage_only_context(tmp_path)
    assert bundle.totalResultCount > 0

    schema = build_analyst_response_schema(bundle)

    assert "abstained" not in schema["$defs"]["AnswerStatus"]["enum"]
    assert schema["properties"]["statements"]["minItems"] >= 1


def test_analyst_schema_excludes_knowledge_kind_without_a_knowledge_basis(tmp_path):
    # A KNOWLEDGE statement needs a retrieved knowledge-state / awareness record
    # to ground (grounding._validate_knowledge). A passage-only bundle has none,
    # so the KNOWLEDGE variant is dropped -- the model cannot emit an ungroundable
    # knowledge claim that would only force an abstention.
    _plan, bundle = _passage_only_context(tmp_path)
    schema = build_analyst_response_schema(bundle)
    kinds = {
        variant["properties"]["statementKind"]["const"]
        for variant in schema["$defs"]["AnalysisStatement"]["oneOf"]
    }
    assert "knowledge" not in kinds
    assert kinds  # other kinds remain available


def test_analyst_schema_requires_truncation_disclosure_when_bundle_truncated(tmp_path):
    # grounding rejects an undisclosed truncation. When the bundle is truncated,
    # force a truncation-disclosure limitation into the draft so the model cannot
    # silently omit it.
    _plan, bundle = _passage_only_context(tmp_path)
    assert bundle.truncated or any(r.truncated for r in bundle.results)
    schema = build_analyst_response_schema(bundle)
    limitations = schema["properties"]["limitations"]
    disclosure = limitations["items"]["const"]
    assert "truncat" in disclosure.casefold()
    assert limitations["minItems"] >= 1


def test_analyst_schema_forbids_answered_status_when_bundle_partial(tmp_path):
    # A partial retrieval bundle cannot support an ANSWERED status (grounding).
    # Constrain the status enum so the model can only report partial/abstained.
    _plan, bundle = _passage_only_context(tmp_path)
    partial_bundle = bundle.model_copy(update={"partial": True})
    schema = build_analyst_response_schema(partial_bundle)
    assert "answered" not in schema["$defs"]["AnswerStatus"]["enum"]


def test_analyst_schema_allows_direct_extraction_when_evidence_links_present():
    # Curated corpora carrying evidence-links / directness metadata keep full
    # EXTRACTED_RECORD/DIRECT expressivity -- the synthesis constraint triggers
    # only when direct grounding is provably impossible.
    _plan, bundle, _draft = _context()
    assert bundle.referenceIndex.evidenceLinks  # this bundle has a direct basis

    schema = build_analyst_response_schema(bundle)

    for variant in schema["$defs"]["AnalysisStatement"]["oneOf"]:
        assert "const" not in variant["properties"]["statementForm"]
        assert "const" not in variant["properties"]["directness"]


def test_analyst_grounds_an_inferred_synthesis_over_passage_only_evidence(tmp_path):
    # The payoff: an inferred-synthesis statement citing a retrieved passage
    # passes deterministic grounding, so a passage-only corpus yields a cited
    # answer rather than only an abstention.
    plan, bundle = _passage_only_context(tmp_path)
    passage_id = bundle.referenceIndex.passageIds[0]
    draft = AnalysisDraft(
        analysisVersion="e3-analyst-v1",
        runId=plan.runId,
        planId=plan.planId,
        corpusId=plan.corpusId,
        status=AnswerStatus.ANSWERED,
        statements=[
            AnalysisStatement(
                statementId="s1",
                text="Read together, the retrieved passages indicate an assurance of support.",
                statementKind=StatementKind.FACT,
                statementForm=StatementForm.EVIDENCE_SYNTHESIS,
                basisRecordRefs=[passage_id],
                citations=[
                    AnalysisCitation(toolCallId="search-call", passageId=passage_id)
                ],
                directness=DirectnessAssessment.INFERRED,
                limitations=["Retrieval was truncated; reflects only returned passages."],
            )
        ],
    )
    provider = DeterministicModelProvider()
    provider.enqueue_value(draft)

    result = EvidenceAnalyst(provider).analyze("How did the war break out?", plan, bundle)

    assert result == draft


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
    # This claim-evidence bundle carries no knowledge-state / awareness record,
    # so a KNOWLEDGE statement could never ground: the variant is excluded.
    kinds = {
        variant["properties"]["statementKind"].get("const")
        for variant in statement_variants
    }
    assert "knowledge" not in kinds

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
