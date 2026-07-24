"""Tenant-scoped IPM router.

Only Inspection, TreatmentApplication and user-contributed pest reference
images (REQ-010) are tenant-scoped. Pest, Disease, Treatment themselves remain
global reference data.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Query, Request, Response, UploadFile

from app.api.v1.attachments.permissions import require_attachment_permission
from app.api.v1.ipm.router import _application_response, _inspection_response
from app.api.v1.ipm.schemas import (
    HarvestSafetyResponse,
    InspectionCreate,
    InspectionResponse,
    KarenzPeriodResponse,
    PestImageResponse,
    TreatmentApplicationCreate,
    TreatmentApplicationResponse,
)
from app.common.auth import get_current_tenant, is_platform_admin
from app.common.dependencies import get_ipm_service, get_pest_image_service, get_tenant_service
from app.common.exceptions import FileTooLargeError, InvalidFileTypeError, NotFoundError
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.core.permissions import Action
from app.domain.models.ipm import Inspection, TreatmentApplication
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ipm_service import IpmService
from app.domain.services.pest_image_service import (
    GALLERY_THUMBNAIL_SIZE,
    PestImageService,
    PestImageView,
    PestInspectionImageView,
    PestRecognitionImageView,
)
from app.domain.services.tenant_service import TenantService

router = APIRouter(prefix="/ipm", tags=["ipm"], responses=NOT_FOUND_RESPONSE)

# Chunk size for the bounded streaming upload read (1 MiB) — mirrors the
# attachment router so an oversized body is never fully buffered (SEC-005).
_UPLOAD_CHUNK_SIZE = 1024 * 1024


def _parse_content_length(request: Request) -> int | None:
    raw = request.headers.get("content-length")
    if raw is None or not raw.strip().isdigit():
        return None
    return int(raw)


async def _read_upload_bounded(file: UploadFile, max_bytes: int) -> bytes:
    """Read an ``UploadFile`` in bounded chunks, capping memory at ``max_bytes``."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FileTooLargeError(max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)


def _pest_image_response(view: PestImageView, tenant_slug: str) -> PestImageResponse:
    """Map a view to a response, choosing tenant-scoped vs. global content URIs.

    Own contributions are served through the caller's tenant attachment URIs
    (``/api/v1/t/{slug}/attachments/{id}``). Foreign *promoted* contributions
    are served through the global, read-only pest-image content endpoint
    (``/api/v1/ipm/pest-images/{contribution_id}``) — the caller is not a member
    of the owning tenant, so a tenant URI would be forbidden for them.
    """
    contribution = view.contribution
    contribution_id = contribution.key or ""
    attachment_id = contribution.attachment_id

    if view.is_own:
        uri = f"/api/v1/t/{tenant_slug}/attachments/{attachment_id}"
        thumbnail_uri = f"{uri}/thumbnails/{GALLERY_THUMBNAIL_SIZE}" if view.has_thumbnail else None
    else:
        uri = f"/api/v1/ipm/pest-images/{contribution_id}"
        thumbnail_uri = f"{uri}/thumbnails/{GALLERY_THUMBNAIL_SIZE}" if view.has_thumbnail else None

    return PestImageResponse(
        id=contribution_id,
        pest_key=contribution.pest_key,
        attachment_id=attachment_id,
        uri=uri,
        thumbnail_uri=thumbnail_uri,
        status=contribution.status,
        caption=contribution.caption,
        # SEC-002 — never disclose a *foreign* contributor's identity to normal
        # tenant members. ``contributed_by`` is PII; for promoted images of
        # other tenants (``is_own=False``) the full provenance stays behind the
        # platform-admin moderation endpoint (``PestContributionModerationItem``).
        contributed_by=contribution.contributed_by if view.is_own else None,
        created_at=contribution.created_at,
        is_own=view.is_own,
        is_active=contribution.is_active,
        source="contribution",
    )


def _inspection_image_response(view: PestInspectionImageView, pest_key: str, tenant_slug: str) -> PestImageResponse:
    """Map an inspection-sourced photo onto the shared gallery response.

    Read-only provenance: it is always the tenant's own data (``is_own=True``),
    served via tenant-scoped attachment URIs, with no contribution id / status
    (the attachment id is the stable client key). ``contributed_by`` stays
    ``None`` — this is not a curated upload.
    """
    attachment_id = view.attachment_id
    uri = f"/api/v1/t/{tenant_slug}/attachments/{attachment_id}"
    thumbnail_uri = f"{uri}/thumbnails/{GALLERY_THUMBNAIL_SIZE}" if view.has_thumbnail else None
    return PestImageResponse(
        id=attachment_id,
        pest_key=pest_key,
        attachment_id=attachment_id,
        uri=uri,
        thumbnail_uri=thumbnail_uri,
        status=None,
        caption=None,
        contributed_by=None,
        created_at=None,
        is_own=True,
        source="inspection",
    )


