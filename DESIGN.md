---
name: Chronicle
description: An illuminated Atlantic atlas where a historical question becomes an evidence-backed investigation.
colors:
  ink-deep: "#06121B"
  prussian-navy: "#0B2231"
  atlantic-blue: "#173F56"
  warm-bone: "#E9DEC5"
  oxidized-copper: "#C45E3C"
  registration-cyan: "#72A8B5"
  raised-ink: "#081A26"
  hover-atlantic: "#0F2D3D"
  active-atlantic: "#103044"
  bright-bone: "#F0E7D5"
  body-cyan: "#B7D1D7"
  light-registration-cyan: "#9BC6CF"
  muted-registration-cyan: "#9FBAC0"
  copper-hover: "#D77554"
  copper-soft: "#E7A88F"
  copper-pale: "#EFC0AD"
  error-copper: "#F0B59F"
typography:
  display:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(5rem, 7.2vw, 6rem)"
    fontWeight: 400
    lineHeight: 0.88
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(2.6rem, 5vw, 4.8rem)"
    fontWeight: 400
    lineHeight: 0.95
  title:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "1.45rem"
    fontWeight: 400
    lineHeight: 1
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.12em"
  workspaceTitle:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "clamp(2.5rem, 4.8vw, 5rem)"
    fontWeight: 400
    lineHeight: 0.92
  compactBody:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.58
rounded:
  square: "0px"
  circular: "50%"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
components:
  navigation-link:
    textColor: "{colors.warm-bone}"
    typography: "{typography.label}"
    padding: "8px 0"
  question-field:
    backgroundColor: "{colors.ink-deep}"
    textColor: "{colors.warm-bone}"
    rounded: "{rounded.square}"
    padding: "10px 14px 9px 20px"
  ask-action:
    backgroundColor: "transparent"
    textColor: "{colors.warm-bone}"
    rounded: "{rounded.circular}"
    size: "56px"
  starter-investigation:
    backgroundColor: "rgb(6 18 27 / 88%)"
    textColor: "{colors.warm-bone}"
    rounded: "{rounded.square}"
    padding: "14px 16px"
  button-primary:
    backgroundColor: "{colors.oxidized-copper}"
    textColor: "{colors.ink-deep}"
    rounded: "{rounded.square}"
    padding: "10px 16px"
    height: "44px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.warm-bone}"
    rounded: "{rounded.square}"
    padding: "10px 16px"
    height: "44px"
---

# Design System: Chronicle

## Overview

**Creative North Star: "Illuminated Atlas Table"**

Chronicle opens as an illuminated atlas table where a question becomes an investigation. Ink-blue Atlantic geography establishes orientation while warm bone type, oxidized copper actions, and engraved linework focus attention on evidence-backed inquiry. The system is atmospheric but operational: the map creates place and depth, while the task plane remains stable, opaque enough for legibility, and honest about the prototype's two curated investigations.

The shipped material language comes from sourced coastline geometry, graticules, physical labels, tonal layering, and one-pixel rules—not simulated paper or faux archival grain. Provenance-cleared period maps and archival fragments may extend the world later, but they must arrive as distinct, documented evidence layers rather than decoration.

**Key Characteristics:**

- Sourced Atlantic geography as the environmental foundation.
- Compressed display type, system-body text, and simplified hierarchy.
- Deep ink surfaces, warm bone text, copper action, and cyan registration cues.
- Predominantly square controls and one-pixel rules with restrained functional circles.
- Tonal and line-based depth, with motion subordinate to orientation and task clarity.

## Colors

The palette is a cold Atlantic field warmed by bone typography and one oxidized copper signal.

### Primary

- **Oxidized Copper:** Use sparingly for the main action, focus confirmation, progress, and singular emphasis.

### Secondary

- **Registration Cyan:** Use for graticules, coastline registration, physical labels, completed stages, and quiet evidence cues; it remains subordinate to the ink field.

### Neutral

