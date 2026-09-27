"""E10 analyst-schema compaction: the bundle-derived response schema is compacted
from per-record/per-kind ``oneOf`` variants to enum-constrained single objects.

These tests hold the compaction honest:
* **rejection parity** -- the same invalid citation/reference combinations that were
  rejected before are still rejected by the authoritative deterministic path
  (``validate_grounding`` + the Pydantic contract), not by the schema;
* **schema size** -- the citation/statement ``$defs`` are single objects, not ``oneOf``;
* **scaling** -- schema growth across increasing evidence breadth is linear (enum
  entries), not combinatorial (variant explosion), with no cliff under the budget.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus
from chronicle.ai.agents.analyst_schema import build_analyst_response_schema
from chronicle.ai.agents.grounding import validate_grounding
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
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.orchestration.policies import AgentExecutionPolicy
from chronicle.ai.orchestration.runner import InvestigationRunner
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import EvidenceLinkRole, RightsStatus, SourceType
from chronicle.corpus.manifest import CorpusRegistry, CorpusSource


def _corpus(tmp_path, body: str, *, paragraphs: int = 1):
    text = "\n\n".join(body for _ in range(paragraphs))
    candidate = SourceCandidate(
        candidateId="wikipedia:en:1", connector="wikipedia", title="Origins",
        sourceType=SourceType.TERTIARY_REFERENCE, fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED, url="https://example.org/1", language="en",
    )
    acquired = AcquiredSource(
        candidate=candidate, text=text, contentType="text/plain",
        contentSha256="hash-1", charCount=len(text),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )
    investigation = build_corpus(
        topic="the outbreak", interpreted_question="How did it start?",
        geographic_scope=["Europe"], date_earliest=date(1914, 1, 1),
        date_latest=date(1914, 12, 31), acquired=[acquired], passages=chunk_source(acquired),
    )
    path = tmp_path / f"{investigation.packageId}.json"
    path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")
    registry = CorpusRegistry()
    registry.register(
        CorpusSource(
            corpus_id=investigation.packageId, package_path=path, title="Acquired",
            benchmark_role="test", expected_package_id=investigation.packageId,
        )
    )
    return registry.get_corpus(investigation.packageId)


def _bundle(corpus, queries: list[str], *, max_results: int = 4, follow_up: str | None = None):
    calls = [
        PlannedToolCall(
            callId=f"call-{i}", toolName="search_passages",
            purposeCode=ToolPurpose.SEARCH_CONTEXT,
            arguments={"query": q, "maxResults": max_results},
        )
        for i, q in enumerate(queries)
    ]
    plan = InvestigationPlan(
        planId="plan-x", runId="run-x", corpusId=corpus.corpus_id,
        disposition=PlanDisposition.PROCEED, normalizedQuestion="How did it start?",
        questionType=QuestionType.DIRECT_EVIDENCE, plannedToolCalls=calls,
    )
    policy = AgentExecutionPolicy(maxResultsPerTool=max_results)
    runner = InvestigationRunner(build_default_registry(), policy=policy)
    bundle = runner.execute_initial(plan, corpus).bundle
    if follow_up is not None:
        # The 4th (total-budget) tool call is the finalization follow-up, not part
        # of the <=3 initial plan; reach maximum breadth the same way production does.
        follow_up_call = PlannedToolCall(
            callId="call-followup", toolName="search_passages",
            purposeCode=ToolPurpose.SEARCH_CONTEXT,
            arguments={"query": follow_up, "maxResults": max_results},
        )
        bundle = runner.execute_follow_up(plan, follow_up_call, corpus, bundle).bundle
    return plan, bundle


def _draft(plan, *, citations, basis) -> AnalysisDraft:
    """Build a single-statement draft (models are frozen, so invalid variants are
    constructed directly rather than mutated)."""
    return AnalysisDraft(
        analysisVersion="e3-analyst-v1", runId=plan.runId, planId=plan.planId,
        corpusId=plan.corpusId, status=AnswerStatus.PARTIAL,
        statements=[
            AnalysisStatement(
                statementId="s1",
                text="Read together, the retrieved passages describe the outbreak.",
                statementKind=StatementKind.FACT, statementForm=StatementForm.EVIDENCE_SYNTHESIS,
                basisRecordRefs=basis, citations=citations,
                directness=DirectnessAssessment.INFERRED,
                limitations=["Retrieval was truncated; reflects only returned passages."],
            )
        ],
        limitations=["Retrieval was truncated; reflects only returned passages."],
    )


def _valid_draft(plan, bundle) -> AnalysisDraft:
    passage_id = bundle.referenceIndex.passageIds[0]
    call_id = bundle.results[0].plannedCallId
    return _draft(
        plan,
        citations=[AnalysisCitation(toolCallId=call_id, passageId=passage_id)],
        basis=[passage_id],
    )


# --- rejection parity --------------------------------------------------------

def test_valid_inferred_synthesis_still_passes(tmp_path):
    corpus = _corpus(tmp_path, "War broke out in 1914 after the assurance of support. " * 12)
    plan, bundle = _bundle(corpus, ["war"], max_results=1)
    report = validate_grounding(_valid_draft(plan, bundle), plan, bundle)
    assert report.valid, [i.message for i in report.issues]


def test_unknown_tool_call_is_rejected(tmp_path):
    corpus = _corpus(tmp_path, "War broke out in 1914 after the assurance of support. " * 12)
    plan, bundle = _bundle(corpus, ["war"], max_results=1)
    passage_id = bundle.referenceIndex.passageIds[0]
    draft = _draft(
        plan,
        citations=[AnalysisCitation(toolCallId="ghost-call", passageId=passage_id)],
        basis=[passage_id],
    )
    report = validate_grounding(draft, plan, bundle)
    assert not report.valid and any(i.code.value == "unknown_tool_call" for i in report.issues)


def test_unknown_basis_record_is_rejected(tmp_path):
    corpus = _corpus(tmp_path, "War broke out in 1914 after the assurance of support. " * 12)
    plan, bundle = _bundle(corpus, ["war"], max_results=1)
    passage_id = bundle.referenceIndex.passageIds[0]
    call_id = bundle.results[0].plannedCallId
    draft = _draft(
        plan,
        citations=[AnalysisCitation(toolCallId=call_id, passageId=passage_id)],
        basis=["psg-9999-9999"],
    )
    report = validate_grounding(draft, plan, bundle)
    assert not report.valid and any(i.code.value == "unknown_record" for i in report.issues)


def test_record_not_returned_by_cited_call_is_rejected(tmp_path):
    corpus = _corpus(tmp_path, "War broke out in 1914 after the assurance of support. " * 12)
    plan, bundle = _bundle(corpus, ["war"], max_results=1)
    call_id = bundle.results[0].plannedCallId
    # A syntactically-real id that the cited call did not return.
    draft = _draft(
        plan,
        citations=[AnalysisCitation(toolCallId=call_id, passageId="psg-9999-9999")],
        basis=[bundle.referenceIndex.passageIds[0]],
    )
    report = validate_grounding(draft, plan, bundle)
    assert not report.valid and any(i.code.value == "unknown_record" for i in report.issues)


def test_role_without_evidence_link_is_rejected(tmp_path):
    corpus = _corpus(tmp_path, "War broke out in 1914 after the assurance of support. " * 12)
    plan, bundle = _bundle(corpus, ["war"], max_results=1)
    passage_id = bundle.referenceIndex.passageIds[0]
    call_id = bundle.results[0].plannedCallId
    draft = _draft(
        plan,
        citations=[
            AnalysisCitation(
                toolCallId=call_id, passageId=passage_id, role=EvidenceLinkRole.SUPPORTING
            )
        ],
        basis=[passage_id],
    )
    report = validate_grounding(draft, plan, bundle)
    assert not report.valid and any(i.code.value == "citation_mismatch" for i in report.issues)


def test_pydantic_rejects_knowledge_without_awareness():
    with pytest.raises(ValidationError):
        AnalysisStatement(
            statementId="s1", text="x", statementKind=StatementKind.KNOWLEDGE,
            statementForm=StatementForm.EVIDENCE_SYNTHESIS, basisRecordRefs=["p1"],
            citations=[AnalysisCitation(toolCallId="c", passageId="p1")],
            directness=DirectnessAssessment.INFERRED, knowledgeAwareness=None,
        )


def test_pydantic_rejects_synthesis_not_marked_inferred():
    with pytest.raises(ValidationError):
        AnalysisStatement(
            statementId="s1", text="x", statementKind=StatementKind.FACT,
            statementForm=StatementForm.EVIDENCE_SYNTHESIS, basisRecordRefs=["p1"],
            citations=[AnalysisCitation(toolCallId="c", passageId="p1")],
            directness=DirectnessAssessment.DIRECT,
        )


# --- schema shape / size -----------------------------------------------------

def test_citation_and_statement_are_single_objects_not_oneof(tmp_path):
    corpus = _corpus(tmp_path, "War broke out in 1914 after the assurance of support. " * 12)
    _plan, bundle = _bundle(corpus, ["war"], max_results=4)
    schema = build_analyst_response_schema(bundle)
    citation = schema["$defs"]["AnalysisCitation"]
    statement = schema["$defs"]["AnalysisStatement"]
    assert "oneOf" not in citation and citation["type"] == "object"
    assert "oneOf" not in statement and statement["type"] == "object"
    # Well under the earlier ~14.2k; leaves ample analyst-prompt headroom.
    assert len(json.dumps(schema, separators=(",", ":"))) < 9000


# --- scaling regression: no combinatorial cliff ------------------------------

def test_schema_growth_is_linear_across_breadth(tmp_path, capsys):
    # Eight short single-token passages. At the deployed per-tool budget (2 results
    # per search), 1..4 complementary searches (the #10 max is maxTotalToolCalls=4)
    # deterministically assemble 2..8 distinct records, spanning low breadth to the
    # realistic maximum -- so any hidden cliff above the 3-passage case would show.
    # Each paragraph is long enough to chunk into its own passage (~660 chars),
    # so the corpus has 8 distinct passages; at mr=2 a call stays under the 6000
    # per-tool character cap.
    paras = [
        f"recordtoken{i} evidence note number {i} about the outbreak. " * 12 for i in range(8)
    ]
    corpus = _corpus(tmp_path, "\n\n".join(paras))

    def pair_queries(pairs: int) -> list[str]:
        return [f"recordtoken{2 * j} recordtoken{2 * j + 1}" for j in range(pairs)]

    # 1..3 initial searches (plan cap) reach 2..6 records; the 8-record maximum
    # adds the one finalization follow-up (maxTotalToolCalls=4 x 2 results).
    levels = {
        2: (pair_queries(1), None),
        4: (pair_queries(2), None),
        6: (pair_queries(3), None),
        8: (pair_queries(3), "recordtoken6 recordtoken7"),
    }
    sizes: dict[int, dict[str, int]] = {}
    for target, (queries, follow_up) in levels.items():
        _plan, bundle = _bundle(corpus, queries, max_results=2, follow_up=follow_up)
        schema = build_analyst_response_schema(bundle)
        citation = schema["$defs"]["AnalysisCitation"]
        statement = schema["$defs"]["AnalysisStatement"]
        # Shape stays a single object at every breadth level.
        assert "oneOf" not in citation and "oneOf" not in statement
        sizes[target] = {
            "records": len(bundle.referenceIndex.passageIds)
            + len(bundle.referenceIndex.sourceIds)
            + len(bundle.referenceIndex.documentIds),
            "schema": len(json.dumps(schema, separators=(",", ":"))),
            "citation": len(json.dumps(citation, separators=(",", ":"))),
            "statement": len(json.dumps(statement, separators=(",", ":"))),
        }

    with capsys.disabled():
        print("\n  breadth | records | schema | citation | statement")
        for level in sorted(sizes):
            s = sizes[level]
            print(f"    ~{level:<4} | {s['records']:^7} | {s['schema']:^6} | {s['citation']:^8} | {s['statement']:^9}")

    low = min(sizes)
    # The statement object does not grow combinatorially with breadth (only its
    # basisRecordRefs enum grows), so it stays bounded and small.
    assert sizes[8]["statement"] < 2 * sizes[low]["statement"]
    # No cliff: the biggest breadth level's whole schema is still well under budget.
    assert sizes[8]["schema"] < 9000
    # Per-record schema growth is small (enum entries, not ~400-char variants).
    growth = sizes[8]["schema"] - sizes[low]["schema"]
    extra_records = max(1, sizes[8]["records"] - sizes[low]["records"])
    assert growth / extra_records < 200
