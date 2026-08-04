"""Discovery-query provider — chronicle_phase_c_adjusted_plan.md §8.

Input: prior data including "scope". Output adds "discoveryQueries", a list
of structured query descriptions (not real search queries — nothing is
actually searched in Phase C2).
"""


def prepare_discovery_queries(data: dict) -> dict:
    slug = data["slug"]
    topic = data["topic"]

    queries = [
        {
            "id": f"query-{slug}-1",
            "queryText": f'"{topic}" primary sources',
            "purpose": "primary-source-search",
            "expectedSourceType": "primary-official-diplomatic",
            "targetProviderCategory": "mock-archive",
        }
    ]
    return {**data, "discoveryQueries": queries}
