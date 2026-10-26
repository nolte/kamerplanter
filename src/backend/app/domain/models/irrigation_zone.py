"""The irrigation zone: beds of one site that are watered together (REQ-053 §14.1, §20.11; WP 7.1, #2467).

A zone groups beds for one watering round — by hand, along a drip line at one valve, under one sprinkler. It
is the anchor for demand, last and next watering, consumption and, later, the actuator (§14.1). The bed keeps
its own ``Location.irrigation_system`` (how it is equipped); the zone is the grouping.

Unlike ``locations`` and ``garden_objects`` a zone **does** carry ``tenant_key`` (§20.13, E-01): it is
tenant-scoped master data of one site. ``site_key`` comes from the path on create and from the stored
document afterwards (§22.3 T-01) — never from a request body.

**Which beds a zone covers** is held twice and kept in step by every writer: the ``zone_covers`` edge
(zone → location, unique on ``_to`` since migration v0099, so a bed is in at most one zone) and
``Location.irrigation_zone_key``. The edge answers "which beds does this zone water", the field answers
"which zone waters this bed" without a traversal.

**The technical coupling (WP 7.4, SR-014).** ``actuator_key`` (an actuator of the tenant at a location of the same
site, edge ``zone_actuated_by``), ``flow_rate_source`` ``ha_entity`` and ``flow_rate_ha_entity_id`` (a granted
Home Assistant entity with ``device_class`` water or volume_flow_rate) are written by a caller with the
``technical`` admin scope only; the service decides it. The stored defaults are ``null`` / ``manual``.

**Agronomic values (E-10).** ``application_efficiency`` is stored as sent and stays ``null`` otherwise — the
type defaults with a source (drip 0.88, R-005) are WP 7.5, nothing here invents one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import CareEventAllocation, FlowRateSource, IrrigationZoneType
from app.domain.models.garden_plan import MAX_PLAN_OBJECTS_PER_SITE

#: ``color`` (§20.11): a six-digit hex colour, the outline/hatching of the zone on the plan (GP-FR-110).
COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"
#: SR-014: the Home Assistant flow-rate entity (written from WP 7.4 on).
HA_FLOW_ENTITY_PATTERN = r"^sensor\.[a-z0-9_]{1,64}$"
#: The colour a zone gets when the request names none — the example of §20.11, a presentation default only.
DEFAULT_ZONE_COLOR = "#2E7D32"
#: ``PUT /irrigation-zones/{key}/locations``: a site holds at most this many locations and objects together
#: (GP-NFR-017), so a zone cannot cover more beds than that.
MAX_ZONE_LOCATIONS = MAX_PLAN_OBJECTS_PER_SITE


def _stripped_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class IrrigationZone(BaseModel):
    """A stored ``irrigation_zones`` document (§20.11)."""

    model_config = ConfigDict(populate_by_name=True)

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    site_key: str
    name: str = Field(min_length=1, max_length=200)
    irrigation_type: IrrigationZoneType = IrrigationZoneType.MANUAL
    #: A ``water_source`` garden object of the same site (GP-NFR-058), linked by ``zone_supplied_by``.
    water_source_key: str | None = None
    #: An actuator of the tenant at a location of the same site (``zone_actuated_by``) — WP 7.4.
    actuator_key: str | None = None
    flow_rate_l_per_min: float | None = Field(default=None, gt=0)
    flow_rate_source: FlowRateSource = FlowRateSource.MANUAL
    flow_rate_ha_entity_id: str | None = Field(default=None, pattern=HA_FLOW_ENTITY_PATTERN)
    #: Gross-to-net factor of the watering (W-017), ``0 < x <= 1``; ``null`` = unknown (E-10).
    application_efficiency: float | None = Field(default=None, gt=0, le=1)
    color: str = Field(default=DEFAULT_ZONE_COLOR, pattern=COLOR_PATTERN)
    #: Free text ("mornings, 20 min"); shown, never interpreted.
    schedule_hint: str | None = Field(default=None, max_length=500)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("A zone needs a name.")
        return stripped

    @field_validator("schedule_hint")
    @classmethod
    def strip_schedule_hint(cls, value: str | None) -> str | None:
        return _stripped_or_none(value)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IrrigationZoneInput(_Strict):
    """What a client sends to create a zone (GP-API-050). ``site_key`` is the path's (T-01)."""

    name: str = Field(min_length=1, max_length=200)
    irrigation_type: IrrigationZoneType = IrrigationZoneType.MANUAL
    water_source_key: str | None = Field(default=None, min_length=1, max_length=200)
    color: str = Field(default=DEFAULT_ZONE_COLOR, pattern=COLOR_PATTERN)
    schedule_hint: str | None = Field(default=None, max_length=500)
    application_efficiency: float | None = Field(default=None, gt=0, le=1)
    #: The technical coupling: needs the ``technical`` admin scope (see the module docstring).
    actuator_key: str | None = Field(default=None, max_length=200)
    flow_rate_l_per_min: float | None = Field(default=None, gt=0)
    flow_rate_source: FlowRateSource | None = None
    flow_rate_ha_entity_id: str | None = Field(default=None, pattern=HA_FLOW_ENTITY_PATTERN)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("A zone needs a name.")
        return stripped


