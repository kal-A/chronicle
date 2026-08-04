"""Timeline provider — chronicle_phase_c_adjusted_plan.md §8.

Part of HISTORICAL_MODEL_ASSEMBLED. Trivial in the generic mock (one event
-> one timeline entry) — a real provider would identify turning points and
date-type distinctions across many events.
"""


def build_timeline(data: dict) -> dict:
    timeline = [
        {"id": f"timeline-{event['id']}", "eventId": event["id"], "order": index}
        for index, event in enumerate(data["events"])
    ]
    return {**data, "timeline": timeline}