- **Deep Ink:** Use for the page ground, stable task surfaces, and dark control interiors.
- **Prussian Navy:** Use for the full-bleed geographic field and broad environmental surfaces.
- **Atlantic Blue:** Use for focused or slightly lifted navy states without introducing a new hue family.
- **Warm Bone:** Use for primary text, keylines, and illuminated cartographic linework, with opacity reductions for secondary copy.
- **Raised Ink / Hover Atlantic:** Approved tonal steps within the same ink-blue family for timeline, canvas, dock, and hover surfaces.
- **Bright Bone / Body Cyan:** Approved high-contrast reading tones for text placed over cartography; light/muted cyan variants carry labels and provenance.

### Named Rules

**The Blue Field Rule.** The visual field must read ink-blue, never green, sepia-only, or generic gradient blue.

**The Copper Signal Rule.** Copper is reserved for action, focus, progress, and singular emphasis; its restraint makes it legible.

## Typography

**Display Font:** Barlow Condensed (with sans-serif fallback)
**Body Font:** System UI (ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif)
**Label Font:** System UI

**Character:** The display face is narrow, cartographic, and locally packaged under OFL-1.1; it compresses large questions into a confident engraved silhouette. The system stack keeps explanations, controls, evidence summaries, and long reading clear.

### Hierarchy

- **Display:** Regular, tightly tracked, and compressed on desktop; the homepage question stays on one line at the reviewed desktop width and wraps intentionally without horizontal scaling on mobile.
- **Headline:** Regular condensed type for major section statements such as the workflow cue.
- **Title:** Regular condensed type for compact workflow steps, scope review, and generation state.
- **Body:** Regular system text with generous leading for introductory and evidence-oriented reading.
- **Label:** Semibold system text, uppercase, and widely tracked for navigation, eyebrows, source notes, and compact state labels.

### Named Rules

**The Compressed Display Rule.** Barlow Condensed leads brand and display moments; system UI carries reading and control copy.

**The Simplified Hierarchy Rule.** Use one dominant display, one explanatory body voice, and quiet labels; do not stack competing headline treatments.

## Layout

The homepage is a full-bleed Atlantic field with an absolutely positioned header and a centered task plane capped at 900px. The reviewed desktop composition uses a wide, compressed, single-line question and a two-column starter grid; the workflow below shifts from a two-column explanation to a single column on smaller screens. Horizontal page gutters are 32px per side on desktop and 16px per side on mobile.

The investigation workspace is a continuation of that field: a title/control header, horizontal atlas timeline, dominant period-map canvas, and evidence dock. It uses the same ink, bone, cyan, and copper hierarchy rather than returning to the neutral prototype shell. Mobile stacks the controls and uses the existing bottom sheet beneath a tall map canvas.

At 760px and below, the map widens and crops rather than shrinking into illegibility, the compass and source note leave the visual layer, and the task plane becomes an opaque ink reading surface with top and bottom rules. Display text aligns left and wraps naturally; starters, scope facts, progress stages, and actions become single-column. At 430px and below, the secondary navigation item hides and the question/action grid preserves a 54px circular control.

**The Question-First Rule.** The question surface is always the dominant operational plane; geography supplies orientation and atmosphere without competing with entry, scope review, or progress.

## Elevation & Depth

Chronicle is primarily flat and tonal. Depth comes from the Prussian field against deep-ink controls, dual coastline strokes, low-opacity graticules, and one-pixel rules. The question field uses a deep structural shadow, and the mobile task plane adds a larger shadow solely to keep reading stable over the cropped map.

### Shadow Vocabulary

- **Question Anchor:** A deep downward shadow beneath the question form establishes the primary interaction plane.
- **Mobile Reading Plane:** A broader, slightly stronger shadow separates the opaque mobile task surface from moving geographic detail.

### Named Rules

**The Material Truth Rule.** Depth comes from sourced geography, tonal layering, line contrast, and reading-stability shadows; never add faux unsourced paper or grain.

## Shapes

The form language is predominantly square: inputs, starter investigations, scope actions, and content rules use zero-radius corners and one-pixel strokes. The circular ask action and compass are deliberate functional and cartographic exceptions, not a general rounded-control vocabulary. Coastlines use round caps and joins so sourced geometry reads as inked linework rather than angular UI chrome.

