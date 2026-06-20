"""REQ-034 §7 — tenant-scoped plant-instance photo gallery endpoints.

Mounted under ``/api/v1/t/{tenant_slug}/plant-instances/{key}/photos``. Sits on
the NFR-013 attachment fundament (full server-side upload pipeline) and adds the
*fachliche* link between a gallery photo (``category == plant``) and a plant
instance (REQ-034 §2.1).

Permissions (REQ-034 §6, REQ-024 §1a — "Plant Instance Photos" matrix row):

* Upload      → ``Action.CREATE`` on ``ATTACHMENT``
* List        → ``Action.READ``   on ``ATTACHMENT`` (viewer allowed, AC-13)
* Set cover   → ``Action.UPDATE`` on ``ATTACHMENT``
* Delete      → ``Action.DELETE`` on ``ATTACHMENT``

Responses expose only ``attachment_id`` + stable tenant-scoped URIs — never
bucket / backend / storage-key details (AC-03/AC-04). The DINOv2 reference hook
(REQ-034 §4) is dispatched best-effort after a successful upload and never
blocks the response.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request, Response, UploadFile

from app.api.v1.attachments.permissions import require_attachment_permission
from app.api.v1.attachments.tenant_router import _parse_content_length, _read_upload_bounded
from app.api.v1.plant_instances.photo_schemas import (
    AssessmentAdapterResponse,
    AssessmentAdaptersResponse,
    PlantPhotoAssessRequest,
    PlantPhotoListResponse,
    PlantPhotoMetadataUpdate,
    PlantPhotoResponse,
    QualityAssessmentResponse,
    QualitySuggestionResponse,
)
from app.common.dependencies import (
    get_attachment_service,
    get_identification_service,
    get_plant_photo_service,
)
from app.common.enums import AttachmentCategory
from app.common.exceptions import FileTooLargeError, InvalidFileTypeError
from app.core.permissions import Action
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, can_render
from app.domain.interfaces.attachment_repository import UNSET
from app.domain.models.attachment import Attachment, QualityAssessment
from app.domain.models.tenant_context import TenantContext
from app.domain.services.attachment_service import AttachmentService
from app.domain.services.identification_service import IdentificationService
from app.domain.services.plant_photo_service import PlantPhotoService

logger = structlog.get_logger()

router = APIRouter(prefix="/plant-instances/{key}/photos", tags=["plant-photos"])


def _assessment_response(assessment: QualityAssessment | None) -> QualityAssessmentResponse | None:
    """Map a stored :class:`QualityAssessment` onto its API response (REQ-034 §4a.2)."""
    if assessment is None:
        return None
    return QualityAssessmentResponse(
        adapter=assessment.adapter,
        assessed_at=assessment.assessed_at.isoformat(),
        is_plant=assessment.is_plant,
        rating=assessment.rating,
        expected_species_matched=assessment.expected_species_matched,
        suggestions=[
            QualitySuggestionResponse(
                scientific_name=s.scientific_name,
                confidence=s.confidence,
                external_id=s.external_id,
            )
            for s in assessment.suggestions
        ],
    )


def _photo_response(attachment: Attachment, tenant_slug: str, *, is_cover: bool) -> PlantPhotoResponse:
    attachment_id = attachment.key or ""
    uri = f"/api/v1/t/{tenant_slug}/attachments/{attachment_id}"
    thumbnail_uris = None
    if can_render(attachment.mime_type):
        from app.api.v1.attachments.schemas import ThumbnailUris

        small, medium, large = THUMBNAIL_SIZES
        thumbnail_uris = ThumbnailUris(
            small=f"{uri}/thumbnails/{small}",
            medium=f"{uri}/thumbnails/{medium}",
            large=f"{uri}/thumbnails/{large}",
        )
    return PlantPhotoResponse(
        attachment_id=attachment_id,
        uri=uri,
        thumbnail_uris=thumbnail_uris,
        is_cover=is_cover,
        mime_type=attachment.mime_type,
        byte_size=attachment.byte_size,
        caption=attachment.caption,
        taken_on=attachment.taken_on.isoformat() if attachment.taken_on else None,
        quality_assessment=_assessment_response(attachment.quality_assessment),
        created_at=attachment.created_at.isoformat() if attachment.created_at else None,
    )


def _resolved_cover(cover_photo_ref: str | None, photo_ids: list[str]) -> str | None:
    """Resolve the effective cover: explicit ``cover_photo_ref`` else first photo."""
    if cover_photo_ref and cover_photo_ref in photo_ids:
        return cover_photo_ref
    return photo_ids[0] if photo_ids else None


@router.post("", response_model=PlantPhotoResponse, status_code=201)
async def upload_plant_photo(
    key: str,
    request: Request,
    file: UploadFile,
    ctx: TenantContext = Depends(require_attachment_permission(Action.CREATE)),
    photo_service: PlantPhotoService = Depends(get_plant_photo_service),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> PlantPhotoResponse:
    """Upload a gallery photo and link it to the plant instance (REQ-034 §7).

    The per-instance quota (``STORAGE_MAX_PHOTOS_PER_INSTANCE``) is enforced
    *before* any bytes are written (AC-15), so a rejected upload never leaves
    orphan storage objects.
    """
    # AC-15 — quota + instance existence pre-check before reading/writing bytes.
    plant = photo_service.assert_can_add_photo(key, ctx.tenant_key)

    mime_type = (file.content_type or "").lower().strip()
    if not mime_type:
        raise InvalidFileTypeError("", [])

    # SEC-005 — reject oversized uploads before buffering the body.
    max_bytes = attachment_service.max_upload_bytes()
    content_length = _parse_content_length(request)
    if content_length is not None and content_length > max_bytes:
        raise FileTooLargeError(max_bytes)
    data = await _read_upload_bounded(file, max_bytes)

    attachment = await attachment_service.upload(
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        data=data,
        mime_type=mime_type,
        original_filename=file.filename or "photo",
        category=AttachmentCategory.PLANT,
    )
    photo_service.link_photo(key, attachment.key or "", ctx.tenant_key)

    # REQ-034 §4 — best-effort DINOv2 reference contribution (no-op until the
    # inference service is enabled). Never blocks the upload or raises.
    _maybe_feed_reference(attachment.key or "", key, plant.species_key, ctx)

    is_cover = plant.cover_photo_ref is None or not plant.photo_refs
    return _photo_response(attachment, ctx.tenant_slug, is_cover=is_cover)


def _maybe_feed_reference(
    attachment_id: str,
    plant_instance_key: str,
    species_key: str,
    ctx: TenantContext,
) -> None:
    """Dispatch the reference-contribution Celery task (REQ-034 §4).

    Only fires when the plant has a known species. All other guards
    (inference enabled, not light-mode, consent, backlog) are evaluated inside
    the task so the upload path stays minimal and the hook is a hard no-op in
    Phase 1. Dispatch failures are swallowed — the gallery must never break.
    """
    if not species_key:
        return
    try:
        from app.tasks.reference_contribution_tasks import feed_user_reference

        feed_user_reference.delay(attachment_id, plant_instance_key, ctx.tenant_key, ctx.user_key)
    except Exception:  # noqa: BLE001 — a broker hiccup must not fail the upload
        logger.warning(
            "feed_user_reference_dispatch_failed",
            tenant_key=ctx.tenant_key,
            plant_instance_key=plant_instance_key,
        )


@router.get("", response_model=PlantPhotoListResponse)
def list_plant_photos(
    key: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    photo_service: PlantPhotoService = Depends(get_plant_photo_service),
) -> PlantPhotoListResponse:
    """List a plant instance's gallery photos, newest first (REQ-034 §7)."""
    plant, photos = photo_service.list_photos(key, ctx.tenant_key)
    photo_ids = [p.key or "" for p in photos]
    cover = _resolved_cover(plant.cover_photo_ref, photo_ids)
    return PlantPhotoListResponse(
        plant_instance_key=key,
        cover_photo_ref=cover,
        photos=[_photo_response(p, ctx.tenant_slug, is_cover=(p.key == cover)) for p in photos],
    )


