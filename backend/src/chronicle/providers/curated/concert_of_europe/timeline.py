"""Chronological ordering of the five curated events."""

EVENT_ORDER = [
    "event-congress-of-vienna",
    "event-troppau-protocol",
    "event-laibach-authorization",
    "event-naples-intervention",
    "event-congress-of-verona",
]


def build_timeline(data: dict) -> dict:
    events_by_id = {event["id"]: event for event in data["events"]}
    timeline = [
        {"id": f"timeline-{event_id}", "eventId": event_id, "order": index}
        for index, event_id in enumerate(EVENT_ORDER)
        if event_id in events_by_id
    ]
    return {**data, "timeline": timeline}