class IrrigationZonePatch(_Strict):
    """``PATCH /irrigation-zones/{key}``: only the fields present change; ``null`` clears a clearable one."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    irrigation_type: IrrigationZoneType | None = None
    water_source_key: str | None = Field(default=None, min_length=1, max_length=200)
    color: str | None = Field(default=None, pattern=COLOR_PATTERN)
    schedule_hint: str | None = Field(default=None, max_length=500)
    application_efficiency: float | None = Field(default=None, gt=0, le=1)
    actuator_key: str | None = Field(default=None, max_length=200)
    flow_rate_l_per_min: float | None = Field(default=None, gt=0)
    flow_rate_source: FlowRateSource | None = None
    flow_rate_ha_entity_id: str | None = Field(default=None, pattern=HA_FLOW_ENTITY_PATTERN)

    @model_validator(mode="after")
    def refuse_clearing_a_required_field(self) -> Self:
        for name in ("name", "irrigation_type", "color"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be cleared.")
        if self.name is not None and not self.name.strip():
            raise ValueError("A zone needs a name.")
        return self


class ZoneLocationsInput(_Strict):
    """``PUT /irrigation-zones/{key}/locations`` (GP-API-051): the complete set of beds the zone covers."""

    location_keys: list[str] = Field(max_length=MAX_ZONE_LOCATIONS)

    @field_validator("location_keys")
    @classmethod
    def refuse_empty_keys(cls, value: list[str]) -> list[str]:
        if any(not key or len(key) > 200 for key in value):
            raise ValueError("Every location key is a non-empty key of at most 200 characters.")
        return value


@dataclass(frozen=True)
class IrrigationZoneView:
    """A zone with the beds it covers (from the ``zone_covers`` edges), in key order."""

    zone: IrrigationZone
    location_keys: tuple[str, ...]


@dataclass(frozen=True)
class ZoneCoverageChange:
    """What ``replace_zone_locations`` changed: beds added, beds released, and beds taken from another zone."""

    added: tuple[str, ...]
    removed: tuple[str, ...]
    #: location key → the zone it was taken from ("a bed is in at most one zone").
    moved_from: dict[str, str]


@dataclass(frozen=True)
class LastWatering:
    """The newest watering of a bed or a zone (GP-FR-112): when, from which record, and how it was measured."""

    at: datetime
    source: Literal["care_event", "watering_event"]
    location_key: str | None
    #: ``measured`` unless a zone round split a total over its beds (GP-FR-117): never shown as measured then.
    allocation: str = "measured"


@dataclass(frozen=True)
class NextPlannedWatering:
    """The oldest open ``watering`` task of a zone's beds; ``due_date`` is ``None`` for a task without a date."""

    task_key: str
    location_key: str
    due_date: datetime | None


