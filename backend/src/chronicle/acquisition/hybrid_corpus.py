"""A corpus decorator that adds semantic recall + re-ranking to passage search.

``HybridCorpus`` wraps any :class:`InvestigationCorpus` and overrides only
``search_passages``. It has two modes, chosen by what the injected reranker can do:

* **Re-rank only** (reranker exposes ``order`` but not ``recall``): asks the inner
  corpus for an *expanded* lexical candidate set, then reorders those candidates
  with a semantic reranker before returning the caller's requested top-k. This is
  a precision re-rank *within* the lexical candidate set -- it cannot surface a
  passage the lexical lane missed entirely.

* **Recall-additive** (reranker exposes ``recall``): in addition to the expanded
  lexical candidates, it queries the semantic index over the *whole* corpus and
  fuses the two rankings (RRF). Passages the lexical lane dropped -- e.g. relevant
  passages that share no query tokens with a differently-worded question -- can now
  enter the result. A bounded reserve caps how many result slots such semantic-only
  passages may take, so a strong lexical hit is never fully displaced; when the
  lexical lane is thin, semantic-only passages fill the remaining slots. This lifts
  recall for **passages-only draft corpora**, which is the only shape ``HybridCorpus``
  ever decorates (see ``CorpusBuildService``): auto-acquired draft corpora carry
  passages but no claims/relationships/evidence-links/dates, which is why a
  semantic-only hit is materialised with empty links/dates below. Curated,
  synthesized corpora are never wrapped, so their retrieval is unchanged.

Both modes are optional: with no reranker (or an empty semantic index) the result
is exactly the inner corpus's lexical result, so any environment without a local
embedding model behaves as before. No budget, no result cap, and no grounding or
validation gate is touched -- this changes *which* passages fill the caller's
existing ``maxResults`` slots, adding relevant recall, not the number of slots.
"""

from __future__ import annotations

from typing import Protocol

from ..corpus.contracts import (
    MAX_EXCERPT_LENGTH,
    MAX_RESULT_COUNT,
    PassageSearchHit,
    PassageSearchRequest,
    PassageSearchResult,
)
from ..corpus.protocol import InvestigationCorpus
from .retrieval import DEFAULT_RRF_K, reciprocal_rank_fusion

#: How many lexical candidates to gather per requested result before re-ranking.
#: Wider than the request so the semantic lane can promote strong matches the
#: lexical score ranked lower, bounded by the corpus tool's hard result cap.
CANDIDATE_FACTOR = 4

#: Truncation marker appended to an over-long excerpt (matches corpus/search.py).
_TRUNCATION_MARKER = " […]"


class PassageReranker(Protocol):
    def order(self, query: str, candidate_ids: list[str]) -> list[str]: ...


class PassageRecaller(Protocol):
    """A reranker that can additionally retrieve passages the lexical lane missed."""

    def order(self, query: str, candidate_ids: list[str]) -> list[str]: ...
    def recall(self, query: str, *, k: int = 8) -> list[tuple[str, float]]: ...


#: A semantic-only passage is admitted only when its similarity to the query is
#: strictly positive. Cosine <= 0 means "unrelated or opposed", never a recall
#: candidate. This is a similarity guard, not a tuned threshold: real embeddings
#: return positive similarities for the nearest passages, so in production the
#: reserve is filled by the genuinely-most-similar missed passages; it only
#: suppresses recall over a corpus with nothing even weakly similar to the query.
_MIN_SEMANTIC_SIMILARITY = 0.0


def _reserve_for(max_results: int) -> int:
    """How many of ``max_results`` slots are reserved for the most-similar
    passages the lexical lane missed. Floor-half keeps the top ``max_results -
    reserve`` lexical hits whenever lexical hits exist (so a strong lexical hit is
    never fully displaced); a single-slot request reserves nothing, so the best
    lexical hit always wins the one slot."""
    return max_results // 2


def _truncate_excerpt(excerpt: str) -> str:
    if len(excerpt) <= MAX_EXCERPT_LENGTH:
        return excerpt
    return excerpt[: MAX_EXCERPT_LENGTH - len(_TRUNCATION_MARKER)] + _TRUNCATION_MARKER


