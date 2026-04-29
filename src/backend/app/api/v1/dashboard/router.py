"""REQ-009 Dashboard read-side router.

Exposes a single tenant-scoped endpoint that returns the consolidated
DashboardSummary built by DashboardService. The WebSocket fan-out for
live updates (Spec §3) lands as a follow-up.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.common.auth import get_current_user
from app.common.dependencies import get_dashboard_service
from app.domain.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


class DashboardCountsResponse(BaseModel):
    plants_total: int
    plants_active: int
    open_tasks_today: int
    overdue_tasks: int
    tanks_low: int
    care_reminders_due: int


class DashboardSummaryResponse(BaseModel):
    generated_at: datetime
    tenant_key: str
    counts: DashboardCountsResponse
    upcoming_tasks: list[dict[str, Any]] = Field(default_factory=list)
    recent_activities: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    tenant_key: str = "",
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    """Return the consolidated dashboard summary for ``tenant_key``."""

    summary = service.get_summary(tenant_key)
    return DashboardSummaryResponse(
        generated_at=summary.generated_at,
        tenant_key=summary.tenant_key,
        counts=DashboardCountsResponse(**summary.counts.__dict__),
        upcoming_tasks=summary.upcoming_tasks,
        recent_activities=summary.recent_activities,
    )
