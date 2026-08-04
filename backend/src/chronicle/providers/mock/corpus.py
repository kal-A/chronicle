"""Corpus assembler (CORPUS_PREPARED) — deterministic software, not a
"provider" in the AI-output sense (AGENTS.md §4: deterministic software owns
citation existence). Turns ACCEPTED source assessments into real
Source/Document/Passage records matching schema.ts's shapes exactly, since
these — unlike the informal intermediate stage dicts — flow straight into
the final validated package.
"""

from ..util import SENTINEL_DATE


def assemble_corpus(data: dict) -> dict:
    slug = data["slug"]
    topic = data["topic"]
    candidates_by_id = {c["candidateId"]: c for c in data["sourceCandidates"]}
    accepted = [a for a in data["sourceAssessments"] if a["status"].startswith("ACCEPTED")]

    sources = []
    documents = []
    passages = []
    for index, assessment in enumerate(accepted, start=1):
        candidate = candidates_by_id[assessment["candidateId"]]
        source_id = f"source-{slug}-{index}"
        document_id = f"document-{slug}-{index}"
        passage_id = f"passage-{slug}-{index}"

        sources.append(
            {
                "id": source_id,
                "title": candidate["title"],
                "sourceType": candidate["sourceType"],
                "authorOrOrigin": candidate["authorOrOrigin"],
                "dateOfSource": {
                    "precision": "approximate",
                    "earliest": SENTINEL_DATE,
                    "latest": SENTINEL_DATE,
                    "label": "Placeholder date",
                },
                "originalLanguage": candidate["originalLanguage"],
                "rightsStatus": candidate["rightsStatus"],
                "curationStatus": "prototype-curated",
                "knownLimitations": "Phase C2 generic mock source; not real historical scholarship.",
                "linkOrLocation": candidate["canonicalUrl"],
            }
        )
        documents.append(
            {
                "id": document_id,
                "sourceId": source_id,
                "editionCitation": f"Mock edition citation for {topic}",
                "visibility": "public",
                "knownLimitations": "Synthetic edition generated for Phase C2 pipeline verification.",
            }
        )
        passages.append(
            {
                "id": passage_id,
                "documentId": document_id,
                "excerpt": (
                    f"A short mock excerpt concerning {topic}, generated deterministically "
                    "for Phase C2 pipeline verification — not a real quotation."
                ),
                "locator": "p. 1 (mock)",
            }
        )

    return {**data, "corpus": {"sources": sources, "documents": documents, "passages": passages}}
