"""Source-candidate provider — chronicle_phase_c_adjusted_plan.md §8/§9.

Input: prior data including "discoveryQueries". Output adds
"sourceCandidates" — deliberately not a full §9 candidate model (25 fields);
only what downstream stages (assessment, corpus assembly) actually consume,
per the C2 plan's "intermediate stage data stays informal" scoping note.
"""


def discover_source_candidates(data: dict) -> dict:
    slug = data["slug"]
    topic = data["topic"]
    query = data["discoveryQueries"][0]

    candidates = [
        {
            "candidateId": f"candidate-{slug}-1",
            "provider": "mock-archive",
            "providerItemId": f"mock-item-{slug}-1",
            "discoveryQueryId": query["id"],
            "canonicalUrl": f"mock://sources/{slug}-1",
            "title": f"A primary account concerning {topic}",
            "authorOrOrigin": "Unattributed contemporary observer (Phase C2 mock)",
            "sourceType": "primary-official-diplomatic",
            "originalLanguage": "English",
            "rightsStatus": "public-domain",
            "fullTextAvailable": True,
        }
    ]
    return {**data, "sourceCandidates": candidates}