def _recognition_image_response(view: PestRecognitionImageView, pest_key: str) -> PestImageResponse:
    """Map a global recognition reference image onto the shared gallery response.

    REQ-010 / REQ-044 — the image is hosted externally (CC-licensed
    ``source_url``); no pixel is stored locally, so ``uri`` is that external URL,
    ``thumbnail_uri`` is ``None`` and ``attachment_id`` is empty. It is always
    global / read-only (``is_own=False``, no contribution lifecycle) and the
    CC-BY ``attribution`` / ``license`` travel with it. The stable client key is
    ``recognition:{prototype_id}`` (disjoint from contribution / attachment ids).
    """
    return PestImageResponse(
        id=f"recognition:{view.prototype_id}",
        pest_key=pest_key,
        attachment_id="",
        uri=view.source_url,
        thumbnail_uri=None,
        status=None,
        caption=None,
        contributed_by=None,
        created_at=None,
        is_own=False,
        is_active=view.is_active,
        source="recognition",
        attribution=view.attribution,
        license=view.license,
    )


@router.post("/plants/{plant_key}/inspections", response_model=InspectionResponse, status_code=201)
def create_inspection(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: InspectionCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    """Record an IPM inspection for a plant."""
    inspection = Inspection(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_inspection(plant_key, inspection)
    return _inspection_response(created)


@router.get("/plants/{plant_key}/inspections", response_model=list[InspectionResponse])
def list_inspections(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    """List a plant's IPM inspections (paginated)."""
    inspections, _ = service.get_inspections(plant_key, pagination.offset, pagination.limit)
    return [_inspection_response(i) for i in inspections]


@router.post(
    "/plants/{plant_key}/treatment-applications",
    response_model=TreatmentApplicationResponse,
    status_code=201,
)
def create_treatment_application(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: TreatmentApplicationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    """Record a treatment application for a plant."""
    app = TreatmentApplication(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_treatment_application(plant_key, app)
    return _application_response(created)


@router.get("/plants/{plant_key}/treatment-applications", response_model=list[TreatmentApplicationResponse])
def list_treatment_applications(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    """List a plant's treatment applications (paginated)."""
    apps, _ = service.get_applications(plant_key, pagination.offset, pagination.limit)
    return [_application_response(a) for a in apps]


@router.get("/plants/{plant_key}/karenz", response_model=list[KarenzPeriodResponse])
def get_karenz_periods(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    """List active Karenz (pre-harvest waiting) periods for a plant."""
    return service.get_karenz_periods(plant_key)


@router.get("/plants/{plant_key}/harvest-safety", response_model=HarvestSafetyResponse)
def check_harvest_safety(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    planned_date: str | None = Query(default=None, description="Planned harvest date (ISO-8601) to check against."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    """Check whether a plant may be harvested given active Karenz periods."""
    pd = datetime.fromisoformat(planned_date) if planned_date else None
    can_harvest, blocking = service.check_harvest_safety(plant_key, pd)
    return HarvestSafetyResponse(can_harvest=can_harvest, blocking_treatments=blocking)


@router.get("/plants/{plant_key}/inspection-schedule")
def get_inspection_schedule(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    current_phase: str = Query("vegetative", description="Current growth phase driving the inspection cadence."),
    pressure_level: str = Query("none", description="Current pest-pressure level driving the inspection cadence."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    """Return the recommended inspection schedule for a plant."""
    return service.get_inspection_schedule(plant_key, current_phase, pressure_level)


# ── REQ-010 User-contributed pest reference images (tenant-private gallery) ──
#
# ``pests`` are global reference data, but a user's photos are tenant-private:
# every endpoint is gated by tenant membership AND the RBAC attachment
# permission (a viewer may READ but not CREATE/DELETE), and the service scopes
# all reads/deletes to ``ctx.tenant_key`` so one tenant can never see or remove
# another tenant's images (strict isolation).


@router.post("/pests/{pest_key}/images", response_model=PestImageResponse, status_code=201)
async def contribute_pest_image(
    pest_key: Annotated[str, Path(description="Document key of the global pest.")],
    request: Request,
    file: UploadFile,
    caption: str | None = Form(default=None, description="Optional caption for the contributed image."),
    ctx: TenantContext = Depends(require_attachment_permission(Action.CREATE)),
    service: PestImageService = Depends(get_pest_image_service),
) -> PestImageResponse:
    """Contribute a user photo for a global pest (proxy-upload, full pipeline)."""
    mime_type = (file.content_type or "").lower().strip()
    if not mime_type:
        raise InvalidFileTypeError("", [])

    # SEC-005 — reject oversized uploads before buffering the body.
    max_bytes = service.attachment_service_max_upload_bytes()
    content_length = _parse_content_length(request)
    if content_length is not None and content_length > max_bytes:
        raise FileTooLargeError(max_bytes)
    data = await _read_upload_bounded(file, max_bytes)

    view = await service.contribute(
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        pest_key=pest_key,
        data=data,
        mime_type=mime_type,
        filename=file.filename or "upload",
        caption=caption,
    )
    return _pest_image_response(view, ctx.tenant_slug)


@router.get("/pests/{pest_key}/images", response_model=list[PestImageResponse])
def list_pest_images(
    pest_key: Annotated[str, Path(description="Document key of the global pest.")],
    # Plain ``False`` default (not ``Query(False)``) so the house-style direct
    # call in unit tests gets a real boolean and the admin gate short-circuits;
    # FastAPI still exposes it as the ``?include_inactive=`` query parameter.
    include_inactive: bool = False,
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    service: PestImageService = Depends(get_pest_image_service),
    tenant_service: TenantService = Depends(get_tenant_service),
) -> list[PestImageResponse]:
    """List reference images for a pest from the caller's tenant perspective.

    Returns, in order:

    * the tenant's own contributions (tenant attachment URIs, ``is_own``);
    * all globally-promoted contributions of other tenants (global content URIs);
    * read-only photos of the tenant's own inspections in which this pest was
      detected (``source == "inspection"``);
    * the GLOBAL, read-only recognition reference images of the pest's detection
      class (``source == "recognition"``), hosted externally (CC-licensed
      ``source_url``); appended best-effort — an inference-service outage or a
      pest without ``detection_slug`` simply yields none.

    Foreign *private* contributions are never returned (strict isolation), and
    only the calling tenant's inspections are scanned. An attachment that is
    already surfaced as a contribution is not repeated as an inspection tile
    (contribution provenance wins).

    ``include_inactive`` is a platform-admin-only curation flag: it additionally
    returns *deselected* contribution / recognition tiles (dimmed in the UI).
    It is silently ignored for non-admins (forced to ``False``) — a normal
    member only ever sees active images, never a 403.
    """
    # Curation override is platform-admin-only; force it off for everyone else
    # (display-only privilege — no 403, just the default active-only behaviour).
    effective_include_inactive = include_inactive and is_platform_admin(tenant_service, ctx.user_key)

    views = service.list_for_pest(ctx.tenant_key, pest_key, include_inactive=effective_include_inactive)
    responses = [_pest_image_response(v, ctx.tenant_slug) for v in views]

    contributed_attachment_ids = {r.attachment_id for r in responses}
    inspection_views = service.list_inspection_images_for_pest(ctx.tenant_key, pest_key)
    responses.extend(
        _inspection_image_response(v, pest_key, ctx.tenant_slug)
        for v in inspection_views
        if v.attachment_id not in contributed_attachment_ids
    )

    # REQ-044 — append the global recognition reference images last. Different
    # source (external CC-licensed URLs, no local pixel), so no dedup needed.
    recognition_views = service.list_recognition_images_for_pest(pest_key, include_inactive=effective_include_inactive)
    responses.extend(_recognition_image_response(v, pest_key) for v in recognition_views)
    return responses


@router.delete("/pests/{pest_key}/images/{image_id}", status_code=204)
async def delete_pest_image(
    pest_key: Annotated[str, Path(description="Document key of the global pest.")],
    image_id: Annotated[str, Path(description="Identifier of the pest-image contribution to delete.")],
    ctx: TenantContext = Depends(require_attachment_permission(Action.DELETE)),
    service: PestImageService = Depends(get_pest_image_service),
) -> Response:
    """Delete a tenant-owned contribution (and its attachment). 404 if foreign/absent."""
    deleted = await service.delete(ctx.tenant_key, ctx.user_key, image_id)
    if not deleted:
        raise NotFoundError("PestImageContribution", image_id)
    return Response(status_code=204)
