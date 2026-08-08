"""Canonical, lossless projections shared by corpus and tool retrieval."""

from __future__ import annotations

from .contracts import EvidenceLinkProjection


def project_evidence_link(*, link, passage, document, source, target) -> EvidenceLinkProjection:
    """Attach an EvidenceLink's role to its exact target and corpus scope.

    The package stores review status and visibility on the target record,
    not on EvidenceLink itself, so callers must resolve and provide both.
    """

    return EvidenceLinkProjection(
        evidenceLinkId=link.id,
        targetType=link.targetType.value,
        targetId=link.targetId,
        role=link.role.value,
        reviewerNote=link.reviewerNote,
        reviewStatus=target.reviewStatus.value,
        visibility=target.visibility.value,
        passageId=passage.id,
        documentId=document.id,
        sourceId=source.id,
    )
