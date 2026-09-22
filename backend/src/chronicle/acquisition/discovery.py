"""Discovery aggregation: fan a query across connectors, merge, gate, dedupe, rank.

Runs every connector's ``discover``, drops candidates whose full text is not
available (metadata/snippets are never evidence), deduplicates by candidate id,
and then selects the ingestable candidates by **topic relevance** so that a
namesake (e.g. a film that shares only one word with the topic) does not crowd
out the on-topic sources. Relevance is pure token overlap against the topic and
the scope-resolved terms — no subject names in code, so the anti-topic-branching
guard still holds. A connector that fails is skipped, not fatal — one dead source
must never sink the whole investigation; its error is collected for reporting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .connectors.base import ConnectorError, SourceConnector
from .contracts import DiscoveryQuery, SourceCandidate

#: Very common words carry no disambiguating signal, so they are ignored when
#: matching a candidate to a topic. Deliberately small and generic (no subject
#: vocabulary) — the goal is to drop articles/prepositions/question words, not to
#: encode any domain.
_STOPWORDS = frozenset(
    {
        "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "was", "were",
        "is", "are", "be", "by", "with", "at", "as", "its", "it", "that", "this",
        "from", "about", "into", "over", "what", "who", "whom", "when", "where",
        "why", "how", "did", "do", "does", "which",
    }
)

_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass
class DiscoveryResult:
    #: ingestable candidates (full text retrievable) — become corpus evidence
    candidates: list[SourceCandidate] = field(default_factory=list)
    #: reputable pointers whose full text is not freely retrievable — surfaced as
    #: references, never ingested as evidence (rights/free-source discipline)
    references: list[SourceCandidate] = field(default_factory=list)
    #: connector name -> error message, for connectors that failed this run
    errors: dict[str, str] = field(default_factory=dict)


def _tokens(text: str) -> set[str]:
    return {t for t in _WORD_RE.findall(text.lower()) if len(t) >= 3 and t not in _STOPWORDS}


def _candidate_haystacks(candidate: SourceCandidate) -> tuple[str, str]:
    """(title, body) lowercased text used for matching. ``body`` folds in the
    snippet and any connector-provided description — display/ranking signal only,
    never evidence."""

    title = (candidate.title or "").lower()
    description = str(candidate.retrievalMetadata.get("description") or "")
    body = f"{candidate.snippet or ''} {description}".lower()
    return title, body


def _relevance(
    candidate: SourceCandidate,
    *,
    topic_tokens: set[str],
    term_tokens: set[str],
    topic_phrase: str,
) -> float:
    """A deterministic on-topic score: the full topic phrase in the title is the
    strongest signal, scope-term matches next, then individual topic tokens."""

    title, body = _candidate_haystacks(candidate)
    title_tokens = _tokens(title)
    body_tokens = _tokens(body)
    score = 0.0
    if topic_phrase:
        if topic_phrase in title:
            score += 3.0
        elif topic_phrase in body:
            score += 1.5
    score += sum(1.0 for t in topic_tokens if t in title_tokens)
    score += sum(0.5 for t in topic_tokens if t in body_tokens and t not in title_tokens)
    score += sum(2.0 for t in term_tokens if t in title_tokens or t in body_tokens)
    return score


def _is_on_topic(
    candidate: SourceCandidate,
    *,
    topic_tokens: set[str],
    term_tokens: set[str],
    topic_phrase: str,
    multiword_topic: bool,
) -> bool:
    """Whether a candidate is about the topic rather than a namesake.

    With no disambiguating signal (a one-word topic and no scope terms) every
    candidate passes — namesakes cannot be told apart, and dropping recall would
    be worse. When scope terms exist they are the discriminator: a candidate must
    either contain the full topic phrase or match a scope term. With a multi-word
    topic but no terms, matching any topic token is enough (ranking sorts the
    rest)."""

    if not topic_tokens and not term_tokens:
        return True
    title, body = _candidate_haystacks(candidate)
    hay = f"{title} {body}"
    hay_tokens = _tokens(hay)
    if multiword_topic and topic_phrase and topic_phrase in hay:
        return True
    if term_tokens:
        return bool(term_tokens & hay_tokens)
    return bool(topic_tokens & hay_tokens)


def discover_sources(
    connectors: list[SourceConnector],
    query: DiscoveryQuery,
    *,
    max_total: int | None = None,
) -> DiscoveryResult:
    result = DiscoveryResult()
    seen: set[str] = set()
    ingestable: list[SourceCandidate] = []
    for connector in connectors:
        try:
            candidates = connector.discover(query)
        except ConnectorError as error:
            result.errors[connector.name] = str(error)
            continue
        for candidate in candidates:
            if candidate.candidateId in seen:
                continue
            seen.add(candidate.candidateId)
            if not candidate.fullTextAvailable:
                # the evidence gate: not ingestable, but kept as a reference pointer
                result.references.append(candidate)
                continue
            ingestable.append(candidate)

    result.candidates = _select_by_relevance(ingestable, query, max_total=max_total)
    return result


def _select_by_relevance(
    ingestable: list[SourceCandidate],
    query: DiscoveryQuery,
    *,
    max_total: int | None,
) -> list[SourceCandidate]:
    """Keep the on-topic candidates, best first, capped at ``max_total``. Falls
    back to the full ranked set if the topic filter would drop everything, so a
    weak scope never yields an empty corpus."""

    topic_phrase = query.topic.strip().lower()
    topic_tokens = _tokens(query.topic)
    term_tokens: set[str] = set()
    for term in query.terms:
        term_tokens |= _tokens(term)
    multiword_topic = len(topic_tokens) >= 2

    scored: list[tuple[bool, float, int, SourceCandidate]] = []
    for index, candidate in enumerate(ingestable):
        on_topic = _is_on_topic(
            candidate,
            topic_tokens=topic_tokens,
            term_tokens=term_tokens,
            topic_phrase=topic_phrase,
            multiword_topic=multiword_topic,
        )
        score = _relevance(
            candidate,
            topic_tokens=topic_tokens,
            term_tokens=term_tokens,
            topic_phrase=topic_phrase,
        )
        scored.append((on_topic, score, index, candidate))

    pool = [row for row in scored if row[0]] or scored  # never empty out
    pool.sort(key=lambda row: (-row[1], row[2]))  # score desc, then discovery order
    selected = pool if max_total is None else pool[:max_total]
    return [candidate.model_copy(update={"relevance": score}) for _on, score, _i, candidate in selected]
