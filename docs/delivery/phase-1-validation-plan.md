# Phase 1 Product Validation Plan

## Decision Being Tested

Does a synchronized narrative, timeline, map, focused graph, and evidence panel help a reader understand a contested historical decision better than a linear narrative alone, without making the reader feel lost or overstating certainty?

The mocked assistant is evaluated separately as a navigation affordance. It cannot compensate for failure of the direct exploration experience.

## Prototype Gate 1 — One-Scene Interaction Test

Use Scene 2, “Vienna and Berlin: The Blank Cheque,” from `docs/research/phase-1-scene-outline.md`.

### Participants

Recruit at least five people matching the primary target-user description who are not contributors to Chronicle. Prior July Crisis expertise is not required. Record prior familiarity but do not select only history enthusiasts.

This is a formative usability test, not statistically representative research. Results identify serious comprehension/navigation problems and inform whether expansion is justified.

### Tasks

Without coaching beyond the opening prompt, ask each participant to:

1. Explain what decision or exchange the scene centers on.
2. Identify where and when the key communication occurred.
3. Open the evidence behind the reported German assurance.
4. Explain the difference between the documentary fact and the disputed causal interpretation.
5. Select an actor or event in a non-narrative facet and describe what changed elsewhere.
6. Return to their previous focus using visible navigation or browser history.
7. Find an uncertainty or evidence limitation without being told where it is.

After the tasks, ask what felt clearer than a normal article, what felt confusing, and which facet they would remove if forced to simplify the experience.

### Evidence Collected

- Task success without intervention.
- Wrong turns and requests for help.
- Whether the participant correctly distinguishes source text from later interpretation.
- Whether focus changes are noticed and understood.
- Whether the reader can state the location precision and uncertainty honestly.
- Short qualitative notes and severity-ranked usability issues; no session recording without explicit participant consent.

### Gate 1 Success Threshold

Proceed to expand the prototype only if:

- At least 4 of 5 participants complete Tasks 1–3 without intervention.
- At least 4 of 5 correctly distinguish the documented assurance from the disputed claim about its causal significance after using the interface.
- At least 4 of 5 successfully trigger and understand one cross-facet focus change.
- No accessibility or navigation failure blocks more than one participant.
- No participant leaves with a more certain causal claim than the interface's evidence classification supports; any such failure is treated as a blocking content/design defect.

If the threshold is missed, revise and retest the one-scene slice. Do not add the remaining scenes merely to create the appearance of progress.

## Prototype Gate 2 — Four-Scene Coherence Test

After Gate 1 passes, expand to the four-scene outline and test with at least five additional target users. Participants follow the narrative and then investigate one question of their choice.

Proceed to Phase 2 only if:

- At least 4 of 5 can describe the crisis as a sequence of decisions involving multiple actors, rather than a single automatic causal chain.
- At least 4 of 5 can relocate a previously viewed claim through a different facet without losing context.
- At least 4 of 5 can find supporting evidence and recognize a disputed or insufficient-evidence state.
- The majority reports that synchronization added useful understanding rather than merely visual novelty.
- All blocking usability/accessibility findings are resolved or explicitly accepted by Kamal with rationale.

## Required Output

Store a dated validation report in `docs/delivery/validation/` containing participant profile summaries, task results, observations, issues, design changes, and the explicit proceed/revise/stop decision. Do not store participant names or unnecessary personal data.

