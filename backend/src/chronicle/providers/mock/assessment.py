"""Source-assessment provider — chronicle_phase_c_adjusted_plan.md §8/§9.

Every candidate is deterministically accepted in the generic C2 mock (there's
only ever one, and no real editorial judgment exists to reject it with) —
see §9's assessment-state list for what a real provider would eventually
choose between.
"""


def assess_sources(data: dict) -> dict:
    assessments = [
        {
            "candidateId": candidate["candidateId"],
            "status": "ACCEPTED_EVIDENCE",
            "reason": "Mock acceptance for Phase C2 pipeline-mechanics proof; not a real editorial judgment.",
        }
        for candidate in data["sourceCandidates"]
    ]
    return {**data, "sourceAssessments": assessments}
