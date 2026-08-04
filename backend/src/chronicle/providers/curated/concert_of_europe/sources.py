"""Real, hand-researched scope and source curation for "The Concert of
Europe and Revolutionary Intervention, 1814-1822" — Phase C3's proof that
the pipeline can carry genuinely researched content, not just C2's
disclosed-synthetic mock content. Covers the four stages before corpus
assembly (SCOPE_PROPOSED, DISCOVERY_QUERIES_PREPARED,
SOURCE_CANDIDATES_DISCOVERED, SOURCES_ASSESSED) plus the curated source list
corpus.py turns into Source/Document/Passage records.

Sourcing discipline: every quoted excerpt is either (a) a direct quotation
independently corroborated across multiple secondary descriptions of the
same primary text, or (b) an explicitly labelled paraphrase/summary, never
a fabricated "verbatim" quote of wording not independently confirmed. Each
source's knownLimitations discloses exactly which of these it is — the same
honesty discipline docs/research/scene-2-map-source.md applies to its map.
"""

SLUG = "concert-of-europe"

TOPIC = "The Concert of Europe and Revolutionary Intervention"


def propose_scope(data: dict) -> dict:
    scope = {
        "interpretedQuestion": (
            "How did the Congress system established at Vienna in 1814-15 evolve into an "
            "explicit doctrine of collective military intervention against revolution, and "
            "how did Britain's dissent fracture that consensus by the Congress of Verona in 1822?"
        ),
        "dateRange": {
            "precision": "range",
            "earliest": "1814-09-18",
            "latest": "1822-12-14",
            "label": "The Congress system, from the opening of the Congress of Vienna to the close of the Congress of Verona",
        },
        "geographicScope": [
            "Austrian Empire",
            "Kingdom of Prussia",
            "Russian Empire",
            "United Kingdom",
            "France",
            "Kingdom of the Two Sicilies",
            "Spain",
        ],
        "themes": [
            "diplomatic history",
            "the Concert of Europe",
            "the principle of intervention",
            "conservative restoration after 1815",
        ],
        "inclusions": [
            "The Congress of Vienna (1814-1815) and its territorial settlement",
            "The Troppau Protocol (1820) and the principle of intervention",
            "The Congress of Laibach (1821) and the Austrian intervention in Naples",
            "The Congress of Verona (1822) and the authorization of French intervention in Spain",
            "Britain's dissent from the general right of intervention",
        ],
        "exclusions": [
            "The 1823 French invasion of Spain itself (the Hundred Thousand Sons of Saint Louis)",
            "The Greek War of Independence",
            "Domestic German measures (e.g. the Carlsbad Decrees) not directly tied to the Congress system",
        ],
        "approvalStatus": "approved",
    }
    return {**data, "slug": SLUG, "scope": scope}


def prepare_discovery_queries(data: dict) -> dict:
    queries = [
        {
            "id": "query-concert-of-europe-1",
            "queryText": "Final Act of the Congress of Vienna 1815 full text",
            "purpose": "primary-source-search",
            "expectedSourceType": "primary-official-diplomatic",
            "targetProviderCategory": "public-domain-treaty-text",
        },
        {
            "id": "query-concert-of-europe-2",
            "queryText": "Troppau Protocol 1820 text principle of intervention",
            "purpose": "primary-source-search",
            "expectedSourceType": "primary-official-diplomatic",
            "targetProviderCategory": "public-domain-treaty-text",
        },
        {
            "id": "query-concert-of-europe-3",
            "queryText": "Castlereagh State Paper 5 May 1820 British rejection general right of intervention",
            "purpose": "primary-source-search",
            "expectedSourceType": "primary-official-diplomatic",
            "targetProviderCategory": "public-domain-treaty-text",
        },
    ]
    return {**data, "discoveryQueries": queries}


