# Phase E6 — Live Investigation Assistant (in progress)

## Outcome

The investigation Ask panel now uses Chronicle's real FastAPI and local-Qwen agent workflow. It no longer presents a simulated answer inside the investigation workspace.

This is a working first E6 vertical slice, not phase closure. A question grounded in a selected evidence record completed with `answer_ready` and an exact citation. A broader corpus-search question completed all five stages and safely returned `abstained` rather than exposing an unsupported conclusion.

## Implemented

- A shared investigation-assistant controller submits questions, supplies the current investigation/map/time/source context, listens to server-sent progress events, falls back to polling, and resumes failed runs from their last safe stage.
- The Ask panel exposes the five agent stages: Scope, Retrieve, Analyze, Verify, and Compose.
- The final surface distinguishes cited findings from abstentions and shows citations, limitations, tool activity, recovery controls, and safe map actions.
- Planner output is constrained to tools and record identifiers valid for the active corpus and question intent.
- Analyst output is constrained to retrieved evidence identities and exact citation tuples.
- File-backed run persistence is protected against concurrent polling writes and transient Windows replace failures.
- The default local-Qwen timeout and retrieval bounds were adjusted for the real CPU-only workflow.

## Real-Qwen validation

### Supported selected-evidence case

The complete Planner → retrieval → Analyst → Critic → Guide workflow returned `answer_ready` with the grounded conclusion that Szögyény reported Wilhelm II saying Austria-Hungary could count on Germany's full support. The answer included one matching evidence citation.

### Broader search case

The question “What does the July 5 report say about German support?” completed every agent stage and retrieved two relevant passages. The candidate analysis was not reliable enough for publication, so the Critic/Guide path returned `abstained`. This is the intended safety behavior, but it also shows that generic answer usefulness is not yet sufficient.

## Remaining E6 closure work

- Add semantic-entailment evaluation so a statement cannot reverse who supported whom while still passing lexical grounding checks.
- Reduce CPU-only end-to-end latency; the broad live run took several minutes because four Qwen calls execute sequentially.
- Build a small historical-question evaluation set covering correct answers, insufficient evidence, conflicting evidence, temporal roles, and actor-knowledge questions.
- Improve source deep-linking and retain conversation state across reloads.
- Replace the landing page's two-package keyword routing with the later discovery/retrieval system; live web research, downloads, embeddings, and database retrieval are outside E6.

## Verification

- Backend AI/API/storage slice: 377 passed, 1 skipped, 5 live-model tests deselected.
- Frontend: 117 tests passed.
- Type checking and linting passed.
- Production build passed; the existing MapLibre bundle-size advisory remains.
- Manual browser validation covered a supported cited result, a complete safe abstention, progress streaming, and recovery presentation.

No commit, push, or merge was performed.
