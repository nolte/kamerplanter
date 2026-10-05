"""MT-015 (#2112) — the platform admin maintains each tenant's Home Assistant entity allowlist.

Kamerplanter talks to **one** Home Assistant instance, the operator's (REQ-005
§1.3, REQ-018 §1.3). A tenant uses — binds to a sensor, an actuator, a weather
source or a notification destination, and has read or switched on its behalf —
only the entities granted to it here.

* ``GET    /admin/ha-entity-grants/tenants/{tenant_key}`` — the tenant's grants.
* ``GET    /admin/ha-entity-grants/tenants/{tenant_key}/inventory`` — the
  instance's whole inventory, each entity marked ``granted`` for the tenant
  (graceful on an HA outage: the grants alone).
* ``POST   /admin/ha-entity-grants/tenants/{tenant_key}`` — grant entities
  (idempotent).
* ``DELETE /admin/ha-entity-grants/tenants/{tenant_key}/{entity_id}`` — withdraw
  a grant. Sensors and actuators keep their binding but are no longer read or
  switched; ingest skips them.

Gating: ``require_platform_admin`` (light-mode-aware), like every admin router.
An unknown tenant key is a 404.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from app.api.v1.admin.ha_entity_grants.schemas import (
    HaEntityGrantResponse,
    HaEntityGrantsRequest,
    HaEntityGrantsResult,
    HaEntityInventoryItem,
    HaEntityInventoryResponse,
)
from app.common.auth import require_platform_admin
from app.common.dependencies import get_ha_entity_grant_service, get_tenant_service
from app.common.exceptions import NotFoundError
from app.common.openapi_responses import AUTH_CRUD_RESPONSES
from app.domain.models.ha_entity_grant import HA_ENTITY_ID_MAX_LENGTH, HA_ENTITY_ID_PATTERN, HaEntityGrant
from app.domain.models.user import User
from app.domain.services.ha_entity_grant_service import HaEntityGrantService
from app.domain.services.tenant_service import TenantService

router = APIRouter(prefix="/admin/ha-entity-grants", tags=["admin-ha-entity-grants"], responses=AUTH_CRUD_RESPONSES)

TenantKey = Annotated[str, Path(description="Document key of the tenant.", max_length=128)]


def _existing_tenant(tenant_key: str, tenant_service: TenantService) -> str:
    """``tenant_key`` when such a tenant exists, else 404 (raised by the service)."""
    tenant_service.get_tenant(tenant_key)
    return tenant_key


def _grant_response(grant: HaEntityGrant) -> HaEntityGrantResponse:
    return HaEntityGrantResponse(entity_id=grant.entity_id, source=str(grant.source), created_at=grant.created_at)


@router.get("/tenants/{tenant_key}", response_model=list[HaEntityGrantResponse])
def list_ha_entity_grants(
    tenant_key: TenantKey,
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
    grants: HaEntityGrantService = Depends(get_ha_entity_grant_service),
) -> list[HaEntityGrantResponse]:
    """The Home Assistant entities released for a tenant. Platform admin only."""
    _existing_tenant(tenant_key, tenant_service)
    return [_grant_response(g) for g in grants.list_grants(tenant_key)]


@router.get("/tenants/{tenant_key}/inventory", response_model=HaEntityInventoryResponse)
def get_ha_entity_inventory(
    tenant_key: TenantKey,
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
    grants: HaEntityGrantService = Depends(get_ha_entity_grant_service),
) -> HaEntityInventoryResponse:
    """The Home Assistant inventory with the tenant's grant state per entity. Platform admin only."""
    _existing_tenant(tenant_key, tenant_service)
    configured, entries = grants.inventory(tenant_key)
    return HaEntityInventoryResponse(
        ha_configured=configured,
        entities=[HaEntityInventoryItem(**entry) for entry in entries],
    )


@router.post("/tenants/{tenant_key}", response_model=HaEntityGrantsResult)
def add_ha_entity_grants(
    tenant_key: TenantKey,
    body: HaEntityGrantsRequest,
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
    grants: HaEntityGrantService = Depends(get_ha_entity_grant_service),
) -> HaEntityGrantsResult:
    """Release Home Assistant entities for a tenant (idempotent). Platform admin only."""
    _existing_tenant(tenant_key, tenant_service)
    created = grants.grant(tenant_key, body.entity_ids)
    return HaEntityGrantsResult(created=created, grants=[_grant_response(g) for g in grants.list_grants(tenant_key)])


@router.delete("/tenants/{tenant_key}/{entity_id}", status_code=204)
def revoke_ha_entity_grant(
    tenant_key: TenantKey,
    entity_id: Annotated[
        str,
        Path(
            description="Home Assistant entity id to withdraw.",
            max_length=HA_ENTITY_ID_MAX_LENGTH,
            pattern=f"^{HA_ENTITY_ID_PATTERN.pattern}$",
        ),
    ],
    _user: User = Depends(require_platform_admin),
    tenant_service: TenantService = Depends(get_tenant_service),
    grants: HaEntityGrantService = Depends(get_ha_entity_grant_service),
) -> Response:
    """Withdraw one grant. Platform admin only. 404 when the entity was not granted."""
    _existing_tenant(tenant_key, tenant_service)
    if not grants.revoke(tenant_key, entity_id):
        raise NotFoundError("HaEntityGrant", entity_id)
    return Response(status_code=204)
