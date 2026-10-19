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

**What is written from WP 7.4 on.** ``actuator_key`` and the ``flow_rate_*`` fields belong to the stored
shape (§20.11) but are a technical coupling (SR-014: scope ``technical``, a granted Home Assistant entity, an
actuator of the same site). Until WP 7.4 a request that sets one of them is refused (422
``irrigation_zone.coupling_not_available``); the stored defaults are ``null`` / ``manual``.

**Agronomic values (E-10).** ``application_efficiency`` is stored as sent and stays ``null`` otherwise — the
type defaults with a source (drip 0.88, R-005) are WP 7.5, nothing here invents one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.common.enums import FlowRateSource, IrrigationZoneType
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

#: The fields of the technical coupling (§14.1, SR-014): stored, but written from WP 7.4 on.
COUPLING_FIELDS: tuple[str, ...] = (
    "actuator_key",
    "flow_rate_l_per_min",
    "flow_rate_source",
    "flow_rate_ha_entity_id",
)


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
    #: Part of the contract, refused with 422 until WP 7.4 when set (see the module docstring).
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
