"""Request/response schemas of the irrigation zones (REQ-053 §20.11, §21.6 GP-API-050/051; WP 7.1, #2467).

``site_key`` and ``tenant_key`` are absent from every body (T-01, ``check_tenant_body_field``): the site is the
path's on create and the stored document's afterwards. ``flow_rate_ha_entity_id`` is not part of the response:
which members may read the bound entity is decided with the coupling itself (WP 7.4, SR-014, GP-NFR-060).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.common.enums import FlowRateSource, IrrigationZoneType
from app.domain.models.irrigation_zone import (
    IrrigationZoneInput,
    IrrigationZonePatch,
    IrrigationZoneView,
    ZoneCoverageChange,
    ZoneLocationsInput,
)


class IrrigationZoneCreate(IrrigationZoneInput):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "South zone (drip line)",
                    "irrigation_type": "drip",
                    "water_source_key": "go_91ab",
                    "color": "#2E7D32",
                    "schedule_hint": "mornings, 20 min",
                }
            ]
        },
    )


class IrrigationZoneUpdate(IrrigationZonePatch):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"name": "South zone", "water_source_key": None}]},
    )


class IrrigationZoneLocationsUpdate(ZoneLocationsInput):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"location_keys": ["loc_bed_1", "loc_bed_2"]}]},
    )


class IrrigationZoneResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "zone_sued",
                    "site_key": "site_7f3a",
                    "name": "South zone (drip line)",
                    "irrigation_type": "drip",
                    "water_source_key": "go_91ab",
                    "actuator_key": None,
                    "flow_rate_l_per_min": None,
                    "flow_rate_source": "manual",
                    "application_efficiency": None,
                    "color": "#2E7D32",
                    "schedule_hint": "mornings, 20 min",
                    "location_keys": ["loc_bed_1", "loc_bed_2"],
                }
            ]
        }
    )

    key: str
    site_key: str
    name: str
    irrigation_type: IrrigationZoneType
    water_source_key: str | None = None
    actuator_key: str | None = None
    flow_rate_l_per_min: float | None = None
    flow_rate_source: FlowRateSource = FlowRateSource.MANUAL
    application_efficiency: float | None = None
    color: str
    schedule_hint: str | None = None
    #: The beds the zone covers (``zone_covers``), sorted by key.
    location_keys: list[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class IrrigationZoneLocationsResponse(IrrigationZoneResponse):
    """The zone after ``PUT …/locations``, with what changed — a moved bed names the zone it left."""

    added: list[str]
    removed: list[str]
    #: location key → the zone it was taken from.
    moved_from: dict[str, str]


def _dump(model: BaseModel) -> dict[str, Any]:
    """``model_dump`` through a receiver typed as the pydantic base (see the call-graph sweep's blind-spot ceiling)."""
    return model.model_dump()


def zone_to_response(view: IrrigationZoneView) -> IrrigationZoneResponse:
    zone = view.zone
    return IrrigationZoneResponse(
        key=zone.key or "",
        site_key=zone.site_key,
        name=zone.name,
        irrigation_type=zone.irrigation_type,
        water_source_key=zone.water_source_key,
        actuator_key=zone.actuator_key,
        flow_rate_l_per_min=zone.flow_rate_l_per_min,
        flow_rate_source=zone.flow_rate_source,
        application_efficiency=zone.application_efficiency,
        color=zone.color,
        schedule_hint=zone.schedule_hint,
        location_keys=list(view.location_keys),
        created_at=zone.created_at,
        updated_at=zone.updated_at,
    )


def zone_locations_to_response(view: IrrigationZoneView, change: ZoneCoverageChange) -> IrrigationZoneLocationsResponse:
    base = zone_to_response(view)
    return IrrigationZoneLocationsResponse(
        **_dump(base),
        added=list(change.added),
        removed=list(change.removed),
        moved_from=dict(change.moved_from),
    )
