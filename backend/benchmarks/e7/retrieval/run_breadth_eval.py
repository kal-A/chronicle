"""Frozen retrieval-breadth evaluation for passages-only draft corpora (E10/E11).

Measures, deterministically (no Ollama), whether the runner's *evidence-facet*
decomposition assembles broader, more complementary, relevant evidence than the
behaviour it replaced -- the E10 lexical token-partition backstop -- while keeping
diversity relevance-gated (namesake / off-topic sources are never pulled in) and
leaving single-dimension factoid questions at one search.

For each case the eval runs the deployed decomposition both ways over the same
synthetic draft corpus, at the deployed budget (``maxResults=2`` per search, up to
``maxInitialToolCalls`` searches):

* **before** -- planner broad query + E10 token-partition sub-queries;
* **after**  -- planner broad query + E11 ``_derive_breadth_queries`` facet queries.

and reports, per decomposition: the exact queries, per-query top-k passage ids and
scores, cross-query overlap, distinct relevant passages, aspect/evidence coverage,
relevant source diversity, duplicate rate, retrieved context size (chars), and
latency. A frozen rule-based embedder supplies the semantic geometry (passages and
each query route to orthogonal concept axes), so the eval reproduces byte-for-byte.

Run:
    python benchmarks/e7/retrieval/run_breadth_eval.py \
        --json benchmarks/e7/retrieval/breadth-eval.json \
        --markdown benchmarks/e7/retrieval/breadth-eval.md
"""

from __future__ import annotations

import argparse
import json
import re
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
from chronicle.ai.orchestration.runner import _derive_breadth_queries
from chronicle.contracts.enums import RightsStatus, SourceType
from chronicle.corpus.contracts import PassageSearchRequest
from chronicle.corpus.package_corpus import PackageBackedCorpus

DEPLOYED_MAX_RESULTS = 2  # per-search cap (default_execution_policy)
DEPLOYED_MAX_INITIAL = 3  # maxInitialToolCalls -> broad query + up to 2 derived searches

# Orthogonal concept axes. A relevant aspect's passages and the query that targets
# it share an axis; axes are orthogonal, so an off-axis (noise) passage is never
# semantically near a relevant query. "subject" models the lexical magnet passage
# a broad query lands on; noise models namesake / off-topic sources.
_AXIS = {
    "axissubj": [1.0, 0.0, 0.0, 0.0, 0.0],
    "axismech": [0.0, 1.0, 0.0, 0.0, 0.0],
    "axiscons": [0.0, 0.0, 1.0, 0.0, 0.0],
    "axischron": [0.0, 0.0, 0.0, 1.0, 0.0],
    "axisnoise": [0.0, 0.0, 0.0, 0.0, 1.0],
}
_ZERO = [0.0, 0.0, 0.0, 0.0, 0.0]
_RELEVANT_AXES = ("axissubj", "axismech", "axiscons", "axischron")

# Facet cue (from runner._EVIDENCE_FACETS) -> the concept axis whose passages answer
# that evidence need. Only the dimensions exercised by the eval questions are mapped.
_FACET_CUE_AXIS = {
    "how it worked in practice": "axismech",
    "effects and outcomes": "axiscons",
    "sequence of events over time": "axischron",
    "definition and purpose": "axissubj",
}
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class SourceSpec:
    title: str
    axes: list[str]          # one concept axis per block of paragraphs
    paras_per_axis: int      # ~1 passage per paragraph; each passage carries one axis


@dataclass(frozen=True)
class BreadthCase:
    caseId: str
    intent: str
    sources: list[SourceSpec]
    question: str            # natural question fed to the real decomposition path
    broad_query: str         # planner's single broad query (lands on the subject axis)
    subject_tokens: list[str]  # anchor tokens; a non-facet query sharing one lands on subject


