# Geographic and Map Generation

## Separate Pipelines

Historical geographic data and historical map assets are separate. A period image is not automatically geographic data, and coordinates do not grant permission to display a map.

## Geographic Records

Extract historical/current names, place roles, routes, communication paths, affected regions, applicable dates, and uncertainty. Resolve using stable identifiers, authoritative gazetteers, archive metadata, sourced coordinates, aliases, and human-review flags.

Precision values include building, street/route, city, administrative region, broad region, disputed, and unknown. Rendering cannot exceed the evidence's precision.

## Map Asset Registry

Store represented period, creator, archive/publisher, coverage, scale/projection, stable ID, URL, rights/licence, IIIF/image service, georeferencing, limitations, and suitability. Unknown rights exclude display. Search-result visibility is not a licence.

## Georeferencing

Prefer already georeferenced assets or historical GIS; then IIIF georeference metadata; then a period image beside a separate geographic layer; then AI-assisted control points requiring verification. Do not place precise overlays on ungeoreferenced scans.

## Typed Map Scene

`MapScene` contains timeframe, viewport, optional asset reference, markers, routes, communications, regions, labels, evidence references, uncertainty notes, and interaction targets. The composer emits data only; the renderer owns MapLibre behavior.

## Verification

Check place/time validity, precision, evidence links, rights, period fit, georeference support, asset attribution, viewport scope, and clutter budgets. Map failures produce a schematic/list or an explicit omission, never fabricated geography.

