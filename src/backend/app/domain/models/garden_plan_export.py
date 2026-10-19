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

from app.common.enums import BedStatus, GardenObjectType, GeometrySource, SiteType, SlotRole, SunExposure
from app.domain.models.garden_object import GardenObjectProps
from app.domain.models.geometry import BedFrameGeometry, Geometry
from app.domain.models.site import SiteConditions, SoilProfile

SCHEMA_VERSION = "1"


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
