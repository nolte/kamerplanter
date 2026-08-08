"""Tenant-scoped Home Assistant publish-selection endpoints.

Lets a tenant choose which plants, tanks and locations are exported to Home
Assistant as sensors (opt-in). The ``/enabled-keys`` route is the export-facing
read a Home Assistant coordinator polls.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.v1.ha_publish.schemas import (
    HaPublishBulkUpdate,
    HaPublishEnabledKeysResponse,
    HaPublishSettingResponse,
    HaPublishSettingUpdate,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_ha_publish_service
from app.core.permissions import Action
from app.domain.models.ha_publish_setting import HaPublishEntityType
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ha_publish_service import HaPublishService

router = APIRouter(prefix="/ha-publish", tags=["ha-publish"])


def _to_response(entity_type: HaPublishEntityType, entity_key: str, enabled: bool) -> HaPublishSettingResponse:
    return HaPublishSettingResponse(entity_type=entity_type, entity_key=entity_key, enabled=enabled)


@router.get("", response_model=list[HaPublishSettingResponse])
def list_settings(
    entity_type: HaPublishEntityType | None = Query(default=None, description="Filter by publishable entity type."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HaPublishService = Depends(get_ha_publish_service),
):
    """List the publish selection for this tenant (optionally by entity type)."""
    settings = service.list_settings(ctx.tenant_key, entity_type)
    return [_to_response(s.entity_type, s.entity_key, s.enabled) for s in settings]


@router.get("/enabled-keys/{entity_type}", response_model=HaPublishEnabledKeysResponse)
def list_enabled_keys(
    entity_type: Annotated[HaPublishEntityType, Path(description="Publishable entity type.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: HaPublishService = Depends(get_ha_publish_service),
):
    """Entity keys a Home Assistant coordinator should publish for this tenant."""
    keys = service.list_enabled_keys(ctx.tenant_key, entity_type)
    return HaPublishEnabledKeysResponse(entity_type=entity_type, entity_keys=keys)


@router.put("", response_model=list[HaPublishSettingResponse])
def bulk_set(
    body: HaPublishBulkUpdate,
    ctx: TenantContext = Depends(require_permission("ha-publish", Action.UPDATE)),
    service: HaPublishService = Depends(get_ha_publish_service),
):
    """Set the publish flag for several entities of one type at once."""
    settings = service.bulk_set_published(
        ctx.tenant_key,
        body.entity_type,
        {entry.entity_key: entry.enabled for entry in body.entries},
    )
    return [_to_response(s.entity_type, s.entity_key, s.enabled) for s in settings]


@router.get("/{entity_type}/{entity_key}", response_model=HaPublishSettingResponse)
def get_status(
    entity_type: Annotated[HaPublishEntityType, Path(description="Publishable entity type.")],
    entity_key: Annotated[str, Path(description="Document key of the entity.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: HaPublishService = Depends(get_ha_publish_service),
):
    """Whether a single entity is published to Home Assistant (opt-in default: false)."""
    enabled = service.is_published(ctx.tenant_key, entity_type, entity_key)
    return _to_response(entity_type, entity_key, enabled)


@router.put("/{entity_type}/{entity_key}", response_model=HaPublishSettingResponse)
def set_status(
    entity_type: Annotated[HaPublishEntityType, Path(description="Publishable entity type.")],
    entity_key: Annotated[str, Path(description="Document key of the entity.")],
    body: HaPublishSettingUpdate,
    ctx: TenantContext = Depends(require_permission("ha-publish", Action.UPDATE)),
    service: HaPublishService = Depends(get_ha_publish_service),
):
    """Enable or disable publishing a single entity to Home Assistant."""
    setting = service.set_published(ctx.tenant_key, entity_type, entity_key, body.enabled)
    return _to_response(setting.entity_type, setting.entity_key, setting.enabled)