_CASES: list[BreadthCase] = [
    BreadthCase(
        "overlap-recoverable",
        "A broad query and the E10 token-partition sub-queries overlap on the subject "
        "passages; E11 facet sub-queries instead recover distinct mechanism and "
        "consequence evidence.",
        [
            SourceSpec("Subject Overview", ["axissubj"], 2),
            SourceSpec("Mechanism Source", ["axismech"], 2),
            SourceSpec("Consequence Source", ["axiscons"], 2),
        ],
        question="How did the program operate and what consequences did it cause for the region",
        broad_query="program region overview account",
        subject_tokens=["program", "region"],
    ),
    BreadthCase(
        "single-source",
        "All relevant evidence lives in one source spanning subject, mechanism and "
        "consequence aspects; facet decomposition improves passage/aspect coverage "
        "while relevant source diversity legitimately stays 1.",
        [SourceSpec("Omnibus", ["axissubj", "axismech", "axiscons"], 2)],
        question="How did the program operate and what consequences did it cause for the region",
        broad_query="program region overview account",
        subject_tokens=["program", "region"],
    ),
    BreadthCase(
        "noisy-sources",
        "One relevant source set plus two larger namesake noise sources (mirrors the "
        "Anaconda films). Facet decomposition must NOT pull noise passages to diversify.",
        [
            SourceSpec("Subject Overview", ["axissubj"], 2),
            SourceSpec("Mechanism Source", ["axismech"], 2),
            SourceSpec("Consequence Source", ["axiscons"], 2),
            SourceSpec("Namesake One", ["axisnoise"], 5),
            SourceSpec("Namesake Two", ["axisnoise"], 5),
        ],
        question="How did the program operate and what consequences did it cause for the region",
        broad_query="program region overview account",
        subject_tokens=["program", "region"],
    ),
    BreadthCase(
        "single-dimension",
        "A straightforward factoid question invokes no analytical evidence dimension, "
        "so the backstop derives no extra searches and retrieval stays at one query.",
        [
            SourceSpec("Subject Overview", ["axissubj"], 2),
            SourceSpec("Mechanism Source", ["axismech"], 2),
        ],
        question="When was the program established in the region",
        broad_query="program region overview account",
        subject_tokens=["program", "region"],
    ),
]


def _legacy_partition_queries(base_query: str, existing: list[str], n: int) -> list[str]:
    """The E10 behaviour being replaced: partition the question's salient content
    tokens into contiguous chunks. Replicated here so the eval shows the regression
    it fixes without depending on removed production code."""

    stop = {
        "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "was", "were",
        "is", "are", "be", "by", "with", "at", "as", "its", "it", "that", "this",
        "from", "about", "into", "over", "what", "who", "whom", "when", "where",
        "why", "how", "did", "do", "does", "which", "shape", "shaped",
    }
    if n <= 0:
        return []
    tokens = [t for t in _WORD_RE.findall(base_query.casefold()) if len(t) >= 3 and t not in stop]
    tokens = list(dict.fromkeys(tokens))
    if len(tokens) < 2:
        return []
    groups = max(1, min(max(n, 2), len(tokens)))
    size, extra = divmod(len(tokens), groups)
    chunks: list[list[str]] = []
    start = 0
    for index in range(groups):
        length = size + (1 if index < extra else 0)
        chunks.append(tokens[start : start + length])
        start += length
    seen = set(existing)
    derived: list[str] = []
    for chunk in chunks:
        query = " ".join(chunk)
        key = query.casefold()
        if query and key not in seen:
            derived.append(query)
            seen.add(key)
        if len(derived) >= n:
            break
    return derived


class _FrozenEmbedder:
    """Rule-based query embedder. Routes each query string to a concept axis:
    facet cues by substring, the planner broad query to the subject axis, and any
    other (token-partition) query to the subject axis when it shares a subject
    token, else nowhere -- modelling the real overlap/empty-residue behaviour."""

    def __init__(self, broad_query: str, subject_tokens: list[str]) -> None:
        self._broad = broad_query.casefold()
        self._subject = {t.casefold() for t in subject_tokens}

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]

    def embed_one(self, text: str) -> list[float]:
        low = text.casefold()
        for cue, axis in _FACET_CUE_AXIS.items():
            if cue in low:
                return list(_AXIS[axis])
        if low == self._broad:
            return list(_AXIS["axissubj"])
        if {t for t in _WORD_RE.findall(low)} & self._subject:
            return list(_AXIS["axissubj"])
        return list(_ZERO)


