"""Real Person/Place entities for the Concert of Europe congresses.
Coordinates are real geographic facts (unlike the mock provider set, this
package has genuine, unambiguous places); `precision` on each period record
reflects how specifically the historical record situates the place/name for
that period, not location-fetching accuracy."""


def extract_entities(data: dict) -> dict:
    persons = [
        {
            "id": "person-metternich",
            "entityType": "person",
            "canonicalName": "Klemens von Metternich",
            "alsoKnownAs": ["Prince Metternich", "Klemens Wenzel von Metternich"],
            "description": (
                "Foreign Minister (later Chancellor) of the Austrian Empire, 1809-1848; the principal "
                "architect of the post-1815 Congress system and its principle of collective intervention "
                "against revolution."
            ),
            "reviewStatus": "proposed",
        },
        {
            "id": "person-alexander-i",
            "entityType": "person",
            "canonicalName": "Alexander I of Russia",
            "alsoKnownAs": ["Tsar Alexander I"],
            "description": (
                "Emperor of Russia, 1801-1825; proposer of the Holy Alliance (1815) and, alongside "
                "Metternich, a principal signatory of the Troppau Protocol (1820)."
            ),
            "reviewStatus": "proposed",
        },
        {
            "id": "person-castlereagh",
            "entityType": "person",
            "canonicalName": "Robert Stewart, Viscount Castlereagh",
            "alsoKnownAs": ["Lord Castlereagh"],
            "description": (
                "British Foreign Secretary, 1812-1822; represented Britain at the Congress of Vienna and "
                "authored the May 1820 State Paper rejecting a general right of intervention. Died by "
                "suicide on 12 August 1822, shortly before the Congress of Verona."
            ),
            "reviewStatus": "proposed",
        },
        {
            "id": "person-canning",
            "entityType": "person",
            "canonicalName": "George Canning",
            "alsoKnownAs": [],
            "description": (
                "Succeeded Castlereagh as British Foreign Secretary in September 1822; continued Britain's "
                "dissent from the Congress system's interventionist principle at and after the Congress of "
                "Verona (1822), instructing the Duke of Wellington's delegation there without altering "
                "Castlereagh's prepared position."
            ),
            "reviewStatus": "proposed",
        },
    ]

    places = [
        _place("place-vienna", "Vienna", "Vienna", "Austrian Empire", 48.2082, 16.3738),
        _place("place-troppau", "Troppau", "Troppau (present-day Opava, Czech Republic)", "Austrian Empire (Austrian Silesia)", 49.9387, 17.9026),
        _place("place-laibach", "Laibach", "Laibach (present-day Ljubljana, Slovenia)", "Austrian Empire (Duchy of Carniola)", 46.0569, 14.5058),
        _place("place-naples", "Naples", "Naples", "Kingdom of the Two Sicilies", 40.8518, 14.2681),
        _place("place-verona", "Verona", "Verona", "Austrian Empire (Kingdom of Lombardy-Venetia)", 45.4384, 10.9916),
    ]

    return {**data, "entities": [*persons, *places]}


def _place(entity_id: str, canonical_name: str, name_at_time: str, controlling_polity: str, lat: float, lng: float) -> dict:
    return {
        "id": entity_id,
        "entityType": "place",
        "canonicalName": canonical_name,
        "periodRecords": [
            {
                "periodLabel": "1814-1822 (the Congress system)",
                "nameAtTime": name_at_time,
                "controllingPolity": controlling_polity,
                "precision": "city",
            }
        ],
        "reviewStatus": "proposed",
        "coordinates": {"lat": lat, "lng": lng},
    }
