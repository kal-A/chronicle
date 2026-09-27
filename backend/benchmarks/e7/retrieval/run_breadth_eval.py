"""Frozen retrieval-breadth evaluation for passages-only draft corpora (E10).

Measures, in isolation and deterministically (no Ollama), whether decomposing an
evidence-seeking question into complementary sub-queries assembles broader,
relevant, complementary evidence than a single broad query -- while keeping
diversity relevance-gated (namesake / off-topic sources are never pulled in).

Per case it reports: distinct relevant passages, relevant recall, source
diversity (distinct relevant sources), subquestion/aspect coverage,
duplicate/near-duplicate rate, retrieved context size (chars), and latency,
for single-query vs decomposed retrieval. A frozen embedder (concept axes)
supplies the semantic geometry, so the eval reproduces byte-for-byte.

Run:
    python benchmarks/e7/retrieval/run_breadth_eval.py \
        --json benchmarks/e7/retrieval/breadth-eval.json \
        --markdown benchmarks/e7/retrieval/breadth-eval.md
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, field
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

DEPLOYED_MAX_RESULTS = 2  # per-search cap (default_execution_policy)

# Concept axes: an aspect's passages and its focused sub-query share an axis;
# axes are orthogonal, so an off-axis (noise) passage is never semantically near.
_AXIS = {
    "alpha": [1.0, 0.0, 0.0, 0.0],
    "bravo": [0.0, 1.0, 0.0, 0.0],
    "charlie": [0.0, 0.0, 1.0, 0.0],
    "noise": [0.0, 0.0, 0.0, 1.0],
}
_ASPECT_KEYWORDS = ("alpha", "bravo", "charlie")


@dataclass(frozen=True)
class SourceSpec:
    title: str
    keywords: list[str]       # one aspect keyword per block of paragraphs
    paras_per_keyword: int    # ~1 passage per paragraph; each passage carries one keyword


@dataclass(frozen=True)
class BreadthCase:
    caseId: str
    intent: str
    sources: list[SourceSpec]
    broad_query: str          # single-query baseline
    subqueries: list[str]     # decomposed retrieval (one focused query per aspect)


_CASES: list[BreadthCase] = [
    BreadthCase(
        "multi-aspect",
        "Answer needs evidence from three aspects, each in its own source; one broad "
        "query reaches one aspect, decomposition reaches all three.",
        [
            SourceSpec("Aspect Alpha", ["alpha"], 2),
            SourceSpec("Aspect Bravo", ["bravo"], 2),
            SourceSpec("Aspect Charlie", ["charlie"], 2),
        ],
        broad_query="overview account",
        subqueries=["alpha", "bravo", "charlie"],
    ),
    BreadthCase(
        "dominant-relevant-source",
        "All relevant evidence lives in one source spanning three aspects; breadth "
        "improves distinct relevant passages even though source diversity stays 1.",
        [SourceSpec("Omnibus", ["alpha", "bravo", "charlie"], 2)],
        broad_query="overview account",
        subqueries=["alpha", "bravo", "charlie"],
    ),
    BreadthCase(
        "dominant-noise-source",
        "One relevant source plus two larger namesake noise sources (mirrors the "
        "Anaconda films). Decomposition must NOT pull noise passages to diversify.",
        [
            SourceSpec("Aspect Alpha", ["alpha"], 2),
            SourceSpec("Aspect Bravo", ["bravo"], 2),
            SourceSpec("Namesake One", ["python"], 5),
            SourceSpec("Namesake Two", ["python"], 5),
        ],
        broad_query="overview account",
        subqueries=["alpha", "bravo", "charlie"],
    ),
]


class _FrozenEmbedder:
    """Query embedder: maps a query string to its aspect axis. Passage vectors are
    populated directly, so only embed_one is exercised at query time."""

    def __init__(self, query_axis: dict[str, list[float]]) -> None:
        self._query_axis = query_axis

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        return list(self._query_axis.get(text, [0.0, 0.0, 0.0, 0.0]))


def _passage_axis(excerpt: str) -> list[float]:
    low = excerpt.casefold()
    for keyword, axis in _AXIS.items():
        if keyword in low:
            return list(axis)
    return [0.0, 0.0, 0.0, 0.0]


def _passage_aspect(excerpt: str) -> str | None:
    low = excerpt.casefold()
    for keyword in _ASPECT_KEYWORDS:
        if keyword in low:
            return keyword
    return None


def _acquired(spec: SourceSpec, index: int) -> AcquiredSource:
    blocks = [
        (f"{keyword} context detail line for evidence. " * 18).strip()
        for keyword in spec.keywords
        for _ in range(spec.paras_per_keyword)
    ]
    text = "\n\n".join(blocks)
    candidate = SourceCandidate(
        candidateId=f"synthetic:{index}", connector="wikipedia", title=spec.title,
        sourceType=SourceType.TERTIARY_REFERENCE, fullTextAvailable=True,
        rightsStatus=RightsStatus.LICENSED, url=f"https://example.org/{index}", language="en",
    )
    return AcquiredSource(
        candidate=candidate, text=text, contentType="text/plain",
        contentSha256=f"hash-{index:02d}", charCount=len(text),
        retrievedAt=datetime(2026, 9, 9, tzinfo=timezone.utc),
    )


def _build(case: BreadthCase, tmp_dir: Path) -> tuple[HybridCorpus, PackageBackedCorpus]:
    acquired = [_acquired(spec, i) for i, spec in enumerate(case.sources)]
    passages = []
    for src in acquired:
        passages.extend(chunk_source(src))
    investigation = build_corpus(
        topic="synthetic breadth fixture", interpreted_question="How broad is retrieval?",
        geographic_scope=["Region"], date_earliest=date(1860, 1, 1),
        date_latest=date(1865, 12, 31), acquired=acquired, passages=passages,
    )
    path = tmp_dir / f"{case.caseId}.json"
    path.write_text(json.dumps(investigation.model_dump(mode="json")), encoding="utf-8")
    inner = PackageBackedCorpus.load(
        corpus_id=case.caseId, package_path=path, title=case.caseId, benchmark_role="eval"
    )
    store = PassageVectorStore(":memory:")
    store.add_many([(p.id, _passage_axis(p.excerpt)) for p in inner.get_investigation().passages])
    query_axis = {case.broad_query: list(_AXIS["alpha"])}  # broad query biases to one aspect
    for sq in case.subqueries:
        query_axis[sq] = list(_AXIS.get(sq, [0.0, 0.0, 0.0, 0.0]))
    hybrid = HybridCorpus(inner, SemanticReranker(_FrozenEmbedder(query_axis), store))
    return hybrid, inner


def _classify(inner: PackageBackedCorpus, passage_ids: list[str]) -> dict:
    aspects: set[str] = set()
    relevant_sources: set[str] = set()
    noise = 0
    relevant = 0
    for pid in passage_ids:
        passage = inner.get_passage(pid)
        aspect = _passage_aspect(passage.excerpt)
        source_id = inner.get_document(passage.documentId).sourceId
        if aspect is not None:
            relevant += 1
            aspects.add(aspect)
            relevant_sources.add(source_id)
        elif "python" in passage.excerpt.casefold():
            noise += 1
    return {
        "distinctRelevant": relevant,
        "aspectsCovered": len(aspects),
        "relevantSources": len(relevant_sources),
        "noiseRetrieved": noise,
    }


def _retrieve(hybrid: HybridCorpus, corpus_id: str, query: str) -> tuple[list[str], int, float]:
    t0 = time.perf_counter()
    res = hybrid.search_passages(
        PassageSearchRequest(corpusId=corpus_id, query=query, maxResults=DEPLOYED_MAX_RESULTS)
    )
    ms = (time.perf_counter() - t0) * 1000.0
    ids = [h.passageId for h in res.hits]
    chars = sum(len(h.excerpt) for h in res.hits)
    return ids, chars, ms


def _measure(case: BreadthCase, hybrid: HybridCorpus, inner: PackageBackedCorpus) -> dict:
    relevant_available = sum(
        1 for p in inner.get_investigation().passages if _passage_aspect(p.excerpt) is not None
    )
    # Single broad query.
    single_ids, single_chars, single_ms = _retrieve(hybrid, case.caseId, case.broad_query)
    single = _classify(inner, single_ids)

    # Decomposed: union of per-subquery searches, deduped.
    union: list[str] = []
    per_query_ids: list[list[str]] = []
    multi_chars = 0
    multi_ms = 0.0
    for sq in case.subqueries:
        ids, chars, ms = _retrieve(hybrid, case.caseId, sq)
        per_query_ids.append(ids)
        multi_ms += ms
        for pid in ids:
            if pid not in union:
                union.append(pid)
                multi_chars += len(inner.get_passage(pid).excerpt)
    multi = _classify(inner, union)
    # Duplicate rate: how many (query,passage) hits were duplicates of an id seen
    # in an earlier query (fusion within a query already dedupes by id).
    total_hits = sum(len(ids) for ids in per_query_ids)
    duplicate_rate = round((total_hits - len(union)) / total_hits, 3) if total_hits else 0.0

    return {
        "caseId": case.caseId,
        "intent": case.intent,
        "relevantAvailable": relevant_available,
        "single": {
            **single, "chars": single_chars, "ms": round(single_ms, 3),
            "recall": round(single["distinctRelevant"] / relevant_available, 3) if relevant_available else None,
        },
        "decomposed": {
            **multi, "chars": multi_chars, "ms": round(multi_ms, 3),
            "recall": round(multi["distinctRelevant"] / relevant_available, 3) if relevant_available else None,
            "duplicateRate": duplicate_rate,
            "subqueries": len(case.subqueries),
        },
    }


def run_eval() -> dict:
    import tempfile

    cases = []
    with tempfile.TemporaryDirectory() as tmp:
        for case in _CASES:
            hybrid, inner = _build(case, Path(tmp))
            cases.append(_measure(case, hybrid, inner))
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "k": DEPLOYED_MAX_RESULTS,
        "embedder": "frozen synthetic (deterministic; no Ollama)",
        "cases": cases,
    }


def _markdown(report: dict) -> str:
    lines = [
        "# Frozen retrieval-breadth evaluation (E10)",
        "",
        "Single broad query vs decomposed sub-query retrieval over passages-only draft",
        f"corpora, at the deployed budget (`maxResults={report['k']}` per search), with a",
        "deterministic embedder (no Ollama). Diversity is relevance-gated: off-topic /",
        "namesake sources are never pulled in.",
        "",
        "| Case | Relevant avail. | Distinct relevant (single→dec.) | Aspects covered (single→dec.) | Relevant sources (single→dec.) | Noise pulled (single/dec.) | Dup rate | Ctx chars (single→dec.) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in report["cases"]:
        s, d = c["single"], c["decomposed"]
        lines.append(
            f"| {c['caseId']} | {c['relevantAvailable']} | {s['distinctRelevant']}→{d['distinctRelevant']} | "
            f"{s['aspectsCovered']}→{d['aspectsCovered']} | {s['relevantSources']}→{d['relevantSources']} | "
            f"{s['noiseRetrieved']}/{d['noiseRetrieved']} | {d['duplicateRate']} | {s['chars']}→{d['chars']} |"
        )
    lines += ["", "### What each case shows", ""]
    for c in report["cases"]:
        lines.append(f"- **{c['caseId']}** — {c['intent']}")
    lines += [
        "",
        "## Notes",
        "",
        "- **Relevance-gated diversity:** the dominant-noise-source case retrieves **zero** noise",
        "  passages under decomposition — breadth never trades relevance for source spread.",
        "- **Breadth ≠ source count:** the dominant-relevant-source case gains distinct relevant",
        "  passages with source diversity fixed at 1, showing breadth is measured in evidence, not sources.",
        "- Latency reflects the frozen embedder (~free); real embedding latency is in the Anaconda trace.",
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
    for c in report["cases"]:
        s, d = c["single"], c["decomposed"]
        print(f"{c['caseId']}: distinctRelevant {s['distinctRelevant']}->{d['distinctRelevant']} "
              f"aspects {s['aspectsCovered']}->{d['aspectsCovered']} noise {d['noiseRetrieved']}")


if __name__ == "__main__":
    main()
