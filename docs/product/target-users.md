# Target Users

## Primary: Curious General Readers

People with a general interest in history who are frustrated by the tradeoff between "quick and shallow" (a summary article) and "deep but unstructured" (a 500-page book, or a pile of primary sources with no navigation aid). They want to actually *understand a system of causes*, not just read a narrative once. They are the primary audience for Chronicle Explore and the group every UX decision should be validated against first.

**What they need from Chronicle:** a guided entry point (narrative/chapters) that doesn't require prior expertise, with the option to go as deep as they want (timeline, map, graph, evidence) without ever feeling lost or having to abandon context to look something up elsewhere.

## Secondary: History Students and Enthusiasts

People with more background who want to interrogate specific claims, compare interpretations, and trace evidence chains — closer to how a researcher works, but without needing archive access or specialist tools. They are more likely to use the investigation assistant for pointed questions ("what's disputed here," "what did X know by date Y") and more likely to explore the graph and evidence panel directly rather than only following the guided narrative.

**What they need from Chronicle:** transparent provenance, the ability to see disagreement between sources/historians rather than a flattened consensus, and confidence that AI-assisted answers are grounded rather than invented.

## Tertiary (Later Phases): Trusted Contributors / Editors

Once Chronicle Studio exists (Phase 6+), a small trusted group who upload sources, review AI-proposed extractions, and maintain investigation quality. Not the primary audience for early phases, but the domain model must not make their eventual workflow structurally impossible (see `docs/architecture/domain-model.md`, `docs/product/shared-evidence-network.md`).

## Non-Users (Explicitly Out of Scope for Now)

- Professional archivists needing full citation-management/export tooling
- Institutions needing multi-tenant SaaS features (billing, org management)
- Casual chat-only users who want an unstructured Q&A history bot — this is explicitly the failure mode Chronicle is designed not to be (`product-vision.md`)

## Portfolio Audience (Cross-Cutting Concern)

Chronicle also has to read well to a technical hiring audience (see `product-principles.md` item 9) evaluating product judgment, historical-domain rigor, and full-stack/AI systems design. This audience isn't a target *user* of the product, but it does inform the bar for documentation, testing, and architectural clarity throughout.