@router.put("/{attachment_id}/cover", response_model=PlantPhotoListResponse)
def set_cover_photo(
    key: str,
    attachment_id: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.UPDATE)),
    photo_service: PlantPhotoService = Depends(get_plant_photo_service),
) -> PlantPhotoListResponse:
    """Mark a gallery photo as the instance cover (REQ-034 §7 / AC-06)."""
    photo_service.set_cover(key, attachment_id, ctx.tenant_key)
    plant, photos = photo_service.list_photos(key, ctx.tenant_key)
    photo_ids = [p.key or "" for p in photos]
    cover = _resolved_cover(plant.cover_photo_ref, photo_ids)
    return PlantPhotoListResponse(
        plant_instance_key=key,
        cover_photo_ref=cover,
        photos=[_photo_response(p, ctx.tenant_slug, is_cover=(p.key == cover)) for p in photos],
    )


@router.get("/assess/adapters", response_model=AssessmentAdaptersResponse)
def list_assessment_adapters(
    key: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    identification_service: IdentificationService = Depends(get_identification_service),
) -> AssessmentAdaptersResponse:
    """List the recognition adapters selectable for a quality check (REQ-034 §4a.1).

    Read-permission only so viewers can see which adapters exist (even though
    they may not trigger an assessment). Disabled adapters (e.g. DINOv2 before
    Phase 2) are still returned so the UI can offer them greyed-out instead of
    hiding the option — no dead code.
    """
    adapters = [AssessmentAdapterResponse(**a) for a in identification_service.list_assessment_adapters()]
    return AssessmentAdaptersResponse(adapters=adapters)


