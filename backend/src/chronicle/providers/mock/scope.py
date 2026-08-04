"""Scope provider — chronicle_phase_c_adjusted_plan.md §8.

Input: {"topic": str}. Output adds "slug" (used to build every deterministic
id downstream) and "scope" (an InvestigationScope-shaped dict).
"""

from ..util import SENTINEL_DATE, slugify


def propose_scope(data: dict) -> dict:
    topic = data["topic"]
    slug = slugify(topic)

    scope = {
        "interpretedQuestion": f'What happened regarding "{topic}"?',
        "dateRange": {
            "precision": "approximate",
            "earliest": SENTINEL_DATE,
            "latest": SENTINEL_DATE,
            "label": "Placeholder period — Phase C2 generic mock has no real date evidence",
        },
        "geographicScope": [f'Unspecified locale for "{topic}"'],
        "themes": ["general history"],
        "inclusions": [f"Events directly concerning: {topic}"],
        "exclusions": ["Unrelated contemporaneous events"],
        "approvalStatus": "proposed",
    }
    return {**data, "slug": slug, "scope": scope}
