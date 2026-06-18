from fastapi import APIRouter, Depends, Query

from app.api.v1.care_reminders.schemas import CareDashboardEntryResponse
from app.common.auth import get_current_tenant
from app.common.dependencies import get_care_reminder_service
from app.domain.models.tenant_context import TenantContext
from app.domain.services.care_reminder_service import CareReminderService

router = APIRouter(prefix="/care-reminders", tags=["care-reminders"])


@router.get("/dashboard", response_model=list[CareDashboardEntryResponse])
def get_care_dashboard(
    hemisphere: str = Query("north", pattern="^(north|south)$"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: CareReminderService = Depends(get_care_reminder_service),
):
    """Build the care dashboard from the active plants of the current tenant.

    Tenant isolation is enforced via ``get_current_tenant``; only plants of the
    authenticated tenant are considered (removed plants are excluded).
    """
    entries = service.get_care_dashboard_for_tenant(ctx.tenant_key, hemisphere)
    return [CareDashboardEntryResponse(**e.model_dump()) for e in entries]
