"""The shared boundary every E7 answer strategy is measured across.

Four strategies (single-prompt, basic-RAG, planner-analyst, full-workflow) run
the same case and return a normalized :class:`StrategyResult`. The runner and
metrics only ever see this boundary, so a strategy that uses fewer calls or less
evidence is still scored on identical terms. The concrete adapters live in
Task 4; this module defines only the types and the protocol they implement.
"""

from __future__ import annotations

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from ..agents import (
    EvidenceAnalyst,
    InvestigationPlanner,
)
from ..agents.analyst import AnalystValidationError
from ..agents.planner import PlannerValidationError
from ..contracts.analysis import AnalysisCitation, AnswerStatus
from ..contracts.plan import PlanDisposition
from ..contracts.retrieval import RetrievedReferenceIndex
from ..contracts.run import (
    AgentRunRecord,
    CorpusSnapshot,
    InvestigationRequest,
    WorkspaceContextSnapshot,
)
from ...corpus.contracts import DEFAULT_RESULT_COUNT, PassageSearchRequest
from ..models.metadata import ModelCallRecord
from ..orchestration.factory import build_default_workflow
from ..orchestration.policies import AgentExecutionPolicy
from ..orchestration.runner import InvestigationRunner
from ..orchestration.statuses import AgentRunStatus
from ..tools import build_default_registry
from .baseline_prompts import (
    BASIC_RAG_PROMPT_VERSION,
    SINGLE_PROMPT_PROMPT_VERSION,
    EvaluationAnswer,
    basic_rag_system,
    basic_rag_user,
    build_single_prompt_context,
    single_prompt_system,
    single_prompt_user,
)
from .contracts import StrategyId

if TYPE_CHECKING:  # opaque handles / annotations only -- not needed at runtime
    from ...corpus.protocol import InvestigationCorpus
    from ..models.protocol import ModelProvider
    from .contracts import EvaluationCase


class EvaluationStatement(BaseModel):
    """One normalized statement an answer asserts, with its citations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    statementId: str = Field(min_length=1)
    text: str
    citations: tuple[AnalysisCitation, ...] = ()


class ObservedStatement(BaseModel):
    """A raw declarative span mapped back to a normalized statement (or left
    unmapped). Preserves exact text and origin so nothing silently drops out of
    the statement denominator during scoring."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observedStatementId: str = Field(min_length=1)
    text: str
    sourceField: str
    originStatementIds: tuple[str, ...] = ()
    citationIds: tuple[str, ...] = ()
    duplicateGroupId: str | None = None