@dataclass(frozen=True)
class ZoneWateringFacts:
    """What the stores say about a zone's beds; the service adds the demand (WP 7.5)."""

    last_watering: LastWatering | None
    next_planned: NextPlannedWatering | None
    consumption_liters: float


#: One watering round is a garden's worth of water, not a reservoir's: the ceiling catches a typo (10 000 000 L).
MAX_ROUND_LITERS = 100_000.0


class ZoneWateringInput(_Strict):
    """``POST /irrigation-zones/{key}/log-watering`` (GP-API-053): one total, divided over the zone's beds."""

    volume_liters: float = Field(gt=0, le=MAX_ROUND_LITERS)
    #: ``by_area`` divides by ``Location.area_m2``, ``equal`` evenly. ``by_demand`` waits for WP 7.5 (#2466 item 1).
    allocation: CareEventAllocation
    performed_at: datetime | None = None
    summary: str | None = Field(default=None, max_length=500)

    @field_validator("allocation")
    @classmethod
    def refuse_measured(cls, value: CareEventAllocation) -> CareEventAllocation:
        if value is CareEventAllocation.MEASURED:
            raise ValueError("A divided total is `by_area` or `equal`; `measured` is a value taken per bed.")
        return value

    @field_validator("performed_at")
    @classmethod
    def aware_utc(cls, value: datetime | None) -> datetime | None:
        """A naive instant is read as UTC (§20.13: ``performed_at`` is UTC)."""
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @field_validator("summary")
    @classmethod
    def strip_summary(cls, value: str | None) -> str | None:
        return _stripped_or_none(value)


@dataclass(frozen=True)
class BedShare:
    """What one bed of the round received."""

    location_key: str
    liters: float


@dataclass(frozen=True)
class ZoneWateringResult:
    """The round: one care event per bed that got a share, and the beds `by_area` could not place (no area)."""

    event_keys: tuple[str, ...]
    shares: tuple[BedShare, ...]
    allocation: CareEventAllocation
    performed_at: datetime
    skipped_location_keys: tuple[str, ...]


@dataclass(frozen=True)
class NextPlannedView:
    task_key: str
    location_key: str
    due_date: datetime | None
    #: The UTC calendar-day rule of #2461 (:func:`~app.domain.calculators.overdue_calculator.is_overdue`).
    overdue: bool


@dataclass(frozen=True)
class ConsumptionPart:
    """Litres of the last 30 days from one kind of source (GP-FR-114): the provenance travels with the figure."""

    source: Literal["manual_log", "actuator_runtime_manual_rate", "actuator_runtime_ha_rate"]
    liters: float


@dataclass(frozen=True)
class ZoneHint:
    """A hint the zone panel shows (GP-FR-119): a stable ``code`` for the client's wording and its figures."""

    code: str
    params: dict[str, float | int | str | list[str]]


@dataclass(frozen=True)
class ZoneStatusView:
    """GP-API-052: the zone's last and next watering, today's demand and the last 30 days' consumption."""

    zone_key: str
    last_watering: LastWatering | None
    next_planned: NextPlannedView | None
    #: Net litres the zone's beds need today (REQ-037 depth x area); ``None`` when no bed has a demand for today.
    demand_liters_today: float | None
    consumption_liters_30d: float
    #: Net / efficiency; ``None`` while the efficiency is unknown (E-10) - only drip has a sourced default.
    demand_gross_liters_today: float | None = None
    application_efficiency: float | None = None
    #: ``zone`` (set by a person) or ``type_default`` (drip, R-005); ``None`` = efficiency unknown.
    efficiency_source: Literal["zone", "type_default"] | None = None
    hints: tuple[ZoneHint, ...] = ()
    #: Where ``consumption_liters_30d`` comes from; the parts add up to it. Empty when nothing was recorded.
    consumption: tuple[ConsumptionPart, ...] = ()
