import re
from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import (
    BedStatus,
    GeometryKind,
    GeometrySource,
    GrowingMediumKind,
    IrrigationSystem,
    LightType,
    Orientation,
    PhMethod,
    SiteType,
    SiteWaterRegime,
    SlotRole,
    SoilConditionFlag,
    SoilDrainage,
    SoilTexture,
    SunExposure,
)
from app.domain.calculators.geometry_calculator import BoundingBox, area_m2, bounding_box
from app.domain.models.geometry import (
    AREA_KINDS,
    FULL_TURN_DEG,
    MAX_DIMENSION_M,
    MIN_DIMENSION_M,
    BedFrameGeometry,
    Geometry,
    round_length,
)

#: How ``Site.hardiness_zone`` was determined (REQ-039). ``manual`` is never
#: overwritten by the automatic refresh; ``derived_*`` values are recomputed.
HardinessZoneSource = Literal["manual", "derived_gps", "derived_postal", "frostline_us"]

#: ``<number><a|b>`` USDA half-zone label.
_HARDINESS_ZONE_PATTERN = re.compile(r"^\d{1,2}[ab]$")

# ── Garden-plan defaults (REQ-053) ──────────────────────────────────────────

#: Snap grid of a new plan, 10 cm (GP-FR-011).
DEFAULT_GRID_M = 0.10
#: Neighbourhood factor for ``adjacent_to`` derivation (GP-FR-130): 1.5 × the larger
#: spacing — the diagonal (√2) is a neighbour, the next-but-one triangle neighbour (1.73) is not.
DEFAULT_ADJACENCY_FACTOR = 1.5
#: Grid pitch assumed for a legacy slot grid (REQ-053 §9.2a): 0.30 m, an 11-litre pot.
#: Migration v0093 reads ``Location.pitch_m`` and falls back to this value; the model
#: default is that same assumption, written down once more because the migration
#: support module must not be imported by a domain model.
DEFAULT_PITCH_M = 0.30
#: Geometry kinds a site boundary may take (REQ-053 §9.5: rect, polygon).
BOUNDARY_KINDS: frozenset[GeometryKind] = frozenset({GeometryKind.RECT, GeometryKind.POLYGON})
#: Geometry kind each slot role requires (REQ-053 §20.5): a position is a point, a row a
#: polyline, a zone a polygon.
SLOT_ROLE_KINDS: dict[SlotRole, GeometryKind] = {
    SlotRole.POSITION: GeometryKind.POINT,
    SlotRole.ROW: GeometryKind.POLYLINE,
    SlotRole.ZONE: GeometryKind.POLYGON,
}


class TapWaterProfile(BaseModel):
    ec_ms: float = Field(ge=0, le=2.0)
    ph: float = Field(ge=3.0, le=10.0)
    alkalinity_ppm: float = Field(default=0, ge=0, le=500)
    gh_ppm: float = Field(default=0, ge=0, le=1000)
    calcium_ppm: float = Field(default=0, ge=0, le=500)
    magnesium_ppm: float = Field(default=0, ge=0, le=200)
    chlorine_ppm: float = Field(default=0, ge=0, le=5)
    chloramine_ppm: float = Field(default=0, ge=0, le=5)
    measurement_date: date | None = None
    source_note: str | None = None


class RoWaterProfile(BaseModel):
    ec_ms: float = Field(default=0.02, ge=0, le=0.5)
    ph: float = Field(default=6.5, ge=3.0, le=10.0)


class SiteWaterConfig(BaseModel):
    has_ro_system: bool = False
    tap_water_profile: TapWaterProfile | None = None
    ro_water_profile: RoWaterProfile | None = None


