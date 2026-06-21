"""Tenant-scoped IPM router.

Only Inspection, TreatmentApplication and user-contributed pest reference
images (REQ-010) are tenant-scoped. Pest, Disease, Treatment themselves remain
global reference data.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Form, Query, Request, Response, UploadFile

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
from app.common.auth import get_current_tenant
from app.common.dependencies import get_ipm_service, get_pest_image_service
from app.common.exceptions import FileTooLargeError, InvalidFileTypeError, NotFoundError
from app.core.permissions import Action
from app.domain.models.ipm import Inspection, TreatmentApplication
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ipm_service import IpmService
from app.domain.services.pest_image_service import GALLERY_THUMBNAIL_SIZE, PestImageService, PestImageView

router = APIRouter(prefix="/ipm", tags=["ipm"])

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
        contributed_by=contribution.contributed_by,
        created_at=contribution.created_at,
        is_own=view.is_own,
    )


@router.post("/plants/{plant_key}/inspections", response_model=InspectionResponse, status_code=201)
def create_inspection(
    plant_key: str,
    body: InspectionCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    inspection = Inspection(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_inspection(plant_key, inspection)
    return _inspection_response(created)


@router.get("/plants/{plant_key}/inspections", response_model=list[InspectionResponse])
def list_inspections(
    plant_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    inspections, _ = service.get_inspections(plant_key, offset, limit)
    return [_inspection_response(i) for i in inspections]


@router.post(
    "/plants/{plant_key}/treatment-applications",
    response_model=TreatmentApplicationResponse,
    status_code=201,
)
def create_treatment_application(
    plant_key: str,
    body: TreatmentApplicationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    app = TreatmentApplication(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_treatment_application(plant_key, app)
    return _application_response(created)


@router.get("/plants/{plant_key}/treatment-applications", response_model=list[TreatmentApplicationResponse])
def list_treatment_applications(
    plant_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    apps, _ = service.get_applications(plant_key, offset, limit)
    return [_application_response(a) for a in apps]


@router.get("/plants/{plant_key}/karenz", response_model=list[KarenzPeriodResponse])
def get_karenz_periods(
    plant_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    return service.get_karenz_periods(plant_key)


@router.get("/plants/{plant_key}/harvest-safety", response_model=HarvestSafetyResponse)
def check_harvest_safety(
    plant_key: str,
    planned_date: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    pd = datetime.fromisoformat(planned_date) if planned_date else None
    can_harvest, blocking = service.check_harvest_safety(plant_key, pd)
    return HarvestSafetyResponse(can_harvest=can_harvest, blocking_treatments=blocking)


@router.get("/plants/{plant_key}/inspection-schedule")
def get_inspection_schedule(
    plant_key: str,
    current_phase: str = Query("vegetative"),
    pressure_level: str = Query("none"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
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
    pest_key: str,
    request: Request,
    file: UploadFile,
    caption: str | None = Form(default=None),
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
    pest_key: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.READ)),
    service: PestImageService = Depends(get_pest_image_service),
) -> list[PestImageResponse]:
    """List reference images for a pest from the caller's tenant perspective.

    Returns the tenant's own contributions (tenant attachment URIs, ``is_own``)
    plus all globally-promoted contributions of other tenants (global content
    URIs). Foreign *private* images are never returned (strict isolation).
    """
    views = service.list_for_pest(ctx.tenant_key, pest_key)
    return [_pest_image_response(v, ctx.tenant_slug) for v in views]


@router.delete("/pests/{pest_key}/images/{image_id}", status_code=204)
async def delete_pest_image(
    pest_key: str,
    image_id: str,
    ctx: TenantContext = Depends(require_attachment_permission(Action.DELETE)),
    service: PestImageService = Depends(get_pest_image_service),
) -> Response:
    """Delete a tenant-owned contribution (and its attachment). 404 if foreign/absent."""
    deleted = await service.delete(ctx.tenant_key, ctx.user_key, image_id)
    if not deleted:
        raise NotFoundError("PestImageContribution", image_id)
    return Response(status_code=204)
