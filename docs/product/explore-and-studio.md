# Explore and Studio

Chronicle has a generation workflow and two long-term product surfaces.

## Chronicle Explore (inspection surface)

The public-facing reading/investigation experience. A user opens a polished historical investigation and explores it immediately — no account required for the seeded public content. An investigation includes a guided narrative (chapters/scenes), a synchronized timeline, a contextual map, a focused systems graph, entities (people, institutions, ideas, decisions, events), primary/secondary sources, conflicting interpretations, "known at the time" views, and an evidence-grounded assistant.

Explore remains the primary reader-facing inspection surface, but further manual content expansion is frozen. The next work makes it a generic renderer for generated packages while the bounded generation pipeline becomes the product core. See `ai-first-product-definition.md` and `docs/decisions/ADR-ai-generation-is-the-product-core.md`.

**Phase D update:** Explore's default presentation of an investigation is the map-first workspace (persistent map, docked/sheet assistant panel, lenses), not the article-first layout this document originally described. The narrative/evidence/systems-graph experience described above is preserved as "Inspector," a mode within Explore, not a separate surface and not Studio. See `docs/product/map-first-workspace-instructions.md` and `docs/decisions/ADR-002-map-first-workspace.md`.

## Chronicle Studio (built later)

The authoring and editorial environment, for trusted users to upload research documents, run LLM-assisted extraction, review proposed events/actors/dates/places/claims, connect evidence to entities, create timeline entries/map scenes/graph relationships, compare new evidence against existing knowledge, route sources across relevant investigations, review proposed changes before publication, and publish/update Explore investigations.

Studio remains later trusted-user tooling. Its review/publication concepts are represented in the package and domain contracts from the start, but Studio UI follows the generic renderer and generation pipeline.

## The Boundary in Practice

| Concern | Explore | Studio |
|---|---|---|
| Reading a published investigation | Yes | No |
| Asking the grounded assistant about published data | Yes | No |
| Uploading a private source | No (until Phase 5's private-workspace slice) | Yes |
| Reviewing/approving AI-proposed extractions | No | Yes |
| Editing published timeline/map/graph content | No | Yes |
| Seeing disputed interpretations | Yes (as reviewed content) | Yes (as part of authoring) |
| Cross-investigation source routing | No | Yes (Phase 8) |

When a feature request is ambiguous about which surface it belongs to, default to Explore only if it's read-only and grounded in already-reviewed data; anything that creates, edits, or approves content belongs in Studio, even if it's tempting to bolt onto Explore for expedience.