class SitePlan(BaseModel):
    """The garden plan of a site (REQ-053 §20.2), embedded in :class:`Site`.

    A site without a ``plan`` is a site without a garden plan (the pre-REQ-053
    behaviour). ``boundary`` is the garden outline in the plan frame (§9.2) and
    may be absent — an indoor site keeps no outline and relies on containment in
    its locations (§9.2a). ``plan_revision`` counts structural changes (GP-NFR-007)
    and is raised by the plan service, never by a client.
    """

    boundary: Geometry | None = None
    #: Compass azimuth of geographic north, clockwise, ``0 = +y`` (GP-FR-015) — the
    #: opposite sense of ``rotation_deg``; convert with named helpers, never ad hoc.
    north_angle_deg: float = 0.0
    default_grid_m: float = Field(default=DEFAULT_GRID_M, gt=0, le=10.0)
    adjacency_factor: float = Field(default=DEFAULT_ADJACENCY_FACTOR, gt=0, le=10.0)
    plan_revision: int = Field(default=0, ge=0)
    plan_updated_at: datetime | None = None
    #: Account key of the last structural change; the account erasure replaces it (GP-NFR-055, ``ErasureEngine``).
    plan_updated_by: str | None = None

    @field_validator("north_angle_deg")
    @classmethod
    def validate_north_angle(cls, value: float) -> float:
        if not 0.0 <= value < FULL_TURN_DEG:
            raise ValueError(f"north_angle_deg must lie within 0..{FULL_TURN_DEG} (exclusive), got {value}.")
        rounded = round_length(value)
        return 0.0 if rounded == FULL_TURN_DEG else rounded

    @field_validator("boundary")
    @classmethod
    def validate_boundary_kind(cls, value: Geometry | None) -> Geometry | None:
        if value is not None and value.kind not in BOUNDARY_KINDS:
            raise ValueError(f"A site boundary must be a rect or polygon, got {value.kind}.")
        return value


class SoilProfile(BaseModel):
    """The v1 soil profile of a bed location (REQ-053 §15.1, GP-FR-120/121).

    Three independent axes — grain size (``soil_texture``), filling
    (``growing_medium_kind``) and state (``conditions``) — plus the last known
    measurements. Everything is optional and defaults to *unknown* where the
    enum has that value; no agronomic value is invented (E-10). The v2 fields
    (``stone_content_class``, ``target_ph``, ``established_on``, ``mulch_factor`` …)
    arrive with the soil work package.
    """

    growing_medium_kind: GrowingMediumKind | None = None
    soil_texture: SoilTexture = SoilTexture.UNKNOWN
    drainage: SoilDrainage = SoilDrainage.UNKNOWN
    site_water_regime: SiteWaterRegime = SiteWaterRegime.UNKNOWN
    conditions: list[SoilConditionFlag] = Field(default_factory=list)
    #: REQ-019 substrate for ``raised_bed_mix`` / ``potting_mix`` (GP-FR-121).
    substrate_key: str | None = None
    ph: float | None = Field(default=None, ge=0.0, le=14.0)
    ph_method: PhMethod | None = None
    ec_ms_cm: float | None = Field(default=None, ge=0.0)
    humus_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("conditions")
    @classmethod
    def validate_conditions_unique(cls, value: list[SoilConditionFlag]) -> list[SoilConditionFlag]:
        if len(set(value)) != len(value):
            raise ValueError("conditions must not repeat a flag")
        return value


#: A ``position`` slot is one plant place (legacy tent grids held up to 20 pots per cell).
MAX_POSITION_CAPACITY = 20
#: A ``row`` or ``zone`` slot stands for an area: its capacity is the plants the layout fits (GP-FR-064). A bed of
#: 1 000 m² sown at 5 cm holds far more than 20, so the bound is the batch ceiling of positions, not 20.
MAX_AREA_CAPACITY = 100_000


