# Generation-First User Experience

## Experience Sequence

### 1. Investigation Request

Lead with “What would you like to understand?” Accept topic, question, comparison, connection, knowledge-state question, or optional source. Offer a small set of meaningful controls: depth, date range, geographic focus, thematic focus, and primary-source emphasis.

### 2. Scope Proposal

Before discovery, show the interpreted question, dates, geography, actors, institutions, themes, source categories, inclusions, exclusions, ambiguities, and expected outputs. Broad requests cannot start unrestricted generation. The user approves or adjusts the scope.

### 3. Visible Workflow

Show structured stage state rather than chain-of-thought:

```text
Defining scope → Searching → Assessing → Acquiring → Extracting
→ Resolving → Building timeline → Comparing → Criticizing relationships
→ Preparing geography → Verifying → Ready / Partial / Failed
```

Users can inspect candidate sources, acceptance/rejection reasons, coverage, failures, retries, limitations, and remaining work.

### 4. Investigation Canvas

Use progressive disclosure rather than giving every facet equal weight:

1. Overview and direct synthesis
2. Key factors and principal disagreements
3. Sequence and knowledge states
4. Perspectives
5. Map and connections
6. Evidence and sources
7. Limitations and generation report

Timeline, map, graph, and evidence retain synchronized focus and URL state. Generated interaction specifications drive navigation; generated code never does.

### 5. Grounded Assistant

The assistant operates over the generated package and corpus through typed tools. It cites passages, distinguishes fact from interpretation, exposes insufficient evidence, and returns typed UI actions such as focusing a timeline range, map scene, relationship path, or passage.

## Required States

- Scope needs clarification
- Awaiting scope approval
- Running with per-stage progress
- Paused or resumable failure
- Partial result with limitations
- Invalid package blocked by verification
- Valid draft investigation
- Human-reviewed/published investigation

## Accessibility

Workflow progress is announced without noisy live-region churn. Every visual map/graph has a first-class structured alternative. Uncertainty, rejection, and stage status are conveyed with text, not color alone. Keyboard focus and URL navigation remain part of the renderer contract.

