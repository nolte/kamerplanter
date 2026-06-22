"""REQ-044 — admin API for the few-shot pest-recognition index.

Coverage per taxonomy class, a per-class gallery of the indexed reference images
(provenance + attribution, no embeddings), manual curation, and a UI-startable
acquisition job. Platform-admin only; in light mode the sole system user is the
admin (see require_platform_admin).
"""

from fastapi import APIRouter, Depends

from app.api.v1.admin.pests.schemas import (
    PestAcquireResponse,
    PestContributionModerationItem,
    PestContributionModerationList,
    PestCoverageEntry,
    PestCurationImage,
    PestCurationImageList,
    PestRecognitionStatusResponse,
    PromotePestContributionRequest,
    PromotePestContributionResponse,
    SetPestImageActiveRequest,
    SetPestImageActiveResponse,
)
from app.common.auth import require_platform_admin
from app.common.dependencies import get_pest_image_service
from app.common.enums import PestImageStatus
from app.common.exceptions import NotFoundError, ValidationError
from app.config.settings import settings
from app.data_access.external.pest_inference_client import PestDetectionInferenceClient
from app.domain.models.pest_taxonomy import PEST_TAXONOMY
from app.domain.models.user import User
from app.domain.services.pest_image_service import (
    GALLERY_THUMBNAIL_SIZE,
    PestImageService,
    PestImageView,
)

router = APIRouter(prefix="/admin/pests", tags=["admin-pests"])


def _moderation_item(view: PestImageView) -> PestContributionModerationItem:
    """Map a contribution view to a moderation row with global content URIs."""
    contribution = view.contribution
    contribution_id = contribution.key or ""
    content_uri = f"/api/v1/ipm/pest-images/{contribution_id}"
    thumbnail_uri = f"{content_uri}/thumbnails/{GALLERY_THUMBNAIL_SIZE}" if view.has_thumbnail else None
    return PestContributionModerationItem(
        id=contribution_id,
        pest_key=contribution.pest_key,
        attachment_id=contribution.attachment_id,
        content_uri=content_uri,
        thumbnail_uri=thumbnail_uri,
        status=contribution.status,
        caption=contribution.caption,
        tenant_key=contribution.tenant_key,
        contributed_by=contribution.contributed_by,
        created_at=contribution.created_at,
        promoted_at=contribution.promoted_at,
        promoted_by=contribution.promoted_by,
    )


def _client() -> PestDetectionInferenceClient:
    return PestDetectionInferenceClient(settings.inference_service_url)


@router.get("/status", response_model=PestRecognitionStatusResponse)
def get_pest_recognition_status(_user: User = Depends(require_platform_admin)) -> PestRecognitionStatusResponse:
    """Aggregated coverage of the few-shot pest index, per taxonomy class."""
    client = _client()
    coverage_rows = client.coverage() if settings.pest_detection_enabled else []
    by_label = {row["label"]: row for row in coverage_rows}

    target = settings.pest_reference_min_usable
    classes: list[PestCoverageEntry] = []
    index_count = 0
    for taxon in PEST_TAXONOMY:
        row = by_label.get(taxon.slug, {})
        total = int(row.get("total", 0))
        active = int(row.get("active", 0))
        index_count += total
        classes.append(
            PestCoverageEntry(
                label=taxon.slug,
                common_name=taxon.common_name_de,
                category=taxon.category.value,
                scientific_name=taxon.scientific_name,
                gbif_taxon_key=taxon.gbif_taxon_key,
                total=total,
                active=active,
                target=target,
                usable=active >= target,
            )
        )

    service_ready = client.is_ready() if settings.pest_detection_enabled else False
    return PestRecognitionStatusResponse(
        feature_enabled=settings.pest_detection_enabled,
        service_ready=service_ready,
        index_count=index_count,
        target_per_class=target,
        classes=classes,
    )


@router.post("/acquire", response_model=PestAcquireResponse, status_code=202)
def start_pest_acquisition(_user: User = Depends(require_platform_admin)) -> PestAcquireResponse:
    """Dispatch the cold-start acquisition job for all classes (from the UI)."""
    from app.tasks.pest_dataset_tasks import acquire_pest_dataset_task

    task = acquire_pest_dataset_task.delay()
    return PestAcquireResponse(status="queued", task_id=getattr(task, "id", None))


