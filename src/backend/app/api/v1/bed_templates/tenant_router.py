"""Bed templates (REQ-053 §20.12, §21.7, §21.8 "Beetvorlage"; WP 7.8, #2474).

``GET /bed-templates`` answers the system templates and the tenant's own. The gate decides the caller's rank only
(read all roles, create and change from grower, delete lead only); whose row it is - the tenant's, a system one
(platform admin only) or another tenant's (404) - is decided in the service (§22.3 T-01..T-03).

The exchange pair (GP-API-070/071, WP 9.9): ``GET /bed-templates/{key}/export`` (every member) delivers one template
as a JSON file without keys, owner, author or note; ``POST /bed-templates/import`` (from grower) reads such a file,
at most 256 KB, as a new template of the caller's tenant.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, Response
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth.router import limiter, tenant_rate_limit_key, user_rate_limit_key
from app.api.v1.bed_templates.schemas import (
    BedTemplateCreate,
    BedTemplateExchangeFile,
    BedTemplateImportResponse,
    BedTemplateResponse,
    BedTemplateUpdate,
    bed_template_to_response,
    import_report_to_response,
)
from app.common.auth import get_budgeted_tenant, get_current_tenant, get_is_platform_admin, require_permission
from app.common.body_limit import read_bounded_body
from app.common.dependencies import get_bed_template_service
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
    request_body_schema,
)
from app.common.pagination import PaginationParams, get_pagination
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.models.bed_template_exchange import MAX_FILE_BYTES
from app.domain.models.tenant_context import TenantContext
from app.domain.services.bed_template_service import BedTemplateService
from app.domain.services.garden_plan_export_service import safe_filename_part

router = APIRouter(tags=["bed-templates"], responses=NOT_FOUND_RESPONSE)

_TEMPLATE_KEY = Annotated[str, Path(description="Document key of the bed template.")]


@router.get("/bed-templates", response_model=list[BedTemplateResponse])
def list_bed_templates(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> list[BedTemplateResponse]:
    """The system templates (standard sizes) and the tenant's own, by name (GP-FR-044, GP-FR-045)."""
    templates = service.list_templates(tenant_key=ctx.tenant_key, offset=pagination.offset, limit=pagination.limit)
    return [bed_template_to_response(template) for template in templates]


@router.post(
    "/bed-templates",
    response_model=BedTemplateResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def create_bed_template(
    body: BedTemplateCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.BED_TEMPLATE, Action.CREATE)),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> BedTemplateResponse:
    """Create a template of the tenant (from grower).

    `default_geometry` is in the bed frame (rect, circle or polygon; the anchor of the shape at the origin).
    422 `reference.not_found` when `location_type_key` or a `recurring_task_templates` key does not exist for the
    tenant, 422 `bed_template.not_a_bed_type` for a location type that is no bed type, 422
    `bed_template.quota_exceeded` at the tenant's ceiling.
    """
    created = service.create_template(tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role, data=body)
    return bed_template_to_response(created)


