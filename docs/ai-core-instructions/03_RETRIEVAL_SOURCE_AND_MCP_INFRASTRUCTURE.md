<!-- See 00_START_HERE.md for the encoding-fix note that applies to this whole instruction set. -->

# Chronicle — Retrieval, Sources, APIs, and MCP Infrastructure

[← Agent architecture](./02_AGENT_ARCHITECTURE.md) · [Next: Domain generalization and evaluation →](./04_DOMAIN_GENERALIZATION_AND_EVALUATION.md)

## 1. Core rule

> **The LLM plans and evaluates retrieval. Deterministic adapters search, fetch, parse, normalize, cache, and validate sources.**

The LLM must not directly scrape arbitrary webpages and treat the result as evidence.

## 2. Retrieval phases

### Phase E

Use deterministic retrieval over the existing Chronicle corpora.

### Phase F

Add live source discovery.

### Phase G

Add acquisition, parsing, OCR, embeddings, hybrid retrieval, and reranking.

## 3. Initial internal corpus retrieval

Build a corpus service over existing:

- Sources;
- Documents;
- Passages;
- Claims;
- EvidenceLinks;
- Relationships;
- Events;
- People;
- Institutions;
- Places;
- KnowledgeStates.

Required retrieval approaches:

- exact lexical search;
- normalized-name search;
- date filtering;
- source-type filtering;
- evidence-role filtering;
- claim and relationship traversal;
- source-diversity constraints.

Define an embeddings interface now, but embeddings are not required for the first slice.

## 4. Future source providers

### Scholarly metadata

- OpenAlex;
- Crossref;
- Semantic Scholar.

### Archives and cultural heritage

- Library of Congress;
- Internet Archive;
- Europeana;
- DPLA;
- official national archives;
- university primary-source collections.

### Entity and geographic support

- Wikidata;
- authoritative gazetteers;
- IIIF georeference metadata;
- historical GIS collections.

These support entity resolution and geography; they are not automatically historical evidence.

### Controlled web fallback

Possible services:

- Tavily;
- Firecrawl;
- direct fetch;
- Playwright for dynamic public pages.

Search snippets are candidates, never evidence.

## 5. Provider adapter architecture

```python
class DiscoveryProvider(Protocol):
    name: str
    version: str

    async def search(
        self,
        query: DiscoveryQuery,
        context: DiscoveryContext,
    ) -> list[SourceCandidate]:
        ...
```

Every provider must support:

- timeouts;
- bounded retries;
- rate-limit handling;
- caching;
- query provenance;
- raw-response retention or hashing;
- normalized output;
- partial failure;
- health checks;
- provider-version tracking.

## 6. Source candidate registry

Every discovered result becomes a candidate before it can become evidence.

Required fields:

- candidate ID;
- provider;
- provider record ID;
- discovery query ID;
- canonical URL;
- stable identifier;
- title;
- creators;
- institution or publisher;
- source creation date;
- publication date;
- source type;
- primary/secondary classification;
- language;
- description;
- access state;
- full-text state;
- rights state;
- duplicate group;
- relevance assessment;
- evidentiary role;
- perspective contribution;
- assessment status;
- rejection or deferral reason.

## 7. Acquisition

Automatically acquire only permitted material.

Preferred order:

1. openly accessible HTML;
2. public-domain or open-licensed PDF;
3. archive OCR/transcript;
4. IIIF manifest and images;
5. user-supplied files;
6. metadata-only record.

When full text is unavailable, preserve metadata and link it, mark it unprocessed, and never claim to have read it.

## 8. Processing tools

### HTML

- Trafilatura;
- Beautiful Soup for controlled parsing;
- readability fallback.

### PDFs

- PyMuPDF for pages, text, blocks, coordinates, and images;
- OCRmyPDF for scanned PDFs;
- preserve page mapping and originals.

### Browser fallback

- Playwright;
- Playwright MCP during development;
- use only when ordinary HTTP retrieval or official APIs are insufficient.

## 9. MCP strategy

### Consume useful MCP tools

Possible development or fallback tools:

- Fetch MCP;
- Playwright MCP;
- Firecrawl MCP;
- Tavily MCP.

Do not couple production logic directly to a third-party MCP server. Wrap external tools behind Chronicle-owned interfaces.

### Build a Chronicle MCP server later

Potential tools:

```text
plan_historical_research
search_scholarly_sources
search_archival_sources
get_source_candidate
assess_source_candidate
acquire_source
search_passages
get_claim_evidence
find_counterevidence
trace_historical_relationship
get_actor_knowledge_state
get_map_context
```

Design Phase E tool contracts so they can later be exposed through MCP without rewriting them.

## 10. Security and rights

Add policies for:

- SSRF prevention;
- private-network blocking;
- URL allow/deny rules;
- redirect and content-size limits;
- file-type validation;
- robots and terms compliance;
- paywall avoidance;
- licence and rights metadata;
- quote-length limits;
- source attribution;
- content retention.

## 11. Retrieval auditability

For every answer, Chronicle should be able to show:

- tools called;
- queries used;
- records returned;
- passages selected;
- sources consulted;
- source roles;
- rejected evidence;
- critic changes;
- final citation mapping.

## 12. First implementation boundary

Phase E should not perform live internet discovery.

Build:

- corpus interface;
- lexical retrieval;
- claim/evidence lookup;
- relationship traversal;
- knowledge-state lookup;
- tool registry;
- agent-callable typed tools;
- tests across multiple benchmark corpora.

Phase F then adds live providers.
