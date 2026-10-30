"""The JSON backup of a garden plan, ``schema_version: "1"`` (REQ-053 GP-FR-140/147, GP-API-004, GP-NFR-051).

What a backup holds is what the **structure** is: the site's plan settings, the locations with their geometry
and soil profile, the garden objects and the slots (in the bed frame, as stored). What it must never hold is
named by the *absence* of a field: there is no plant, task, care event, photo or attachment field, and no
``*_by`` / ``*_user_key`` field and no ``tenant_key`` on any model below, so a new column on ``Location`` or
``GardenObject`` cannot leak into the file by being added to the model — it has to be added here on purpose
(``tests/unit/domain/models/test_garden_plan_export.py`` pins the exclusion).

``key`` values are the stored keys. They are **references inside the file** (a slot names its bed, an object its
parent area), not an identity: the import (GP-FR-141, GP-NFR-051) assigns new keys to everything and rewrites
the references through a key map built from them, so a backup restored into another site or tenant never
collides with, or claims, an existing document.

The site's ``gps_coordinates``, ``name`` of a member, assignments and notes of other documents are not part of
the plan (SR-024); the site contributes only its name and type.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import (
    BedStatus,
    GardenObjectType,
    GeometrySource,
    IrrigationZoneType,
    SiteType,
    SlotRole,
    SunExposure,
)
from app.domain.models.garden_object import GardenObjectProps
from app.domain.models.garden_plan import MAX_PLAN_OBJECTS_PER_SITE, MAX_PLAN_ZONES, MAX_SLOTS_PER_SITE
from app.domain.models.geometry import BedFrameGeometry, Geometry
from app.domain.models.irrigation_zone import COLOR_PATTERN, DEFAULT_ZONE_COLOR
from app.domain.models.site import SiteConditions, SoilProfile

SCHEMA_VERSION = "1"

#: What ``GET /plan/export`` writes (GP-FR-172): the whole site, exactly the named beds and objects, or the named
#: beds with everything below them. A partial file is the same ``schema_version "1"`` document - it simply holds less.
type ExportScope = Literal["site", "selection", "subtree"]
EXPORT_SCOPES: tuple[str, ...] = ("site", "selection", "subtree")
#: How many keys one partial export may name (a site holds at most 500 locations and objects, GP-NFR-017).
MAX_EXPORT_KEYS = 100
#: A garden object is addressed in ``keys`` with this prefix, because a location and an object may share a key string.
OBJECT_KEY_PREFIX = "object:"


class _ExportModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ExportSite(_ExportModel):
    name: str
    type: SiteType


class ExportPlanSettings(_ExportModel):
    boundary: Geometry | None = None
    north_angle_deg: float = 0.0
    default_grid_m: float
    adjacency_factor: float
    plan_revision: int = Field(ge=0, description="Informational: the import starts a new revision history.")


class ExportLocation(_ExportModel):
    key: str
    parent_location_key: str | None = None
    name: str
    location_type_key: str
    description: str | None = None
    notes: str | None = None
    geometry: Geometry | None = None
    area_m2: float = 0.0
    height_m: float | None = None
    bed_status: BedStatus = BedStatus.ACTIVE
    sun_exposure: SunExposure = SunExposure.UNKNOWN
    soil_profile: SoilProfile | None = None
    site_conditions: SiteConditions | None = None
    irrigation_zone_key: str | None = None
    #: Provenance (WP 7.9): the bed template this bed was placed from. Additive inside ``schema_version "1"``.
    #: The import resolves it against the system templates and the target tenant's own, else drops it and reports
    #: it in ``dropped_references[]``; the template itself is not part of the file.
    template_key: str | None = Field(default=None, min_length=1, max_length=200)
    locked: bool = False
    z_order: int = 0
    pitch_m: float | None = None


class ExportSlot(_ExportModel):
    key: str
    slot_id: str
    location_key: str
    slot_role: SlotRole = SlotRole.POSITION
    capacity_plants: int = 1
    #: Expressed in the bed frame of ``location_key`` (§9.2), exactly as stored.
    geometry: BedFrameGeometry | None = None
    row_index: int | None = None
    sequence: int | None = None
    geometry_source: GeometrySource | None = None
    container_volume_l: float | None = None
    planned_spacing_cm: float | None = None


class ExportGardenObject(_ExportModel):
    key: str
    parent_location_key: str | None = None
    object_type: GardenObjectType
    label: str = ""
    geometry: Geometry
    props: GardenObjectProps
    off_site: bool = False
    locked: bool = False
    z_order: int = 0
    notes: str | None = None


class ExportZone(_ExportModel):
    """An irrigation zone (GP-FR-140, §20.11).

    Which beds a zone covers is carried by ``ExportLocation.irrigation_zone_key`` (a reference to ``key`` here),
    not repeated on the zone. ``water_source_key`` names a ``water_source`` garden object *of the file*.

    Never in the file, by absence: ``actuator_key``, ``flow_rate_ha_entity_id`` and ``flow_rate_source`` - the
    technical coupling is re-made by a person with the ``technical`` scope after a restore (GP-FR-141, SR-014).
    """

    key: str
    name: str = Field(min_length=1, max_length=200)
    irrigation_type: IrrigationZoneType = IrrigationZoneType.MANUAL
    water_source_key: str | None = None
    application_efficiency: float | None = Field(default=None, gt=0, le=1)
    flow_rate_l_per_min: float | None = Field(default=None, gt=0)
    color: str = Field(default=DEFAULT_ZONE_COLOR, pattern=COLOR_PATTERN)
    schedule_hint: str | None = Field(default=None, max_length=500)


class GardenPlanExport(BaseModel):
    """``GET /sites/{key}/plan/export`` — the whole structure of one site's plan."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "schema_version": "1",
                    "exported_at": "2026-10-18T09:30:00Z",
                    "site": {"name": "Garten", "type": "outdoor"},
                    "plan": {
                        "boundary": {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 6, "rotation_deg": 0},
                        "north_angle_deg": 0,
                        "default_grid_m": 0.5,
                        "adjacency_factor": 1.0,
                        "plan_revision": 12,
                    },
                    "locations": [],
                    "slots": [],
                    "garden_objects": [],
                    "zones": [],
                }
            ]
        }
    )

    schema_version: Literal["1"] = SCHEMA_VERSION  # type: ignore[assignment]
    exported_at: datetime
    site: ExportSite
    plan: ExportPlanSettings | None = None
    locations: list[ExportLocation] = Field(default_factory=list)
    slots: list[ExportSlot] = Field(default_factory=list)
    garden_objects: list[ExportGardenObject] = Field(default_factory=list)
    #: Additive inside ``schema_version "1"``: a file written before WP 7.2 has no ``zones`` and reads as ``[]``.
    zones: list[ExportZone] = Field(default_factory=list, max_length=MAX_PLAN_ZONES)


class GardenPlanImportDocument(GardenPlanExport):
    """A backup **as the import reads it** (#2542 W-1): the lists of an untrusted file are capped before any lookup.

    A file may not hold more locations, garden objects or slots than one site may (GP-NFR-017); without the caps
    an oversized file was read whole and every one of its beds resolved its zone and substrate before
    ``_check_quotas`` refused it. The caps sit here and not on :class:`GardenPlanExport`, because that model is
    also what the export *writes*: the location quota is enforced by the plan batch and the import, but a location
    created through the site API is not counted against it, so a site above the quota must still be exportable.
    """

    locations: list[ExportLocation] = Field(default_factory=list, max_length=MAX_PLAN_OBJECTS_PER_SITE)
    slots: list[ExportSlot] = Field(default_factory=list, max_length=MAX_SLOTS_PER_SITE)
    garden_objects: list[ExportGardenObject] = Field(default_factory=list, max_length=MAX_PLAN_OBJECTS_PER_SITE)
