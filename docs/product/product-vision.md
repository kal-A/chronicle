# Product Vision

## What Chronicle Is

Chronicle is an AI-powered historical investigation generator and interactive systems atlas. It builds bounded, source-backed draft investigations from a user's topic, question, comparison, or source, then lets users inspect what happened, where, when, who decided what, what actors knew, what pressures shaped decisions, where accounts conflict, and what evidence supports each interpretation.

It should feel like an interactive historical documentary, atlas, timeline, systems map, evidence explorer, and investigation assistant, combined into one coherent experience.

## What Chronicle Is Not

- A generic history chatbot
- A Wikipedia clone
- A conventional academic project manager
- A graph visualization looking for a purpose
- An autonomous historian
- A source summarizer with no durable knowledge model
- A thin AI wrapper
- A barely functional technical prototype

The distinction matters because each of these is a plausible-looking but weaker version of the product. A chatbot answers questions but has no durable, navigable knowledge structure. A graph viz looks impressive but doesn't teach anything if it isn't grounded in a real investigation. A source summarizer is useful once and forgotten; Chronicle's evidence network is meant to compound in value as more investigations connect to it.

## Why This Product

Static historical articles and generic timelines are good at presenting a single linear account. They're bad at showing a reader *why* things happened, *what was contested*, *what different actors could and couldn't have known*, and *how a system of pressures* (not a single cause) produced an outcome. Generic chatbots can answer questions fluently but have no durable grounding — they can't show you the actual evidence, can't represent disagreement between historians, and will confidently invent detail. Chronicle exists in the gap between "static and trustworthy" and "flexible and unreliable."

## First Golden Investigation

The Blank Cheque scene from the **July Crisis of 1914** is Chronicle's first golden package fixture: a curated, provenance-rich regression case for the generic renderer and generation verifier. It is not a mandate to manually author the remaining investigation. The initial supported generation domain is defined in `supported-domain-strategy.md`.

The architecture must not hard-code the application around this one event — see `docs/architecture/domain-model.md`.

## Long-Term Shape

A generation workflow produces versioned investigation packages over a shared evidence network. Explore inspects generated results; Studio later supports correction, review, enrichment, and publication. See `ai-first-product-definition.md` and `generation-first-user-experience.md`.