class StrategyResult(BaseModel):
    """The normalized, comparable outcome of one strategy on one case/repeat."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    caseId: str
    strategyId: StrategyId
    corpusId: str
    answerStatus: AnswerStatus
    answerText: str
    statements: tuple[EvaluationStatement, ...] = ()
    references: RetrievedReferenceIndex | None = None
    modelCallCount: int = Field(ge=0)
    latencyMs: float = Field(ge=0)
    # Identity: what produced this result, for auditability and resume matching.
    benchmarkVersion: str
    providerName: str
    providerVersion: str
    modelName: str
    promptVersions: tuple[str, ...] = ()
    repeat: int = Field(default=0, ge=0)


@dataclass(frozen=True)
class EvaluationInput:
    """One unit of work: a case, the corpus snapshot to run it over, the model
    provider, and the repeat index. Corpus and provider are opaque handles."""

    case: "EvaluationCase"
    corpus: "InvestigationCorpus"
    provider: "ModelProvider"
    repeat: int = 0


@runtime_checkable
class EvaluationStrategy(Protocol):
    """A comparable answer strategy. Adapters wrap existing orchestration; they
    never rewrite an answer to score better and never read gold rubric fields."""

    id: StrategyId

    def run(self, evaluation_input: EvaluationInput) -> StrategyResult: ...


# --- shared adapter helpers ------------------------------------------------


def _run_id(case: "EvaluationCase", strategy: StrategyId, repeat: int) -> str:
    return f"eval-{strategy.value}-{case.caseId}-r{repeat}"


def _corpus_snapshot(corpus: "InvestigationCorpus") -> CorpusSnapshot:
    manifest = corpus.get_manifest()
    investigation = corpus.get_investigation()
    return CorpusSnapshot(
        corpusId=corpus.corpus_id,
        packageId=investigation.packageId,
        packageHash=manifest.packageHash,
        packageRevision=investigation.packageRevision,
        schemaVersion=investigation.schemaVersion,
        capabilities=tuple(manifest.supportedCapabilities),
        knownOmissions=tuple(manifest.knownOmissions),
    )


def _request(case: "EvaluationCase", corpus: "InvestigationCorpus", run_id: str) -> InvestigationRequest:
    return InvestigationRequest(
        runId=run_id,
        corpusId=corpus.corpus_id,
        userQuestion=case.question,
        workspaceContext=WorkspaceContextSnapshot(selectedRecords=()),
    )


def _model_name(model_calls: list[ModelCallRecord]) -> str:
    return model_calls[-1].modelName if model_calls else "unknown"


def _identity_fields(
    case: "EvaluationCase",
    provider: "ModelProvider",
    model_calls: list[ModelCallRecord],
) -> dict:
    metadata = provider.provider_metadata
    return {
        "benchmarkVersion": case.benchmarkVersion,
        "providerName": metadata.providerName,
        "providerVersion": metadata.providerVersion,
        "modelName": _model_name(model_calls),
        "promptVersions": tuple(dict.fromkeys(mc.promptVersion for mc in model_calls)),
    }


# --- agent-wrapping adapters ----------------------------------------------


class PlannerAnalystStrategy:
    """Planner -> typed retrieval -> Analyst, stopping before Critic/Guide.
    Evaluates the grounded ``AnalysisDraft`` directly; actions are unavailable."""

    id = StrategyId.PLANNER_ANALYST

    def run(self, evaluation_input: EvaluationInput) -> StrategyResult:
        case, corpus, provider, repeat = (
            evaluation_input.case,
            evaluation_input.corpus,
            evaluation_input.provider,
            evaluation_input.repeat,
        )
        run_id = _run_id(case, self.id, repeat)
        registry = build_default_registry()
        runner = InvestigationRunner(registry)
        planner = InvestigationPlanner(provider)
        analyst = EvidenceAnalyst(provider)
        model_calls: list[ModelCallRecord] = []
        started = time.perf_counter()

        try:
            plan = planner.plan(_request(case, corpus, run_id), _corpus_snapshot(corpus), registry.list_specs())
        except PlannerValidationError as exc:
            if exc.modelCall is not None:
                model_calls.append(exc.modelCall)
            return self._abstained(case, provider, model_calls, started, str(exc), references=None)
        if planner.last_execution is not None:
            model_calls.append(planner.last_execution.modelCall)
        if plan.disposition is PlanDisposition.ABSTAIN:
            return self._abstained(
                case, provider, model_calls, started, plan.unsupportedReason or "planner abstained", references=None
            )

        bundle = runner.execute_initial(plan, corpus).bundle
        try:
            draft = analyst.analyze(case.question, plan, bundle)
        except AnalystValidationError as exc:
            if exc.modelCall is not None:
                model_calls.append(exc.modelCall)
            return self._abstained(
                case, provider, model_calls, started,
                exc.validationReport.model_dump_json() if exc.validationReport else str(exc),
                references=bundle.referenceIndex,
            )
        if analyst.last_execution is not None:
            model_calls.append(analyst.last_execution.modelCall)

        statements = tuple(
            EvaluationStatement(statementId=s.statementId, text=s.text, citations=tuple(s.citations))
            for s in draft.statements
        )
        return StrategyResult(
            caseId=case.caseId,
            strategyId=self.id,
            corpusId=corpus.corpus_id,
            answerStatus=draft.status,
            answerText=draft.abstentionReason or "",
            statements=statements,
            references=bundle.referenceIndex,
            modelCallCount=len(model_calls),
            latencyMs=(time.perf_counter() - started) * 1000,
            repeat=repeat,
            **_identity_fields(case, provider, model_calls),
        )

    def _abstained(self, case, provider, model_calls, started, reason, *, references) -> StrategyResult:
        return StrategyResult(
            caseId=case.caseId,
            strategyId=self.id,
            corpusId=case.corpusId,
            answerStatus=AnswerStatus.ABSTAINED,
            answerText=reason[:4000],
            statements=(),
            references=references,
            modelCallCount=len(model_calls),
            latencyMs=(time.perf_counter() - started) * 1000,
            repeat=0,
            **_identity_fields(case, provider, model_calls),
        )


class FullWorkflowStrategy:
    """The production LangGraph workflow: Planner -> retrieval -> Analyst ->
    Critic -> Guide. Evaluates the validated ``AgentAnswer`` (or the run's
    principled abstention)."""

    id = StrategyId.FULL_WORKFLOW

    def run(self, evaluation_input: EvaluationInput) -> StrategyResult:
        # Imported here to avoid a hard import-time dependency on the file-based
        # store for callers that only use the other adapters.
        from ...storage.agent_run_store import AgentRunStore

        case, corpus, provider, repeat = (
            evaluation_input.case,
            evaluation_input.corpus,
            evaluation_input.provider,
            evaluation_input.repeat,
        )
        run_id = _run_id(case, self.id, repeat)
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="chronicle-eval-") as tmp:
            store = AgentRunStore(Path(tmp))
            # Built by the shared factory so the evaluated workflow is the same
            # configuration the deployed API runs (policy/budgets, retrieval
            # floor, COMPACT planner specs) -- not a parallel eval-only config.
            workflow = build_default_workflow(provider, store)
            record = AgentRunRecord(
                runId=run_id,
                request=_request(case, corpus, run_id),
                corpusSnapshot=_corpus_snapshot(corpus),
            )
            result = workflow.run(record, corpus)

        latency = (time.perf_counter() - started) * 1000
        model_calls = list(result.modelCalls)
        references = result.retrievalBundle.referenceIndex if result.retrievalBundle else None
        answer = result.finalAnswer
        if result.status is AgentRunStatus.ANSWER_READY and answer is not None:
            citations_by_statement: dict[str, list[AnalysisCitation]] = {}
            for entry in answer.citations:
                citations_by_statement.setdefault(entry.statementId, []).append(entry.citation)
            statements = tuple(
                EvaluationStatement(
                    statementId=point.statementId,
                    text=point.text,
                    citations=tuple(citations_by_statement.get(point.statementId, ())),
                )
                for point in [*answer.keyPoints, *answer.disagreements]
            )
            answer_status = answer.status
            answer_text = answer.directAnswer
        else:
            statements = ()
            answer_status = AnswerStatus.ABSTAINED
            answer_text = result.abstentionReason or ""

        return StrategyResult(
            caseId=case.caseId,
            strategyId=self.id,
            corpusId=corpus.corpus_id,
            answerStatus=answer_status,
            answerText=answer_text,
            statements=statements,
            references=references,
            modelCallCount=len(model_calls),
            latencyMs=latency,
            repeat=repeat,
            **_identity_fields(case, provider, model_calls),
        )


# --- baseline adapters -----------------------------------------------------


def _baseline_result(
    case: "EvaluationCase",
    strategy_id: StrategyId,
    provider: "ModelProvider",
    generated,
    *,
    references: RetrievedReferenceIndex | None,
    started: float,
    repeat: int,
) -> StrategyResult:
    answer: EvaluationAnswer = generated.value
    model_calls = [generated.modelCall]
    statements = tuple(
        EvaluationStatement(statementId=f"s-{index + 1}", text=item.text, citations=tuple(item.citations))
        for index, item in enumerate(answer.statements)
    )
    return StrategyResult(
        caseId=case.caseId,
        strategyId=strategy_id,
        corpusId=case.corpusId,
        answerStatus=answer.status,
        answerText=answer.directAnswer,
        statements=statements,
        references=references,
        modelCallCount=len(model_calls),
        latencyMs=(time.perf_counter() - started) * 1000,
        repeat=repeat,
        **_identity_fields(case, provider, model_calls),
    )


def _index_from_hits(hits) -> RetrievedReferenceIndex:
    passage_ids, source_ids, document_ids, links = [], [], [], []
    for hit in hits:
        passage_ids.append(hit.passageId)
        source_ids.append(hit.sourceId)
        document_ids.append(hit.documentId)
        links.extend(hit.evidenceLinks)
    return RetrievedReferenceIndex(
        evidenceLinks=list(links)[:16],
        passageIds=tuple(passage_ids),
        sourceIds=tuple(source_ids),
        documentIds=tuple(document_ids),
    )


class SinglePromptStrategy:
    """One model call over a retrieval-free, deterministically selected corpus
    context. No typed tool or agent role is used."""

    id = StrategyId.SINGLE_PROMPT

    def run(self, evaluation_input: EvaluationInput) -> StrategyResult:
        case, corpus, provider, repeat = (
            evaluation_input.case,
            evaluation_input.corpus,
            evaluation_input.provider,
            evaluation_input.repeat,
        )
        budget = AgentExecutionPolicy().maxAggregateRetrievalCharacters
        context, _included = build_single_prompt_context(corpus, budget, case.benchmarkVersion)
        started = time.perf_counter()
        generated = provider.generate_structured(
            system_prompt=single_prompt_system(),
            user_prompt=single_prompt_user(case.question, context),
            response_model=EvaluationAnswer,
            prompt_version=SINGLE_PROMPT_PROMPT_VERSION,
        )
        return _baseline_result(
            case, self.id, provider, generated, references=None, started=started, repeat=repeat
        )


class BasicRagStrategy:
    """Deterministic search_passages retrieval under the production result cap,
    then one model answer call. No planner or agent roles."""

    id = StrategyId.BASIC_RAG

    def run(self, evaluation_input: EvaluationInput) -> StrategyResult:
        case, corpus, provider, repeat = (
            evaluation_input.case,
            evaluation_input.corpus,
            evaluation_input.provider,
            evaluation_input.repeat,
        )
        started = time.perf_counter()
        search = corpus.search_passages(
            PassageSearchRequest(
                corpusId=corpus.corpus_id, query=case.question, maxResults=DEFAULT_RESULT_COUNT
            )
        )
        retrieved = "\n".join(
            f"[passage {hit.passageId} | source {hit.sourceId}] {hit.excerpt}" for hit in search.hits
        )
        generated = provider.generate_structured(
            system_prompt=basic_rag_system(),
            user_prompt=basic_rag_user(case.question, retrieved),
            response_model=EvaluationAnswer,
            prompt_version=BASIC_RAG_PROMPT_VERSION,
        )
        return _baseline_result(
            case, self.id, provider, generated,
            references=_index_from_hits(search.hits), started=started, repeat=repeat,
        )


def build_strategies() -> dict[StrategyId, EvaluationStrategy]:
    """All four comparable strategy adapters keyed by id."""

    return {
        StrategyId.SINGLE_PROMPT: SinglePromptStrategy(),
        StrategyId.BASIC_RAG: BasicRagStrategy(),
        StrategyId.PLANNER_ANALYST: PlannerAnalystStrategy(),
        StrategyId.FULL_WORKFLOW: FullWorkflowStrategy(),
    }


__all__ = [
    "EvaluationStatement",
    "ObservedStatement",
    "StrategyResult",
    "EvaluationInput",
    "EvaluationStrategy",
    "SinglePromptStrategy",
    "BasicRagStrategy",
    "PlannerAnalystStrategy",
    "FullWorkflowStrategy",
    "build_strategies",
]