class Slot(BaseModel):
    """A plant place within a location.

    Carries **no** ``tenant_key`` (#2107): its tenant is its location's site's, and
    the field it used to declare was never written — every document held ``""``,
    which read as "global" to any check that trusted it (#1397). Ownership is
    resolved slot → location → site (``location_ownership.resolve_owned_slot``).

    The legacy ``(row, col)`` grid cell is gone from the model (REQ-053 O-02,
    #2324): migration v0093 derived a bed-frame ``point`` geometry plus
    ``row_index``/``sequence`` from it, and the fields below read them (WP 1.7).
    Stored documents **keep** the attribute — v0093 copies, it does not move; the
    model ignores it on read (``extra="ignore"``) and the repository's merge update
    never strips an undeclared key, so it stays as the source for a later catch-up
    run. ``geometry`` is optional: a slot created between v0093 and this model is
    *unplaced* (``None``), and the substitute layout of §9.2a is a later wave.

    ``geometry`` is expressed in the **bed frame** of the slot's location (§9.2):
    the origin is the bed's anchor, so moving or rotating the bed changes one
    document, not every slot. Its kind follows ``slot_role`` (§20.5).
    """

    key: str | None = Field(default=None, alias="_key")
    slot_id: str
    location_key: str = ""
    capacity_plants: int = Field(default=1, ge=1, le=MAX_AREA_CAPACITY)
    currently_occupied: bool = False
    last_sanitization: datetime | None = None
    # ── Garden plan (REQ-053 §20.5) ──
    slot_role: SlotRole = SlotRole.POSITION
    geometry: BedFrameGeometry | None = None
    #: Row of a layout the slot belongs to (0-based), when it was placed by one.
    row_index: int | None = Field(default=None, ge=0)
    #: 1-based rank within the location (§20.5 ``R2P05 → 11``), for stable ordering.
    sequence: int | None = Field(default=None, ge=1)
    geometry_source: GeometrySource | None = None
    #: Pot volume in litres (W-016): in a tent the pot, not the spacing, limits the plant.
    container_volume_l: float | None = Field(default=None, gt=0)
    #: Direct sowing recorded on a ``row``/``zone`` slot before plants exist (§11.3 "gesät").
    sown_at: date | None = None
    #: Set when the run that used the slot was closed (GP-FR-055); archived slots are history.
    archived_at: datetime | None = None
    planned_spacing_cm: float | None = Field(default=None, gt=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("slot_id")
    @classmethod
    def validate_slot_id(cls, v: str) -> str:
        if v != v.upper():
            raise ValueError("Slot ID must be all uppercase")
        if "_" not in v:
            raise ValueError("Slot ID must follow format 'LOCATION_POSITION' (e.g., 'TENT01_A1')")
        return v

    @model_validator(mode="after")
    def validate_capacity_matches_role(self) -> Self:
        if self.slot_role is SlotRole.POSITION and self.capacity_plants > MAX_POSITION_CAPACITY:
            raise ValueError(f"A position slot holds at most {MAX_POSITION_CAPACITY} plants.")
        return self

    @model_validator(mode="after")
    def validate_geometry_matches_role(self) -> Self:
        if self.geometry is not None:
            required = SLOT_ROLE_KINDS[self.slot_role]
            if self.geometry.kind is not required:
                raise ValueError(
                    f"A slot with role {self.slot_role} needs a {required} geometry, got {self.geometry.kind}."
                )
        return self


class Location(BaseModel):
    """A place within a site (room, tent, bed …).

    Carries **no** ``tenant_key`` (#2107), for the reason :class:`Slot` gives: the
    site is the tenant anchor (``location_ownership.require_owned_site``). Legacy
    documents may still hold a ``tenant_key`` stamped by migration v0004; it is
    ignored on read, and v0087 unsets it (the repository's merge update does not —
    an undeclared key survives every PUT).

    The legacy ``(L, W, H)`` extent triple is gone from the model as well (REQ-053
    O-02, #2324): v0093 derived a ``rect`` geometry and ``height_m`` from it, and
    the fields below read them (WP 1.7). As for :class:`Slot`, stored documents
    keep the attribute and the model ignores it on read. ``geometry`` is optional:
    a location without one stays in every list (GP-ACC-035) and is *unplaced* on
    the plan.

    ``geometry`` is expressed in the plan frame (§9.2) and must enclose an area
    (rect, circle, polygon — §9.5). ``area_m2`` and ``bbox`` are **derived** from
    it whenever it is set (GP-FR-006/007, GP-ACC-035); without a geometry
    ``area_m2`` stays the manually maintained value and ``bbox`` is ``None``.
    """

    key: str | None = Field(default=None, alias="_key")
    name: str
    site_key: str = ""
    parent_location_key: str | None = None
    location_type_key: str = ""
    depth: int = 0
    path: str = ""
    area_m2: float = Field(ge=0)
    orientation: Orientation | None = None
    light_type: LightType = LightType.NATURAL
    irrigation_system: IrrigationSystem = IrrigationSystem.MANUAL
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
    tank_key: str | None = None
    #: Frost exposure override (Issue #706, additive — defaults keep legacy
    #: locations valid). ``None`` inherits frost exposure from the parent site
    #: type (current behaviour, no backfill); ``True`` forces the location to be
    #: treated as frost-exposed; ``False`` forces it as protected/indoor.
    frost_exposed: bool | None = None
    # ── Garden plan (REQ-053 §20.3, §10.1) ──
    description: str | None = Field(default=None, max_length=1000)
    geometry: Geometry | None = None
    #: Height of a raised bed or planter in metres (GP-FR-043); bounded like a width (V-01).
    height_m: float | None = Field(default=None, ge=MIN_DIMENSION_M, le=MAX_DIMENSION_M)
    #: ``[min_x, min_y, max_x, max_y]`` in the plan frame, derived from ``geometry`` (GP-FR-007).
    bbox: BoundingBox | None = None
    #: Bed lifecycle (§7.4); meaningful for bed types, carried inertly by the others.
    bed_status: BedStatus = BedStatus.ACTIVE
    sun_exposure: SunExposure = SunExposure.UNKNOWN
    irrigation_zone_key: str | None = None
    soil_profile: SoilProfile | None = None
    #: Free text, no markdown (§10.1).
    notes: str | None = Field(default=None, max_length=4000)
    #: Locked against accidental moves in the editor (GP-FR-032).
    locked: bool = False
    z_order: int = 0
    #: Grid pitch assumed for legacy slots of this location (§9.2a, migration v0093).
    pitch_m: float = Field(default=DEFAULT_PITCH_M, ge=MIN_DIMENSION_M, le=MAX_DIMENSION_M)
    #: Permanent crop (asparagus, berry shrubs): excluded from crop rotation (GP-FR-137, W-013).
    rotation_exempt: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("lights_on", "lights_off")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is not None:
            if not re.match(r"^\d{2}:\d{2}$", v):
                raise ValueError("Time must be in HH:MM format")
            hours, minutes = v.split(":")
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                raise ValueError("Invalid time value")
        return v

    @field_validator("geometry")
    @classmethod
    def validate_geometry_kind(cls, value: Geometry | None) -> Geometry | None:
        if value is not None and value.kind not in AREA_KINDS:
            raise ValueError(f"A location geometry must enclose an area (rect, circle, polygon), got {value.kind}.")
        return value

    @model_validator(mode="after")
    def derive_from_geometry(self) -> Self:
        """GP-ACC-035: a set geometry overwrites ``area_m2`` and yields ``bbox``; none clears ``bbox``."""
        if self.geometry is None:
            self.bbox = None
        else:
            self.area_m2 = area_m2(self.geometry)
            self.bbox = bounding_box(self.geometry)
        return self


class Site(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str
    type: SiteType = SiteType.INDOOR
    gps_coordinates: tuple[float, float] | None = None
    #: Legacy free-text climate zone (REQ-002). REQ-039 introduces the structured
    #: ``hardiness_zone`` below; both are kept in sync so legacy consumers keep
    #: reading ``climate_zone`` while the winter-hardiness ampel prefers the
    #: derived zone.
    climate_zone: str = ""
    #: Manually maintained unless ``plan.boundary`` is set — then derived from it (REQ-053 §20.2).
    total_area_m2: float = Field(default=0.0, ge=0)
    timezone: str = "UTC"
    water_config: SiteWaterConfig | None = None
    # ── Hardiness zone (REQ-039, additive — defaults keep legacy sites valid) ──
    #: Structured USDA half-zone label (e.g. ``"7a"``), or ``None`` when unknown.
    hardiness_zone: str | None = None
    hardiness_zone_source: HardinessZoneSource = "manual"
    hardiness_zone_resolved_at: datetime | None = None
    #: Mean annual minimum temperature (°C) the zone was derived from (REQ-041
    #: climate normals); ``None`` for a manually set or not-yet-resolved zone.
    mean_annual_minimum_c: float | None = None
    # ── Frost dates (REQ-015 §3.8) ──
    last_frost_date_avg: date | None = None
    first_frost_date_avg: date | None = None
    eisheilige_date: date | None = None
    # REQ-046 §2.1 — derived, denormalized view of the active source names from
    # :WeatherSourceConfig ([e.source_name for e in sources if e.enabled]); kept
    # for legacy consumers. New consumers read :WeatherSourceConfig.
    weather_source_priority: list[str] = Field(default_factory=list)
    # ── Garden plan (REQ-053 §20.2) — ``None`` is a site without a plan ──
    plan: SitePlan | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("gps_coordinates")
    @classmethod
    def validate_gps(cls, v: tuple[float, float] | None) -> tuple[float, float] | None:
        if v is not None:
            lat, lon = v
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lon <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return v

    @field_validator("hardiness_zone")
    @classmethod
    def validate_hardiness_zone(cls, v: str | None) -> str | None:
        if v is not None and not _HARDINESS_ZONE_PATTERN.match(v):
            raise ValueError("Hardiness zone must match '<number><a|b>' (e.g. '7a')")
        return v

    @model_validator(mode="after")
    def derive_total_area(self) -> Self:
        """``total_area_m2`` is computed from the boundary when one is set (REQ-053 §20.2, GP-ACC-001)."""
        if self.plan is not None and self.plan.boundary is not None:
            self.total_area_m2 = area_m2(self.plan.boundary)
        return self
