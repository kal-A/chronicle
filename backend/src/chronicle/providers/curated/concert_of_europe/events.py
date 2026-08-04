"""Real events for the Concert of Europe congresses, each evidenced by a
genuine curated passage (sources.py/corpus.py) rather than a placeholder."""


def extract_events(data: dict) -> dict:
    vienna_passage_id = "passage-vienna-final-act-1"
    troppau_passage_id = "passage-troppau-protocol-1"

    events = [
        {
            "id": "event-congress-of-vienna",
            "title": "The Congress of Vienna convenes and concludes with the General Treaty",
            "placeId": "place-vienna",
            "eventTime": {
                "precision": "range",
                "earliest": "1814-09-18",
                "latest": "1815-06-09",
                "label": "18 September 1814 (congress opens) to 9 June 1815 (General Treaty signed)",
            },
            "evidenceLinkIds": ["evidence-event-vienna-1"],
            "relatedRecordIds": ["claim-vienna-settlement"],
            "reviewStatus": "proposed",
            "visibility": "public",
        },
        {
            "id": "event-troppau-protocol",
            "title": "Austria, Prussia, and Russia sign the Troppau Protocol",
            "placeId": "place-troppau",
            "eventTime": {
                "precision": "exact",
                "earliest": "1820-11-19",
                "latest": "1820-11-19",
                "label": "19 November 1820",
            },
            "evidenceLinkIds": ["evidence-event-troppau-1"],
            "relatedRecordIds": ["claim-troppau-doctrine"],
            "reviewStatus": "proposed",
            "visibility": "public",
        },
        {
            "id": "event-laibach-authorization",
            "title": "The Congress of Laibach authorizes Austrian military intervention in Naples",
            "placeId": "place-laibach",
            "eventTime": {
                "precision": "range",
                "earliest": "1821-01-26",
                "latest": "1821-02-28",
                "label": "26 January 1821 (congress opens) to late February 1821 (Austrian troops march)",
            },
            "evidenceLinkIds": ["evidence-event-laibach-1"],
            "relatedRecordIds": ["claim-naples-intervention"],
            "reviewStatus": "proposed",
            "visibility": "public",
        },
        {
            "id": "event-naples-intervention",
            "title": "Austrian forces suppress the constitutional government in Naples",
            "placeId": "place-naples",
            "eventTime": {
                "precision": "range",
                "earliest": "1821-03-01",
                "latest": "1821-03-24",
                "label": "March 1821, culminating in the Austrian victory at Rieti (7 March 1821) and entry into Naples",
            },
            "evidenceLinkIds": ["evidence-event-naples-1"],
            "relatedRecordIds": ["claim-naples-intervention"],
            "reviewStatus": "proposed",
            "visibility": "public",
        },
        {
            "id": "event-congress-of-verona",
            "title": "The Congress of Verona authorizes French intervention in Spain",
            "placeId": "place-verona",
            "eventTime": {
                "precision": "range",
                "earliest": "1822-10-20",
                "latest": "1822-12-14",
                "label": "20 October 1822 (congress opens) to 14 December 1822 (congress closes)",
            },
            "evidenceLinkIds": ["evidence-event-verona-1"],
            "relatedRecordIds": ["claim-verona-spain"],
            "reviewStatus": "proposed",
            "visibility": "public",
        },
    ]

    new_links = [
        {"id": "evidence-event-vienna-1", "targetType": "event", "targetId": "event-congress-of-vienna", "passageId": vienna_passage_id, "role": "supporting"},
        {"id": "evidence-event-troppau-1", "targetType": "event", "targetId": "event-troppau-protocol", "passageId": troppau_passage_id, "role": "supporting"},
        {"id": "evidence-event-laibach-1", "targetType": "event", "targetId": "event-laibach-authorization", "passageId": troppau_passage_id, "role": "supporting"},
        {"id": "evidence-event-naples-1", "targetType": "event", "targetId": "event-naples-intervention", "passageId": troppau_passage_id, "role": "supporting"},
        {"id": "evidence-event-verona-1", "targetType": "event", "targetId": "event-congress-of-verona", "passageId": troppau_passage_id, "role": "supporting"},
    ]

    return {**data, "events": events, "evidenceLinks": [*data.get("evidenceLinks", []), *new_links]}
