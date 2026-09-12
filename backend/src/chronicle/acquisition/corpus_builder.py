"""corpus_builder: acquired sources + passages -> a valid GeneratedInvestigation.

The output is an *evidence-only draft*: it carries the acquired sources, documents,
and passages the agents will retrieve from, plus the minimal presentation scaffolding
the package contract requires (one scope place, one non-material narrative block, one
scene). It deliberately contains no claims, relationships, events, knowledge states,
timeline, or map — those are the agents' and reviewers' job, not acquisition's — so it
fabricates no historical assertions. It is marked ``status=partial`` with its omissions
spelled out, and every source is ``curationStatus=passages-extracted`` with honest
``knownLimitations`` noting it is auto-acquired and unreviewed.

Because the output is a normal (if partial) GeneratedInvestigation, the existing
PackageBackedCorpus loads it and the four agents investigate it exactly as they do a
curated fixture. The package can later be enriched in place as agents add records.

Topic-agnostic: nothing here names or branches on a subject (see
tests/ai/tools/test_no_topic_branching_guard.py).
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timezone

from ..contracts.enums import (
    ApprovalStatus,
    CurationStatus,
    DatePrecision,
    Facet,
    FocusKind,
    GenerationOutcome,
    LocationPrecision,
    PackageStatus,
    RequestType,
    RequestedDepth,
    ReviewStatus,
    Visibility,
)
from ..contracts.generated_investigation import (
    SUPPORTED_GENERATED_INVESTIGATION_VERSION,
    GeneratedInvestigation,
    GenerationReport,
    InteractionSpecification,
    InvestigationRequest,
    InvestigationScene,
    InvestigationScope,
    Presentation,
)
from ..contracts.shared import (
    Document,
    HistoricalDate,
    NarrativeBlock,
    Passage,
    PlaceEntity,
    PlacePeriodRecord,
    Source,
)
from ..contracts.validation import validate_generated_investigation
from .assembly import Enrichment
from .contracts import AcquiredSource, ExtractedPassage

_UNREVIEWED_POLITY = "Not established (auto-acquired draft; requires research)"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _slug(text: str) -> str:
    cleaned = "".join(char if char.isalnum() else "-" for char in text.lower())
    parts = [part for part in cleaned.split("-") if part]
    return "-".join(parts)[:48] or "topic"


def deterministic_package_id(topic: str, acquired: list[AcquiredSource]) -> str:
    """Same topic + same acquired content -> same package id, so re-runs are stable."""
    digest = hashlib.sha256()
    digest.update(topic.encode("utf-8"))
    for content_hash in sorted(source.contentSha256 for source in acquired):
        digest.update(content_hash.encode("utf-8"))
    return f"acq-{_slug(topic)}-{digest.hexdigest()[:12]}"


def _historical_range(earliest: date, latest: date, label: str | None) -> HistoricalDate:
    precision = DatePrecision.EXACT if earliest == latest else DatePrecision.RANGE
    return HistoricalDate(precision=precision, earliest=earliest, latest=latest, label=label)


def build_corpus(
    *,
    topic: str,
    interpreted_question: str,
    geographic_scope: list[str],
    date_earliest: date,
    date_latest: date,
    acquired: list[AcquiredSource],
    passages: list[ExtractedPassage],
    date_label: str | None = None,
    request_type: RequestType = RequestType.EVENT_RECONSTRUCTION,
    requested_depth: RequestedDepth = RequestedDepth.STANDARD,
    generated_at: datetime | None = None,
    package_id: str | None = None,
    enrich: Callable[[list[Passage]], Enrichment] | None = None,
) -> GeneratedInvestigation:
    if not geographic_scope:
        raise ValueError("geographic_scope must name at least one place for the scope")

    generated_at = generated_at or _utcnow()
    package_id = package_id or deterministic_package_id(topic, acquired)
    scope_date = _historical_range(date_earliest, date_latest, date_label)

    # --- sources + documents (one document per source) -----------------------
    source_id_by_candidate: dict[str, str] = {}
    document_id_by_candidate: dict[str, str] = {}
    sources: list[Source] = []
    documents: list[Document] = []
    for index, acquired_source in enumerate(acquired):
        candidate = acquired_source.candidate
        source_id = f"src-{index:04d}"
        document_id = f"doc-{index:04d}"
        source_id_by_candidate[candidate.candidateId] = source_id
        document_id_by_candidate[candidate.candidateId] = document_id

        acquired_day = acquired_source.retrievedAt.date()
        sources.append(
            Source(
                id=source_id,
                title=candidate.title,
                sourceType=candidate.sourceType,
                authorOrOrigin=candidate.author or f"{candidate.connector} (auto-acquired)",
                dateOfSource=HistoricalDate(
                    precision=DatePrecision.APPROXIMATE,
                    earliest=acquired_day,
                    latest=acquired_day,
                    label="acquisition date (source date unverified)",
                ),
                originalLanguage=candidate.language or "unknown",
                rightsStatus=candidate.rightsStatus,
                curationStatus=CurationStatus.PASSAGES_EXTRACTED,
                knownLimitations=(
                    f"Auto-acquired via the {candidate.connector} connector and not human-reviewed; "
                    "edition, translation, and source date are unverified."
                ),
                linkOrLocation=candidate.url or candidate.candidateId,
            )
        )
        documents.append(
            Document(
                id=document_id,
                sourceId=source_id,
                editionCitation=(
                    f"Full text retrieved {acquired_day.isoformat()} "
                    f"(sha256 {acquired_source.contentSha256[:12]})"
                ),
                visibility=Visibility.PUBLIC,
                knownLimitations="Auto-extracted plain text; no edition or translation verification.",
            )
        )

    # --- passages ------------------------------------------------------------
    passages_by_candidate: dict[str, list[ExtractedPassage]] = defaultdict(list)
    for extracted in passages:
        passages_by_candidate[extracted.sourceCandidateId].append(extracted)

    built_passages: list[Passage] = []
    passage_ids: list[str] = []
    for candidate_id, document_id in document_id_by_candidate.items():
        for extracted in passages_by_candidate.get(candidate_id, []):
            passage_id = f"psg-{document_id.split('-')[1]}-{extracted.ordinal:04d}"
            passage_ids.append(passage_id)
            built_passages.append(
                Passage(
                    id=passage_id,
                    documentId=document_id,
                    excerpt=extracted.text,
                    locator=extracted.locator,
                )
            )

    # --- optional structured enrichment (stages 7/9/12, injected) -----------
    # The enricher runs over the *built* passages so its evidence links cite the
    # real passage ids assigned above. Default None keeps this an evidence-only
    # draft with byte-identical behavior. An enricher that finds nothing grounded
    # returns an empty Enrichment and the corpus likewise stays evidence-only.
    enrichment = enrich(built_passages) if enrich is not None else None
    has_enrichment = enrichment is not None and not enrichment.is_empty
    events = list(enrichment.events) if has_enrichment else []
    evidence_links = list(enrichment.evidence_links) if has_enrichment else []
    timeline = list(enrichment.timeline) if has_enrichment else []

    # --- geography: scope scaffolding, upgraded by extracted + geolocated ----
    # Scope names are explicitly unreviewed stubs (no coordinates). When the
    # enricher resolved a place of the same name, the richer extracted record
    # wins and the duplicate stub is dropped, so no place is double-listed.
    period_label = date_label or f"{date_earliest.year}-{date_latest.year}"
    scope_places: list[PlaceEntity] = []
    for index, place_name in enumerate(dict.fromkeys(geographic_scope)):
        scope_places.append(
            PlaceEntity(
                id=f"place-{index:04d}",
                entityType="place",
                canonicalName=place_name,
                periodRecords=[
                    PlacePeriodRecord(
                        periodLabel=period_label,
                        nameAtTime=place_name,
                        controllingPolity=_UNREVIEWED_POLITY,
                        precision=LocationPrecision.APPROXIMATE,
                    )
                ],
                reviewStatus=ReviewStatus.PROPOSED,
            )
        )
    if has_enrichment:
        enriched_names = {place.canonicalName.casefold() for place in enrichment.places}
        scope_places = [
            place for place in scope_places if place.canonicalName.casefold() not in enriched_names
        ]
        places = scope_places + list(enrichment.places)
    else:
        places = scope_places

    # --- capability flags: timeline lights up only when events were built ----
    # Map stays omitted: the contract couples it to a raster MapAsset, and the
    # generated-map rendering over these coordinates is a later slice. We never
    # advertise a capability the workspace cannot yet render for this corpus.
    coordinates_present = any(place.coordinates is not None for place in places)
    omitted_capabilities = ["map", "graph", "claims", "relationships", "knowledge_states"]
    enabled_facets = [Facet.EVIDENCE]
    if not has_enrichment:
        omitted_capabilities.insert(0, "timeline")
    else:
        enabled_facets.append(Facet.TIMELINE)

    # --- presentation scaffolding (one non-material block, one scene) --------
    if has_enrichment:
        summary_text = (
            f"Draft evidence corpus for “{topic}”. "
            f"{len(sources)} source(s) and {len(built_passages)} passage(s) were auto-acquired "
            f"from free sources; {len(events)} grounded event(s) and a timeline were extracted. "
            "All records are proposed drafts and have not been reviewed. No synthesis, claims, "
            "relationships, or knowledge states have been generated yet."
        )
    else:
        summary_text = (
            f"Draft evidence corpus for “{topic}”. "
            f"{len(sources)} source(s) and {len(built_passages)} passage(s) were auto-acquired "
            "from free sources and have not been reviewed. No synthesis, claims, relationships, "
            "events, knowledge states, timeline, or geography have been generated yet."
        )
    summary_block = NarrativeBlock(
        id="nb-0000",
        order=0,
        text=summary_text,
        isMaterialAssertion=False,
    )
    scene = InvestigationScene(
        id="scene-0000",
        title=interpreted_question or topic,
        curationStatus=CurationStatus.IDENTIFIED,
        dateRange=scope_date,
        placeIds=[place.id for place in places],
        sourceIds=[source.id for source in sources],
        documentIds=[document.id for document in documents],
        passageIds=passage_ids,
        eventIds=[event.id for event in events],
        narrativeBlockIds=[summary_block.id],
    )
    presentation = Presentation(
        title=topic,
        synthesis=[summary_block],
        sceneIds=[scene.id],
    )
    interaction_spec = InteractionSpecification(
        defaultSceneId=scene.id,
        focusKinds=[FocusKind.SOURCE, FocusKind.PASSAGE],
        enabledFacets=enabled_facets,
        omittedCapabilities=omitted_capabilities,
    )

    omissions = [
        "Sources were auto-acquired from free connectors and are not human-reviewed.",
    ]
    if has_enrichment:
        omissions.insert(
            0,
            "Draft corpus: grounded events and a timeline were extracted, but no synthesis, "
            "claims, relationships, or knowledge states have been generated.",
        )
        if coordinates_present:
            omissions.append(
                "Geography carries period-aware coordinates for located places, but controlling "
                "polity is unreviewed and the generated map is not yet rendered."
            )
        else:
            omissions.append(
                "Extracted places could not be located in period; no coordinates were asserted."
            )
    else:
        omissions.insert(
            0,
            "Evidence-only corpus: no synthesis, claims, relationships, events, "
            "knowledge states, timeline, or map has been generated.",
        )
        omissions.append(
            "Geography is a scope placeholder; controlling polity and coordinates are not established."
        )
    report = GenerationReport(
        outcome=GenerationOutcome.PARTIAL,
        omissions=omissions,
    )

    investigation = GeneratedInvestigation(
        schemaVersion=SUPPORTED_GENERATED_INVESTIGATION_VERSION,
        packageId=package_id,
        packageRevision=1,
        generatedAt=generated_at,
        request=InvestigationRequest(
            id="req-0000",
            rawInput=topic,
            requestType=request_type,
            requestedDepth=requested_depth,
            createdAt=generated_at,
        ),
        scope=InvestigationScope(
            interpretedQuestion=interpreted_question,
            dateRange=scope_date,
            geographicScope=list(dict.fromkeys(geographic_scope)),
            approvalStatus=ApprovalStatus.PROPOSED,
        ),
        status=PackageStatus.PARTIAL,
        presentation=presentation,
        entities=list(places),
        events=events,
        sources=sources,
        documents=documents,
        passages=built_passages,
        evidenceLinks=evidence_links,
        timeline=timeline,
        scenes=[scene],
        interactionSpec=interaction_spec,
        generationReport=report,
    )

    # Fail loudly here rather than at corpus load time if scaffolding drifts.
    return validate_generated_investigation(investigation.model_dump(mode="json"))
