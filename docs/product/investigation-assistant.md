# Investigation Assistant

> Product behavior remains applicable. The AI-first typed-tool and package/corpus boundary is specified in `docs/architecture/investigation-assistant.md`.

The investigation assistant is a central Chronicle feature, but it is narrowly grounded — an access point into the investigation's reviewed evidence, not a general history chatbot layered on top of it.

## Useful Question Types

- Explain this event or connection.
- What evidence supports this interpretation?
- Where do these sources or actors disagree?
- What did this actor or institution know by this date?
- How did Event A influence Event B?
- Which claims remain disputed?
- What evidence is missing?
- Show this event from another actor's perspective.
- Which locations were active during this period?
- How does this uploaded source affect the current investigation? (Studio-side, Phase 5+)

Phase 4 ships four of these, polished, rather than all ten shallowly: *explain this event/connection*, *compare these accounts/actors*, *what was known by this date*, *what is disputed or missing*. See `docs/delivery/development-phases.md` Phase 4.

## Answers Are Actions, Not Just Text

An answer may focus the timeline, move the map to relevant locations, highlight graph nodes/relationships, open source passages, compare interpretations, or suggest a guided path through the investigation. The assistant is a navigation layer over the other four views, not a fifth, separate surface.

## Hard Constraints

The assistant must not:

- Behave like an unrestricted general history chatbot.
- Use unsourced model knowledge as investigation evidence.
- Invent citations.
- Claim an actor knew something merely because information existed somewhere (in the world, or in the assistant's training data) — knowledge claims must be backed by a reviewed "known at the time" record, not inferred.
- Flatten disputed interpretations into a single confident answer.
- Present unreviewed user uploads as public fact.
- Hide insufficient evidence behind polished language — "the evidence doesn't establish this" is a valid, expected answer.
- Make public editorial changes without human review.

## Architectural Shape

The assistant is query planning → bounded tool calls against reviewed data (source search, source comparison, reviewed-relationship tracing, timeline context, map context, actor-knowledge reconstruction, evidence-gap detection) → answer composition → verification pass before the answer reaches the user. See `docs/architecture/ai-agent-architecture.md` for the tool contracts and `docs/architecture/provenance-and-review.md` for what "reviewed data" means. This is deliberately not an open-ended agent loop — see `AGENTS.md` §4.
