# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Chronicle primarily serves history-minded investigators: serious history readers, students, independent researchers, and curious people who want to follow historical rabbit holes with more structure and evidence than a generic search or chat answer provides. Professional historians are an important advanced audience, but the MVP does not claim to replace the depth of professional archival, historiographical, collaborative, or publication workflows.

## Product Purpose

Chronicle is a centralized place to begin and visualize historical investigations. A user asks about a topic, event, person, period, comparison, connection, or source; Chronicle proposes a bounded scope, builds an auditable evidence-backed draft investigation, and lets the user explore it through geography, time, relationships, claims, sources, uncertainty, and limitations.

Success means a curious question can become a navigable investigation without sacrificing evidence, disagreement, or uncertainty, and a user can move naturally from an initial question into deeper exploration.

## Positioning

Chronicle bridges static trustworthy history and flexible but unreliable AI answers. Its distinctive mechanism is a bounded, auditable investigation pipeline whose output becomes a durable interactive historical model rather than a disposable chat response. The map-first workspace, timeline, relationship system, evidence inspector, and contextual assistant are coordinated views over the same versioned investigation and evidence network.

## Operating Context

The first page is an app-like Ask surface where a user can immediately enter a historical question or begin an investigation. Chronicle interprets the request, proposes a scope, shows visible generation progress, and opens a geographically bounded investigation workspace. The initial Ask surface persists conceptually as the contextual assistant and evidence/source panel within the investigation.

Users may arrive with a serious research question or simply an interest they want to pursue as a historical rabbit hole. The experience must support both without overstating professional-research completeness.

## Capabilities and Constraints

- Generated investigations are drafts, not autonomous historical truth.
- Claims, relationships, knowledge states, maps, and synthesis must remain traceable to reviewed evidence and deterministic validation.
- The landing page may communicate broad temporal and geographic possibility, but an investigation map is bounded to the specific locations and periods relevant to that investigation.
- The initial reliable generation domain is intentionally narrower than Chronicle's long-term period- and region-agnostic product identity.
- The first page should remain compact: an immediate question surface plus one concise explanatory demonstration, not an expansive marketing site.
- Optional contextual information may appear through accessible info controls and progressive disclosure rather than permanent interface clutter.
- Current implementation and portfolio demonstrations must not imply unfinished research, retrieval, publication, or professional collaboration capabilities already exist.

## Brand Commitments

- Product name: Chronicle.
- Chronicle is not specific to the Congress of Vienna, the July Crisis, European history, or any single event or period.
- The product should feel map-first, investigative, historically deep, and systems-aware, with strategic-map inspiration rather than game mechanics or alternate-history simulation.
- The first page retains a clear conversational question field while an atmospheric historical atlas communicates breadth through changing temporal/geographic contexts, cartographic fragments, coastlines, routes, documents, and artifacts.
- The visual product should be distinctive and portfolio-worthy without obscuring the investigation task or competing with the AI agent system as the product core.

## Evidence on Hand

- A working React/TypeScript Ask → scope → progress → investigation flow.
- A generic versioned `GeneratedInvestigation` contract and renderer.
- Two registered investigation packages used as implementation and regression evidence: the Blank Cheque and Concert of Europe investigations.
- A map-first investigation workspace, Inspector mode, evidence views, timeline, relationship graph, source views, and accessibility tests.
- A Python deterministic generation pipeline, local model-provider foundation, corpus layer, and typed evidence tools; later agent and HTTP integration remains in development.
- No testimonials, customer logos, usage metrics, or professional-historian validation are currently available and none should be fabricated.

## Product Principles

1. Begin with curiosity; reward depth.
2. Make evidence, disagreement, uncertainty, and limitations inspectable.
3. Let geography and time clarify an investigation without implying unsupported precision.
4. Keep AI work bounded, auditable, resumable, and subordinate to deterministic integrity gates.
5. Use progressive disclosure so a newcomer can begin immediately and a serious reader can keep drilling down.

## Accessibility & Inclusion

The web experience must remain keyboard operable, responsive, screen-reader compatible, and understandable without relying on color, motion, maps, or graphs alone. Motion-heavy landing treatments require a meaningful reduced-motion/static alternative. Visual historical material must not compromise the legibility or operability of the Ask surface.