**The Functional Circle Rule.** Reserve circles for directional action and cartographic instrumentation; all other controls remain square unless a new function proves the exception.

## Components

### Navigation

- **Style:** A wordmark-only brand lockup sits opposite two compact uppercase links behind a single warm-bone rule.
- **States:** Links shift from warm bone to copper on hover and retain a visible warm-bone keyboard outline.
- **Mobile:** At 430px and below, keep Explore and hide About to protect the wordmark and task entrance.

### Question Field

- **Shape:** A square, copper-keylined field with a fully opaque deep-ink surface and an embedded circular action.
- **Focus:** Focus-within changes the keyline to warm bone and adds a two-pixel copper confirmation ring; the text caret is copper.
- **Prompt:** Keep the placeholder direct and historical; the action caption reads “Begin an investigation.”

### Circular Ask Action

- **Shape:** A 56px outlined circle containing a simple directional arrow; it is the homepage's primary geometric exception.
- **States:** Hover fills copper and reverses the icon to deep ink. Disabled state remains visibly unavailable at reduced opacity.

### Starter Investigations

- **Style:** Two always-visible square investigation buttons sit in a two-column desktop grid and a single mobile column.
- **Content:** Each uses a cyan search glyph and a real curated question. The adjacent statement explicitly says the prototype searches two curated investigations.
- **States:** Hover shifts the surface toward Atlantic blue and raises the copper border signal without adding elevation.

### No-Match Recovery

- **Style:** A compact alert with a one-pixel copper left rule and no enclosing card.
- **Content:** State plainly that nothing curated matches yet, then leave the two real starters visible as recovery paths.

### Scope Review

- **Style:** An embedded, high-contrast raised-ink reading field within the task plane, not a modal. One cyan keyline and a downward soft shadow protect dense evidence copy from the moving map.
- **Content:** Present scope, current evidence, and evidence coverage as three desktop columns that stack on mobile.
- **Actions:** Pair one copper primary action with one transparent secondary action; offer only behavior that exists.

### Generation Progress

- **Style:** Reuse the scope-review reading field and condensed title, then show the real eight-stage sequence in two columns or one on mobile.
- **States:** Future stages are muted, the current stage uses warm bone, and completed stages use registration cyan. Reduced-motion timing accelerates without removing status semantics.

### Named Rules

**The Two-Starters Rule.** Always show exactly the two currently curated investigations and never imply universal search or live generation.

**The One-Pixel Recovery Rule.** A no-match state uses one copper rule and direct copy, never a heavy warning panel that displaces the viable starters.

### Investigation Workspace

- **Map:** The scene's curated period plate is the dominant canvas. A missing plate remains an explicitly named schematic, never an invented basemap.
- **Timeline:** A horizontal atlas strip uses tabular dates and copper focus without card elevation.
- **Dock:** Ask, Explore, Evidence, and Sources remain in the proven accessible tab pattern, recolored into the atlas system; resizing, collapse, keyboard navigation, and mobile sheet behavior are preserved.
- **Arrival:** The homepage transition names the destination scene and submitted question, then the real scene map reveals left-to-right once. Routine lens, focus, and tab changes do not replay it.

## Do's and Don'ts

### Do:

- **Do** use Natural Earth 1:50m public-domain coastline geometry or another documented authoritative source for geographic foundations.
- **Do** keep interface copy semantic and code-rendered, and describe the Atlantic layer as modern physical orientation with no political borders.
- **Do** keep detailed geography behind an opaque-enough task surface, especially on mobile.
- **Do** pair every motion treatment with the global reduced-motion override; the coastline reveal uses a 480ms transform transition with the established custom easing.
- **Do** preserve visible selection, caret, focus, and themed scrollbar states within the Chronicle world.

### Don't:

- **Don't** use generated map shapes, unsupported historical borders, routes, or labels as geographic truth.
- **Don't** add unsourced paper textures, faux document panels, or decorative archival grain.
- **Don't** imply open-ended search, live AI generation, or more than the two curated investigations currently implemented.
- **Don't** put detailed map linework directly behind small reading text without a stable ink surface.
- **Don't** round square controls or proliferate circles beyond directional and cartographic functions.
