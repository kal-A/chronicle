# Phase D0 Gate Validation Report — Template

Fill this in after actually running the study defined in `docs/delivery/phase-d0-validation-plan.md` with at least 5 non-contributor target users on the map-first workspace build. Do not fill this in from the automated Playwright coverage alone — `tests/e2e/workspace-journey.spec.ts`, `tests/e2e/ask-entry-journey.spec.ts`, and `tests/e2e/concert-of-europe-journey.spec.ts` prove the interface *lets* someone complete each task; they cannot establish that a real reader *comprehends* the workspace or the Ask flow correctly, which is the actual thing this gate exists to test. See `plans/current-phase.md` for the current status of recruiting participants.

**Do not store participant names or unnecessary personal data**, per the validation plan.

---

## Study Metadata

- **Date(s) conducted:**
- **Build/commit tested:**
- **Facilitator:**
- **Number of participants:**

## Participant Profile Summary

For each participant, record only what's needed to interpret results — no names.

| # | Prior topic familiarity (1914 crisis / Concert of Europe) | Relevant background (if any) | Participated in Phase 1 Gate 1? | Device/browser |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

## Task Results

One row per participant per task, from `phase-d0-validation-plan.md`'s task list:

1. Ask a question and follow the flow into the workspace.
2. Explain what investigation they landed in and why.
3. Switch lenses and describe what changed.
4. Explain a Systems-lens relationship's evidentiary status.
5. Resize/collapse the panel (or operate the bottom sheet) and reopen it.
6. Find a disclosed limitation or uncertainty unprompted.
7. Find and use the Inspector link, and explain what changed there.

| # | Task 1 | Task 2 | Task 3 | Task 4 | Task 5 | Task 6 | Task 7 | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |

Mark each cell: complete without intervention / complete with a hint / did not complete.

## Disclosure Check (Task 8)

For each participant, record their verbatim or close-paraphrase answer to: "When you asked your question, what did you think the system did behind the scenes?"

| # | Answer | Believed live/bespoke generation occurred? (Y/N) |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

Any "Y" is a blocking disclosure defect per the validation plan — record it prominently below, not buried in general notes.

## Post-Task Questions

For each participant, record answers to:
- What felt clearer than the current article-first (Inspector) view?
- What felt confusing?
- Did the lens concept make sense as "different ways of looking at the same investigation"?

## Observations

- **Wrong turns / requests for help:**
- **Lens-switch comprehension:** were canvas changes noticed and correctly attributed to the lens choice, not mistaken for a glitch?
- **Systems-lens evidence-strength encoding:** understood without prompting (line style + text, not color alone)?
- **Panel/bottom-sheet operability:** discoverable and operable without intervention, including by at least one participant using keyboard only?
- **Inspector hand-off:** found and purpose understood?
- **Accessibility/navigation failures:** did any block more than one participant?

## Severity-Ranked Issues Found

| Severity | Issue | Affected task(s) | Recommended fix |
|---|---|---|---|
| Blocking | | | |
| Important | | | |
| Minor | | | |

## Gate D0 Threshold Check

Per `docs/delivery/phase-d0-validation-plan.md`:

- [ ] At least 4 of 5 participants completed Tasks 1–3 without intervention.
- [ ] At least 4 of 5 correctly described at least one Systems-lens relationship's evidentiary status.
- [ ] At least 4 of 5 successfully operated the docked panel or bottom sheet without intervention.
- [ ] No participant believed the system performed live, bespoke generation for their question (zero "Y" in the Disclosure Check table).
- [ ] No accessibility or navigation failure blocked more than one participant.

## Design Changes Made (if any, before retest)

## Decision

**Proceed / Revise / Stop** (circle one, with rationale):

If Revise: what changed, and is a retest required before treating the map-first workspace as the validated default experience?
