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
