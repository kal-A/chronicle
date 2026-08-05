# Phase D0 Product Validation Plan — Map-First Workspace

Companion to `docs/delivery/phase-1-validation-plan.md`, same discipline: a formative usability test with real target users, not a survey of automated coverage. `tests/e2e/workspace-journey.spec.ts`, `tests/e2e/ask-entry-journey.spec.ts`, and `tests/e2e/concert-of-europe-journey.spec.ts` prove the interface *lets* someone complete each task (real Chromium, keyboard operability, no detectable a11y violations). They cannot establish that a real reader *comprehends* what the workspace shows them, or that the mocked Ask flow reads honestly rather than deceptively — which is what this gate exists to test.

## Decision Being Tested

Does the map-first workspace (persistent map/graph canvas, docked/sheet assistant panel, lens switching) help a reader investigate a historical question at least as well as the prior article-first single-scene layout (still reachable as Inspector), without making the reader feel lost, overstating certainty, or leaving them confused about what the Ask entry surface actually did?

The Ask entry surface's keyword-matched mock generation flow (`src/features/investigation/ask/`) is evaluated separately as an *interaction pattern* — participants are not being asked to judge real generation quality, since there is no live generation pipeline behind it yet (see `topicMatch.ts`'s docstring). A design that leaves participants believing the system generated something bespoke for their question, when it actually matched them to one of two pre-existing packages, is a disclosure failure, not a success — the participant debrief must surface whether this happened.

## Prototype Gate D0 — Workspace and Ask-Surface Interaction Test

Use both existing packages: "The German Assurance and Vienna's Posture, 4–10 July 1914" (blank-cheque) and "The Concert of Europe and Revolutionary Intervention, 1814–1822" (concert-of-europe).

### Participants

Recruit at least five people matching the primary target-user description who are not contributors to Chronicle and were not participants in the Phase 1 Gate 1 study (a fresh sample avoids familiarity bias with the article-first layout being compared against). Record prior familiarity with either topic, but do not select only history enthusiasts.

This is a formative usability test, not statistically representative research.

### Tasks

Without coaching beyond the opening prompt, ask each participant to:

1. Starting from `/`, ask a question in their own words about one of the two available topics and follow the flow through scope review and generation into the workspace.
2. Explain, after arriving, what investigation they landed in and why (checks whether the keyword-match/scope-review step was legible, not a confusing non sequitur).
3. Switch between at least two lenses (e.g. Sequence and Systems) and describe what changed on the canvas and why.
4. Using the Systems lens specifically, explain the relationship between two connected nodes, including whether it's disputed or well-supported (checks the labelled-graph redesign against the old numbered-claim-ID graph it replaced for this audience).
5. Resize or collapse the docked panel (or, on a small viewport, operate the bottom sheet), then reopen it.
6. Find a disclosed limitation or uncertainty (e.g. via the Uncertainty lens or a scene with no period map) without being told where to look.
7. Locate and use the link into Inspector mode, and explain in their own words what changed about the experience there.
8. **Debrief question, asked directly:** "When you asked your question, what did you think the system did behind the scenes?" Record verbatim or close paraphrase — this is the disclosure check described above.

After the tasks, ask what felt clearer than the current article-first view, what felt confusing, and whether the lens concept made sense as "different ways of looking at the same investigation."

### Evidence Collected

- Task success without intervention, per task.
- Whether the participant's mental model of the Ask flow (task 8) matches reality; any participant who believes the system performed bespoke live research or writing is a disclosure failure, recorded prominently.
- Whether lens switches were noticed and correctly attributed to a deliberate choice, not a glitch.
- Whether the Systems lens's relationship labels and evidence-strength encoding (line style + text, never color alone) were understood without prompting.
- Whether panel resize/collapse and the mobile bottom sheet were discoverable and operable, including by keyboard for at least one participant per cohort of five.
- Whether the Inspector hand-off was found and its purpose understood.
- Short qualitative notes and severity-ranked usability issues; no session recording without explicit participant consent.

### Gate D0 Success Threshold

Proceed to build on the map-first workspace as the default experience only if:

- At least 4 of 5 participants complete Tasks 1–3 without intervention.
- At least 4 of 5 correctly describe at least one Systems-lens relationship's evidentiary status (supported vs. disputed vs. indirectly supported) after using the interface.
- At least 4 of 5 successfully operate the docked panel or bottom sheet (resize/collapse/reopen) without intervention.
- No participant reports believing the system performed live, bespoke generation for their specific question (Task 8) — any such case is a blocking disclosure defect, not a minor note, and must be fixed (e.g. clearer copy in `ScopeReviewCard.tsx`/`GenerationProgress.tsx`) before this gate can be considered passed.
- No accessibility or navigation failure blocks more than one participant.

If the threshold is missed, revise and retest before treating the map-first workspace as validated. Do not proceed to further Phase D work (the persistent in-workspace Ask tab, live generation) merely to create the appearance of progress.

## Required Output

Store a dated validation report in `docs/delivery/validation/` using `docs/delivery/validation/phase-d0-gate-template.md`, containing participant profile summaries, task results, the disclosure-check findings, observations, issues, design changes, and the explicit proceed/revise/stop decision. Do not store participant names or unnecessary personal data.
