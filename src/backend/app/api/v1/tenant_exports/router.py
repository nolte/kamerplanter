"""Routes of the tenant export and import (REQ-056 §8, §14, #2138) — full mode only.

``/tenants/{slug}/exports…`` is deliberately **not** behind
:func:`~app.common.auth.get_current_tenant`: a ``pending_deletion`` tenant resolves for
nobody (#2105), yet its management may export it inside the grace (REQ-056 §8.1). The
service resolves the slug and proves lead ∧ management from the stored membership;
an unknown slug and a tenant the caller may not export are one answer (403, §12.2).
None of these routes accepts an API key or a service account (403).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Path, Request, UploadFile
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth.router import limiter, user_rate_limit_key
from app.api.v1.tenant_exports.schemas import TenantExportCreateRequest, TenantExportResponse, TenantImportResponse
from app.common.auth import get_authenticated_with_api_key, require_account_principal, require_platform_admin
from app.common.dependencies import get_tenant_export_service
from app.common.openapi_responses import AUTH_CRUD_RESPONSES, STEP_UP_RESPONSES
from app.common.pagination import PaginationParams, get_pagination
from app.common.request_ip import resolve_client_ip
from app.config.settings import settings
from app.domain.models.user import User
from app.domain.services.tenant_export_service import (
    StepUpFactors,
    TenantExportService,
    member_mapping_from_form,
)

tenant_router = APIRouter(prefix="/tenants", tags=["tenants"], responses=AUTH_CRUD_RESPONSES)
admin_router = APIRouter(prefix="/admin/platform", tags=["admin-platform"], responses=AUTH_CRUD_RESPONSES)

#: The import route, relative to ``admin_router``; its full path carries the route's own body ceiling
#: in ``RequestBodyLimitMiddleware`` (``TENANT_IMPORT_MAX_UPLOAD_MB``, #2138). The guard
#: ``tests/unit/guards/test_tenant_import_body_ceiling_names_the_route.py`` holds the path to the app's route.
IMPORT_ROUTE = "/tenant-imports"
TENANT_IMPORT_PATH = f"/api/v1{admin_router.prefix}{IMPORT_ROUTE}"

_ZIP_RESPONSE: dict[int | str, dict[str, Any]] = {
    200: {"content": {"application/zip": {}}, "description": "The tenant archive as a ZIP file."}
}


def _archive_response(stream: AsyncIterator[bytes], export_key: str) -> StreamingResponse:
    return StreamingResponse(
        stream,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="kamerplanter-tenant-export-{export_key}.zip"'},
    )


# ── the tenant's management ─────────────────────────────────────────


@tenant_router.post(
    "/{tenant_slug}/exports", status_code=202, response_model=TenantExportResponse, responses=STEP_UP_RESPONSES
)
def request_tenant_export(
    body: TenantExportCreateRequest,
    tenant_slug: str = Path(description="URL slug of the tenant to export."),
    user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> TenantExportResponse:
    """Request an export of the whole tenant (REQ-056 §8.2, AK-26 … AK-28) — ``202 Accepted``.

    The lead role **and** the ``management`` scope, from the stored membership, plus the requester's
    own step-up (``tenant_export``, bound to the tenant's key: ``current_password`` or ``step_up_token`` /
    ``step_up_code``). Possible in ``active`` and ``pending_deletion``. ``409 EXPORT_ALREADY_RUNNING``
    while one runs; ``429`` past ``TENANT_EXPORTS_PER_DAY`` in 24 hours. Every member with the
    management scope is mailed, and ``tenant_export_requested`` is audited. A Celery task writes the
    archive; poll ``GET /tenants/{slug}/exports`` until ``completed``.
    """
    request = service.request_export(
        requester=user,
        authenticated_with_api_key=via_api_key,
        origin="tenant_management",
        factors=body.to_factors(),
        client_ip=client_ip,
        slug=tenant_slug,
    )
    return TenantExportResponse.from_request(request)


@tenant_router.get("/{tenant_slug}/exports", response_model=list[TenantExportResponse])
def list_tenant_exports(
    tenant_slug: str = Path(description="URL slug of the exported tenant."),
    pagination: PaginationParams = Depends(get_pagination),
    user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> list[TenantExportResponse]:
    """The caller's own exports of the tenant, newest first (paginated); lead ∧ management, never an API key."""
    return [
        TenantExportResponse.from_request(r)
        for r in service.list_exports(
            requester=user,
            authenticated_with_api_key=via_api_key,
            origin="tenant_management",
            slug=tenant_slug,
            offset=pagination.offset,
            limit=pagination.limit,
        )
    ]


