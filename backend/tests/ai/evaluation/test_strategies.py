"""Shared strategy-boundary contract tests (E7 Slice 1, Task 3).

These cover only the normalized result boundary and the strategy protocol; the
four concrete adapters and their deterministic-provider runs arrive in Task 4.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from chronicle.ai.contracts.analysis import AnswerStatus
from chronicle.ai.evaluation.contracts import StrategyId
from chronicle.ai.evaluation.strategies import (
    EvaluationStatement,
    EvaluationStrategy,
    StrategyResult,
)


def _result(**kw) -> StrategyResult:
    base = dict(
        caseId="direct-reported-assurance",
        strategyId=StrategyId.SINGLE_PROMPT,
        corpusId="blank-cheque-golden",
        answerStatus=AnswerStatus.ANSWERED,
        answerText="A cited answer.",
        statements=(),
        references=None,
        modelCallCount=1,
        latencyMs=1.0,
        benchmarkVersion="e7-v1",
        providerName="deterministic",
        providerVersion="e1-deterministic-v1",
        modelName="deterministic-test-model",
        promptVersions=("single-prompt-v1",),
        repeat=0,
    )
    base.update(kw)
    return StrategyResult(**base)


def test_strategy_result_is_frozen_and_carries_identity():
    result = _result()
    assert result.strategyId is StrategyId.SINGLE_PROMPT
    assert result.benchmarkVersion == "e7-v1"
    with pytest.raises(ValidationError):
        result.answerText = "mutated"  # frozen


def test_strategy_result_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        _result(unexpected="x")


def test_evaluation_statement_holds_normalized_text_and_citations():
    statement = EvaluationStatement(statementId="s-1", text="A claim.", citations=())
    assert statement.statementId == "s-1"


def test_evaluation_strategy_is_runtime_checkable():
    class _Stub:
        id = StrategyId.SINGLE_PROMPT

        def run(self, evaluation_input):  # pragma: no cover - structural check only
            raise NotImplementedError

    assert isinstance(_Stub(), EvaluationStrategy)
    assert not isinstance(object(), EvaluationStrategy)


# --- agent-wrapping adapters (Task 4a) -------------------------------------

from chronicle.ai.contracts.analysis import (
    AnalysisCitation,
    AnalysisDraft,
    AnalysisStatement,
    DirectnessAssessment,
    StatementForm,
    StatementKind,
)
from chronicle.ai.contracts.critique import CriticDecision, CriticVerdict
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.evaluation.benchmark import load_evaluation_benchmark
from chronicle.ai.evaluation.strategies import EvaluationInput, _run_id, build_strategies
from chronicle.ai.models import DeterministicModelProvider
from chronicle.ai.orchestration.factory import default_execution_policy
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import EvidenceLinkRole
from chronicle.corpus import CorpusRegistry


def _case(slug: str):
    return next(c for c in load_evaluation_benchmark() if c.caseId == slug)


def _cold_fixture(corpus, run_id: str):
    """A cold-question fixture: a search_passages plan (authorized without a
    workspace selection, unlike the get_claim_evidence path) grounded against a
    real retrieval bundle, plus an approving critic decision. Mirrors an actual
    evaluation run, where no record is pre-selected."""
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
                callId="search",
                toolName="search_passages",
                purposeCode=ToolPurpose.FIND_SUPPORT,
                arguments={"query": "support"},
            )
        ],
    )
    # Compute the expected evidence link under the shared production retrieval
    # config (default_execution_policy + floor) that the full_workflow strategy
    # now uses, so the scripted citation resolves against the workflow's real
    # bundle. The top hit is also present in the simpler planner_analyst bundle.
    bundle = (
        InvestigationRunner(
            registry, policy=default_execution_policy(), retrieval_floor=True
        )
        .execute_initial(plan, corpus)
        .bundle
    )
    link = bundle.referenceIndex.evidenceLinks[0]
    statement = AnalysisStatement(
        statementId="statement-1",
        text="The retrieved report records an assurance of support.",
        statementKind=StatementKind.FACT,
        statementForm=StatementForm.EXTRACTED_RECORD,
        basisRecordRefs=[link.targetId],
        citations=[
            AnalysisCitation(
                toolCallId="search",
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
        corpusId=corpus.corpus_id,
        status=AnswerStatus.ANSWERED,
        statements=[statement],
        # Under the shared production policy the aggregate retrieval window is
        # capped, so this bundle is truncated; a valid grounded draft must
        # disclose that (grounding rejects an undisclosed truncation). Harmless
        # for the non-truncating planner_analyst baseline that shares this fixture.
        limitations=[
            "Retrieval was truncated; this reflects only the returned records, not the full corpus."
        ],
    )
    decision = CriticDecision(
        criticVersion="e4-critic-v1",
        runId=run_id,
        planId=plan.planId,
        corpusId=corpus.corpus_id,
        verdict=CriticVerdict.APPROVE,
        acceptedStatementIds=[statement.statementId],
        rationaleSummary="The statement is grounded and appropriately bounded.",
    )
    return plan, draft, decision


def test_build_strategies_exposes_the_agent_adapters_as_the_protocol():
    strategies = build_strategies()
    assert StrategyId.PLANNER_ANALYST in strategies
    assert StrategyId.FULL_WORKFLOW in strategies
    assert all(isinstance(s, EvaluationStrategy) for s in strategies.values())
    assert all(s.id is key for key, s in strategies.items())


def test_planner_analyst_adapter_produces_grounded_statements():
    case = _case("direct-reported-assurance")
    corpus = CorpusRegistry().get_corpus(case.corpusId)
    # The plan carries the run identity the adapter builds for the request; the
    # planner enforces plan.runId == request.runId, exactly as in production.
    plan, draft, _decision = _cold_fixture(corpus, _run_id(case, StrategyId.PLANNER_ANALYST, 0))
    provider = DeterministicModelProvider()
    provider.enqueue_value(plan)
    provider.enqueue_value(draft)

    result = build_strategies()[StrategyId.PLANNER_ANALYST].run(
        EvaluationInput(case=case, corpus=corpus, provider=provider)
    )

    assert result.strategyId is StrategyId.PLANNER_ANALYST
    assert result.answerStatus is AnswerStatus.ANSWERED
    assert result.statements and result.statements[0].citations
    assert result.references is not None
    assert result.modelCallCount == 2  # planner + analyst; retrieval is not a model call
    assert result.providerName == "deterministic"


def test_full_workflow_adapter_normalizes_the_validated_answer():
    case = _case("direct-reported-assurance")
    corpus = CorpusRegistry().get_corpus(case.corpusId)
    plan, draft, decision = _cold_fixture(corpus, _run_id(case, StrategyId.FULL_WORKFLOW, 0))
    provider = DeterministicModelProvider()
    for value in (plan, draft, decision):  # Guide composes deterministically (no model call)
        provider.enqueue_value(value)

    result = build_strategies()[StrategyId.FULL_WORKFLOW].run(
        EvaluationInput(case=case, corpus=corpus, provider=provider)
    )

    assert result.strategyId is StrategyId.FULL_WORKFLOW
    assert result.answerStatus is AnswerStatus.ANSWERED
    assert result.answerText  # the Guide's composed directAnswer
    assert result.statements and result.statements[0].citations
    assert result.modelCallCount == 3  # planner + analyst + critic


def test_full_workflow_adapter_reports_abstention_as_a_result_not_a_crash():
    case = _case("direct-reported-assurance")
    corpus = CorpusRegistry().get_corpus(case.corpusId)
    plan, draft, _decision = _cold_fixture(corpus, _run_id(case, StrategyId.FULL_WORKFLOW, 0))
    provider = DeterministicModelProvider()
    provider.enqueue_value(plan)
    provider.enqueue_value(draft)
    provider.enqueue_malformed("critic cannot comply")
    provider.enqueue_malformed("critic still cannot comply")

    result = build_strategies()[StrategyId.FULL_WORKFLOW].run(
        EvaluationInput(case=case, corpus=corpus, provider=provider)
    )

    assert result.answerStatus is AnswerStatus.ABSTAINED
    assert result.statements == ()


# --- baseline adapters (Task 4b) -------------------------------------------

from chronicle.ai.evaluation.baseline_prompts import (
    EvaluationAnswer,
    EvaluationAnswerStatement,
    build_single_prompt_context,
    single_prompt_system,
    single_prompt_user,
)
from chronicle.ai.orchestration.policies import AgentExecutionPolicy


def _baseline_answer() -> EvaluationAnswer:
    return EvaluationAnswer(
        status=AnswerStatus.ANSWERED,
        directAnswer="The report records an assurance of support.",
        statements=[
            EvaluationAnswerStatement(
                text="The report records an assurance of support.",
                citations=[AnalysisCitation(toolCallId="baseline", passageId="jc-src-002-p1")],
            )
        ],
    )


def test_single_prompt_adapter_answers_without_retrieval():
    case = _case("direct-reported-assurance")
    corpus = CorpusRegistry().get_corpus(case.corpusId)
    provider = DeterministicModelProvider()
    provider.enqueue_value(_baseline_answer())

    result = build_strategies()[StrategyId.SINGLE_PROMPT].run(
        EvaluationInput(case=case, corpus=corpus, provider=provider)
    )

    assert result.strategyId is StrategyId.SINGLE_PROMPT
    assert result.answerStatus is AnswerStatus.ANSWERED
    assert result.statements and result.statements[0].statementId == "s-1"
    assert result.references is None  # single prompt performs no retrieval
    assert result.modelCallCount == 1


def test_single_prompt_never_calls_search_passages(monkeypatch):
    case = _case("direct-reported-assurance")
    corpus = CorpusRegistry().get_corpus(case.corpusId)

    def _boom(*args, **kwargs):
        raise AssertionError("single_prompt must not retrieve")

    monkeypatch.setattr(corpus, "search_passages", _boom)
    provider = DeterministicModelProvider()
    provider.enqueue_value(_baseline_answer())

    result = build_strategies()[StrategyId.SINGLE_PROMPT].run(
        EvaluationInput(case=case, corpus=corpus, provider=provider)
    )

    assert result.answerStatus is AnswerStatus.ANSWERED


def test_basic_rag_adapter_retrieves_then_answers():
    case = _case("direct-reported-assurance")
    corpus = CorpusRegistry().get_corpus(case.corpusId)
    provider = DeterministicModelProvider()
    provider.enqueue_value(_baseline_answer())

    result = build_strategies()[StrategyId.BASIC_RAG].run(
        EvaluationInput(case=case, corpus=corpus, provider=provider)
    )

    assert result.strategyId is StrategyId.BASIC_RAG
    assert result.answerStatus is AnswerStatus.ANSWERED
    assert result.references is not None  # retrieval produced a reference index
    assert result.modelCallCount == 1


def test_no_gold_rubric_field_reaches_a_baseline_prompt():
    case = _case("missing-consistency-verification")  # carries an unacceptableClaims rubric
    assert case.unacceptableClaims  # sanity: this case has a gold claim to leak
    corpus = CorpusRegistry().get_corpus(case.corpusId)
    context, _ = build_single_prompt_context(
        corpus, AgentExecutionPolicy().maxAggregateRetrievalCharacters, case.benchmarkVersion
    )
    prompt = single_prompt_system() + "\n" + single_prompt_user(case.question, context)

    for phrase in case.unacceptableClaims:
        assert phrase not in prompt
    assert "expectedAbstention" not in prompt
    assert "unacceptableClaims" not in prompt
