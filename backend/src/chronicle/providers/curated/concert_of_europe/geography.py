"""Real, rights-cleared period map for the Vienna congress scene only.

Unlike C2's mock geography provider (which always abstains), this package
has a genuine period-accurate map available for 1815 — but it is
deliberately NOT reused for the 1820-1822 scene: the plate documents the
Congress of Vienna's 1815 territorial settlement, not the Troppau/
Laibach/Verona-era situation five to seven years later, so attaching it
there would misrepresent period fit. That later scene honestly has no map,
disclosed in composition.py's generationReport.omissions — the same
"disclose the gap rather than silently resolve it" discipline
docs/research/scene-2-map-source.md documents for its Balkans gap.

See docs/research/concert-of-europe-map-source.md for the full source,
rights, and georeferencing write-up.
"""

MAP_ASSET_ID = "map-asset-shepherd-1815"
VIENNA_SCENE_ID = "scene-congress-of-vienna"
MAP_SCENE_ID = "map-scene-vienna"


def assemble_geography(data: dict) -> dict:
    map_asset = {
        "id": MAP_ASSET_ID,
        "imagePath": "/maps/concert-of-europe/shepherd-treaty-adjustments-1815.jpg",
        "bounds": {
            "topLeft": {"lat": 60, "lng": -2},
            "topRight": {"lat": 60, "lng": 27},
            "bottomRight": {"lat": 36, "lng": 27},
            "bottomLeft": {"lat": 36, "lng": -2},
        },
        "defaultView": {"center": {"lat": 48.2082, "lng": 16.3738}, "zoom": 4.5},
        "periodLabel": "1815 (the Congress of Vienna's territorial settlement)",
        "sourceCitation": (
            "William R. Shepherd, Historical Atlas (New York: Henry Holt and Company, 1911), "
            "plate \"Treaty Adjustments, 1814, 1815,\" p. 157."
        ),
        "attribution": "Perry-Castaneda Library Map Collection, University of Texas Libraries",
        "license": "Public domain (US publication, 1911)",
        "georeferencingNote": (
            "This plate (unlike Scene 2's separate, continent-wide 1911 Shepherd plate) covers Western "
            "and Central Europe only, from roughly the English Channel to Galicia and from southern "
            "Scandinavia to the western Mediterranean. It carries its own printed reference grid "
            "(lettered columns/rows with degree labels visible along the top and right margins, "
            "approximately 10-25 deg E and 40-55 deg N); rectangular bounds here were read by visual "
            "inspection of that grid, extended slightly to the plate's true edges, and are a disclosed "
            "approximation, not a survey-grade transform. Vienna falls well within the plate's "
            "least-distorted central region. The plate reflects the 1815 settlement only; it is "
            "intentionally not attached to the 1820-1822 scene, whose political geography (e.g. Naples, "
            "Verona under Austrian Lombardy-Venetia) it does not independently verify."
        ),
        "rightsStatus": "public-domain",
        "periodFitDecision": "approved",
        "georeferencingPrecision": "approximate",
    }

    map_scene = {
        "id": MAP_SCENE_ID,
        "sceneId": VIENNA_SCENE_ID,
        "mapAssetId": MAP_ASSET_ID,
        "markers": [{"placeId": "place-vienna", "precision": "city"}],
    }

    return {**data, "mapAssets": [map_asset], "mapScenes": [map_scene]}
