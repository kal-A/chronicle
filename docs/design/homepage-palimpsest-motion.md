# Chronicle Homepage — Palimpsest Reveal

## Purpose

Use one authored map interaction to make the Ask surface feel like an investigation uncovering historical context. The effect belongs to the atmospheric background; it must never delay, obscure, or damage the user's question.

The selected homepage world is **Illuminated Atlas Table**. Its dominant field is ink navy and Prussian blue, not green; cyan is limited to small registration/evidence cues.

## Interaction

- **Idle:** hold one map scene for roughly 8–12 seconds. A very slow masked reveal exposes portions of the next cartographic layer; no conventional slideshow fade.
- **Typing:** each short burst of input expands a soft eroded mask near the active question field, as though the upper map has been gently rubbed clear. The response should begin within 100–150 ms and settle within 300–500 ms.
- **Pointer:** optional pointer movement may slightly bias the reveal boundary on fine-pointer devices. It must not require rubbing or dragging to use Chronicle.
- **Map change:** once enough of the next layer is exposed, the old layer becomes the texture beneath it and the sequence can continue to another map. Use geographic and temporal changes, not only color changes.
- **Focus protection:** the headline, question field, suggestions, navigation, and workflow strip remain on a stable high-contrast plane while the atlas moves beneath them.

## Content and Accuracy

- Homepage maps communicate historical breadth; investigation maps remain specific to their actual period and geography.
- Prefer recognizable coastlines, historical map scans, routes, and broad geographic labels.
- Never imply that modern borders are historical, invent precise locations, or present decorative routes as evidence.
- Each eventual production map layer needs provenance metadata even when used atmospherically.
- The neutral coastline foundation comes from sourced geographic geometry, not image generation. Natural Earth is the starting candidate for broad physical coastlines; investigation-specific period plates follow Chronicle's existing rights, georeferencing, limitation, and review pattern.
- Generated comps and transition storyboards are art direction only. They must not be reused as production basemap pixels.

## Homepage to Investigation Transition

The transition runs only after the user has reviewed scope and generation has completed. Initial Ask submission still proceeds through Chronicle's real scope and progress states.

1. **Ready, 0–150 ms:** controls acknowledge completion and the destination `MapScope` is available.
2. **Disassemble, 150–500 ms:** peripheral atlas fragments, lines, and texture separate into bounded ink particles. The question field stays intact.
3. **Resolve, 400–900 ms:** particles follow the destination bounds and assemble the verified coastline/period layer. They do not wander as a generic starfield.
4. **Open, 750–1100 ms:** the map fits the investigation scope, workspace controls appear, and the question field completes its shared-element move into the docked assistant or mobile bottom sheet.

The destination is the real investigation map. Particle positions are sampled from validated coastline/route geometry or from a disclosed schematic; the animation never invents an intermediate map. The effect plays once when an investigation opens, not on routine scene or lens changes.

Reference behavior: [CollectUI landing-page example](https://collectui.com/designs/landing-page-ui-design-inspiration/3261b20d-d0c7-4143-b7d1-83c79a5f0118). Chronicle borrows only its line-art dissolve/reassembly principle, not its mountain imagery, layout, or brand treatment.

## Motion and Performance

- Preferred implementation: two or three map layers with CSS/SVG masks or a small canvas shader. Do not add a large animation dependency for the effect.
- Expensive blur, texture, and mask work stays inside the map field and pauses when the page is hidden.
- `prefers-reduced-motion` uses one static layered map and a short opacity/color transition when the question changes; it removes spatial drift and auto-cycling.
- Text and controls remain semantic HTML. Do not rasterize the Ask interface into the map artwork.
- Start with a conservative particle budget and profile on desktop and mobile before increasing it. Pause and release animation work when the page is hidden.
- Reduced-motion map opening uses a 150–250 ms crossfade plus direct `fitBounds`; the shared question context remains visible without particle travel.

## Lighting Contract

- Preserve dark cinematic edges but maintain a controlled midtone pool around the task.
- Primary text uses warm high-contrast ivory; secondary text cannot depend on low-opacity gray over detailed maps.
- The Ask field uses an opaque-enough dark surface and a precise light keyline, with no broad glow.
- Map detail remains visible outside the focus region so the background reads as cartography rather than black texture.

## Implemented Prototype Slice — 2026-08-15

- The hero begins on an empty ink field. The sourced Natural Earth coastline itself is drawn from no visible geometry while the headline and supporting copy type as one authored sequence; it is not a highlight or mask over a pre-rendered coastline. Graticules arrive after the coastline is legible, then labels, compass, source note, and the faint settled-ink underlay. Reduced-motion users receive the complete text and map immediately.
- The scope-review and generation states use an opaque ink field, larger body copy, and higher-contrast evidence labels so the map remains atmosphere rather than a readability hazard.
- Completion now passes through a bounded cartographic-particle transition that preserves the submitted question and names the destination scene.
- The destination workspace carries the same atlas palette and visual hierarchy. Its actual scene-specific period map (or explicitly labeled schematic fallback) reveals into the primary canvas; the timeline, lens controls, evidence, and sources remain fully interactive.
- The transition is presentation over an existing curated package. It is not yet a live generation response, and no UI copy claims otherwise.
