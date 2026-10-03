"""E10: the deterministic breadth backstop.

Over a passages-only *draft* corpus the runner ensures several complementary
``search_passages`` calls (up to the initial tool-call budget) so a plan that
under-decomposes an evidence-seeking question still assembles complementary
evidence. Curated/synthesized corpora are untouched. Deterministic -- no model.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus
from chronicle.ai.contracts.plan import (
    InvestigationPlan,
    PlanDisposition,
    PlannedToolCall,
    QuestionType,
    ToolPurpose,
)
from chronicle.ai.orchestration.factory import default_execution_policy
from chronicle.ai.orchestration.runner import (
    InvestigationRunner,
    _derive_breadth_queries,
    _is_analytical_question,
    _subject_anchor,
)
from chronicle.ai.tools import build_default_registry
from chronicle.contracts.enums import RightsStatus, SourceType
from chronicle.corpus import CorpusRegistry
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import PackageBackedCorpus

_QUESTION = "How did the coastal blockade shape the naval campaign strategy and supply lines"
_FACTOID = "When was the coastal blockade naval campaign established"
_SEARCH = "search_passages"


def _source(cid: str, title: str, text: str) -> AcquiredSource:
    candidate = SourceCandidate(
        candidateId=cid, connector="wikipedia", title=title,
        sourceType=SourceType.TERTIARY_REFERENCE, fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED, url=f"https://example.org/{cid}", language="en",
    )
    return AcquiredSource(
        candidate=candidate, text=text, contentType="text/plain",
        contentSha256=f"h-{cid}", charCount=len(text),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def _draft_corpus(tmp_path) -> PackageBackedCorpus:
    sources = [
        _source("s1", "Blockade", "The coastal blockade sealed the ports and cut supply lines. " * 20),
        _source("s2", "Campaign", "The naval campaign strategy shifted after the river offensive. " * 20),
    ]
    passages = []
    for s in sources:
        passages.extend(chunk_source(s))
    investigation = build_corpus(
        topic="a naval campaign", interpreted_question=_QUESTION,
        geographic_scope=["Region"], date_earliest=date(1860, 1, 1),
        date_latest=date(1865, 12, 31), acquired=sources, passages=passages,
    )
    path = tmp_path / "draft.json"
    path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")
    return PackageBackedCorpus.load(
        corpus_id="draft", package_path=path, title="Draft", benchmark_role="test"
    )


def _magnet_corpus(tmp_path) -> PackageBackedCorpus:
    """A draft corpus with several distinct passages that all share the query terms,
    so excluding the top hit still leaves eligible distinct passages to fall through to."""
    blocks = [
        f"The coastal blockade cut supply lines, detail {word} for the evidence record. " * 12
        for word in ("one", "two", "three", "four")
    ]
    sources = [_source("s1", "Blockade", "\n\n".join(blocks))]
    passages = []
    for s in sources:
        passages.extend(chunk_source(s))
    investigation = build_corpus(
        topic="a naval campaign", interpreted_question=_QUESTION,
        geographic_scope=["Region"], date_earliest=date(1860, 1, 1),
        date_latest=date(1865, 12, 31), acquired=sources, passages=passages,
    )
    path = tmp_path / "magnet.json"
    path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")
    return PackageBackedCorpus.load(
        corpus_id="magnet", package_path=path, title="Magnet", benchmark_role="test"
    )


def _proceed_plan(corpus_id: str, queries: list[str]) -> InvestigationPlan:
    calls = [
        PlannedToolCall(
            callId=f"call-{i}", toolName=_SEARCH, purposeCode=ToolPurpose.SEARCH_CONTEXT,
            arguments={"query": q, "maxResults": 2},
        )
        for i, q in enumerate(queries)
    ]
    return InvestigationPlan(
        planId="plan-b", runId="run-b", corpusId=corpus_id,
        disposition=PlanDisposition.PROCEED, normalizedQuestion=_QUESTION,
        questionType=QuestionType.DIRECT_EVIDENCE, plannedToolCalls=calls,
    )


def _runner() -> InvestigationRunner:
    return InvestigationRunner(
        build_default_registry(), policy=default_execution_policy(), retrieval_floor=True
    )


def test_breadth_backstop_expands_single_search_over_draft(tmp_path):
    corpus = _draft_corpus(tmp_path)
    plan = _proceed_plan(corpus.corpus_id, ["coastal blockade strategy"])

    augmented = _runner()._augment_with_floor(plan, corpus, plan.plannedToolCalls)

    searches = [c for c in augmented if c.toolName == _SEARCH]
    assert len(searches) == default_execution_policy().maxInitialToolCalls  # 3
    queries = [c.arguments["query"].casefold() for c in searches]
    assert len(set(queries)) == len(queries)  # all distinct
    assert len({c.callId for c in augmented}) == len(augmented)  # unique callIds


def test_breadth_backstop_noop_when_already_at_budget(tmp_path):
    corpus = _draft_corpus(tmp_path)
    plan = _proceed_plan(corpus.corpus_id, ["one blockade", "two campaign", "three supply"])

    augmented = _runner()._augment_with_floor(plan, corpus, plan.plannedToolCalls)

    assert len([c for c in augmented if c.toolName == _SEARCH]) == 3
    assert augmented == plan.plannedToolCalls  # unchanged


def test_breadth_backstop_skips_curated_corpus():
    corpus = CorpusRegistry().get_corpus("blank-cheque-golden")  # curated: claims/relationships
    plan = _proceed_plan(corpus.corpus_id, ["assurance report"])

    augmented = _runner()._augment_with_floor(plan, corpus, plan.plannedToolCalls)

    assert len([c for c in augmented if c.toolName == _SEARCH]) == 1  # no breadth added


def test_breadth_backstop_executes_multiple_searches_end_to_end(tmp_path):
    corpus = _draft_corpus(tmp_path)
    plan = _proceed_plan(corpus.corpus_id, ["coastal blockade"])

    bundle = _runner().execute_initial(plan, corpus).bundle

    executed_searches = [r for r in bundle.results if r.callRecord.toolName == _SEARCH]
    assert len(executed_searches) == 3
    # Distinct passages actually reach the bundle (breadth is real, not a re-run).
    assert len(bundle.referenceIndex.passageIds) >= 2


def test_derive_breadth_queries_are_distinct_and_non_empty():
    derived = _derive_breadth_queries(_QUESTION, ["coastal blockade strategy"], 2)
    assert len(derived) == 2
    assert all(q.strip() for q in derived)
    assert len({q.casefold() for q in derived}) == 2
    assert "coastal blockade strategy" not in {q.casefold() for q in derived}


def test_derive_breadth_queries_empty_when_no_salient_tokens():
    assert _derive_breadth_queries("how did it", [], 2) == []
    assert _derive_breadth_queries(_QUESTION, [], 0) == []


def test_derived_queries_share_a_subject_anchor_and_vary_by_facet():
    anchor = _subject_anchor(_QUESTION)
    derived = _derive_breadth_queries(_QUESTION, [], 2)

    assert anchor and all(q.startswith(anchor + " ") for q in derived)
    # The varying remainder (the evidence-facet cue) is distinct per query, and is
    # not just a chunk of the question's own words (the old token-partition bug).
    facet_cues = [q[len(anchor) + 1 :] for q in derived]
    assert len(set(facet_cues)) == len(facet_cues)
    assert all(cue.strip() for cue in facet_cues)


def test_analytical_gate_distinguishes_factoid_from_explanatory():
    assert _is_analytical_question(_QUESTION)  # "how ... shape ..."
    assert not _is_analytical_question(_FACTOID)  # "when ..."
    assert not _is_analytical_question("Who proposed the coastal blockade")
    assert _is_analytical_question("Why did the coastal blockade fail")


def test_factoid_question_stays_at_a_single_search(tmp_path):
    corpus = _draft_corpus(tmp_path)
    plan = _proceed_plan(corpus.corpus_id, ["coastal blockade"])
    plan = plan.model_copy(update={"normalizedQuestion": _FACTOID})

    augmented = _runner()._augment_with_floor(plan, corpus, plan.plannedToolCalls)

    # No evidence-facet decomposition for a single-dimension lookup.
    assert len([c for c in augmented if c.toolName == _SEARCH]) == 1
    assert _derive_breadth_queries(_FACTOID, [], 2) == []


# --- Design D: cross-query dedup-aware fall-through ----------------------------


def test_exclude_passage_ids_falls_through_to_next_distinct(tmp_path):
    """A search excluding its own top hit returns the next distinct passage, not the
    excluded one -- the corpus-level fall-through primitive. Deterministic, no model."""
    corpus = _magnet_corpus(tmp_path)
    first = corpus.search_passages(
        PassageSearchRequest(corpusId=corpus.corpus_id, query="blockade supply lines", maxResults=2)
    )
    seen = [h.passageId for h in first.hits]

    second = corpus.search_passages(
        PassageSearchRequest(
            corpusId=corpus.corpus_id, query="blockade supply lines",
            maxResults=2, excludePassageIds=seen,
        )
    )
    returned = {h.passageId for h in second.hits}
    assert not (returned & set(seen))   # already-assembled passages are skipped
    assert returned                     # and the search still contributes distinct evidence


def test_runner_dedup_assembly_no_duplicate_consumes_budget(tmp_path):
    """Over a draft corpus the runner excludes already-assembled passages from each
    later search, so a magnet passage is never returned twice (never double-charged to
    the aggregate budget) and later searches contribute distinct passages."""
    corpus = _magnet_corpus(tmp_path)
    # Two queries that, lexically, both rank the same blockade passages first.
    plan = _proceed_plan(corpus.corpus_id, ["coastal blockade", "blockade supply lines"])

    bundle = _runner().execute_initial(plan, corpus).bundle

    per_call_ids = [
        [h.passageId for h in r.output.hits]
        for r in bundle.results
        if r.output is not None and hasattr(r.output, "hits")
    ]
    flat = [pid for ids in per_call_ids for pid in ids]
    # No passage is returned by more than one search: duplicates never re-enter the
    # bundle, so they never consume a result slot or aggregate characters.
    assert len(flat) == len(set(flat))
    assert len(bundle.referenceIndex.passageIds) == len(set(flat))
    # Fall-through engaged: a later search contributed a passage the first did not.
    assert len(per_call_ids) >= 2 and any(
        set(later) - set(per_call_ids[0]) for later in per_call_ids[1:]
    )
