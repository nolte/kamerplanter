"""Tenant-scoped user preferences router.

Wraps user-preference endpoints under /t/{tenant_slug}/user-preferences so that
get_current_tenant enforces membership. Preferences are user-global
(not per-tenant).
"""

from fastapi import APIRouter, Depends

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
    pref = service.get_preferences(ctx.user_key)
    return UserPreferenceResponse(key=pref.key or "", **pref.model_dump(exclude={"key"}))


@router.patch("", response_model=UserPreferenceResponse)
def update_preferences(
    body: UserPreferenceUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: UserPreferenceService = Depends(get_user_preference_service),
):
    updates = body.model_dump(exclude_none=True)
    pref = service.update_preferences(ctx.user_key, updates)
    return UserPreferenceResponse(key=pref.key or "", **pref.model_dump(exclude={"key"}))