@router.post(
    "/bed-templates/import",
    response_model=BedTemplateImportResponse,
    summary="Check (dry run) or import a bed template file",
    responses={
        **FORBIDDEN_RESPONSE,
        **CONFLICT_RESPONSE,
        **VALIDATION_RESPONSE,
        413: {"description": "The file is larger than 256 KB (`REQUEST_BODY_TOO_LARGE`)."},
        429: {"description": "The tenant's import budget is spent (`RATE_LIMIT_EXCEEDED`)."},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": request_body_schema(BedTemplateExchangeFile)}},
        }
    },
)
@limiter.limit(settings.rate_limit_bed_template_import, key_func=tenant_rate_limit_key)
async def import_bed_template(
    request: Request,
    dry_run: Annotated[bool, Query(description="Check the file and report; write nothing. Default `true`.")] = True,
    name: Annotated[
        str | None,
        Query(min_length=1, max_length=200, description="Use this name instead of the file's (after a 409)."),
    ] = None,
    ctx: TenantContext = Depends(require_permission(ResourceType.BED_TEMPLATE, Action.CREATE)),
    _budget: TenantContext = Depends(get_budgeted_tenant),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> BedTemplateImportResponse:
    """GP-API-071 (from grower). The body is the file of `GET /bed-templates/{key}/export`, at most 256 KB (413).

    It is read **here**, after authentication, the role gate and the per-tenant rate limit
    (`RATE_LIMIT_BED_TEMPLATE_IMPORT`).
    The file must be one JSON object nested at most
    10 levels with `format: "kamerplanter.bed_template"` and a `schema_version` of the current or the previous
    version (422 `bed_template.schema_version_unsupported` otherwise); the schema check is a 422 `VALIDATION_ERROR`.
    Top-level fields the schema does not name - `_key`, `tenant_key`, `created_by`, `recurring_task_templates` ... -
    are ignored and reported, never stored; no reference of the file is resolved. 422 `reference.not_found` /
    `bed_template.not_a_bed_type` for a bed type this installation does not have, 422
    `bed_template.quota_exceeded` at 200 own templates, 409 `bed_template.name_taken` with
    `details[0].suggested_name` when a template of that name exists (system or own, compared without case).
    `dry_run=true` (default) runs every check and writes nothing.
    """
    raw = await read_bounded_body(request, MAX_FILE_BYTES)
    report = await run_in_threadpool(
        service.import_template,
        raw,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        role=ctx.role,
        dry_run=dry_run,
        name=name,
    )
    return import_report_to_response(report)


@router.get(
    "/bed-templates/{key}/export",
    response_model=BedTemplateExchangeFile,
    summary="Download one bed template as a JSON file",
)
@limiter.limit(settings.rate_limit_plan_export, key_func=user_rate_limit_key)
def export_bed_template(
    request: Request,
    key: _TEMPLATE_KEY,
    ctx: TenantContext = Depends(get_current_tenant),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> Response:
    """GP-API-070 (every member): `format`, `schema_version`, name, bed type, geometry, height and planting grid -
    no key, no `tenant_key`, no `created_by`, no task templates, no note. A system template can be exported too;
    another tenant's template answers 404. Delivered as an attachment."""
    document = service.export_template(key, tenant_key=ctx.tenant_key)
    return Response(
        content=document.model_dump_json(),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="bed-template-{safe_filename_part(key)}.json"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch(
    "/bed-templates/{key}",
    response_model=BedTemplateResponse,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def patch_bed_template(
    key: _TEMPLATE_KEY,
    body: BedTemplateUpdate,
    ctx: TenantContext = Depends(require_permission(ResourceType.BED_TEMPLATE, Action.UPDATE)),
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> BedTemplateResponse:
    """Change the fields present (from grower); `height_m: null` clears the height.

    A system template can be changed by a platform admin only (403 for everybody else); another tenant's template
    answers 404.
    """
    updated = service.patch_template(
        key, tenant_key=ctx.tenant_key, role=ctx.role, patch=body, is_platform_admin=is_platform_admin
    )
    return bed_template_to_response(updated)


@router.delete(
    "/bed-templates/{key}",
    status_code=204,
    responses=FORBIDDEN_RESPONSE,
)
def delete_bed_template(
    key: _TEMPLATE_KEY,
    ctx: TenantContext = Depends(require_permission(ResourceType.BED_TEMPLATE, Action.DELETE)),
    is_platform_admin: bool = Depends(get_is_platform_admin),
    service: BedTemplateService = Depends(get_bed_template_service),
) -> None:
    """Delete a template (lead only). Beds placed from it keep their copy of the fields; their `template_key` is
    unset, since it would name nothing. A system template can be deleted by a platform admin only."""
    service.delete_template(key, tenant_key=ctx.tenant_key, role=ctx.role, is_platform_admin=is_platform_admin)
