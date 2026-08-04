"""Geographic provider — chronicle_phase_c_adjusted_plan.md §8.

Part of HISTORICAL_MODEL_ASSEMBLED, run last. A synthetic generic topic has
no real geography to map — producing a fabricated HistoricalMapAsset just
to fill the field would violate the honest-imprecision discipline this
whole project runs on (AGENTS.md §12). So this provider genuinely abstains:
no map asset, no map scene. That abstention is what makes the composed
package's status honestly "partial" rather than a contrived flag — see
composition.py and the C2 plan's "genuine, non-contrived PARTIAL coverage".
"""


def assemble_geography(data: dict) -> dict:
    return {**data, "mapAssets": [], "mapScenes": [], "geographyOmitted": True}
