"""Frozen retrieval evaluation for passages-only draft corpora.

Measures the retrieval layer *in isolation* -- before any answer-quality judgement --
comparing the lexical-only corpus against the recall-additive ``HybridCorpus`` on a
fixed set of evidence-rich queries over a synthetic passages-only draft corpus.

Deterministic by construction: the semantic geometry comes from a frozen embedder
(text -> a fixed concept axis) and a hand-populated vector store, so the eval runs
with no Ollama daemon and reproduces byte-identically. It reports, per query:

* relevant passages retrieved (lexical vs hybrid) -- recall, against explicit labels
* source diversity (distinct sources returned)
* duplicate/overlap behavior (any passage returned twice across the two lanes)
* retrieval depth (lexical candidates considered before top-k)
* latency (wall-clock of the retrieval call; the frozen embedder is ~free -- the
  real nomic-embed-text latency is measured separately in the Anaconda trace)

The corpus content is synthetic and subject-free (no real historical entities), so
this file stays clear of the anti-topic-branching guard's scanned packages.

Run:
    python benchmarks/e7/retrieval/run_retrieval_eval.py \
        --json benchmarks/e7/retrieval/retrieval-eval.json \
        --markdown benchmarks/e7/retrieval/retrieval-eval.md
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from chronicle.acquisition.chunking import chunk_source
from chronicle.acquisition.contracts import AcquiredSource, SourceCandidate
from chronicle.acquisition.corpus_builder import build_corpus
from chronicle.acquisition.hybrid_corpus import HybridCorpus
from chronicle.acquisition.retrieval import SemanticReranker
from chronicle.acquisition.vector_store import PassageVectorStore
from chronicle.contracts.enums import RightsStatus, SourceType
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import PackageBackedCorpus

# Deployed retrieval budget (create_default_app / default_execution_policy).
DEPLOYED_MAX_RESULTS = 2

# Concept axes. A passage's vector is the axis of its concept; a query's vector is
# the axis it is *about*. Cosine 1 within an axis, 0 across axes.
_AXIS = {"A": [1.0, 0.0, 0.0, 0.0], "B": [0.0, 1.0, 0.0, 0.0], "C": [0.0, 0.0, 1.0, 0.0]}
_ABSENT = [0.0, 0.0, 0.0, 1.0]  # a query concept with no source in the corpus


@dataclass(frozen=True)
class SourceSpec:
    title: str
    text: str
    concept: str  # key into _AXIS


@dataclass(frozen=True)
class QueryCase:
    caseId: str
    intent: str
    query: str
    query_concept: str  # "A"/"B"/"C" (present) or "ABSENT"
    relevant_titles: frozenset[str]


# --- the frozen fixture ------------------------------------------------------
# One passages-only draft corpus. Each source is a single passage. Concept A has a
# lexical-matchable source plus two reworded sources the lexical lane cannot reach;
# concept C is reachable only semantically; concept B is a lexical decoy that shares
# a token with a query but is off-topic for it.
_SOURCES: list[SourceSpec] = [
    SourceSpec("Blockade Dispatch", "The harbor blockade sealed the port and halted trade.", "A"),
    SourceSpec("Coastal Interdiction", "Coastal interdiction strangled maritime supply and reshaped the campaign.", "A"),
    SourceSpec("Supply Lines Study", "Sea-lane throttling cut provisioning to the interior forces.", "A"),
    SourceSpec("Harbor Festival", "The harbor festival featured a regatta and a parade.", "B"),
    SourceSpec("Alpine Rail", "An alpine corridor moved brigades to the front by rail-line.", "C"),
]

_CASES: list[QueryCase] = [
    QueryCase(
        "reworded-relevant",
        "Relevant evidence is worded differently from the query; lexical can reach only "
        "one of three relevant sources, the rest are semantic-only.",
        "harbor blockade",
        "A",
        frozenset({"Blockade Dispatch", "Coastal Interdiction", "Supply Lines Study"}),
    ),
    QueryCase(
        "pure-recall-lexical-empty",
        "Query shares no token with any source; the one relevant source is reachable "
        "only semantically (lexical returns nothing relevant).",
        "mountain railway",
        "C",
        frozenset({"Alpine Rail"}),
    ),
    QueryCase(
        "aligned-no-regression",
        "Lexical already reaches the single relevant source; hybrid must retain it and "
        "not displace it (control).",
        "harbor festival regatta",
        "B",
        frozenset({"Harbor Festival"}),
    ),
    QueryCase(
        "absent-evidence",
        "No source is about the query's concept; neither lane should find relevant "
        "evidence (measures the precision cost of unconditional semantic recall).",
        "diplomatic congress protocol",
        "ABSENT",
        frozenset(),
    ),
]


class _FrozenEmbedder:
    """Query embedder: maps each case's query string to its concept axis. Only
    ``embed_one`` is exercised (the store is populated directly), but ``embed`` is
    provided for interface completeness."""

    def __init__(self, query_axis: dict[str, list[float]]) -> None:
        self._query_axis = query_axis

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return list(self._query_axis.get(text, _ABSENT))


def _acquired(spec: SourceSpec, index: int) -> AcquiredSource:
    candidate = SourceCandidate(
        candidateId=f"synthetic:{index}",
        connector="wikipedia",
        title=spec.title,
        sourceType=SourceType.TERTIARY_REFERENCE,
        fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED,
        url=f"https://example.org/{index}",
        language="en",
    )
    return AcquiredSource(
        candidate=candidate,
        text=spec.text,
        contentType="text/plain",
        contentSha256=f"hash-{index:02d}",
        charCount=len(spec.text),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def _build_corpus(tmp_dir: Path) -> PackageBackedCorpus:
    acquired = [_acquired(spec, i) for i, spec in enumerate(_SOURCES)]
    passages = []
    for src in acquired:
        passages.extend(chunk_source(src))
    investigation = build_corpus(
        topic="synthetic retrieval fixture",
        interpreted_question="How is retrieval recall measured?",
        geographic_scope=["Region"],
        date_earliest=date(1860, 1, 1),
        date_latest=date(1865, 12, 31),
        acquired=acquired,
        passages=passages,
    )
    path = tmp_dir / "retrieval-fixture.json"
    path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")
    return PackageBackedCorpus.load(
        corpus_id="retrieval-eval", package_path=path, title="Retrieval Eval", benchmark_role="eval"
    )


def _concept_by_title() -> dict[str, str]:
    return {spec.title: spec.concept for spec in _SOURCES}


def _title_of(corpus: PackageBackedCorpus, passage_id: str) -> str:
    passage = corpus.get_passage(passage_id)
    source_id = corpus.get_document(passage.documentId).sourceId
    return corpus.get_source(source_id).title


def _measure(corpus: PackageBackedCorpus, hybrid: HybridCorpus, case: QueryCase) -> dict:
    request = PassageSearchRequest(corpusId=corpus.corpus_id, query=case.query, maxResults=DEPLOYED_MAX_RESULTS)

    t0 = time.perf_counter()
    lexical = corpus.search_passages(request)
    lexical_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    hybrid_result = hybrid.search_passages(request)
    hybrid_ms = (time.perf_counter() - t0) * 1000.0

    lex_titles = [_title_of(corpus, h.passageId) for h in lexical.hits]
    hyb_titles = [_title_of(corpus, h.passageId) for h in hybrid_result.hits]
    hyb_ids = [h.passageId for h in hybrid_result.hits]

    lex_relevant = sum(1 for t in lex_titles if t in case.relevant_titles)
    hyb_relevant = sum(1 for t in hyb_titles if t in case.relevant_titles)

    return {
        "caseId": case.caseId,
        "intent": case.intent,
        "query": case.query,
        "k": DEPLOYED_MAX_RESULTS,
        "relevantAvailable": len(case.relevant_titles),
        "lexicalReturned": len(lexical.hits),
        "hybridReturned": len(hybrid_result.hits),
        "lexicalRelevant": lex_relevant,
        "hybridRelevant": hyb_relevant,
        "recallGain": hyb_relevant - lex_relevant,
        "lexicalDistinctSources": len(set(lex_titles)),
        "hybridDistinctSources": len(set(hyb_titles)),
        "duplicatePassageIds": len(hyb_ids) - len(set(hyb_ids)),
        "retrievalDepthCandidates": min(DEPLOYED_MAX_RESULTS * 4, 20),
        "lexicalMs": round(lexical_ms, 3),
        "hybridMs": round(hybrid_ms, 3),
        "lexicalTitles": lex_titles,
        "hybridTitles": hyb_titles,
    }


def run_eval() -> dict:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        corpus = _build_corpus(Path(tmp))
        concept_by_title = _concept_by_title()

        # Populate the vector store directly with each passage's concept axis.
        store = PassageVectorStore(":memory:")
        vectors: list[tuple[str, list[float]]] = []
        for passage in corpus.get_investigation().passages:
            title = _title_of(corpus, passage.id)
            vectors.append((passage.id, list(_AXIS[concept_by_title[title]])))
        store.add_many(vectors)

        query_axis = {
            case.query: (_AXIS[case.query_concept] if case.query_concept in _AXIS else _ABSENT)
            for case in _CASES
        }
        embedder = _FrozenEmbedder(query_axis)
        hybrid = HybridCorpus(corpus, SemanticReranker(embedder, store))

        cases = [_measure(corpus, hybrid, case) for case in _CASES]

    lex_total = sum(c["lexicalRelevant"] for c in cases)
    hyb_total = sum(c["hybridRelevant"] for c in cases)
    relevant_available = sum(c["relevantAvailable"] for c in cases)
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "corpusShape": "passages-only draft (no claims/relationships/dates)",
        "k": DEPLOYED_MAX_RESULTS,
        "embedder": "frozen synthetic (deterministic; no Ollama)",
        "aggregate": {
            "relevantAvailable": relevant_available,
            "lexicalRelevantRetrieved": lex_total,
            "hybridRelevantRetrieved": hyb_total,
            "recallGain": hyb_total - lex_total,
            "lexicalRecall": round(lex_total / relevant_available, 3) if relevant_available else None,
            "hybridRecall": round(hyb_total / relevant_available, 3) if relevant_available else None,
            "duplicatePassageIdsTotal": sum(c["duplicatePassageIds"] for c in cases),
        },
        "cases": cases,
    }


def _markdown(report: dict) -> str:
    agg = report["aggregate"]
    lines = [
        "# Frozen retrieval evaluation — passages-only draft corpora",
        "",
        "Retrieval measured in isolation (before answer quality): lexical-only corpus vs.",
        "the recall-additive `HybridCorpus`, at the **deployed** budget "
        f"(`maxResults={report['k']}`), over a synthetic subject-free draft corpus with a",
        "deterministic embedder (no Ollama — reproducible byte-for-byte).",
        "",
        "## Aggregate",
        "",
        f"- Relevant passages available (labeled): **{agg['relevantAvailable']}**",
        f"- Relevant retrieved — lexical: **{agg['lexicalRelevantRetrieved']}** "
        f"(recall {agg['lexicalRecall']}) → hybrid: **{agg['hybridRelevantRetrieved']}** "
        f"(recall {agg['hybridRecall']})",
        f"- **Recall gain: +{agg['recallGain']} relevant passages**",
        f"- Duplicate passages returned (across lanes): {agg['duplicatePassageIdsTotal']} "
        "(fusion dedupes by id)",
        "",
        "## Per case",
        "",
        "| Case | Query | Relevant avail. | Lexical rel. | Hybrid rel. | Gain | Distinct src (lex→hyb) | Dup ids | Hybrid ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for c in report["cases"]:
        lines.append(
            f"| {c['caseId']} | `{c['query']}` | {c['relevantAvailable']} | {c['lexicalRelevant']} | "
            f"{c['hybridRelevant']} | +{c['recallGain']} | {c['lexicalDistinctSources']}→{c['hybridDistinctSources']} | "
            f"{c['duplicatePassageIds']} | {c['hybridMs']} |"
        )
    lines += [
        "",
        "### What each case shows",
        "",
    ]
    for c in report["cases"]:
        lines.append(f"- **{c['caseId']}** — {c['intent']}")
    lines += [
        "",
        "## Design & honest limits",
        "",
        "- The reserve guarantees up to `floor(k/2)` slots to the *most-similar* passages the",
        "  lexical lane missed, while the top `k - reserve` lexical hits are always kept — so a",
        "  strong lexical hit is never fully displaced (see the **aligned-no-regression** control:",
        "  its result is identical to lexical).",
        "- A semantic-only passage is admitted only when cosine similarity is strictly positive.",
        "  On the **absent-evidence** case (query orthogonal to every source) this guard suppresses",
        "  recall entirely, so hybrid returns exactly what lexical does — no noise is injected.",
        "  This is a similarity guard, not a tuned threshold: real embeddings return positive",
        "  similarities for the nearest passages, so in production the reserve is filled by the",
        "  genuinely-most-similar missed passages, and the critic/grounding still gate synthesis.",
        "- Latency here reflects the frozen embedder (~free). Real `nomic-embed-text` embedding",
        "  latency on CPU is measured in the Anaconda end-to-end trace, not here.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--markdown", type=Path, default=None)
    args = parser.parse_args()

    report = run_eval()

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(_markdown(report), encoding="utf-8")

    agg = report["aggregate"]
    print(
        f"retrieval eval: lexical {agg['lexicalRelevantRetrieved']} -> hybrid "
        f"{agg['hybridRelevantRetrieved']} relevant (+{agg['recallGain']}), "
        f"dup ids {agg['duplicatePassageIdsTotal']}"
    )


if __name__ == "__main__":
    main()
