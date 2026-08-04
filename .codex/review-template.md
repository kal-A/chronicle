# Feature Diff Review Template (Review Type C)

Use this for every completed slice/phase. Inputs you should have been given: `AGENTS.md`, the feature brief, acceptance criteria, the approved implementation plan, the current diff, and test results. If any of these is missing, say so before reviewing rather than guessing at scope.

## Output Structure

```markdown
## Feature Diff Review: <feature/phase name>

### Blocking Issues
(Must be fixed before this is considered done. Empty list is a valid, good outcome.)
- ...

### Important Improvements
(Should be fixed soon; not necessarily blocking.)
- ...

### Optional Refinements
(Nice to have; explicitly low priority.)
- ...

### Checklist
- [ ] Meets stated acceptance criteria
- [ ] Frontend/backend contract matches (no drift between OpenAPI schema and actual usage)
- [ ] No provenance loss (docs/architecture/provenance-and-review.md fields populated correctly)
- [ ] No human-review bypass (nothing reaches a public endpoint without reviewed/disputed status)
- [ ] No unreviewed claims leaking into published data
- [ ] Timeline/map semantics correct (no false precision, no modern-border leakage — AGENTS.md §12)
- [ ] Historical certainty not overstated (evidence_classification present and justified)
- [ ] Accessibility requirements met (docs/design/accessibility.md)
- [ ] Security requirements met (AGENTS.md §7)
- [ ] Adequate test coverage for the change
- [ ] No unnecessary complexity introduced
- [ ] No unrelated changes bundled into this diff
```

---

# Codex Handoff Template

Claude produces this at the end of every completed phase, and Codex should expect it as the primary input for a Feature Diff Review or Pre-Release Review.

```markdown
## Codex Handoff: <phase/feature>

Feature or phase:
User problem:
Expected user outcome:
Relevant product documents:
Relevant architecture documents:
Files changed:
Database changes:
API changes:
Tests added:
Commands run:
Known limitations:
Risks:
Acceptance criteria:
Specific areas requiring independent review:
```

The handoff is factual, based on the implemented code — not Claude's internal reasoning about how it got there, and not phrased to ask Codex to agree with the implementation.
