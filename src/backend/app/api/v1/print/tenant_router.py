"""Print/export API endpoints for generating PDF documents."""

from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse

from app.common.auth import get_current_tenant
from app.common.dependencies import get_print_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.domain.models.tenant_context import TenantContext
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
def export_nutrient_plan_pdf(
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
def export_care_checklist_pdf(
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
def export_plant_labels_pdf(
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
