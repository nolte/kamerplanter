from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Path, Response, UploadFile

from app.api.v1.imports.schemas import ImportJobResponse
from app.common.auth import (
    get_active_tenant_context,
    get_current_user,
    get_is_platform_admin,
    require_active_tenant_role,
)
from app.common.dependencies import get_import_service
from app.common.enums import DuplicateStrategy, EntityType, TenantRole
from app.common.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.import_job import ImportJob
from app.domain.models.tenant_context import TenantContext
from app.domain.services.import_service import ImportService

router = APIRouter(
    prefix="/import",
    tags=["import"],
    dependencies=[Depends(get_current_user)],
    responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE},
)

# ── Authorisation (#1501) ───────────────────────────────────────────────────────
#
# An import job is **tenant-owned work**, not catalogue data: it holds the parsed
# rows of an uploaded CSV until somebody confirms them. ``ImportJob`` has carried
# ``tenant_key`` and ``uploaded_by`` from the start and nothing ever wrote either,
# so ``GET /jobs``, ``GET /jobs/{key}`` and ``DELETE /jobs/{key}`` had nothing to
# scope by and were open to every authenticated member of every tenant — one
# tenant's staged master data readable, and destroyable, by another's.
#
# The axis is therefore the tenant one, not the platform-admin one its three
# neighbours in #1501 take. This router carries no ``/t/{slug}/`` segment, so the
# tenant comes from the ``X-Active-Tenant`` header through
# :func:`~app.common.auth.require_active_tenant_role` — the same resolver
# ``confirm_import`` already uses (:func:`get_active_tenant_context`), so the
# ownership stamp written on upload and the scope applied on read can never be two
# different notions of "the caller's tenant".
#
# Ranks: staging and confirming are ordinary edits (grower and above), deleting is
# the irreversibility boundary and is lead-only in the service. Reads are open to
# every member OF THE OWNING TENANT — the scope, not the rank, is what closes them.

# SEC-M-008: Upload security constants
MAX_UPLOAD_SIZE_BYTES = 10_485_760  # 10 MB
ALLOWED_MIME_TYPES = frozenset(
    {
        "text/csv",
        "text/plain",
        "application/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",  # headless browsers often send this for .csv
    }
)


def _job_response(job: ImportJob) -> ImportJobResponse:
    return ImportJobResponse(
        key=job.key or "",
        entity_type=job.entity_type.value,
        status=job.status.value,
        filename=job.filename,
        row_count=job.row_count,
        duplicate_strategy=job.duplicate_strategy.value,
        preview_rows=[
            {
                "row_number": r.row_number,
                "data": r.data,
                "status": r.status.value,
                "errors": [e.model_dump() for e in r.errors],
                "duplicate_key": r.duplicate_key,
            }
            for r in job.preview_rows
        ],
        result=job.result.model_dump() if job.result else None,
        error_message=job.error_message,
        uploaded_by=job.uploaded_by,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/upload", response_model=ImportJobResponse, status_code=202)
async def upload_csv(
    file: Annotated[UploadFile, File(description="CSV file to import (max 10 MB).")],
    entity_type: EntityType = Form(..., description="Master-data entity type the CSV rows describe."),
    duplicate_strategy: DuplicateStrategy = Form(
        DuplicateStrategy.SKIP, description="How to handle rows that duplicate an existing record."
    ),
    ctx: TenantContext = Depends(require_active_tenant_role(TenantRole.GROWER)),
    service: ImportService = Depends(get_import_service),
):
    """Upload a CSV file and stage an import job for preview.

    Grower and above, and the job is stamped with the caller's active tenant and
    user key (#1501) — the two fields every read and the delete below scope by.
    A viewer may not stage an import: they could not confirm it either, so the
    only thing staging would give them is a row nobody can act on.
    """
    # SEC-M-008: Validate MIME type
    content_type = (file.content_type or "").lower().strip()
    if content_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedMediaTypeError(content_type, sorted(ALLOWED_MIME_TYPES))

    content = await file.read()

    # SEC-M-008: Validate file size
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise PayloadTooLargeError(MAX_UPLOAD_SIZE_BYTES)

    job = service.upload(
        content,
        entity_type,
        file.filename or "upload.csv",
        duplicate_strategy,
        uploaded_by=ctx.user_key,
        tenant_key=ctx.tenant_key,
    )
    return _job_response(job)


@router.post("/jobs/{key}/confirm", response_model=ImportJobResponse)
def confirm_import(
    key: Annotated[str, Path(description="Document key of the import job.")],
    service: ImportService = Depends(get_import_service),
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
):
    """Confirm a staged import job and apply its rows into the caller's tenant.

    This is the only write in this router — ``/upload`` merely stages rows for
    preview — and until #1110 it was ungated and un-scoped: rows were built with
    the model default ``tenant_key = ''`` and written repository-direct, so any
    authenticated user could inject master data into the *global* catalogue every
    tenant reads, and could not remove it afterwards (deleting a global row has
    required a platform admin since #1109).

    The tenant comes from :func:`~app.common.auth.get_active_tenant_context` — the
    same resolver ``POST /api/v1/species`` uses — because this router is mounted
    globally and carries no ``/t/{slug}/`` segment to bind to. Passing the whole
    context rather than a separate key and role is what keeps the ownership stamp
    and the permission answer from drifting onto different notions of "the
    caller's tenant"; the service decides per entity type, since botanical
    families have no tenant to be imported into at all.
    """
    job = service.confirm(
        key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )
    return _job_response(job)


@router.get("/jobs/{key}", response_model=ImportJobResponse)
def get_job(
    key: Annotated[str, Path(description="Document key of the import job.")],
    ctx: TenantContext = Depends(get_active_tenant_context),
    service: ImportService = Depends(get_import_service),
):
    """Return a single import job by key, from the caller's tenant only (#1501).

    A foreign job answers 404, not 403: the caller must not learn it exists.
    """
    job = service.get_job(key, tenant_key=ctx.tenant_key)
    return _job_response(job)


@router.get("/jobs", response_model=list[ImportJobResponse])
def list_jobs(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_active_tenant_context),
    service: ImportService = Depends(get_import_service),
):
    """List the caller's tenant's import jobs (paginated, #1501)."""
    items, _total = service.list_jobs(pagination.offset, pagination.limit, tenant_key=ctx.tenant_key)
    return [_job_response(j) for j in items]


@router.delete("/jobs/{key}", status_code=204)
def delete_job(
    key: Annotated[str, Path(description="Document key of the import job.")],
    ctx: TenantContext = Depends(get_active_tenant_context),
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: ImportService = Depends(get_import_service),
):
    """Delete an import job of the caller's own tenant — lead only (#1501).

    The rank is decided in :meth:`ImportService.delete_job`, whose three arguments
    are keyword-only without defaults, so the decision cannot drift between this
    route and any other caller. A foreign job is a 404 before the rank is even
    consulted.
    """
    service.delete_job(
        key,
        tenant_key=ctx.tenant_key,
        caller_role=ctx.role,
        is_platform_admin=is_platform_admin,
    )


@router.get("/templates/{entity_type}")
def get_template(
    entity_type: Annotated[EntityType, Path(description="Master-data entity type to download a CSV template for.")],
    service: ImportService = Depends(get_import_service),
):
    """Download a CSV import template for an entity type."""
    csv_content = service.get_template(entity_type)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity_type.value}_template.csv"},
    )
