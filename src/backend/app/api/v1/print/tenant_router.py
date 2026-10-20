"""Print/export API endpoints for generating PDF documents."""

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.api.v1.auth.router import limiter, tenant_rate_limit_key, user_rate_limit_key
from app.api.v1.garden_plan.export_options import PLAN_EXPORT_TENANT_SCOPE, plan_svg_options
from app.common.auth import get_budgeted_tenant, get_current_tenant
from app.common.dependencies import get_garden_plan_export_service, get_print_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.config.settings import settings
from app.domain.engines.plan_svg_engine import PlanSvgOptions
from app.domain.models.tenant_context import TenantContext
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.print_service import PrintService

router = APIRouter(prefix="/print", tags=["print"], responses=NOT_FOUND_RESPONSE)

ALLOWED_LABEL_FIELDS = {
    "name",
    "scientific_name",
    "family",
    "planted_date",
    "current_phase",
    "location",
    "cultivar",
    "note",
}


@router.get("/nutrient-plan/{plan_key}")
@limiter.limit(settings.rate_limit_export, key_func=user_rate_limit_key)
def export_nutrient_plan_pdf(
    request: Request,
    plan_key: Annotated[str, Path(description="Document key of the nutrient plan.")],
    locale: str = Query("de", pattern="^(de|en)$", description="Document language: de or en."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PrintService = Depends(get_print_service),
) -> StreamingResponse:
    """Export a nutrient plan as PDF document."""
    pdf_bytes = service.generate_nutrient_plan_pdf(
        plan_key=plan_key,
        tenant_key=ctx.tenant_key,
        locale=locale,
    )
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="nutrient-plan-{plan_key}.pdf"',
        },
    )


@router.get("/care-checklist")
@limiter.limit(settings.rate_limit_export, key_func=user_rate_limit_key)
def export_care_checklist_pdf(
    request: Request,
    date: str | None = Query(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Checklist date (YYYY-MM-DD); defaults to today."
    ),
    locale: str = Query("de", pattern="^(de|en)$", description="Document language: de or en."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PrintService = Depends(get_print_service),
) -> StreamingResponse:
    """Export the care checklist as PDF document."""
    pdf_bytes = service.generate_care_checklist_pdf(
        tenant_key=ctx.tenant_key,
        date=date,
        locale=locale,
    )
    filename = f"care-checklist-{date}.pdf" if date else "care-checklist.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/plant-labels")
@limiter.limit(settings.rate_limit_export, key_func=user_rate_limit_key)
def export_plant_labels_pdf(
    request: Request,
    plant_keys: str = Query(..., description="Comma-separated PlantInstance keys"),
    fields: str = Query(
        "name,scientific_name,planted_date",
        description="Comma-separated field names to display on each card",
    ),
    layout: str = Query(
        "grid_2x4", pattern="^(single|grid_2x4|grid_3x3)$", description="Card layout: single, grid_2x4 or grid_3x3."
    ),
    qr_size_mm: int = Query(25, ge=20, le=60, description="QR-code edge length in millimetres."),
    locale: str = Query("de", pattern="^(de|en)$", description="Document language: de or en."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PrintService = Depends(get_print_service),
) -> StreamingResponse:
    """Export plant info cards / labels as PDF with QR codes."""
    parsed_keys = [k.strip() for k in plant_keys.split(",") if k.strip()]
    if not parsed_keys:
        raise HTTPException(status_code=400, detail="At least one plant_key is required.")

    parsed_fields = [f.strip() for f in fields.split(",") if f.strip()]
    invalid_fields = set(parsed_fields) - ALLOWED_LABEL_FIELDS
    if invalid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field names: {', '.join(sorted(invalid_fields))}. "
            f"Allowed: {', '.join(sorted(ALLOWED_LABEL_FIELDS))}",
        )

    pdf_bytes = service.generate_plant_labels_pdf(
        tenant_key=ctx.tenant_key,
        tenant_slug=ctx.tenant_slug,
        plant_keys=parsed_keys,
        fields=parsed_fields,
        layout=layout,
        qr_size_mm=qr_size_mm,
        locale=locale,
    )
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="plant-labels.pdf"',
        },
    )


@router.get("/garden-plan/{site_key}")
@limiter.limit(settings.rate_limit_plan_export, key_func=user_rate_limit_key)
@limiter.shared_limit(
    settings.rate_limit_plan_export_tenant, scope=PLAN_EXPORT_TENANT_SCOPE, key_func=tenant_rate_limit_key
)
async def export_garden_plan_pdf(
    request: Request,
    site_key: Annotated[str, Path(description="Document key of the site.")],
    options: PlanSvgOptions = Depends(plan_svg_options),
    bed_list: bool = Query(False, description="Add a second page listing the beds (name, area, status, sun)."),
    underlay: bool = Query(
        False,
        description=(
            "Print the site's background picture (GP-FR-033) under the plan. Off by default: an aerial view or "
            "photo can reveal where someone lives, so it is printed only when asked for."
        ),
    ),
    ctx: TenantContext = Depends(get_budgeted_tenant),
    service: GardenPlanExportService = Depends(get_garden_plan_export_service),
) -> StreamingResponse:
    """The garden plan to scale as PDF (GP-API-007, GP-FR-142): scale bar, north arrow, legend, title block.

    Default A4 landscape with the finest scale at which the plan fits; ``X-Plan-Suggested-Paper: a3`` when A4
    would need a scale coarser than 1:200. Carries no member names, assignments, notes or coordinates.
    ``underlay=true`` lays the site's background picture under the plan; without it the PDF never carries one.
    422 ``plan.does_not_fit`` when a fixed scale does not fit the paper, ``plan.empty`` when there is nothing to draw.
    """
    picture = await service.load_underlay(site_key, tenant_key=ctx.tenant_key) if underlay else None
    pdf = await run_in_threadpool(
        service.render_pdf,
        site_key,
        tenant_key=ctx.tenant_key,
        options=options,
        bed_list=bed_list,
        underlay=picture,
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{pdf.filename}"',
        "X-Plan-Scale": f"1:{pdf.scale}",
    }
    if pdf.suggest_a3:
        headers["X-Plan-Suggested-Paper"] = "a3"
    return StreamingResponse(BytesIO(pdf.content), media_type="application/pdf", headers=headers)
