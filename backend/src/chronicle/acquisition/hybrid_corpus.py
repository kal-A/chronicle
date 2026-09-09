"""A corpus decorator that adds semantic re-ranking to passage search.

``HybridCorpus`` wraps any :class:`InvestigationCorpus` and overrides only
``search_passages``: it asks the inner corpus for an *expanded* lexical
candidate set, then reorders those candidates with a semantic reranker (RRF fuse
of the lexical order and a local-embedding ranking) before returning the
caller's requested top-k. Every other method is delegated to the inner corpus
unchanged, so the agents' typed tools, the run manager, and the audit trail see
an ordinary corpus.

The reranker is optional: with no reranker (or an empty semantic index) the
result is exactly the inner corpus's lexical result, so curated corpora and any
environment without a local embedding model behave as before. This is a
precision re-rank within the lexical candidate set -- it does not add recall for
passages the lexical lane misses entirely (a deliberate, documented first
increment).
"""

from __future__ import annotations

from typing import Protocol

from ..corpus.contracts import MAX_RESULT_COUNT, PassageSearchRequest, PassageSearchResult
from ..corpus.protocol import InvestigationCorpus

#: How many lexical candidates to gather per requested result before re-ranking.
#: Wider than the request so the semantic lane can promote strong matches the
#: lexical score ranked lower, bounded by the corpus tool's hard result cap.
CANDIDATE_FACTOR = 4


class PassageReranker(Protocol):
    def order(self, query: str, candidate_ids: list[str]) -> list[str]: ...


class HybridCorpus:
    """Wrap a corpus so passage search is semantically re-ranked."""

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
        if not lexical.hits:
            return lexical

        # dict preserves the lexical order of the hits
        hit_by_id = {hit.passageId: hit for hit in lexical.hits}
        ordered_ids = self._reranker.order(request.query, list(hit_by_id))
        reordered = [hit_by_id[passage_id] for passage_id in ordered_ids if passage_id in hit_by_id]
        top = reordered[: request.maxResults]
        return lexical.model_copy(
            update={
                "hits": top,
                "returnedCount": len(top),
                "truncated": lexical.truncated or len(reordered) > len(top),
            }
        )

    def __getattr__(self, name: str):
        # Delegate every non-overridden attribute to the inner corpus. Guarded so
        # a lookup during __init__ (before _inner exists) fails cleanly instead of
        # recursing.
        if name in {"_inner", "_reranker"}:
            raise AttributeError(name)
        return getattr(self._inner, name)


__all__ = ["CANDIDATE_FACTOR", "HybridCorpus", "PassageReranker"]
