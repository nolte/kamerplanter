"""REQ-031 §1.3 — FastAPI guards for the three-stage KI feature toggle."""

from __future__ import annotations

from fastapi import Depends, HTTPException

from app.common.auth import get_current_tenant
from app.common.dependencies import get_tenant_repo
from app.config.settings import settings
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.guards.feature_guard import FeatureGuard
from app.domain.models.ai_assistant import AiTenantSettings
from app.domain.models.tenant_context import TenantContext


def require_ai_feature_flag() -> None:
    """Stage 1 — operator flag. Returns 404 when KI is off cluster-wide (§1.3).

    A 404 (not 403) makes the whole KI API look non-existent, exactly as the spec
    requires: "so als gaebe es sie nicht".
    """
    if not settings.ai_features_enabled:
        raise HTTPException(status_code=404, detail="Not Found")


def require_ai_tenant_enabled(
    ctx: TenantContext = Depends(get_current_tenant),
    tenant_repo: ArangoTenantRepository = Depends(get_tenant_repo),
) -> AiTenantSettings:
    """Stage 2 — tenant setting. Raises ``ai.disabled_for_tenant`` (403) when off.

    Also enforces stage 1 first, so the tenant endpoints answer 404 when the
    operator flag is off regardless of tenant state.
    """
    require_ai_feature_flag()
    tenant = tenant_repo.get_by_key(ctx.tenant_key)
    tenant_settings = tenant.settings if tenant else {}
    return FeatureGuard.require_ai_enabled(tenant_settings)