@router.get("/{label}/images", response_model=PestCurationImageList)
def list_pest_images(label: str, _user: User = Depends(require_platform_admin)) -> PestCurationImageList:
    """List the indexed reference images for a class (gallery + curation source)."""
    payload = _client().list_prototypes(label, limit=200, active_only=False)
    images = [PestCurationImage(**img) for img in payload.get("images", [])]
    return PestCurationImageList(
        label=label,
        count=payload.get("count", len(images)),
        active_count=payload.get("active_count", sum(1 for i in images if i.is_active)),
        images=images,
    )


@router.patch("/{label}/images/{image_id}", response_model=SetPestImageActiveResponse)
def set_pest_image_active(
    label: str,
    image_id: int,
    body: SetPestImageActiveRequest,
    _user: User = Depends(require_platform_admin),
) -> SetPestImageActiveResponse:
    """Activate/deactivate one reference image (manual curation)."""
    _client().set_prototype_active(label, image_id, is_active=body.is_active, reason=body.reason)
    return SetPestImageActiveResponse(label=label, id=image_id, is_active=body.is_active)


# ── REQ-010 — user-contributed pest image moderation (global promotion) ──
#
# Platform-admin-only, cross-tenant. The admin reviews every tenant's photos
# for a pest and promotes the good ones to global visibility (served via the
# global /ipm/pest-images content endpoint). Promotion is also the seam where
# the Phase-2 recognition index gets fed (see PestImageService._on_promotion_changed).


@router.get("/{pest_key}/contributions", response_model=PestContributionModerationList)
def list_pest_contributions(
    pest_key: str,
    _user: User = Depends(require_platform_admin),
    service: PestImageService = Depends(get_pest_image_service),
) -> PestContributionModerationList:
    """List ALL tenants' contributed images for a pest (cross-tenant moderation)."""
    views = service.list_all_for_pest(pest_key)
    items = [_moderation_item(v) for v in views]
    promoted_count = sum(1 for v in views if v.contribution.status == PestImageStatus.PROMOTED)
    return PestContributionModerationList(
        pest_key=pest_key,
        count=len(items),
        promoted_count=promoted_count,
        images=items,
    )


@router.patch("/{pest_key}/contributions/{contribution_id}", response_model=PromotePestContributionResponse)
def set_pest_contribution_promotion(
    pest_key: str,
    contribution_id: str,
    body: PromotePestContributionRequest,
    user: User = Depends(require_platform_admin),
    service: PestImageService = Depends(get_pest_image_service),
) -> PromotePestContributionResponse:
    """Promote/demote AND/OR deselect/re-include a contribution (idempotent).

    ``promote`` toggles global visibility (and seeds the recognition index);
    ``is_active`` is pure gallery curation (deselect without touching the index).
    Either or both may be sent; an unknown contribution yields 404. When both are
    sent the promotion is applied first, then the curation flag.
    """
    view: PestImageView | None = None

    if body.promote is not None:
        view = service.set_promotion(
            contribution_key=contribution_id,
            promote=body.promote,
            admin_user_key=user.key,
        )
        if view is None:
            raise NotFoundError("PestImageContribution", contribution_id)

    if body.is_active is not None:
        view = service.set_active(
            contribution_key=contribution_id,
            is_active=body.is_active,
            admin_user_key=user.key,
        )
        if view is None:
            raise NotFoundError("PestImageContribution", contribution_id)

    if view is None:
        # Neither field provided — nothing to do. Reject rather than silently
        # mutating (e.g. re-activating) the contribution.
        raise ValidationError("Provide 'promote' and/or 'is_active'.")

    contribution = view.contribution
    return PromotePestContributionResponse(
        id=contribution.key or "",
        pest_key=contribution.pest_key,
        status=contribution.status,
        is_active=contribution.is_active,
        promoted_at=contribution.promoted_at,
        promoted_by=contribution.promoted_by,
    )
