"""Tenant-scoped user preferences router.

Wraps user-preference endpoints under /t/{tenant_slug}/user-preferences so that
get_current_tenant enforces membership. Preferences are user-global
(not per-tenant).
"""

from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.user_preferences.schemas import UserPreferenceResponse, UserPreferenceUpdate
from app.common.auth import get_current_tenant
from app.common.dependencies import get_user_preference_service
from app.domain.models.tenant_context import TenantContext
from app.domain.services.user_preference_service import UserPreferenceService

router = APIRouter(prefix="/user-preferences", tags=["user-preferences"])


@router.get("", response_model=UserPreferenceResponse)
def get_preferences(
    ctx: TenantContext = Depends(get_current_tenant),
    service: UserPreferenceService = Depends(get_user_preference_service),
):
    """Return the current user's (tenant-independent) preferences."""
    pref = service.get_preferences(ctx.user_key)
    return to_response(pref, UserPreferenceResponse)


@router.patch("", response_model=UserPreferenceResponse)
def update_preferences(
    body: UserPreferenceUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: UserPreferenceService = Depends(get_user_preference_service),
):
    """Update the current user's preferences (supports dashboard-layout reset)."""
    # REQ-045 reset semantics: dump with exclude_unset so a deliberately-sent
    # ``dashboard_layout: null`` (reset to default) is not swallowed, then keep
    # the historical exclude_none behaviour for every other field.
    updates = body.model_dump(exclude_unset=True)
    updates = {k: v for k, v in updates.items() if v is not None or k == "dashboard_layout"}
    pref = service.update_preferences(ctx.user_key, updates)
    return to_response(pref, UserPreferenceResponse)
