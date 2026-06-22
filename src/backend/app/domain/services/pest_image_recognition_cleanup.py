"""REQ-010 / REQ-025 — recognition-index cleanup for erased pest images (SEC-001).

When a user-contributed pest image is **promoted**, the promotion hook
(:mod:`app.tasks.pest_image_tasks`) sends its EXIF-stripped bytes to the
self-hosted inference-service ``/pest/reference`` endpoint, which stores the
DINOv2 **embedding + provenance** (``source="user_contributed"``,
``source_record_id=<contribution_key>``) in pgvector. That embedding is
personal data: it is derived from a user's photo and carries the owning
contribution key.

The demote path retracts it via :meth:`PestImageService._on_promotion_changed`,
but a **user or tenant erasure** previously dropped only the ArangoDB link
documents (and the attachment bytes), leaving the promoted embedding orphaned in
the recognition index — a GDPR deletion gap (SEC-001).

This module provides the shared retract step both erasure paths call **before**
they delete the link documents/attachments: while the contribution still exists
its ``pest_key`` → ``detection_slug`` → :class:`PestTaxon` label is resolvable.
The retract is best-effort and idempotent — an inference-service hiccup is
logged and swallowed so it can never abort a legally-mandated erasure (mirrors
the best-effort semantics of the promotion hook and the other Phase 0 cleanups).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.common.enums import PestImageStatus
from app.domain.models.pest_taxonomy import get_taxon

if TYPE_CHECKING:
    from app.data_access.external.pest_inference_client import PestDetectionInferenceClient
    from app.domain.interfaces.ipm_repository import IIpmRepository
    from app.domain.models.pest_image import PestImageContribution

logger = structlog.get_logger()

# Mirror the index task's provenance tag so the retract matches the exact rows
# the promotion upserted (see ``USER_CONTRIBUTED_SOURCE`` in pest_image_tasks).
USER_CONTRIBUTED_SOURCE = "user_contributed"


def _resolve_label(ipm_repo: IIpmRepository, pest_key: str) -> str | None:
    """Resolve a pest to its recognition label, exactly as the index task does.

    The label is the pest's ``detection_slug`` mapped 1:1 to a
    :class:`PestTaxon.slug`. Returns ``None`` when the pest is gone, has no
    ``detection_slug``, or the slug is not a known taxon — every such case means
    no embedding could ever have been indexed, so the retract is a clean skip.
    """
    pest = ipm_repo.get_pest_by_key(pest_key)
    if pest is None:
        return None
    slug = (pest.detection_slug or "").strip()
    if not slug:
        return None
    taxon = get_taxon(slug)
    if taxon is None:
        return None
    return taxon.slug


def retract_promoted_contributions(
    contributions: list[PestImageContribution],
    *,
    inference_client: PestDetectionInferenceClient,
    ipm_repo: IIpmRepository,
    erasure_scope: str,
) -> int:
    """Best-effort-retract every promoted contribution's index embedding (SEC-001).

    Iterates the contributions and, for each one that is ``PROMOTED`` and whose
    pest resolves to a recognition label, deactivates the matching
    ``user_contributed`` prototype(s) in the inference-service. Private
    contributions and contributions whose pest has no ``detection_slug`` are
    skipped (they were never indexed). Any inference-service error is logged and
    swallowed so the surrounding erasure always completes.

    ``erasure_scope`` is purely a log discriminator (``"user"`` / ``"tenant"``).
    Returns the number of contributions for which a retract was attempted.
    """
    attempted = 0
    for contribution in contributions:
        if contribution.status != PestImageStatus.PROMOTED:
            continue
        if contribution.key is None:
            continue
        label = _resolve_label(ipm_repo, contribution.pest_key)
        if label is None:
            continue
        attempted += 1
        try:
            deactivated = inference_client.retract_prototype(
                label=label,
                source=USER_CONTRIBUTED_SOURCE,
                source_record_id=contribution.key,
            )
        except Exception as exc:  # noqa: BLE001 — never abort a GDPR erasure
            logger.warning(
                "pest_image_index_retract_failed",
                erasure_scope=erasure_scope,
                contribution_key=contribution.key,
                label=label,
                error=type(exc).__name__,
            )
            continue
        logger.info(
            "pest_image_index_retracted",
            erasure_scope=erasure_scope,
            contribution_key=contribution.key,
            label=label,
            deactivated=deactivated,
        )
    return attempted


__all__ = ["USER_CONTRIBUTED_SOURCE", "retract_promoted_contributions"]
