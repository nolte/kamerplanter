"""Irrigation zones of a site (REQ-053 §14, §21.6 GP-API-050/051; WP 7.1, #2467).

The gate decides the caller's rank only (§21.8 "Bewässerungszone": read all roles, create/change/assign from
grower, delete lead only). Ownership — the path's site, the stored zone, every key of the body — is resolved in
the service (§22.3 T-01…T-03): a foreign and an absent key answer 404 alike, a foreign reference in a body 422
``reference.not_found``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from app.api.v1.auth.router import limiter, user_rate_limit_key
from app.api.v1.irrigation_zones.schemas import (
    IrrigationZoneCreate,
    IrrigationZoneLocationsResponse,
    IrrigationZoneLocationsUpdate,
    IrrigationZoneLogWatering,
    IrrigationZoneResponse,
    IrrigationZoneStatusResponse,
    IrrigationZoneUpdate,
    IrrigationZoneWateringResponse,
    zone_locations_to_response,
    zone_status_to_response,
    zone_to_response,
    zone_watering_to_response,
)
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_irrigation_zone_service
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
)
from app.common.pagination import PaginationParams, get_pagination
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.models.tenant_context import TenantContext
from app.domain.services.irrigation_zone_service import IrrigationZoneService

router = APIRouter(tags=["irrigation-zones"], responses=NOT_FOUND_RESPONSE)

_SITE_KEY = Annotated[str, Path(description="Document key of the site.")]
_ZONE_KEY = Annotated[str, Path(description="Document key of the irrigation zone.")]


@router.get("/sites/{key}/irrigation-zones", response_model=list[IrrigationZoneResponse])
def list_irrigation_zones(
    key: _SITE_KEY,
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> list[IrrigationZoneResponse]:
    """The irrigation zones of a site by name, each with the beds it covers (GP-API-050)."""
    views = service.list_zones(key, tenant_key=ctx.tenant_key, offset=pagination.offset, limit=pagination.limit)
    return [zone_to_response(view) for view in views]


@router.post(
    "/sites/{key}/irrigation-zones",
    response_model=IrrigationZoneResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def create_irrigation_zone(
    key: _SITE_KEY,
    body: IrrigationZoneCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.IRRIGATION_ZONE, Action.CREATE)),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> IrrigationZoneResponse:
    """Create a zone on the site (GP-API-050, from grower).

    422 ``reference.not_found`` when ``water_source_key`` is not a water source of this site or ``actuator_key``
    is not an actuator of the tenant at a location of this site. The technical coupling (``actuator_key``,
    ``flow_rate_source`` ``ha_entity``, ``flow_rate_ha_entity_id``) needs the ``technical`` admin scope (403); a
    flow entity that is not granted to the tenant is 422 ``HA_ENTITY_NOT_GRANTED``, one that is no flow sensor 422
    ``irrigation_zone.flow_entity_device_class``.
    """
    view = service.create_zone(key, tenant_key=ctx.tenant_key, role=ctx.role, data=body, admin_scopes=ctx.admin_scopes)
    return zone_to_response(view)


@router.get("/irrigation-zones/{key}", response_model=IrrigationZoneResponse)
def get_irrigation_zone(
    key: _ZONE_KEY,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> IrrigationZoneResponse:
    """One zone with the beds it covers (GP-API-050)."""
    return zone_to_response(service.get_zone(key, tenant_key=ctx.tenant_key))


@router.patch(
    "/irrigation-zones/{key}",
    response_model=IrrigationZoneResponse,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
def patch_irrigation_zone(
    key: _ZONE_KEY,
    body: IrrigationZoneUpdate,
    ctx: TenantContext = Depends(require_permission(ResourceType.IRRIGATION_ZONE, Action.UPDATE)),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> IrrigationZoneResponse:
    """Change the fields present (GP-API-050, from grower); ``water_source_key: null`` unlinks the source.

    A change of ``actuator_key`` / ``flow_rate_source`` / ``flow_rate_ha_entity_id`` needs the ``technical`` admin
    scope (403, SR-014); the checks of the create route apply to the new values.
    """
    view = service.patch_zone(key, tenant_key=ctx.tenant_key, role=ctx.role, patch=body, admin_scopes=ctx.admin_scopes)
    return zone_to_response(view)


@router.delete(
    "/irrigation-zones/{key}",
    status_code=204,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE},
)
def delete_irrigation_zone(
    key: _ZONE_KEY,
    ctx: TenantContext = Depends(require_permission(ResourceType.IRRIGATION_ZONE, Action.DELETE)),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> None:
    """Delete a zone (lead only, GP-API-050). Its beds lose the zone in the same transaction; audited (SR-011)."""
    service.delete_zone(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)


@router.put(
    "/irrigation-zones/{key}/locations",
    response_model=IrrigationZoneLocationsResponse,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
def replace_irrigation_zone_locations(
    key: _ZONE_KEY,
    body: IrrigationZoneLocationsUpdate,
    ctx: TenantContext = Depends(require_permission(ResourceType.IRRIGATION_ZONE, Action.UPDATE)),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> IrrigationZoneLocationsResponse:
    """Replace the beds of the zone (GP-API-051, from grower).

    Every key must be a location of the zone's site (422 ``reference.not_found`` at ``location_keys[i]``). A bed
    is in at most one zone: one that another zone covered moves here and is named in ``moved_from``.
    """
    view, change = service.replace_locations(
        key, tenant_key=ctx.tenant_key, role=ctx.role, location_keys=body.location_keys
    )
    return zone_locations_to_response(view, change)


@router.get("/irrigation-zones/{key}/status", response_model=IrrigationZoneStatusResponse)
def get_irrigation_zone_status(
    key: _ZONE_KEY,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> IrrigationZoneStatusResponse:
    """The last and the next planned watering of the zone's beds and the litres of the last 30 days (GP-API-052).

    `last_watering.allocation` says whether the quantity was measured or divided over the beds. `next_planned`
    is the oldest open `watering` task of the zone's beds; `overdue` follows the UTC calendar-day rule.
    `demand_liters_today` is REQ-037's depth x area in net litres (`null` without a demand for today); the gross
    value and its `application_efficiency` appear only when an efficiency is known (zone value or the drip
    default) - never estimated (E-10). `hints` carry the water-source reserve in days and beds equipped otherwise.
    """
    return zone_status_to_response(service.zone_status(key, tenant_key=ctx.tenant_key))


@router.post(
    "/irrigation-zones/{key}/log-watering",
    response_model=IrrigationZoneWateringResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_zone_log_watering, key_func=user_rate_limit_key)
def log_irrigation_zone_watering(
    request: Request,
    key: _ZONE_KEY,
    body: IrrigationZoneLogWatering,
    ctx: TenantContext = Depends(require_permission(ResourceType.IRRIGATION_ZONE, Action.UPDATE)),
    service: IrrigationZoneService = Depends(get_irrigation_zone_service),
) -> IrrigationZoneWateringResponse:
    """Log one watering round for every bed of the zone (GP-API-053, from grower; 20 a minute per account).

    `volume_liters` is divided `by_area` or `equal` over the beds and written as one `watering` care event per bed
    in a single transaction, each marked with the `allocation`. Beds without an area are left out of `by_area` and
    named in `skipped_location_keys`; 422 `irrigation_zone.no_beds` / `irrigation_zone.no_bed_area` when nothing can
    be divided.
    """
    result = service.log_watering(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role, data=body)
    return zone_watering_to_response(result)
