"""The shared boundary every E7 answer strategy is measured across.

Four strategies (single-prompt, basic-RAG, planner-analyst, full-workflow) run
the same case and return a normalized :class:`StrategyResult`. The runner and
metrics only ever see this boundary, so a strategy that uses fewer calls or less
evidence is still scored on identical terms. The concrete adapters live in
Task 4; this module defines only the types and the protocol they implement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.analysis import AnalysisCitation, AnswerStatus
from ..contracts.retrieval import RetrievedReferenceIndex
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


__all__ = [
    "EvaluationStatement",
    "ObservedStatement",
    "StrategyResult",
    "EvaluationInput",
    "EvaluationStrategy",
]
