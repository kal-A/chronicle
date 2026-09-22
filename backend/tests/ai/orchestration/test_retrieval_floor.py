"""S1: the retrieval floor.

When a plan omits ``search_passages`` over a corpus that supports it, an opt-in
runner appends one bounded passage search so the analyst still sees the corpus
text — the fix for live investigations that abstained because the planner chose a
tool (e.g. get_map_context) that retrieved nothing. Off by default so
deterministic tests and the E7 harness are unchanged.
"""

from __future__ import annotations

from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.tools import build_default_registry
from chronicle.corpus import CorpusRegistry

_FLOOR_ID = "floor-search-passages"

_CLAIM_CALL = PlannedToolCall(
    callId="claim-call",
    toolName="get_claim_evidence",
    purposeCode=ToolPurpose.FIND_SUPPORT,
    arguments={"claimId": "claim-c1-assurance-reported"},
)
_SEARCH_CALL = PlannedToolCall(
    callId="search-call",
    toolName="search_passages",
    purposeCode=ToolPurpose.SEARCH_CONTEXT,
    arguments={"query": "assurance"},
)


def _plan_and_corpus(calls, run_id="run-floor"):
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")
    plan = InvestigationPlan(
        planId=f"plan-{run_id}",
        runId=run_id,
        corpusId=corpus.corpus_id,
        disposition=PlanDisposition.PROCEED,
        normalizedQuestion="What did the report say about the assurance?",
        questionType=QuestionType.DIRECT_EVIDENCE,
        plannedToolCalls=calls,
    )
    return plan, corpus


def test_floor_appends_passage_search_when_the_plan_omits_it():
    plan, corpus = _plan_and_corpus([_CLAIM_CALL])
    runner = InvestigationRunner(build_default_registry(), retrieval_floor=True)

    bundle = runner.execute_initial(plan, corpus).bundle

    floor_results = [r for r in bundle.results if r.plannedCallId == _FLOOR_ID]
    assert len(floor_results) == 1
    assert floor_results[0].callRecord.toolName == "search_passages"
    assert bundle.referenceIndex.passageIds  # the corpus text reached the bundle


def test_floor_is_off_by_default():
    plan, corpus = _plan_and_corpus([_CLAIM_CALL])
    bundle = InvestigationRunner(build_default_registry()).execute_initial(plan, corpus).bundle
    assert all(r.plannedCallId != _FLOOR_ID for r in bundle.results)


def test_floor_does_not_duplicate_an_existing_search():
    plan, corpus = _plan_and_corpus([_SEARCH_CALL])
    runner = InvestigationRunner(build_default_registry(), retrieval_floor=True)

    bundle = runner.execute_initial(plan, corpus).bundle

    assert all(r.plannedCallId != _FLOOR_ID for r in bundle.results)
    assert sum(r.callRecord.toolName == "search_passages" for r in bundle.results) == 1