def discover_source_candidates(data: dict) -> dict:
    candidates = [
        {
            "candidateId": "candidate-concert-of-europe-vienna",
            "provider": "wikisource",
            "providerItemId": "Final_Act_of_the_Congress_of_Vienna",
            "discoveryQueryId": "query-concert-of-europe-1",
            "canonicalUrl": "https://en.wikisource.org/wiki/Final_Act_of_the_Congress_of_Vienna/General_Treaty",
            "title": "General Treaty of the Congress of Vienna",
            "authorOrOrigin": "Plenipotentiaries of Austria, France, Great Britain, Portugal, Prussia, Russia, and Sweden",
            "sourceType": "primary-official-diplomatic",
            "originalLanguage": "French (English translation cited)",
            "rightsStatus": "public-domain",
            "fullTextAvailable": True,
        },
        {
            "candidateId": "candidate-concert-of-europe-troppau",
            "provider": "compiled-edition",
            "providerItemId": "hertslet-map-of-europe-by-treaty-vol-1",
            "discoveryQueryId": "query-concert-of-europe-2",
            "canonicalUrl": "https://en.wikisource.org/wiki/1911_Encyclop%C3%A6dia_Britannica/Troppau,_Congress_of",
            "title": "Protocol of the Preliminary Conference at Troppau",
            "authorOrOrigin": "Plenipotentiaries of Austria, Prussia, and Russia (Metternich, Hardenberg, Bernstorff, Nesselrode, Capo d'Istria)",
            "sourceType": "primary-official-diplomatic",
            "originalLanguage": "French (English translation cited)",
            "rightsStatus": "public-domain",
            "fullTextAvailable": False,
        },
        {
            "candidateId": "candidate-concert-of-europe-castlereagh",
            "provider": "compiled-edition",
            "providerItemId": "british-and-foreign-state-papers-vol-8",
            "discoveryQueryId": "query-concert-of-europe-3",
            "canonicalUrl": "British and Foreign State Papers, Vol. VIII (London: James Ridgway, 1830)",
            "title": "State Paper of 5 May 1820 (Castlereagh's Circular rejecting a general right of intervention)",
            "authorOrOrigin": "Robert Stewart, Viscount Castlereagh, British Foreign Secretary",
            "sourceType": "primary-official-diplomatic",
            "originalLanguage": "English",
            "rightsStatus": "public-domain",
            "fullTextAvailable": False,
        },
    ]
    return {**data, "sourceCandidates": candidates}


def assess_sources(data: dict) -> dict:
    reasons = {
        "candidate-concert-of-europe-vienna": (
            "Full text independently located at a stable public-domain hosting (Wikisource); "
            "accepted as primary evidence for the Vienna settlement."
        ),
        "candidate-concert-of-europe-troppau": (
            "The Protocol's key clause is independently corroborated by multiple secondary "
            "descriptions with consistent wording, but a directly hosted full primary text was "
            "not located in this pass — accepted with a disclosed sourcing limitation "
            "(see corpus.py's knownLimitations for this source)."
        ),
        "candidate-concert-of-europe-castlereagh": (
            "A real, historically documented State Paper; accepted, but its exact wording is "
            "represented here as a paraphrase rather than a verbatim quotation, since an "
            "independently verifiable full-text transcription was not located in this pass."
        ),
    }
    assessments = [
        {
            "candidateId": candidate["candidateId"],
            "status": "ACCEPTED_EVIDENCE",
            "reason": reasons[candidate["candidateId"]],
        }
        for candidate in data["sourceCandidates"]
    ]
    return {**data, "sourceAssessments": assessments}


