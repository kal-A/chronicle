# Source Discovery and Acquisition

## Multi-Provider Discovery

The scope planner decomposes a request into names/aliases, dates, actors, institutions, places, document types, primary-source terms, historiographical terms, known events, and map queries. Every query is stored with its scope revision, provider, timestamp, and result set.

Provider categories are scholarly metadata, archives/libraries, official/institutional collections, and curated web fallback. Initial likely adapters include OpenAlex/Crossref metadata and selected archive APIs, but adapter adoption requires current API/rights verification during its implementation phase.

```python
class DiscoveryProvider(Protocol):
    async def search(self, query: DiscoveryQuery) -> list[SourceCandidate]: ...
```

Search snippets and metadata are discovery inputs, never evidence.

## Candidate Registry

Every result is registered before acquisition with provider/query provenance, canonical URL, stable identifiers, title, creator/institution, publication/source dates, source class, language, description, rights/access metadata, full-text availability, relevance estimate, duplicate group, assessment status, and reason.

## Deduplication

Use DOI, archive ID, ISBN+edition, catalogue ID, stable URL, then normalized title/author/year. Fuzzy matching only proposes duplicate groups. Originals, scans, editions, transcriptions, translations, and excerpts remain distinct Documents related to a Source.

## Acquisition Rules

Preferred order: open HTML; public-domain/open PDF; archive OCR/transcript; IIIF; user file; metadata-only. Respect paywalls, authentication, robots rules, licences, and archive terms. If full text is unavailable, retain metadata/link and mark it unprocessed; no stage may claim to have assessed its text.

## Normalization

Preserve original bytes, content hash, acquisition time, MIME type, page/image boundaries, headings, OCR confidence, stable Passage IDs, and mappings back to pages/lines/image regions. Cleaning may create a derived representation but never destroy the citation map.

## Corpus Retrieval

Combine lexical retrieval, embeddings when introduced, metadata and review filters, temporal filters, graph expansion, and source-diversity constraints. Retrieval results include why each passage matched and avoid flooding results with derivative or near-duplicate sources.

## Coverage Report

Report coverage by source class, primary/secondary, perspective/institution/national context, time, actor, place, language, accessible versus metadata-only, accepted/rejected, and independent/derivative. Imbalance produces a limitation, not hidden confidence loss.

