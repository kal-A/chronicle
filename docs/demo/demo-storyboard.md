# Chronicle demo — storyboard & recording script

A 3–5 minute demo that proves Chronicle's strongest real behavior: a **local,
multi-agent, source-grounded historical investigation with deterministic validation** —
not a UI tour. Everything below maps to features that exist; nothing here invents a
capability or a number. Measured figures come from
[`../architecture/performance-benchmark.md`](../architecture/performance-benchmark.md).

**Target length:** ~4:30. **Voice:** calm, technical, honest.

---

## The honesty rules (read first)

These are non-negotiable and shape the whole plan:

1. **Never imply prerecorded output is live.** If a run was executed earlier, say so on
   screen and in narration.
2. **Never fake execution, timers, or results.** No mocked stage animations, no invented
   latency counters, no staged "answer" the system didn't produce.
3. **Time-compression is allowed only for dead waiting, and must be disclosed** — an
   on-screen caption like *"generation time-compressed — stages are real, only waiting
   removed."* The stages, evidence, and answer shown must be the ones the system actually
   produced.
4. **Cite only measured numbers**, labeled as dev-machine, CPU-only (Ryzen 5 6600H).

## The runtime problem, and the recommended honest solution

A full 7B investigation takes **~4.8 min mean end-to-end** on the dev machine (measured;
the analyst stage dominates) — too long to sit through live in a 4–5 min video. Do **not**
speed up or fake it. Recommended approach:

- **Pre-run the investigation before recording** (corpus built, run finished, results
  persisted). Then present it two honest ways, combined:
  - **Main flow = completed-run walkthrough.** Open the already-finished investigation and
    narrate its **real** streamed stages, cited answer, evidence, and map. State up front:
    *"I ran this investigation a few minutes before recording; everything you'll see is its
    real, recorded output."* No waiting, fully honest.
  - **One short "it really runs" clip (~10–15 s).** Start a fresh run on camera so the
    stages genuinely stream, then **cut the model-generation wait** with the disclosed
    time-compression caption. This proves it's live software, not a mockup.
- **Pre-warm acquisition.** For the live "search anything" beat, run that acquisition once
  beforehand so its sources are cached; a cached rebuild is **~1.9 s vs ~80 s cold**
  (measured) — this is genuinely live, just cached, and should be labeled *"sources cached
  from an earlier run."*
- **Model choice:** record on **7B** (the tuned default) for a grounded cited answer. If
  only a low-memory machine is available, record on 3B and state it — but note 3B often
  abstains at the analyst gate (that becomes the abstention beat, honestly).

## Setup required before recording

1. `python bootstrap.py`, then start both servers (backend API on :8000, `npm run dev` on
   :5173). Confirm the API startup banner shows the intended model.
2. Ollama running with the model pulled (`qwen2.5:7b-instruct` for the main flow).
3. **Pre-run the primary investigation** (below) and **confirm it reaches a cited answer**
   (`answer_ready`). If it abstains, either adjust the question or make the abstention the
   validation beat — do not hide it.
4. **Pre-warm** the live-acquisition topic's cache with one earlier run.
5. Open browser tabs for the cutaways: `docs/architecture/architecture-diagram.md`
   (rendered on GitHub), the GitHub **Actions** tab (green CI), and optionally
   `docs/architecture/request-trace.md`.
6. Clean browser window at 1920×1080, system notifications off, cursor highlighting on.

## Primary scenario (exact)

- **Corpus:** the curated **July Crisis / "Blank Cheque"** package (`blank-cheque-golden`) —
  the richest fixture (knowledge-states, counterevidence, causation), so it shows the
  agents' strongest behavior.
- **Question (verify in the pre-run):**
  > *"What did German leaders know and intend when they gave Austria-Hungary the 'blank
  > cheque' in July 1914?"*
  Chosen because it exercises **actor-knowledge**, **causation**, and **counterevidence** —
  not just fact lookup. If the pre-run shows it abstains on part of this, keep that; a
  principled non-answer is a feature, not a failure.

## Storyboard