# Curated Source -> Document -> Passage content, keyed by candidateId so
# corpus.py can join it against the accepted assessments above.
CURATED_SOURCE_CONTENT = {
    "candidate-concert-of-europe-vienna": {
        "sourceId": "source-vienna-final-act",
        "documentId": "document-vienna-final-act",
        "dateOfSource": {"precision": "exact", "earliest": "1815-06-09", "latest": "1815-06-09", "label": "9 June 1815"},
        "editionCitation": (
            "Final Act of the Congress of Vienna, General Treaty, 9 June 1815, English translation "
            "laid before the British Parliament, 2 February 1816."
        ),
        "documentLimitations": (
            "English translation of a French-language original; the translation itself, not the "
            "French original, is what this prototype's excerpt is drawn from."
        ),
        "sourceLimitations": (
            "Primary treaty text, independently located at a stable public-domain hosting. Excerpt below "
            "is a close paraphrase of the settlement's territorial provisions, not a verbatim quotation of "
            "specific article text, since no single short passage of the General Treaty summarizes them."
        ),
        "passages": [
            {
                "id": "passage-vienna-final-act-1",
                "excerpt": (
                    "The General Treaty redrew the map of post-Napoleonic Europe: Prussia received part of "
                    "Saxony and territory along the Rhine; Russia received most of the former Duchy of Warsaw "
                    "as the semi-autonomous 'Congress Poland'; Austria regained Lombardy-Venetia in northern "
                    "Italy; and the 39 German states were organized into a new German Confederation. "
                    "[Paraphrase of the settlement's territorial provisions, not a verbatim quotation.]"
                ),
                "locator": "General Treaty, territorial articles (paraphrased)",
            }
        ],
    },
    "candidate-concert-of-europe-troppau": {
        "sourceId": "source-troppau-protocol",
        "documentId": "document-troppau-protocol",
        "dateOfSource": {"precision": "exact", "earliest": "1820-11-19", "latest": "1820-11-19", "label": "19 November 1820"},
        "editionCitation": (
            "Protocol of the Preliminary Conference at Troppau, 19 November 1820, as reprinted in standard "
            "19th-century diplomatic compilations (e.g. Hertslet, The Map of Europe by Treaty)."
        ),
        "documentLimitations": (
            "This prototype cites the Protocol via secondary reprints rather than a directly verified, "
            "independently hosted primary-text transcription."
        ),
        "sourceLimitations": (
            "The quoted sentence below is independently corroborated with consistent wording across multiple "
            "secondary descriptions of the Protocol (used as a direct quotation for that reason). A directly "
            "hosted full primary-text transcription was not located and verified in this curation pass — "
            "an explicit, disclosed gap, not a silently resolved one."
        ),
        "passages": [
            {
                "id": "passage-troppau-protocol-1",
                "excerpt": (
                    "\"States, which have undergone a change of government due to revolution, the result of "
                    "which threatens other states, ipso facto cease to be members of the European Alliance, "
                    "and remain excluded from it until their situation gives guarantees for legal order and "
                    "stability.\""
                ),
                "locator": "Protocol of Troppau, 19 November 1820 (direct quotation, corroborated across secondary sources)",
            }
        ],
    },
    "candidate-concert-of-europe-castlereagh": {
        "sourceId": "source-castlereagh-state-paper",
        "documentId": "document-castlereagh-state-paper",
        "dateOfSource": {"precision": "exact", "earliest": "1820-05-05", "latest": "1820-05-05", "label": "5 May 1820"},
        "editionCitation": "State Paper of 5 May 1820, British and Foreign State Papers, Vol. VIII (London: James Ridgway, 1830).",
        "documentLimitations": (
            "Cited by volume, not independently paginated for this prototype pass."
        ),
        "sourceLimitations": (
            "A real, historically documented State Paper. The excerpt below is a paraphrase of its "
            "well-established substance, not a verbatim quotation, since an independently verifiable "
            "full-text transcription was not located in this pass."
        ),
        "passages": [
            {
                "id": "passage-castlereagh-state-paper-1",
                "excerpt": (
                    "Castlereagh's circular argued that the Quadruple Alliance of 1815 had been formed against "
                    "a specific, defeated enemy (Napoleonic France), not as a standing charter for the Great "
                    "Powers to police the internal constitutional arrangements of other states; Britain would "
                    "not endorse a general, unqualified right of intervention against revolutions merely because "
                    "they had occurred. [Paraphrase of the State Paper's well-documented substance, not a "
                    "verbatim quotation.]"
                ),
                "locator": "State Paper of 5 May 1820 (paraphrased)",
            }
        ],
    },
}
