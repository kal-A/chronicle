# Phase 1 Gate 1 Validation Report — Template

Fill this in after actually running the Gate 1 study defined in `docs/delivery/phase-1-validation-plan.md` with at least 5 non-contributor target users on the Scene 2 build. Do not fill this in from the automated Playwright coverage alone — `tests/e2e/gate1-journey.spec.ts` and `tests/e2e/keyboard-navigation.spec.ts` prove the interface *lets* someone complete each task; they cannot establish that a real reader *comprehends* the content correctly, which is the actual thing Gate 1 exists to test. See `plans/current-phase.md` for the current status of recruiting participants.

**Do not store participant names or unnecessary personal data**, per the validation plan.

---

## Study Metadata

- **Date(s) conducted:**
- **Build/commit tested:**
- **Facilitator:**
- **Number of participants:**

## Participant Profile Summary

For each participant, record only what's needed to interpret results — no names.

| # | Prior July Crisis familiarity | Relevant background (if any) | Device/browser |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

## Task Results

One row per participant per task, from `phase-1-validation-plan.md`'s Gate 1 task list:

1. Explain what decision or exchange the scene centers on.
2. Identify where and when the key communication occurred.
3. Open the evidence behind the reported German assurance.
4. Explain the difference between the documentary fact and the disputed causal interpretation.
5. Select an actor or event in a non-narrative facet and describe what changed elsewhere.
6. Return to their previous focus using visible navigation or browser history.
7. Find an uncertainty or evidence limitation without being told where it is.

| # | Task 1 | Task 2 | Task 3 | Task 4 | Task 5 | Task 6 | Task 7 | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |

Mark each cell: complete without intervention / complete with a hint / did not complete.

## Post-Task Questions

For each participant, record answers to:
- What felt clearer than a normal article?
- What felt confusing?
- Which facet would you remove if forced to simplify the experience?

## Observations

- **Wrong turns / requests for help:**
- **Fact-vs-interpretation confusion:** did any participant leave more certain about the disputed relationship's causal weight than the evidence actually supports? (Any such case is a blocking defect per the validation plan — record it prominently, not buried in notes.)
- **Cross-facet focus changes:** were they noticed and understood?
- **Accessibility/navigation failures:** did any block more than one participant?

## Severity-Ranked Issues Found

| Severity | Issue | Affected task(s) | Recommended fix |
|---|---|---|---|
| Blocking | | | |
| Important | | | |
| Minor | | | |

## Gate 1 Threshold Check

Per `docs/delivery/phase-1-validation-plan.md`:

- [ ] At least 4 of 5 participants completed Tasks 1–3 without intervention.
- [ ] At least 4 of 5 correctly distinguished the documented assurance from the disputed causal claim after using the interface.
- [ ] At least 4 of 5 successfully triggered and understood a cross-facet focus change.
- [ ] No accessibility or navigation failure blocked more than one participant.
- [ ] No participant left more certain than the interface's evidence classification supports.

## Design Changes Made (if any, before retest)

## Decision

**Proceed / Revise / Stop** (circle one, with rationale):

If Revise: what changed, and is a retest of the one-scene slice required before expanding to the remaining scenes?
