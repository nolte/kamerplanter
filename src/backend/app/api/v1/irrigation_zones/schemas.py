"""Request/response schemas of the irrigation zones (REQ-053 §20.11, §21.6 GP-API-050/051; WP 7.1, #2467).

``site_key`` and ``tenant_key`` are absent from every body (T-01, ``check_tenant_body_field``): the site is the
path's on create and the stored document's afterwards. ``flow_rate_ha_entity_id`` is not part of the response:
which members may read the bound entity is decided with the coupling itself (WP 7.4, SR-014, GP-NFR-060).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.common.enums import CareEventAllocation, FlowRateSource, IrrigationZoneType
from app.domain.models.irrigation_zone import (
    IrrigationZoneInput,
    IrrigationZonePatch,
    IrrigationZoneView,
    ZoneCoverageChange,
    ZoneLocationsInput,
    ZoneStatusView,
    ZoneWateringInput,
    ZoneWateringResult,
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


class IrrigationZoneLogWatering(ZoneWateringInput):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"volume_liters": 60, "allocation": "by_area", "summary": "Morning round, drip line"}]
        },
    )


class LastWateringResponse(BaseModel):
    at: datetime
    source: Literal["care_event", "watering_event"]
    location_key: str | None = None
    #: `measured` or the way a zone round divided its total; an allocated value is not a measured one.
    allocation: CareEventAllocation = CareEventAllocation.MEASURED


class NextPlannedResponse(BaseModel):
    task_key: str
    location_key: str
    due_date: datetime | None = None
    #: Due UTC calendar day before today's (#2461).
    overdue: bool = False


class IrrigationZoneStatusResponse(BaseModel):
    """GP-API-052: what the zone's beds were given and what is planned; demand waits for a sourced value."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "last_watering": {
                        "at": "2026-10-19T06:30:00Z",
                        "source": "care_event",
                        "location_key": "loc_bed_1",
                        "allocation": "by_area",
                    },
                    "next_planned": {
                        "task_key": "task_71",
                        "location_key": "loc_bed_2",
                        "due_date": "2026-10-21T00:00:00Z",
                        "overdue": False,
                    },
                    "demand_liters_today": None,
                    "consumption_liters_30d": 480.0,
                }
            ]
        }
    )

    last_watering: LastWateringResponse | None = None
    next_planned: NextPlannedResponse | None = None
    demand_liters_today: float | None = None
    consumption_liters_30d: float = 0.0


class BedShareResponse(BaseModel):
    location_key: str
    liters: float


class IrrigationZoneWateringResponse(BaseModel):
    """GP-API-053: the round as written - the events (one per bed) and what each bed received."""

    event_keys: list[str]
    shares: list[BedShareResponse]
    allocation: CareEventAllocation
    performed_at: datetime
    #: `by_area` only: beds of the zone without an area, left out of the division.
    skipped_location_keys: list[str]


def zone_status_to_response(view: ZoneStatusView) -> IrrigationZoneStatusResponse:
    last, planned = view.last_watering, view.next_planned
    return IrrigationZoneStatusResponse(
        last_watering=LastWateringResponse(
            at=last.at,
            source=last.source,
            location_key=last.location_key,
            allocation=CareEventAllocation(last.allocation),
        )
        if last is not None
        else None,
        next_planned=NextPlannedResponse(
            task_key=planned.task_key,
            location_key=planned.location_key,
            due_date=planned.due_date,
            overdue=planned.overdue,
        )
        if planned is not None
        else None,
        demand_liters_today=view.demand_liters_today,
        consumption_liters_30d=view.consumption_liters_30d,
    )


def zone_watering_to_response(result: ZoneWateringResult) -> IrrigationZoneWateringResponse:
    return IrrigationZoneWateringResponse(
        event_keys=list(result.event_keys),
        shares=[BedShareResponse(location_key=share.location_key, liters=share.liters) for share in result.shares],
        allocation=result.allocation,
        performed_at=result.performed_at,
        skipped_location_keys=list(result.skipped_location_keys),
    )