class HybridCorpus:
    """Wrap a corpus so passage search is semantically recalled and re-ranked."""

    def __init__(self, inner: InvestigationCorpus, reranker: PassageReranker | None) -> None:
        self._inner = inner
        self._reranker = reranker

    @property
    def corpus_id(self) -> str:
        return self._inner.corpus_id

    def search_passages(self, request: PassageSearchRequest) -> PassageSearchResult:
        if self._reranker is None:
            return self._inner.search_passages(request)

        expanded_limit = min(request.maxResults * CANDIDATE_FACTOR, MAX_RESULT_COUNT)
        lexical = self._inner.search_passages(
            request.model_copy(update={"maxResults": expanded_limit})
        )
        hit_by_id = {hit.passageId: hit for hit in lexical.hits}  # preserves lexical order

        recall_fn = getattr(self._reranker, "recall", None)
        if recall_fn is None:
            return self._rerank_only(request, lexical, hit_by_id)
        return self._recall_additive(request, lexical, hit_by_id, recall_fn)

    def _rerank_only(
        self,
        request: PassageSearchRequest,
        lexical: PassageSearchResult,
        hit_by_id: dict[str, PassageSearchHit],
    ) -> PassageSearchResult:
        if not lexical.hits:
            return lexical
        ordered_ids = self._reranker.order(request.query, list(hit_by_id))
        reordered = [hit_by_id[pid] for pid in ordered_ids if pid in hit_by_id]
        top = reordered[: request.maxResults]
        return lexical.model_copy(
            update={
                "hits": top,
                "returnedCount": len(top),
                "truncated": lexical.truncated or len(reordered) > len(top),
            }
        )

    def _recall_additive(
        self,
        request: PassageSearchRequest,
        lexical: PassageSearchResult,
        hit_by_id: dict[str, PassageSearchHit],
        recall_fn,
    ) -> PassageSearchResult:
        k = request.maxResults
        lexical_ids = list(hit_by_id)  # lexical order
        recall_k = min(max(k * CANDIDATE_FACTOR, 8), MAX_RESULT_COUNT)
        semantic = recall_fn(request.query, k=recall_k)
        semantic_score_by_id = {pid: score for pid, score in semantic}

        # Passages the lexical lane missed entirely, above the similarity guard,
        # in descending-similarity order -- the recall candidates.
        semantic_only = [
            pid
            for pid, score in semantic
            if pid not in hit_by_id and score > _MIN_SEMANTIC_SIMILARITY
        ]
        if not semantic_only:
            # Nothing to add (empty index, or nothing similar the lexical lane
            # missed): behave exactly like the lexical top-k.
            return self._rerank_only(request, lexical, hit_by_id)

        reserve = min(_reserve_for(k), len(semantic_only))
        lexical_keep = k - reserve

        selected: list[str] = []
        # 1. Protect the top lexical hits (never fully displaced).
        selected.extend(lexical_ids[:lexical_keep])
        # 2. Reserve slots for the most-similar missed passages (the recall gain).
        selected.extend(semantic_only[:reserve])
        # 3. Fill any remaining slots: leftover lexical first, then leftover
        #    semantic-only -- so a thin lexical lane yields to more real recall.
        if len(selected) < k:
            for pid in lexical_ids[lexical_keep:]:
                if len(selected) >= k:
                    break
                selected.append(pid)
        if len(selected) < k:
            for pid in semantic_only[reserve:]:
                if len(selected) >= k:
                    break
                selected.append(pid)

        # Order the chosen passages by the fused ranking for a coherent result.
        fused_order = [
            pid for pid, _ in reciprocal_rank_fusion([lexical_ids, [p for p, _ in semantic]], k=DEFAULT_RRF_K)
        ]
        rank = {pid: index for index, pid in enumerate(fused_order)}
        selected.sort(key=lambda pid: rank.get(pid, len(fused_order)))

        hits: list[PassageSearchHit] = []
        for pid in selected:
            if pid in hit_by_id:
                hits.append(hit_by_id[pid])
            else:
                hits.append(self._semantic_only_hit(pid, semantic_score_by_id.get(pid, 0.0)))

        total_available = len({*lexical_ids, *semantic_only})
        return lexical.model_copy(
            update={
                "hits": hits,
                "returnedCount": len(hits),
                "truncated": total_available > len(hits),
            }
        )

    def _semantic_only_hit(self, passage_id: str, score: float) -> PassageSearchHit:
        """Materialise a result for a passage the semantic lane surfaced but the
        lexical lane dropped. Valid because ``HybridCorpus`` only decorates
        passages-only draft corpora: they carry no evidence links, dates, or
        lexical score factors, so those projections are empty by construction."""
        passage = self._inner.get_passage(passage_id)
        document = self._inner.get_document(passage.documentId)
        source = self._inner.get_source(document.sourceId)
        return PassageSearchHit(
            passageId=passage.id,
            documentId=document.id,
            sourceId=source.id,
            excerpt=_truncate_excerpt(passage.excerpt),
            locator=passage.locator,
            gapNote=passage.gapNote,
            score=score,
            scoreFactors=[],
            matchedDates=[],
            matchedDateTotalCount=0,
            matchedDateReturnedCount=0,
            matchedDatesTruncated=False,
            evidenceLinks=[],
            evidenceLinkTotalCount=0,
            evidenceLinkReturnedCount=0,
            evidenceLinksTruncated=False,
            sourceTitle=source.title,
            sourceType=source.sourceType.value,
            sourceCurationStatus=source.curationStatus.value,
            documentVisibility=document.visibility.value,
            sourceLimitations=source.knownLimitations,
            documentLimitations=document.knownLimitations,
        )

    def __getattr__(self, name: str):
        # Delegate every non-overridden attribute to the inner corpus. Guarded so
        # a lookup during __init__ (before _inner exists) fails cleanly instead of
        # recursing.
        if name in {"_inner", "_reranker"}:
            raise AttributeError(name)
        return getattr(self._inner, name)


__all__ = ["CANDIDATE_FACTOR", "HybridCorpus", "PassageReranker", "PassageRecaller"]