@router.post("/{attachment_id}/assess", response_model=PlantPhotoResponse)
async def assess_plant_photo(
    key: str,
    attachment_id: str,
    body: PlantPhotoAssessRequest,
    ctx: TenantContext = Depends(require_attachment_permission(Action.UPDATE)),
    photo_service: PlantPhotoService = Depends(get_plant_photo_service),
) -> PlantPhotoResponse:
    """Assess a gallery photo's recognition quality and persist the verdict (REQ-034 §4a).

    ``Action.UPDATE`` because a verdict is persisted on the photo — a ``viewer``
    may see an existing assessment (it ships in the photo listing) but not
    trigger a new one (AC-13, §4a.3). The chosen adapter, the consent gate
    (external path, full mode) and the rate limit are enforced downstream; an
    unusable adapter surfaces as a 409.

    SEC-004: re-assessing the same unchanged photo with the same adapter returns
    the cached verdict and skips a fresh (cost-bearing) external call. Pass
    ``force: true`` to re-run deliberately.

    REQ-034 §4a.3 / SEC-002: in Light mode (REQ-027) there is no consent
    subsystem, so the external recognition path is *not* gated by a server-side
    consent here — it is unlocked solely by the operator opt-in
    (``IDENTIFICATION_EXTERNAL_IN_LIGHT_MODE``) and disabled by default (409
    otherwise). The third-party-transfer transparency/opt-in is then surfaced
    client-side.
    """
    updated, _assessment = await photo_service.assess_photo(
        key,
        attachment_id,
        ctx.tenant_key,
        ctx.user_key,
        body.adapter,
        force=body.force,
    )
    # Re-resolve the cover flag so the response stays consistent with the gallery.
    _plant, photos = photo_service.list_photos(key, ctx.tenant_key)
    photo_ids = [p.key or "" for p in photos]
    cover = _resolved_cover(_plant.cover_photo_ref, photo_ids)
    return _photo_response(updated, ctx.tenant_slug, is_cover=(updated.key == cover))


@router.patch("/{attachment_id}", response_model=PlantPhotoResponse)
def update_plant_photo_metadata(
    key: str,
    attachment_id: str,
    body: PlantPhotoMetadataUpdate,
    ctx: TenantContext = Depends(require_attachment_permission(Action.UPDATE)),
    photo_service: PlantPhotoService = Depends(get_plant_photo_service),
) -> PlantPhotoResponse:
    """Patch a gallery photo's caption / capture date (REQ-034 §2.1 v1.2).

    True PATCH: only the fields present in the request body are changed. An
    omitted field is left untouched; an explicit ``null`` clears it. The
    omitted-vs-null distinction is recovered from ``model_fields_set`` and
    forwarded to the service as the ``UNSET`` sentinel.
    """
    caption = body.caption if "caption" in body.model_fields_set else UNSET
    taken_on = body.taken_on if "taken_on" in body.model_fields_set else UNSET
    attachment = photo_service.update_photo_metadata(
        key,
        attachment_id,
        ctx.tenant_key,
        caption=caption,
        taken_on=taken_on,
    )
    # Re-resolve the cover flag so the response stays consistent with the gallery.
    _plant, photos = photo_service.list_photos(key, ctx.tenant_key)
    photo_ids = [p.key or "" for p in photos]
    cover = _resolved_cover(_plant.cover_photo_ref, photo_ids)
    return _photo_response(attachment, ctx.tenant_slug, is_cover=(attachment.key == cover))


@router.delete("/{attachment_id}", status_code=204)
async def delete_plant_photo(
    key: str,
    attachment_id: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.DELETE)),
    photo_service: PlantPhotoService = Depends(get_plant_photo_service),
) -> Response:
    """Hard-delete a gallery photo and unlink it (REQ-034 §7 / AC-07)."""
    await photo_service.delete_photo(key, attachment_id, ctx.tenant_key)
    return Response(status_code=204)
