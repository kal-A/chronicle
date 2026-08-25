# Cartographic and Copy Quality Gate

This gate applies to the homepage atlas, the homepage-to-investigation transition, and every investigation map. A screen fails review if its geography or visible language creates a false impression of accuracy.

## 1. Copy and Spelling

- All interface text is rendered from reviewed HTML/application strings. Generated comp text is never shipped or cropped into a production asset.
- Run an automated spelling check across UI strings, investigation fixtures, visible labels, and accessibility text before merge; follow with a human copy review of the rendered desktop and mobile screens.
- Preserve accents, diacritics, apostrophes, and historically appropriate capitalization. Do not silently anglicize a place name.
- Copy review includes truncation, wrapping, 200% zoom, and long-name behavior. A correct label that is clipped or attached to the wrong object still fails.
- Product-state language must be accurate: use "draft", "approximate", "schematic", "modern orientation", or "historical layer unavailable" wherever the underlying data requires it.

## 2. Place Names and Labels

- The primary historical label comes from the period-valid `PlacePeriodRecord.nameAtTime`, supported by its represented period and review status.
- `canonicalName` is an internal identity/fallback. If a modern name aids orientation, present it separately and label it as modern or current.
- Labels for regions, polities, routes, and bodies of water require a documented source and period fit. The model may propose a label but cannot approve or publish it.
- Broad geographic labels must sit over the correct feature. Labels hidden by collision handling are preferable to labels moved onto the wrong landmass or water body.
- Historical scans may retain their original printed labels as part of the facsimile. Interactive Chronicle labels must remain visually distinct from the scan and traceable to structured records.
- Avoid duplicate labels, mixed-period names, unsupported translations, and present-day country names used as unqualified historical labels.

## 3. Location and Precision

- Coordinates come from a sourced place record; having coordinates does not increase the evidence's precision.
- Render `building`, `city`, `region`, and `approximate` locations differently. Never use a precise pin for city-, region-, or approximate-level evidence.
- A location outside the investigation's validated `MapScope`, source coverage, or applicable period is rejected or explicitly disclosed before rendering.
- Key places are checked against at least one authoritative geographic reference and, where relevant, a period gazetteer or reviewed historical source.
- The accessible location list and the visual map must use the same name, period record, precision, and focus state.

## 4. Projection, Scale, and Zoom

- Store and disclose each historical asset's represented period, coverage, original scale when known, projection when known, georeferencing method, and limitations.
- Select coastline detail appropriate to the viewport: broad/global views use generalized geometry; regional investigations use more detailed geometry. Do not imply detail that the source scale cannot support.
- Set maximum zoom from the source geometry/raster resolution and georeferencing quality. Users must not be able to zoom an approximate plate until it appears survey-precise.
- Generate scale bars and coordinates from the live MapLibre camera/projection. Do not bake a decorative scale into a raster comp.
- Fit the initial camera to the validated `MapScope`, including only the surrounding context required for orientation. Never default an investigation to a whole-world view.
- A georeferenced scan is visually checked at several control locations. Misalignment is corrected, disclosed, or rejected; it is never hidden by decorative texture.

## 5. Layer and Transition Integrity

- The neutral coastline, historical scan, political boundary, route, marker, label, and evidence overlay remain separate typed layers with separate provenance.
- The palimpsest effect may reveal or conceal layers but cannot morph one coastline into invented geography.
- The particle transition samples the already validated destination geometry. Its intermediate frame must converge on the same bounds, coastline, and focus shown by the final map.
- If the destination map fails validation or loading, the transition does not resolve into fabricated detail. Show the disclosed schematic/list fallback and preserve the user's question.
- Modern orientation geography, when present, is subdued and explicitly labelled; it never masquerades as period political geography.

## 6. Acceptance Review

Before a map-bearing screen is accepted:

1. Schema validation passes for period records, precision, bounds, citations, rights, and georeferencing notes.
2. Automated spelling/copy checks pass with reviewed exceptions only.
3. Desktop and mobile screenshots show no collisions, clipped labels, illegible text, or misplaced annotations.
4. Key coastlines, islands, locations, and relative positions are compared with the authoritative base.
5. Historical names, boundaries, and routes receive a human period-fit review.
6. Scale, projection, zoom limits, attribution, and geographic limitations are visible or inspectable.
7. Keyboard, screen-reader, reduced-motion, and schematic fallback paths preserve the same factual meaning.

Any unresolved spelling, label, location, period-fit, projection, or scale issue blocks release of that map. Omission with a clear limitation is preferable to confident inaccuracy.
