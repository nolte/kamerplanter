"""REQ-045 — tenant-scoped dashboard personalization endpoints.

Mounted under ``/t/{tenant_slug}/dashboard`` so tenant membership is enforced
via :func:`get_current_tenant`. Adds:

- ``GET  …/dashboard/widgets/catalog`` — the widgets available to the calling
  user, server-authoritatively gated (REQ-042 module visibility, REQ-027 Light
  mode, REQ-031 AI). Unavailable widgets are returned greyed-out (``available``
  false + i18n ``unavailable_reason``), not omitted.
- ``GET  …/dashboard/aggregated?widgets=<keys>`` — the tenant-scoped REQ-009
  aggregation, sliced to the user's *active* widget keys (N+1 avoidance). This
  is the tenant-scoped successor of the global ``/dashboard/summary``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.common.auth import get_current_tenant
from app.common.dependencies import get_dashboard_service, get_user_preference_service
from app.config.settings import settings
from app.domain.models.tenant_context import TenantContext
from app.domain.services.dashboard_service import DashboardService
from app.domain.services.dashboard_widget_catalog import resolve_widget_catalog
from app.domain.services.user_preference_service import UserPreferenceService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardWidgetCatalogEntry(BaseModel):
    """One catalog entry as seen by the calling user (REQ-045 §3.3)."""

    widget_key: str
    category: str
    default_level: str
    default_size: dict[str, int]
    min_size: dict[str, int]
    max_size: dict[str, int]
    required_module: str | None = None
    available: bool
    unavailable_reason: str | None = None


class DashboardWidgetCatalogResponse(BaseModel):
    widgets: list[DashboardWidgetCatalogEntry]


class DashboardAggregatedResponse(BaseModel):
    generated_at: datetime
    tenant_key: str
    widgets: dict[str, Any] = Field(default_factory=dict)


@router.get("/widgets/catalog", response_model=DashboardWidgetCatalogResponse)
def get_widget_catalog(
    ctx: TenantContext = Depends(get_current_tenant),
    prefs: UserPreferenceService = Depends(get_user_preference_service),
) -> DashboardWidgetCatalogResponse:
    """Return the widget catalog with per-user availability."""

    pref = prefs.get_preferences(ctx.user_key)
    resolved = resolve_widget_catalog(
        mode=settings.kamerplanter_mode,
        module_visibility=pref.module_visibility,
    )
    entries = [
        DashboardWidgetCatalogEntry(
            widget_key=item.meta.widget_key,
            category=item.meta.category,
            default_level=str(item.meta.default_level),
            default_size=item.meta.default_size,
            min_size=item.meta.min_size,
            max_size=item.meta.max_size,
            required_module=item.meta.required_module,
            available=item.available,
            unavailable_reason=item.unavailable_reason,
        )
        for item in resolved
    ]
    return DashboardWidgetCatalogResponse(widgets=entries)


# Which summary slice each REQ-009-backed widget consumes. Widgets without an
# entry self-fetch their data (like WinterProtectionWidget) and are simply not
# part of the aggregated payload.
def _slice_summary_for(widget_key: str, summary: Any) -> Any | None:
    counts = summary.counts
    match widget_key:
        case "tasks_today":
            return {"open_tasks_today": counts.open_tasks_today, "upcoming_tasks": summary.upcoming_tasks}
        case "active_plants_summary":
            return {"plants_total": counts.plants_total, "plants_active": counts.plants_active}
        case "tank_status":
            return {"tanks_low": counts.tanks_low}
        case "care_reminders":
            return {"care_reminders_due": counts.care_reminders_due}
        case "next_calendar_events":
            return {"upcoming_tasks": summary.upcoming_tasks}
        case _:
            return None


@router.get("/aggregated", response_model=DashboardAggregatedResponse)
def get_aggregated(
    widgets: str = Query(default="", description="Comma-separated active widget keys (REQ-045)"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardAggregatedResponse:
    """Return REQ-009 aggregation sliced to the user's active widget keys."""

    requested = [key.strip() for key in widgets.split(",") if key.strip()]
    summary = service.get_summary(ctx.tenant_key)
    payloads: dict[str, Any] = {}
    for widget_key in requested:
        payload = _slice_summary_for(widget_key, summary)
        if payload is not None:
            payloads[widget_key] = payload
    return DashboardAggregatedResponse(
        generated_at=summary.generated_at,
        tenant_key=ctx.tenant_key,
        widgets=payloads,
    )