@tenant_router.get(
    "/{tenant_slug}/exports/{export_key}/download", response_class=StreamingResponse, responses=_ZIP_RESPONSE
)
@limiter.limit(settings.rate_limit_export_download)
async def download_tenant_export(
    request: Request,
    tenant_slug: Annotated[str, Path(description="URL slug of the exported tenant.")],
    export_key: Annotated[str, Path(description="Key of the export request.")],
    user: User = Depends(require_account_principal),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> StreamingResponse:
    """Stream the archive to the person who requested it, until it expires (NFR-011 R-05; 404 after).

    Never with an API key (403); every download is audited (``tenant_export_downloaded``).
    """
    export = await run_in_threadpool(
        service.prepare_download,
        export_key,
        requester=user,
        authenticated_with_api_key=via_api_key,
        origin="tenant_management",
        slug=tenant_slug,
    )
    return _archive_response(await service.open_download(export), export.key or export_key)


# ── the platform admin ──────────────────────────────────────────────


@admin_router.post(
    "/tenants/{key}/exports", status_code=202, response_model=TenantExportResponse, responses=STEP_UP_RESPONSES
)
def admin_request_tenant_export(
    body: TenantExportCreateRequest,
    key: str = Path(description="Key of the tenant to export."),
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> TenantExportResponse:
    """Export a tenant as platform admin, in every state but ``deleted`` (REQ-056 §8.2, AK-27); step-up."""
    request = service.request_export(
        requester=admin,
        authenticated_with_api_key=via_api_key,
        origin="platform_admin",
        factors=body.to_factors(),
        client_ip=client_ip,
        tenant_key=key,
    )
    return TenantExportResponse.from_request(request)


@admin_router.get("/tenants/{key}/exports", response_model=list[TenantExportResponse])
def admin_list_tenant_exports(
    key: str = Path(description="Key of the exported tenant."),
    pagination: PaginationParams = Depends(get_pagination),
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> list[TenantExportResponse]:
    """The admin's own exports of the tenant, newest first (paginated); never an API key."""
    return [
        TenantExportResponse.from_request(r)
        for r in service.list_exports(
            requester=admin,
            authenticated_with_api_key=via_api_key,
            origin="platform_admin",
            tenant_key=key,
            offset=pagination.offset,
            limit=pagination.limit,
        )
    ]


@admin_router.get(
    "/tenants/{key}/exports/{export_key}/download", response_class=StreamingResponse, responses=_ZIP_RESPONSE
)
@limiter.limit(settings.rate_limit_export_download)
async def admin_download_tenant_export(
    request: Request,
    key: Annotated[str, Path(description="Key of the exported tenant.")],
    export_key: Annotated[str, Path(description="Key of the export request.")],
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> StreamingResponse:
    """Stream an archive the admin requested, until it expires; never an API key; audited."""
    export = await run_in_threadpool(
        service.prepare_download,
        export_key,
        requester=admin,
        authenticated_with_api_key=via_api_key,
        origin="platform_admin",
        tenant_key=key,
    )
    return _archive_response(await service.open_download(export), export.key or export_key)


@admin_router.post(IMPORT_ROUTE, status_code=202, response_model=TenantImportResponse, responses=STEP_UP_RESPONSES)
@limiter.limit(settings.rate_limit_tenant_import, key_func=user_rate_limit_key)
def admin_import_tenant(
    request: Request,
    archive: UploadFile = File(description="A tenant archive (kamerplanter-tenant-export/1)."),
    member_mapping: str | None = Form(
        default=None,
        description='JSON object {"<archive user key>": {"email": "<e-mail of an existing account>", '
        '"role": "lead|grower|viewer", "admin_scopes": ["management", "technical"]}}. The role and scopes '
        "are the ones you confirm, never the archive's. Unmapped members are dropped and their references "
        "become the pseudonym _anonymized.",
    ),
    plan_key: str | None = Form(default=None, description="Plan of the new tenant; the default plan when omitted."),
    current_password: str | None = Form(default=None, max_length=128),
    step_up_code: str | None = Form(default=None, max_length=32),
    step_up_token: str | None = Form(default=None, max_length=128),
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> TenantImportResponse:
    """Import a tenant archive as a **new** tenant (REQ-056 §8.4) — platform admin + step-up ``tenant_import``.

    The step-up is bound to ``archive:<first 32 hex digits of the upload's SHA-256>`` and checked before
    the upload is parsed. The archive is then verified completely before anything is written: ZIP
    directory bounds, format and migration level (``422 IMPORT_FORMAT_UNSUPPORTED``), checksums
    (``IMPORT_CHECKSUM_MISMATCH``), that every row and edge belongs to the archived tenant, every
    reference field declared (``IMPORT_UNDECLARED_REFERENCE``), every object key and type, every global
    catalogue entry present (``IMPORT_MISSING_CATALOG_ENTRIES``, listed) and every mapped address an
    existing account with a valid role (``IMPORT_MEMBER_NOT_FOUND``). The archive must fit the quotas of
    the plan the new tenant is founded on (REQ-056 §8.4 step 6): the mapped accounts and the owner
    (``422 MEMBER_LIMIT_REACHED``), the attachment bytes (``409 STORAGE_QUOTA_EXCEEDED``) and the gallery
    photos of each plant (``409 PHOTO_QUOTA_EXCEEDED``). ``verified`` in the response says
    whether this installation signed the archive; a foreign or unsigned archive is imported unverified.
    Every document gets a new key. ``202 Accepted``; poll ``GET /admin/platform/tenant-imports/{import_key}``
    for the report. ``413`` above ``TENANT_IMPORT_MAX_UPLOAD_MB`` — this route's own body ceiling; every
    other upload keeps ``STORAGE_MAX_FILE_SIZE_MB``. The ceiling never exceeds ``UPLOAD_SPOOL_BUDGET_MB``.
    """
    handle = archive.file
    handle.seek(0, 2)
    size = handle.tell()
    handle.seek(0)
    accepted = service.request_import(
        handle,
        size_bytes=size,
        requester=admin,
        authenticated_with_api_key=via_api_key,
        member_mapping=member_mapping_from_form(member_mapping),
        plan_key=plan_key,
        factors=StepUpFactors(password=current_password, code=step_up_code, reauth_token=step_up_token),
        client_ip=client_ip,
    )
    return TenantImportResponse.from_request(accepted)


@admin_router.get("/tenant-imports/{import_key}", response_model=TenantImportResponse)
def admin_get_tenant_import(
    import_key: str = Path(description="Key of the import request."),
    admin: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    service: TenantExportService = Depends(get_tenant_export_service),
) -> TenantImportResponse:
    """The import's state and report (counts per collection, no contents); never an API key."""
    return TenantImportResponse.from_request(
        service.get_import(import_key, requester=admin, authenticated_with_api_key=via_api_key)
    )