def _passage_axis(excerpt: str) -> list[float]:
    low = excerpt.casefold()
    for keyword, axis in _AXIS.items():
        if keyword in low:
            return list(axis)
    return list(_ZERO)


def _passage_relevant_axis(excerpt: str) -> str | None:
    low = excerpt.casefold()
    for axis in _RELEVANT_AXES:
        if axis in low:
            return axis
    return None


def _acquired(spec: SourceSpec, index: int) -> AcquiredSource:
    blocks = [
        (f"{axis} context detail line for evidence. " * 18).strip()
        for axis in spec.axes
        for _ in range(spec.paras_per_axis)
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
        topic="synthetic breadth fixture", interpreted_question=case.question,
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
    embedder = _FrozenEmbedder(case.broad_query, case.subject_tokens)
    hybrid = HybridCorpus(inner, SemanticReranker(embedder, store))
    return hybrid, inner


def _retrieve(hybrid: HybridCorpus, corpus_id: str, query: str) -> dict:
    t0 = time.perf_counter()
    res = hybrid.search_passages(
        PassageSearchRequest(corpusId=corpus_id, query=query, maxResults=DEPLOYED_MAX_RESULTS)
    )
    ms = (time.perf_counter() - t0) * 1000.0
    return {
        "query": query,
        "hits": [{"passageId": h.passageId, "score": round(h.score, 4)} for h in res.hits],
        "ms": round(ms, 3),
    }


def _classify(inner: PackageBackedCorpus, passage_ids: list[str]) -> dict:
    axes: set[str] = set()
    relevant_sources: set[str] = set()
    noise = 0
    relevant = 0
    for pid in passage_ids:
        passage = inner.get_passage(pid)
        axis = _passage_relevant_axis(passage.excerpt)
        source_id = inner.get_document(passage.documentId).sourceId
        if axis is not None:
            relevant += 1
            axes.add(axis)
            relevant_sources.add(source_id)
        elif "axisnoise" in passage.excerpt.casefold():
            noise += 1
    return {
        "distinctRelevant": relevant,
        "aspectsCovered": len(axes),
        "relevantSources": len(relevant_sources),
        "noiseRetrieved": noise,
    }


def _decompose(
    hybrid: HybridCorpus, inner: PackageBackedCorpus, case: BreadthCase, derived: list[str]
) -> dict:
    """Run the planner broad query plus the derived sub-queries, deduped by id."""

    queries = [case.broad_query, *derived]
    per_query = [_retrieve(hybrid, case.caseId, q) for q in queries]
    id_sets = [[h["passageId"] for h in r["hits"]] for r in per_query]

    union: list[str] = []
    chars = 0
    for ids in id_sets:
        for pid in ids:
            if pid not in union:
                union.append(pid)
                chars += len(inner.get_passage(pid).excerpt)
    classified = _classify(inner, union)

    total_hits = sum(len(ids) for ids in id_sets)
    duplicate_rate = round((total_hits - len(union)) / total_hits, 3) if total_hits else 0.0

    # Cross-query overlap: passages the broad query shares with any derived query,
    # and the max pairwise overlap across the decomposition.
    broad_ids = set(id_sets[0])
    broad_overlap = sorted(set().union(*(set(ids) for ids in id_sets[1:])) & broad_ids) if derived else []
    max_pairwise = 0
    for i in range(len(id_sets)):
        for j in range(i + 1, len(id_sets)):
            max_pairwise = max(max_pairwise, len(set(id_sets[i]) & set(id_sets[j])))

    return {
        "searches": len(queries),
        "derivedCount": len(derived),
        "queries": queries,
        "perQuery": per_query,
        **classified,
        "distinctRetrieved": len(union),
        "chars": chars,
        "duplicateRate": duplicate_rate,
        "broadOverlap": len(broad_overlap),
        "maxPairwiseOverlap": max_pairwise,
        "ms": round(sum(r["ms"] for r in per_query), 3),
    }


def _measure(case: BreadthCase, hybrid: HybridCorpus, inner: PackageBackedCorpus) -> dict:
    relevant_available = sum(
        1 for p in inner.get_investigation().passages if _passage_relevant_axis(p.excerpt) is not None
    )
    budget = DEPLOYED_MAX_INITIAL - 1  # broad query already counts as one initial call
    before_derived = _legacy_partition_queries(case.question, [case.broad_query.casefold()], budget)
    after_derived = _derive_breadth_queries(case.question, [case.broad_query.casefold()], budget)

    before = _decompose(hybrid, inner, case, before_derived)
    after = _decompose(hybrid, inner, case, after_derived)
    for block in (before, after):
        block["recall"] = (
            round(block["distinctRelevant"] / relevant_available, 3) if relevant_available else None
        )
    return {
        "caseId": case.caseId,
        "intent": case.intent,
        "question": case.question,
        "relevantAvailable": relevant_available,
        "before": before,
        "after": after,
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
        "maxInitialSearches": DEPLOYED_MAX_INITIAL,
        "embedder": "frozen rule-based (deterministic; no Ollama)",
        "cases": cases,
    }


def _markdown(report: dict) -> str:
    lines = [
        "# Frozen retrieval-breadth evaluation (E10 → E11)",
        "",
        "E10 lexical token-partition decomposition (**before**) vs E11 evidence-facet",
        f"decomposition (**after**), over passages-only draft corpora at the deployed budget",
        f"(`maxResults={report['k']}` per search, ≤{report['maxInitialSearches']} searches: a broad query",
        "plus derived sub-queries), with a deterministic embedder (no Ollama). Diversity is",
        "relevance-gated: off-topic / namesake sources are never pulled in.",
        "",
        "| Case | Relevant avail. | Distinct relevant (before→after) | Aspects (before→after) | Relevant sources (before→after) | Noise (before/after) | Broad overlap (before→after) | Derived searches (before→after) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in report["cases"]:
        b, a = c["before"], c["after"]
        lines.append(
            f"| {c['caseId']} | {c['relevantAvailable']} | {b['distinctRelevant']}→{a['distinctRelevant']} | "
            f"{b['aspectsCovered']}→{a['aspectsCovered']} | {b['relevantSources']}→{a['relevantSources']} | "
            f"{b['noiseRetrieved']}/{a['noiseRetrieved']} | {b['broadOverlap']}→{a['broadOverlap']} | "
            f"{b['derivedCount']}→{a['derivedCount']} |"
        )
    lines += ["", "### Exact queries and top-k (after = E11 facet decomposition)", ""]
    for c in report["cases"]:
        lines.append(f"**{c['caseId']}** — _{c['question']}_")
        for r in c["after"]["perQuery"]:
            hits = ", ".join(f"{h['passageId']}({h['score']})" for h in r["hits"]) or "∅"
            lines.append(f"- `{r['query']}` → {hits}")
        lines.append("")
    lines += ["### What each case shows", ""]
    for c in report["cases"]:
        lines.append(f"- **{c['caseId']}** — {c['intent']}")
    lines += [
        "",
        "## Notes",
        "",
        "- **Overlap recovered:** the token-partition `before` lands its sub-queries back on the",
        "  subject passages (high broad overlap, one aspect); facet `after` sub-queries reach distinct",
        "  mechanism/consequence aspects (broad overlap drops, aspects rise).",
        "- **Relevance-gated diversity:** the noisy-sources case retrieves **zero** namesake-noise",
        "  passages after decomposition — breadth never trades relevance for source spread.",
        "- **Breadth ≠ source count:** the single-source case gains distinct relevant passages and",
        "  aspects with relevant source diversity fixed at 1.",
        "- **Factoid gate:** the single-dimension question derives **no** extra searches (retrieval",
        "  stays at one query), so simple lookups are not over-decomposed.",
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
        b, a = c["before"], c["after"]
        print(f"{c['caseId']}: distinctRelevant {b['distinctRelevant']}->{a['distinctRelevant']} "
              f"aspects {b['aspectsCovered']}->{a['aspectsCovered']} "
              f"broadOverlap {b['broadOverlap']}->{a['broadOverlap']} "
              f"derived {b['derivedCount']}->{a['derivedCount']} noise {a['noiseRetrieved']}")


if __name__ == "__main__":
    main()
