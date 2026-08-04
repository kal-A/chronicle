# Concert of Europe Map Source — "Treaty Adjustments, 1814, 1815" (Shepherd, 1911)

Documents the period-accurate basemap used by the Concert of Europe package's "The Congress System Established, 1814-1815" scene, following the same pattern `docs/research/scene-2-map-source.md` established: a scene's map shows the political geography relevant to its events, not a modern basemap, sourced from a rights-cleared period atlas with its limitations disclosed rather than silently resolved.

## Source

- **Plate:** "Treaty Adjustments, 1814, 1815," p. 157.
- **Atlas:** William R. Shepherd, *Historical Atlas* (New York: Henry Holt and Company, 1911).
- **Digitized by:** Perry–Castañeda Library (PCL) Map Collection, University of Texas Libraries — `https://maps.lib.utexas.edu/maps/historical/shepherd_1911/shepherd-c-157.jpg`.
- **Rights:** Public domain (US publication, 1911; well past any copyright term), same basis PCL states for its Shepherd holdings generally.
- **Stored at:** `public/maps/concert-of-europe/shepherd-treaty-adjustments-1815.jpg` (bundled app asset — no runtime network fetch).

## Why this plate

This is a different, narrower plate from the one Scene 2 uses (Scene 2's is the continent-wide "Europe at the Present Time," p. 166–167, drawn as of 1911). "Treaty Adjustments, 1814, 1815" instead shows exactly the outcome of the Congress of Vienna: the redistribution of Saxon and Rhenish territory to Prussia, the "Kingdom of Poland" ceded to Russia, the newly formed German Confederation and its member states, Austria's recovery of Lombardy–Venetia, and the post-1815 borders of France, Switzerland, and the Kingdom of Sardinia — precisely the settlement the package's `claim-vienna-settlement` describes. It covers Western and Central Europe from roughly the English Channel to Galicia, and from southern Scandinavia to the western Mediterranean.

## Georeferencing method (disclosed approximation)

The plate carries its own printed reference grid — lettered columns and rows (A–E, a–e) with degree labels visible along the top and right margins, reading approximately 10°–25° E and 40°–55° N. Corner coordinates for `HistoricalMapAsset.bounds` were read by visual inspection of that grid and extended slightly to the plate's true (uncropped) edges:

| Corner | Lat | Lng |
|---|---|---|
| Top-left | 60°N | 2°W |
| Top-right | 60°N | 27°E |
| Bottom-right | 36°N | 27°E |
| Bottom-left | 36°N | 2°W |

This is a rectangular approximation from visual inspection, not a survey-grade transform — the same disclosed-approximation discipline Scene 2's map documents, applied independently to this plate rather than reused from Scene 2's (that plate has a different extent and would not fit this one). Vienna (48.2082°N, 16.3738°E), the only place this package attaches a map marker to, falls well within the plate's least-distorted central region.

## Explicit Gap — do not silently resolve

**This plate documents the 1815 settlement only.** It is deliberately **not** attached to the package's second scene, "The Principle of Intervention, 1820–1822" (Troppau, Laibach, Naples, Verona) — five to seven years of subsequent history (the Troppau Protocol, the Neapolitan intervention, the Congress of Verona) are not represented on it, and reusing a 1815 plate for 1820s content would misrepresent period fit. `backend/src/chronicle/providers/curated/concert_of_europe/geography.py` documents this reasoning in code; the package's `generationReport.omissions` discloses the resulting no-map gap for that scene rather than hiding it, matching `validate_generated_investigation()`'s rule that map assets require an approved period-fit decision (rule 15) — the honest answer for the 1820s scene is "no map asset," not a misfit one.

## Status

Recorded here as the map-asset-equivalent of `passages-extracted`: acquired, rights-cleared, and its limitations disclosed, but not independently reviewed. See `docs/research/validation-status.md`.
