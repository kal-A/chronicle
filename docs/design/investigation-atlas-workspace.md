# Investigation Atlas Workspace

## Approved direction

The default investigation route is a historical operating surface rather than
an article dashboard. It extends the landing page's dark Atlantic atlas into a
local, source-bound theatre with the interaction density of a grand-strategy
map while retaining Chronicle's research language and evidence standards.

The visual reference is the approved third frame of the landing-to-
investigation sequence: a dominant map, compact command bar, persistent right
research rail, and a time/provenance instrument attached to the map.

## Desktop composition

- The map owns the majority of the viewport and is never placed inside a
  generic dashboard card.
- The command bar contains Chronicle, the investigation title, lens selection,
  focus reset when needed, and Inspector access.
- The scene heading and active event/place appear as restrained map plaques.
- The research rail keeps the submitted question and the Ask, Explore,
  Evidence, and Sources tabs visible.
- Map provenance and georeferencing limitations remain available through an
  expandable control immediately above the time rail.

## Temporal interaction contract

The time control operates on curated `EventRecord` order, not invented
animation time.

1. The selected event becomes the current historical moment.
2. Only events at or before that position are visible on the map.
3. Later event markers disappear when the user scrubs backward and return when
   the user advances.
4. Selecting a time step creates first-class event focus through the existing
   URL-backed `Focus` contract.
5. The active event highlights its documented `placeId`; the Evidence tab
   therefore updates from the same focus rather than maintaining parallel UI
   state.
6. Each visible place exposes the dated events attached to it. Selecting one
   focuses the event and synchronizes the rest of the workspace.

This is the first implementation of the desired Europa Universalis/Crusader
Kings interaction influence: geography, time, and the information rail respond
as one system. It does not yet include play/pause time, authored political
region polygons, animated routes, or map-mode overlays.

## Historical accuracy boundary

- Political borders come only from a cited period map asset.
- Event markers use stored place coordinates and never imply precision beyond
  the corresponding place record.
- No route, territorial highlight, or border state is invented from a model's
  prior knowledge.
- A scene without a suitable researched map keeps the disclosed schematic
  fallback.
- The provenance control exposes the map citation, rights, and georeferencing
  note.

## Search and retrieval boundary

The project already contains a working package-backed corpus search, ten typed
retrieval tools, and the bounded Planner/Evidence Analyst runner. They are
Python-only today. The React landing search still matches the registered
investigation packages, and the investigation Ask tab remains disabled rather
than fabricating a response.

The path to a genuinely working browser search is:

1. Phase E5: FastAPI and streaming expose the now-complete four-agent loop,
   corpus search, and agent-run progress
   through the project's first HTTP boundary.
2. Phase E6: the landing search and investigation Ask panel call that API,
   display scope/retrieval progress, stream grounded results, and preserve
   citations, limitations, abstentions, and failures.

No client-side imitation of the Python retrieval engine should be added merely
to make the input appear live.
