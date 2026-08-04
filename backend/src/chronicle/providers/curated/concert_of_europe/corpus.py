"""Corpus assembler (CORPUS_PREPARED) for the Concert of Europe curated
package — deterministic software (AGENTS.md §4), same role as
providers/mock/corpus.py, but joins against sources.py's hand-curated
CURATED_SOURCE_CONTENT instead of synthetic candidates."""

from .sources import CURATED_SOURCE_CONTENT


def assemble_corpus(data: dict) -> dict:
    candidates_by_id = {c["candidateId"]: c for c in data["sourceCandidates"]}
    accepted = [a for a in data["sourceAssessments"] if a["status"].startswith("ACCEPTED")]

    sources = []
    documents = []
    passages = []
    for assessment in accepted:
        candidate = candidates_by_id[assessment["candidateId"]]
        curated = CURATED_SOURCE_CONTENT[assessment["candidateId"]]

        sources.append(
            {
                "id": curated["sourceId"],
                "title": candidate["title"],
                "sourceType": candidate["sourceType"],
                "authorOrOrigin": candidate["authorOrOrigin"],
                "dateOfSource": curated["dateOfSource"],
                "originalLanguage": candidate["originalLanguage"],
                "rightsStatus": candidate["rightsStatus"],
                "curationStatus": "prototype-curated",
                "knownLimitations": curated["sourceLimitations"],
                "linkOrLocation": candidate["canonicalUrl"],
            }
        )
        documents.append(
            {
                "id": curated["documentId"],
                "sourceId": curated["sourceId"],
                "editionCitation": curated["editionCitation"],
                "visibility": "public",
                "knownLimitations": curated["documentLimitations"],
            }
        )
        for passage in curated["passages"]:
            passages.append(
                {
                    "id": passage["id"],
                    "documentId": curated["documentId"],
                    "excerpt": passage["excerpt"],
                    "locator": passage["locator"],
                }
            )

    return {**data, "corpus": {"sources": sources, "documents": documents, "passages": passages}}
