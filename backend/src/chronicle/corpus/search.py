"""Deterministic, bounded, evidence-preserving lexical passage search."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..contracts.shared import HistoricalDate
from .bounds import CollectionBudget
from .contracts import (
    MAX_EXCERPT_LENGTH,
    PassageDateMatch,
    PassageDateRole,
    PassageSearchHit,
    PassageSearchRequest,
    PassageSearchResult,
    SearchScoreFactor,
)
from .errors import UnknownRecordError
from .indexing import CorpusIndex
from .projections import project_evidence_link

WEIGHT_EXACT_PHRASE_EXCERPT = 10.0
WEIGHT_EXACT_PHRASE_TITLE = 6.0
WEIGHT_ALL_TOKENS = 5.0
WEIGHT_PARTIAL_TOKEN = 3.0
WEIGHT_LINKED_RECORD_TEXT_MATCH = 3.0

_TRUNCATION_MARKER = " […]"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


def _contains_token_sequence(haystack: list[str], needle: list[str]) -> bool:
    if not needle or len(needle) > len(haystack):
        return False
    width = len(needle)
    return any(haystack[offset : offset + width] == needle for offset in range(len(haystack) - width + 1))


def _truncate(excerpt: str) -> str:
    if len(excerpt) <= MAX_EXCERPT_LENGTH:
        return excerpt
    return excerpt[: MAX_EXCERPT_LENGTH - len(_TRUNCATION_MARKER)] + _TRUNCATION_MARKER


def _validate_ids(ids: list[str], known: dict, owner: str) -> None:
    for record_id in ids:
        if record_id not in known:
            raise UnknownRecordError(f'{owner} references unknown record "{record_id}"')


def _date_key(value) -> tuple[int, int]:
    """A filter date as the same (year, day-of-year) key HistoricalDate orders on."""
    return (value.year, value.timetuple().tm_yday)


def _intervals_overlap(historical: HistoricalDate, earliest, latest) -> bool:
    # Cross-era comparison (ADR-005): order on the signed-year key so BC records
    # (which carry no calendar date) still filter against CE date-range queries.
    return (earliest is None or historical.upper_key >= _date_key(earliest)) and (
        latest is None or historical.lower_key <= _date_key(latest)
    )


def _date_candidates(
    index: CorpusIndex, passage, source, links
) -> Iterable[tuple[PassageDateRole, str | None, HistoricalDate]]:
    if passage.sentTime is not None:
        yield PassageDateRole.SENT_TIME, None, passage.sentTime
    if passage.receivedTime is not None:
        yield PassageDateRole.RECEIVED_TIME, None, passage.receivedTime
    yield PassageDateRole.SOURCE_DATE, None, source.dateOfSource
    for link in links:
        if link.targetType.value == "event":
            event = index.events_by_id.get(link.targetId)
            if event is not None:
                yield PassageDateRole.LINKED_EVENT_TIME, event.id, event.eventTime
        elif link.targetType.value == "knownAtTime":
            state = index.knowledge_states_by_id.get(link.targetId)
            if state is not None:
                yield PassageDateRole.LINKED_ACTOR_AWARENESS_TIME, state.id, state.asOfDate


def _matched_dates(
    index: CorpusIndex,
    passage,
    source,
    links,
    request: PassageSearchRequest,
) -> list[PassageDateMatch]:
    if request.dateRange is None:
        return []
    selected = set(request.dateRoles)
    matches = [
        PassageDateMatch(role=role, linkedTargetId=target_id, historicalDate=historical)
        for role, target_id, historical in _date_candidates(index, passage, source, links)
        if role in selected
        and (
            role != PassageDateRole.LINKED_EVENT_TIME
            or not request.eventIds
            or target_id in request.eventIds
        )
        and _intervals_overlap(historical, request.dateRange.earliest, request.dateRange.latest)
    ]
    return sorted(
        matches,
        key=lambda match: (
            match.role.value,
            match.linkedTargetId or "",
            match.historicalDate.lower_key,
            match.historicalDate.upper_key,
        ),
    )


def _target(index: CorpusIndex, target_type: str, target_id: str):
    tables = {
        "claim": index.claims_by_id,
        "relationship": index.relationships_by_id,
        "event": index.events_by_id,
        "knownAtTime": index.knowledge_states_by_id,
    }
    return tables[target_type][target_id]


def _project_link(index: CorpusIndex, link, passage, document, source):
    target = _target(index, link.targetType.value, link.targetId)
    return project_evidence_link(
        link=link,
        passage=passage,
        document=document,
        source=source,
        target=target,
    )


def search_passages(index: CorpusIndex, request: PassageSearchRequest) -> PassageSearchResult:
    _validate_ids(request.sourceIds, index.sources_by_id, "PassageSearchRequest.sourceIds")
    _validate_ids(request.documentIds, index.documents_by_id, "PassageSearchRequest.documentIds")
    _validate_ids(request.claimIds, index.claims_by_id, "PassageSearchRequest.claimIds")
    _validate_ids(request.relationshipIds, index.relationships_by_id, "PassageSearchRequest.relationshipIds")
    _validate_ids(request.entityIds, index.entities_by_id, "PassageSearchRequest.entityIds")
    _validate_ids(request.eventIds, index.events_by_id, "PassageSearchRequest.eventIds")

    query_tokens = _tokenize(request.query)
    entity_names_by_id = {
        entity_id: [
            _tokenize(name)
            for name in [
                index.entities_by_id[entity_id].canonicalName,
                *_aliases(index, entity_id),
            ]
        ]
        for entity_id in request.entityIds
    }

    hits: list[PassageSearchHit] = []
    for passage in index.passages_by_id.values():
        document = index.documents_by_id.get(passage.documentId)
        if document is None:
            continue
        source = index.sources_by_id.get(document.sourceId)
        if source is None:
            continue
        if request.sourceIds and document.sourceId not in request.sourceIds:
            continue
        if request.documentIds and passage.documentId not in request.documentIds:
            continue

        passage_links = sorted(index.evidence_links_by_passage.get(passage.id, []), key=lambda link: link.id)
        linked_claim_ids = {link.targetId for link in passage_links if link.targetType.value == "claim"}
        linked_relationship_ids = {link.targetId for link in passage_links if link.targetType.value == "relationship"}
        linked_event_ids = {link.targetId for link in passage_links if link.targetType.value == "event"}
        evidence_roles = {link.role.value for link in passage_links}

        requested_roles = set(request.evidenceRoles)

        def _has_scoped_link(target_type: str, target_ids: list[str]) -> bool:
            return any(
                link.targetType.value == target_type
                and link.targetId in target_ids
                and (not requested_roles or link.role.value in requested_roles)
                for link in passage_links
            )

        if request.claimIds and not _has_scoped_link("claim", request.claimIds):
            continue
        if request.relationshipIds and not _has_scoped_link(
            "relationship", request.relationshipIds
        ):
            continue
        if request.eventIds and not _has_scoped_link("event", request.eventIds):
            continue
        if request.evidenceRoles and not (
            request.claimIds or request.relationshipIds or request.eventIds
        ) and not requested_roles & evidence_roles:
            continue
        if request.sourceClassifications and source.sourceType.value not in request.sourceClassifications:
            continue
        passage_tokens = _tokenize(passage.excerpt)
        matched_entity_ids: list[str] = []
        matched_entity_terms: set[str] = set()
        for entity_id, names in entity_names_by_id.items():
            matched_names = [name for name in names if _contains_token_sequence(passage_tokens, name)]
            if matched_names:
                matched_entity_ids.append(entity_id)
                for name in matched_names:
                    matched_entity_terms.update(name)
        if request.entityIds and not matched_entity_ids:
            continue

        date_matches = _matched_dates(index, passage, source, passage_links, request)
        if request.dateRange is not None and not date_matches:
            continue
        factors = _score(index, passage, source, document, query_tokens, linked_claim_ids, linked_relationship_ids)
        if not factors:
            continue
        if matched_entity_ids:
            factors.append(
                _factor(
                    "entity_name_filter_match",
                    1.0,
                    matched_entity_terms,
                    matched_entity_ids,
                )
            )
        score = sum(factor.contribution for factor in factors)

        hits.append(
            PassageSearchHit(
                passageId=passage.id,
                documentId=passage.documentId,
                sourceId=source.id,
                excerpt=_truncate(passage.excerpt),
                locator=passage.locator,
                gapNote=passage.gapNote,
                score=score,
                scoreFactors=factors,
                matchedDates=date_matches,
                matchedDateTotalCount=len(date_matches),
                matchedDateReturnedCount=len(date_matches),
                matchedDatesTruncated=False,
                evidenceLinks=[_project_link(index, link, passage, document, source) for link in passage_links],
                evidenceLinkTotalCount=len(passage_links),
                evidenceLinkReturnedCount=len(passage_links),
                evidenceLinksTruncated=False,
                sourceTitle=source.title,
                sourceType=source.sourceType.value,
                sourceCurationStatus=source.curationStatus.value,
                documentVisibility=document.visibility.value,
                sourceLimitations=source.knownLimitations,
                documentLimitations=document.knownLimitations,
            )
        )

    hits.sort(key=lambda hit: (-hit.score, hit.passageId))
    total_matched = len(hits)
    limited = hits[: request.maxResults]
    evidence_budget = CollectionBudget(request.maxResults)
    ordered_links: list[list] = []
    requested_targets = set(request.claimIds) | set(request.relationshipIds) | set(request.eventIds)
    requested_roles = set(request.evidenceRoles)
    for hit in limited:
        ordered_links.append(
            sorted(
                hit.evidenceLinks,
                key=lambda link: (
                    0 if not requested_roles or link.role in requested_roles else 1,
                    0 if not requested_targets or link.targetId in requested_targets else 1,
                    link.evidenceLinkId,
                ),
            )
        )
    allocated_links = _round_robin_allocate(ordered_links, evidence_budget)
    allocated_dates = _round_robin_allocate(
        [hit.matchedDates for hit in limited],
        CollectionBudget(request.maxResults),
    )
    term_budget = CollectionBudget(request.maxResults)
    record_budget = CollectionBudget(request.maxResults)

    bounded_hits: list[PassageSearchHit] = []
    for hit, returned_links, returned_dates in zip(
        limited,
        allocated_links,
        allocated_dates,
        strict=True,
    ):
        bounded_factors: list[SearchScoreFactor] = []
        for factor in hit.scoreFactors:
            matched_terms = term_budget.take(factor.matchedTerms)
            matched_record_ids = record_budget.take(factor.matchedRecordIds)
            bounded_factors.append(
                factor.model_copy(
                    update={
                        "matchedTerms": matched_terms,
                        "matchedTermReturnedCount": len(matched_terms),
                        "matchedTermsTruncated": len(matched_terms)
                        < factor.matchedTermTotalCount,
                        "matchedRecordIds": matched_record_ids,
                        "matchedRecordReturnedCount": len(matched_record_ids),
                        "matchedRecordIdsTruncated": len(matched_record_ids)
                        < factor.matchedRecordTotalCount,
                    }
                )
            )
        bounded_hits.append(
            hit.model_copy(
                update={
                    "scoreFactors": bounded_factors,
                    "matchedDates": returned_dates,
                    "matchedDateReturnedCount": len(returned_dates),
                    "matchedDatesTruncated": len(returned_dates)
                    < hit.matchedDateTotalCount,
                    "evidenceLinks": returned_links,
                    "evidenceLinkReturnedCount": len(returned_links),
                    "evidenceLinksTruncated": len(returned_links) < hit.evidenceLinkTotalCount,
                }
            )
        )
    return PassageSearchResult(
        corpusId=request.corpusId,
        query=request.query,
        totalMatched=total_matched,
        returnedCount=len(bounded_hits),
        hits=bounded_hits,
        truncated=total_matched > len(bounded_hits),
    )


def _aliases(index: CorpusIndex, entity_id: str) -> list[str]:
    return list(getattr(index.entities_by_id[entity_id], "alsoKnownAs", []) or [])


def _factor(name: str, contribution: float, terms: Iterable[str], records: Iterable[str] = ()) -> SearchScoreFactor:
    matched_terms = sorted(set(terms))
    matched_records = sorted(set(records))
    return SearchScoreFactor(
        factor=name,
        contribution=contribution,
        matchedTerms=matched_terms,
        matchedTermTotalCount=len(matched_terms),
        matchedTermReturnedCount=len(matched_terms),
        matchedTermsTruncated=False,
        matchedRecordIds=matched_records,
        matchedRecordTotalCount=len(matched_records),
        matchedRecordReturnedCount=len(matched_records),
        matchedRecordIdsTruncated=False,
    )


def _round_robin_allocate(groups: list[list], budget: CollectionBudget) -> list[list]:
    allocated: list[list] = [[] for _group in groups]
    offset = 0
    while budget.remaining:
        allocated_any = False
        for group_index, group in enumerate(groups):
            if offset < len(group) and budget.remaining:
                allocated[group_index].extend(budget.take([group[offset]]))
                allocated_any = True
        if not allocated_any:
            break
        offset += 1
    return allocated


def _score(index, passage, source, document, query_tokens, linked_claim_ids, linked_relationship_ids):
    factors: list[SearchScoreFactor] = []
    excerpt_tokens = _tokenize(passage.excerpt)
    excerpt_token_set = set(excerpt_tokens)
    query_set = set(query_tokens)

    if _contains_token_sequence(excerpt_tokens, query_tokens):
        factors.append(_factor("exact_phrase_excerpt", WEIGHT_EXACT_PHRASE_EXCERPT, query_tokens))
    for factor_name, text in (
        ("exact_phrase_source_title", source.title),
        ("exact_phrase_edition_citation", document.editionCitation),
    ):
        if _contains_token_sequence(_tokenize(text), query_tokens):
            factors.append(_factor(factor_name, WEIGHT_EXACT_PHRASE_TITLE, query_tokens))

    overlap = query_set & excerpt_token_set
    if overlap:
        if overlap == query_set:
            factors.append(_factor("all_query_terms_excerpt", WEIGHT_ALL_TOKENS, overlap))
        else:
            factors.append(
                _factor(
                    "partial_query_terms_excerpt",
                    WEIGHT_PARTIAL_TOKEN * len(overlap) / len(query_set),
                    overlap,
                )
            )

    matching_claim_ids: list[str] = []
    linked_claim_terms: set[str] = set()
    for claim_id in sorted(linked_claim_ids):
        overlap = query_set & set(_tokenize(index.claims_by_id[claim_id].statement))
        if overlap:
            matching_claim_ids.append(claim_id)
            linked_claim_terms.update(overlap)
    if linked_claim_terms:
        factors.append(
            _factor(
                "linked_claim_text",
                WEIGHT_LINKED_RECORD_TEXT_MATCH * len(linked_claim_terms) / len(query_set),
                linked_claim_terms,
                matching_claim_ids,
            )
        )

    matching_relationship_ids: list[str] = []
    linked_relationship_terms: set[str] = set()
    for relationship_id in sorted(linked_relationship_ids):
        overlap = query_set & set(_tokenize(index.relationships_by_id[relationship_id].relationshipType))
        if overlap:
            matching_relationship_ids.append(relationship_id)
            linked_relationship_terms.update(overlap)
    if linked_relationship_terms:
        factors.append(
            _factor(
                "linked_relationship_type",
                WEIGHT_LINKED_RECORD_TEXT_MATCH * len(linked_relationship_terms) / len(query_set),
                linked_relationship_terms,
                matching_relationship_ids,
            )
        )
    return factors
