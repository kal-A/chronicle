"""Verification (VERIFIED stage) — deterministic software, not a provider
(AGENTS.md §4: deterministic software owns verification, never the "AI"/
provider layer). Runs the composed draft package through C0's
validate_generated_investigation(); if it raises, engine.py's existing
StageExecutionError/FAILED handling takes over unchanged — no new failure
path needed here.

On success, returns the *validated, re-serialized* package as this stage's
output (not the raw pre-validation dict) — that's what makes it the
canonical final form, and it's what engine.py's run_pipeline() inspects for
a top-level "status" field to decide the run's terminal RunStatus.
"""

from ..contracts.validation import validate_generated_investigation


def verify_investigation(data: dict) -> dict:
    draft = data["package"]
    validated = validate_generated_investigation(draft)

    # exclude_none: optional fields (translationCredit, sentTime, receivedTime,
    # gapNote, reviewerNote, mapSceneId, ...) must be *absent*, not present as
    # `null` — Zod's `.optional()` on the TS side accepts undefined, not null,
    # so a present-but-null field fails frontend validation even though it
    # passes Pydantic's Optional[...] = None on the Python side.
    package = validated.model_dump(mode="json", exclude_none=True)
    package["generationReport"]["verificationChecks"] = [
        {
            "id": "schema-and-cross-reference-validation",
            "status": "passed",
            "message": (
                "Package passed Pydantic schema validation and all "
                "cross-reference/historical-integrity rules."
            ),
        }
    ]
    return package
