from __future__ import annotations

import pytest
from pydantic import ValidationError

from chronicle.ai.contracts.analysis import AnswerStatus
from chronicle.ai.contracts.answer import AgentAnswer, AnswerValidationReport
from chronicle.ai.contracts.critique import (
    CriticDecision,
    CriticValidationReport,
    CriticVerdict,
)
from chronicle.ai.contracts.run import (
    AgentRunRecord,
    AgentStageName,
    CorpusSnapshot,
    InvestigationRequest,
)
from chronicle.ai.orchestration.statuses import AgentRunStatus


def _record(**updates) -> AgentRunRecord:
    values = {
        "runId": "run-e4",
        "request": InvestigationRequest(
            runId="run-e4",
            corpusId="blank-cheque-golden",
            userQuestion="What did the report say?",
        ),
        "corpusSnapshot": CorpusSnapshot(
            corpusId="blank-cheque-golden",
            packageId="blank-cheque-golden",
            packageHash="a" * 64,
            packageRevision=1,
            schemaVersion="1.0.0",
        ),
    }
    values.update(updates)
    return AgentRunRecord(**values)


def test_e4_run_record_persists_critic_and_final_answer_artifacts():
    decision = CriticDecision(
        criticVersion="e4-critic-v1",
        runId="run-e4",
        planId="plan-e4",
        corpusId="blank-cheque-golden",
        verdict=CriticVerdict.ABSTAIN,
        rationaleSummary="The bounded evidence is insufficient.",
    )
    answer = AgentAnswer(
        answerVersion="e4-guide-v1",
        runId="run-e4",
        planId="plan-e4",
        corpusId="blank-cheque-golden",
        status=AnswerStatus.ABSTAINED,
        directAnswer="Chronicle cannot answer reliably from this corpus.",
    )
    record = _record(
        status=AgentRunStatus.ANSWER_READY,
        criticDecisions=[decision],
        criticValidations=[CriticValidationReport(valid=True)],
        finalAnswer=answer,
        answerValidation=AnswerValidationReport(valid=True),
    )

    assert record.runtimeVersion == "e5-agent-runtime-v1"
    assert record.criticDecisions == [decision]
    assert record.finalAnswer == answer
    assert AgentStageName.CRITIC.value == "critic"
    assert AgentStageName.GUIDE.value == "guide"


def test_e4_run_record_rejects_cross_run_final_artifacts():
    decision = CriticDecision(
        criticVersion="e4-critic-v1",
        runId="another-run",
        planId="plan-e4",
        corpusId="blank-cheque-golden",
        verdict=CriticVerdict.ABSTAIN,
        rationaleSummary="Insufficient evidence.",
    )

    with pytest.raises(ValidationError, match="critic decision identity"):
        _record(criticDecisions=[decision])