| Time | On screen | Narration (script) |
|---|---|---|
| **0:00–0:20** | Title card → landing page. | "Chronicle is a local-first, multi-agent research engine for history. It runs entirely on your machine — open-weight models through Ollama, no paid APIs — and it's built to stay grounded in sources or abstain, never to make history up." |
| **0:20–0:45** | Ask entry; type the July-Crisis question. Show the honest "suggested topics vs research live" distinction. | "I ask a real historical question. Chronicle either routes to a curated, reviewed corpus or researches an arbitrary topic live from free public sources. Here it's the curated July Crisis package." |
| **0:45–1:05** | *Cutaway #1 (~15 s):* `architecture-diagram.md` lifecycle diagram. | "Under the hood it's an explicit pipeline — acquisition, then four bounded agents (planner, analyst, critic, guide), and a deterministic validation gate after every model call. Not an autonomous swarm; a state machine you can audit." |
| **1:05–1:45** | The investigation workspace streaming stages: **scope → retrieve → analyze → verify → compose**. *(Completed-run walkthrough; caption: "recorded run — real stages.")* Splice the ~10–15 s live streaming clip here with its time-compression caption. | "The four agents run in sequence, streaming each stage. This is a run I executed a few minutes ago — real recorded stages. It genuinely takes a few minutes of local model time; I've removed only the waiting, nothing else." |
| **1:45–2:25** | `GeneratedResult`: the cited answer — direct answer, key points, any disagreements. | "Here's the result: a direct answer with key points, and where the sources disagree, it says so rather than flattening it into one narrative." |
| **2:25–3:00** | Click a citation → `EvidencePanel` / `SourceDetail`: the exact passage and its source. | "Every claim links to evidence. Click a citation and you land on the exact passage and the source it came from — this is enforced deterministically: a claim that can't resolve to a retrieved passage doesn't ship." |
| **3:00–3:35** | Map view (time-indexed territory) and/or relationship graph. | "The workspace is map-first — the geography and timeline are generated from the sourced evidence, not stock imagery, and move with a single time cursor." |
| **3:35–4:10** | The validation/abstention beat. Best option: switch to a **live "search anything"** query (cache pre-warmed) and show either a grounded answer or a **principled abstention**. *Cutaway #2 (~8 s):* the validation-spine diagram. | "Now an arbitrary topic, researched live from free sources. On a small local model it will sometimes say the evidence doesn't support a grounded answer — and abstain. That's the point: the deterministic gates would rather return nothing than fabricate." |
| **4:10–4:30** | *Cutaway #3 (~6 s):* GitHub Actions green CI. Back to landing page. | "It's reproducible from a fresh clone with one command, the backend and frontend suites run in CI, and it's all free and local. That's Chronicle." |

## Code / architecture cutaways (brief, not a walkthrough)

Use only these, only as narrated above — total ≲ 30 s:

1. **Lifecycle diagram** (`docs/architecture/architecture-diagram.md`) — the acquisition →
   agents → validation pipeline. (0:45)
2. **Validation-spine diagram** (same file, second diagram) — model call → deterministic
   gate → abstain-on-failure. (3:35)
3. **CI** — the green GitHub Actions run for backend + frontend. (4:10)

Optional, only if a beat needs it: a 3-second glimpse of `request-trace.md` to reinforce
"every step maps to real code." Do not read code line by line.

## Recommended recording / editing approach

- **Capture:** 1080p screen recording, one clean take per beat; record narration
  separately and lay it over, or narrate live and re-record fumbles.
- **Assemble** the beats in order; insert the three cutaways as picture-in-picture or full
  cuts. Keep cutaways short.
- **The only permissible edit to execution** is removing model-generation dead time in the
  single live clip, always under a visible disclosure caption. Everything else is shown at
  real speed.
- **Captions to prepare:** "recorded run — real recorded output"; "generation
  time-compressed — stages are real, only waiting removed"; "sources cached from an earlier
  run"; and, if used, "running on qwen2.5:7b-instruct, CPU-only".
- **Length target 4:30**, hard cap 5:00. If long, cut the map beat before the evidence or
  validation beats — grounding and abstention are the story.

## What NOT to do

- No fabricated answer, citation, timer, or "live" label on recorded output.
- No claim of speed, accuracy, or scale beyond the measured figures in the performance
  report.
- No implication that a curated-corpus answer was researched live, or vice versa.
- No deep code walkthrough — the cutaways are punctuation, not the subject.
