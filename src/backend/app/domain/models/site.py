import math
import re
from datetime import date, datetime
from typing import Annotated, Any, Literal, Self

from pydantic import AllowInfNan, BaseModel, Field, field_validator, model_validator

from app.common.enums import (
    AccessSide,
    BedStatus,
    EcMethod,
    FrostRisk,
    GeometryKind,
    GeometrySource,
    GrowingMediumKind,
    HeatRetention,
    IrrigationSystem,
    LightType,
    Orientation,
    PhMethod,
    SiteFlag,
    SiteType,
    SiteWaterRegime,
    SlotRole,
    SoilConditionFlag,
    SoilDrainage,
    SoilTexture,
    StoneContentClass,
    SunExposure,
    SunProfileSource,
    SunWindow,
    WindExposure,
)
from app.domain.calculators.geometry_calculator import BoundingBox, area_m2, bounding_box
from app.domain.calculators.orientation_calculator import orientation_from_aspect
from app.domain.calculators.reach_calculator import PATH_ACCESS_MAX_DISTANCE_M, REACH_BOTH_SIDES_M, REACH_ONE_SIDE_M
from app.domain.models.geometry import (
    AREA_KINDS,
    FULL_TURN_DEG,
    MAX_COORDINATE_M,
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


#: Largest pixel coordinate or pixel distance an underlay calibration may name (REQ-053 GP-FR-033). A photograph
#: the pipeline admits is far smaller (decode ceiling, NFR-013); the bound keeps a hostile number out of the maths.
MAX_UNDERLAY_PX = 100_000.0
#: Longest real-world distance a calibration may state, in metres (a plan frame is at most 2 × ``MAX_COORDINATE_M``).
MAX_UNDERLAY_DISTANCE_M = 2000.0
#: Two calibration points closer than this are one point: no scale can be read from them.
MIN_UNDERLAY_POINT_GAP_PX = 1.0
#: The faintest opacity a client may store; below it the picture is invisible and the layer pointless.
MIN_UNDERLAY_OPACITY = 0.05

# NaN and the infinities are refused at the model, not by a downstream ``round`` (a sibling change answered 500 on
# ``Infinity``): every number below carries ``AllowInfNan(False)``.
_PixelCoordinate = Annotated[float, AllowInfNan(False), Field(ge=0, le=MAX_UNDERLAY_PX)]
_PlanCoordinate = Annotated[float, AllowInfNan(False), Field(ge=-MAX_COORDINATE_M, le=MAX_COORDINATE_M)]
#: The placement and look of an underlay - shared by the model and the request that sets it, so a number the
#: model refuses is refused at the edge as 422 and never reaches the model as a 500.
UnderlayOrigin = tuple[_PlanCoordinate, _PlanCoordinate]
UnderlayRotation = Annotated[float, AllowInfNan(False), Field(ge=-FULL_TURN_DEG, le=FULL_TURN_DEG)]
UnderlayOpacity = Annotated[float, AllowInfNan(False), Field(ge=MIN_UNDERLAY_OPACITY, le=1.0)]


class UnderlayCalibration(BaseModel):
    """Two points of the picture (pixels) and the real distance between them (metres) - the scale (GP-FR-033)."""

    p1_px: tuple[_PixelCoordinate, _PixelCoordinate]
    p2_px: tuple[_PixelCoordinate, _PixelCoordinate]
    distance_m: Annotated[float, AllowInfNan(False), Field(gt=0, le=MAX_UNDERLAY_DISTANCE_M)]

    @model_validator(mode="after")
    def validate_points_apart(self) -> Self:
        if self.pixel_distance < MIN_UNDERLAY_POINT_GAP_PX:
            raise ValueError("The two calibration points must lie at least one pixel apart.")
        return self

    @property
    def pixel_distance(self) -> float:
        return math.hypot(self.p2_px[0] - self.p1_px[0], self.p2_px[1] - self.p1_px[1])

    @property
    def metres_per_pixel(self) -> float:
        return self.distance_m / self.pixel_distance


class SiteUnderlay(BaseModel):
    """The background picture of the garden plan to trace over (REQ-053 GP-FR-033, WP 7.14).

    Presentation only - never a data source, never part of the JSON export (GP-FR-140) and in the PDF only when
    asked for. ``attachment_key`` names a ``garden_plan_underlay`` attachment of the site's own tenant; the
    calibration, placement and opacity are the site's, so every member sees the same picture. ``origin`` is
    the plan-frame position (metres) of the picture's top-left pixel and ``rotation_deg`` turns the picture
    about it in the plan's own sense (counter-clockwise, y up - the opposite of ``north_angle_deg``). Whether
    the picture is *shown* is each user's choice and is not stored here.
    """

    attachment_key: str = Field(min_length=1, max_length=64)
    calibration: UnderlayCalibration
    origin: UnderlayOrigin = (0.0, 0.0)
    rotation_deg: UnderlayRotation = 0.0
    opacity: UnderlayOpacity = 0.5

    @field_validator("rotation_deg")
    @classmethod
    def normalise_rotation(cls, value: float) -> float:
        rounded = round_length(value % FULL_TURN_DEG)
        return 0.0 if rounded == FULL_TURN_DEG else rounded


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
    #: The background picture to trace over (GP-FR-033, WP 7.14); one per site, never exported.
    underlay: SiteUnderlay | None = None

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


def with_legacy_ec_method(profile: object) -> object:
    """A stored or archived soil profile that holds ``ec_ms_cm`` and no ``ec_method`` reads as ``ec_method = unknown``.

    The rule of the migration (v0105, U-002) for the places the migration cannot reach: a tenant archive written
    before ``ec_method`` existed and a garden-plan backup or import snapshot of the same age. ``unknown`` is comparable
    with nothing, so nothing is guessed; the alternative - refusing the document - would leave a stored bed unreadable
    or a replace-import snapshot unrestorable. A *request* is stricter (the API schema and ``SoilProfile`` itself refuse
    the pair).
    """
    if not isinstance(profile, dict):
        return profile
    data: dict[str, Any] = profile
    if data.get("ec_ms_cm") is not None and data.get("ec_method") is None:
        return {**data, "ec_method": EcMethod.UNKNOWN.value}
    return profile


#: The measured-value fields of a soil profile an analysis can write (REQ-053 §15.1); each pairs with its method
#: field where it has one (``ph_method``, ``ec_method``).
AnalysisField = Literal["ph", "ec_ms_cm", "humus_percent", "caco3_percent"]


class SoilHandValue(BaseModel):
    """One measured-value field as a person set it (#2706): the value (``None`` = cleared), its method, the instant."""

    value: float | None = None
    #: ``ph_method`` / ``ec_method`` of the entry; ``None`` for a field without a method.
    method: str | None = None
    at: datetime


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
    #: How ``ec_ms_cm`` was measured (U-002): required as soon as ``ec_ms_cm`` is set, and a value is only comparable
    #: within one method - the system never converts between methods.
    ec_method: EcMethod | None = None
    humus_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    caco3_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    #: v2 fields (WP 8.7): stored as stated, never derived. ``target_ph`` stays a field only: its derivation from
    #: ``soil_texture`` is on the "stays null" list until research item R-008 (E-10).
    stone_content_class: StoneContentClass = StoneContentClass.UNKNOWN
    target_ph: float | None = Field(default=None, ge=0.0, le=14.0)
    established_on: date | None = None
    #: The ``performed_at`` of the newest soil analysis whose values the profile holds (WP 8.7). Server-owned: only a
    #: soil analysis, its void or its correction moves it; ``PATCH /locations`` keeps the stored value (#2706).
    last_analysis_at: datetime | None = None
    #: Server-owned (#2706): the hand entries of the measured-value fields, per field ``{value, method, at}``. A
    #: ``null`` value is a value cleared by hand. Per field the newest observation wins - the hand entry (``at``) or
    #: the newest open analysis that measured it (``performed_at``); a tie goes to the hand entry. ``None`` = a row
    #: from before the entries; the first derivation classifies its values (see the soil engine).
    hand_values: dict[AnalysisField, SoilHandValue] | None = None
    #: A substrate change resets the crop-rotation history: plantings before this day do not count (GP-FR-131).
    rotation_reset_at: date | None = None
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("conditions")
    @classmethod
    def validate_conditions_unique(cls, value: list[SoilConditionFlag]) -> list[SoilConditionFlag]:
        if len(set(value)) != len(value):
            raise ValueError("conditions must not repeat a flag")
        return value

    @model_validator(mode="after")
    def _ec_needs_its_method(self) -> Self:
        if self.ec_ms_cm is not None and self.ec_method is None:
            raise ValueError("ec_ms_cm needs ec_method: a conductivity is only readable with its extraction method.")
        return self


class SunProfile(BaseModel):
    """When and how long a bed gets direct sun (REQ-053 §10.2, GP-FR-158/159).

    Every field is optional and defaults to *unknown*; nothing here is derived yet (the shading
    calculation is §29). The coarse class itself stays :attr:`Location.sun_exposure`.
    """

    sun_window: SunWindow = SunWindow.UNKNOWN
    direct_sun_hours_summer: float | None = Field(default=None, ge=0.0, le=24.0)
    #: Leaf shade: sunny in spring, shaded in summer (GP-FR-159).
    foliage_shade_in_summer: bool = False
    source: SunProfileSource = SunProfileSource.MANUAL


#: Sun-class defaults (REQ-053 GP-FR-164, confirmed O-17, RHS): direct sun on the reference day, in hours.
#: ``full_sun`` > 6 h, ``partial_shade`` 3-6 h, ``shade`` 2-3 h, ``deep_shade`` < 2 h.
DEFAULT_FULL_SUN_MIN_HOURS = 6.0
DEFAULT_PARTIAL_SHADE_MIN_HOURS = 3.0
DEFAULT_SHADE_MIN_HOURS = 2.0
#: The reference day of the sun classes: midsummer, 21 June (O-17, ``agrobiology-thresholds-req-053.md``).
DEFAULT_SUN_REFERENCE_MONTH = 6
DEFAULT_SUN_REFERENCE_DAY = 21
#: Upper bound of a reach threshold, metres: a bed frame is at most this wide (V-01).
MAX_REACH_THRESHOLD_M = MAX_DIMENSION_M
#: Upper bound of the path-access distance, metres (#2703): a path more than a step away from the bed edge is no
#: place to tend it from; the bound keeps a typo (30 instead of 0.3) from making every path reach every bed.
MAX_PATH_ACCESS_DISTANCE_M = 1.0
#: A leap year, so 29 February is a valid reference day.
_REFERENCE_YEAR = 2000

_PositiveHours = Annotated[float, AllowInfNan(False), Field(gt=0, le=24.0)]
_PositiveMetres = Annotated[float, AllowInfNan(False), Field(gt=0, le=MAX_REACH_THRESHOLD_M)]
_PathDistanceMetres = Annotated[float, AllowInfNan(False), Field(ge=0, le=MAX_PATH_ACCESS_DISTANCE_M)]


class SunClassThresholds(BaseModel):
    """Where the sun classes of a site begin, and the day they refer to (REQ-053 GP-FR-164, WP 8.24).

    Each bound is the **lower** end of its class in hours of direct sun on the reference day: ``full_sun`` is
    *more than* ``full_sun_min_hours``, ``partial_shade`` from ``partial_shade_min_hours`` up to it, ``shade`` from
    ``shade_min_hours`` up to that, and ``deep_shade`` everything below ``shade_min_hours``. The bounds are
    positive and strictly descending, so every class keeps a range. Kamerplanter computes nothing from them
    yet (§29); they define the classes the help texts name.
    """

    full_sun_min_hours: _PositiveHours = DEFAULT_FULL_SUN_MIN_HOURS
    partial_shade_min_hours: _PositiveHours = DEFAULT_PARTIAL_SHADE_MIN_HOURS
    shade_min_hours: _PositiveHours = DEFAULT_SHADE_MIN_HOURS
    reference_month: int = Field(default=DEFAULT_SUN_REFERENCE_MONTH, ge=1, le=12)
    reference_day: int = Field(default=DEFAULT_SUN_REFERENCE_DAY, ge=1, le=31)

    @model_validator(mode="after")
    def validate_descending(self) -> Self:
        if not self.full_sun_min_hours > self.partial_shade_min_hours > self.shade_min_hours:
            raise ValueError(
                "The sun-class bounds must be strictly descending: "
                "full_sun_min_hours > partial_shade_min_hours > shade_min_hours."
            )
        return self

    @model_validator(mode="after")
    def validate_reference_day(self) -> Self:
        try:
            date(_REFERENCE_YEAR, self.reference_month, self.reference_day)
        except ValueError as exc:
            raise ValueError("reference_month and reference_day must name a day of the year.") from exc
        return self


class ReachThresholds(BaseModel):
    """How wide a bed may be before it is out of reach (REQ-053 GP-FR-166, WP 8.24), in metres.

    ``both_sides_m`` applies with access from two opposite sides, ``one_side_m`` with access from one side and
    when the access is unknown (``app.domain.calculators.reach_calculator``). One side never reaches farther
    than two, so ``one_side_m`` may not exceed ``both_sides_m``.

    ``path_access_max_distance_m`` (#2703, operator decision 2026-11-09) is how close a ``path`` object must come to
    a bed edge, edge to edge, to make that side reachable (``reach_calculator.path_access``): 0.3 m by default, 0 m
    (only a touching path) up to :data:`MAX_PATH_ACCESS_DISTANCE_M`. A stored threshold set without it reads the
    default, so no stored document needs a backfill.
    """

    both_sides_m: _PositiveMetres = REACH_BOTH_SIDES_M
    one_side_m: _PositiveMetres = REACH_ONE_SIDE_M
    path_access_max_distance_m: _PathDistanceMetres = PATH_ACCESS_MAX_DISTANCE_M

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.one_side_m > self.both_sides_m:
            raise ValueError("one_side_m must not exceed both_sides_m.")
        return self


class Microclimate(BaseModel):
    """Local climate of a bed (REQ-053 §10.2, GP-FR-162)."""

    frost_risk: FrostRisk = FrostRisk.UNKNOWN
    cold_air_pocket: bool = False
    heat_retention: HeatRetention = HeatRetention.UNKNOWN


class SiteConditions(BaseModel):
    """Site features of a bed beyond the sun class (REQ-053 §10.2, issue 75), an embedded value type.

    All optional, default *unknown*. It replaces the boolean :attr:`Location.frost_exposed` by
    ``microclimate.frost_risk`` (migration v0098 copies the old value; the old field stays until the
    frost readers are moved over, see ``app.domain.engines.frost_exposure_resolver``).
    """

    sun_profile: SunProfile = Field(default_factory=SunProfile)
    microclimate: Microclimate = Field(default_factory=Microclimate)
    wind_exposure: WindExposure = WindExposure.UNKNOWN
    slope_deg: float | None = Field(default=None, ge=0.0, le=90.0)
    aspect_deg: float | None = Field(default=None, ge=0.0, lt=360.0)
    access_sides: list[AccessSide] = Field(default_factory=list)
    flags: list[SiteFlag] = Field(default_factory=list)

    def with_frost_risk(self, frost_risk: FrostRisk) -> Self:
        """A copy with ``microclimate.frost_risk`` set; everything else (also fields added later) is carried over."""
        values = {name: getattr(self, name) for name in SiteConditions.model_fields}
        part = {name: getattr(self.microclimate, name) for name in Microclimate.model_fields}
        values["microclimate"] = Microclimate(**{**part, "frost_risk": frost_risk})
        return type(self)(**values)

    @field_validator("access_sides", "flags")
    @classmethod
    def _no_repeats(cls, value: list[AccessSide] | list[SiteFlag]) -> list[AccessSide] | list[SiteFlag]:
        if len(set(value)) != len(value):
            raise ValueError("a list of site features must not repeat an entry")
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
    container_volume_l: float | None = Field(default=None, gt=0, allow_inf_nan=False)
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


#: Photos one bed may carry (REQ-053 GP-FR-051, WP 8.18). The closest precedent is the plant gallery's default
#: limit, ``STORAGE_MAX_PHOTOS_PER_INSTANCE = 50`` (REQ-034 §3): a bed is photographed about as often as a plant.
MAX_PHOTOS_PER_LOCATION = 50
#: Longest attachment id a photo reference may hold (attachment keys are ArangoDB ``_key`` values).
MAX_PHOTO_REF_LENGTH = 64


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
    #: The bed template this bed was placed from (REQ-053 §21.7, WP 7.9, #2475): **provenance only** - a copy of
    #: the template's fields was taken, so later edits to the template change nothing here; deleting the template
    #: unsets it (#2528). A system (global) key or one of the tenant's own; the export carries it, the import
    #: resolves it or clears it as provenance (never a refusal).
    template_key: str | None = None
    soil_profile: SoilProfile | None = None
    #: Sun profile, microclimate, wind, slope … of the bed (§10.2, WP 3.9); ``None`` = nothing entered.
    site_conditions: SiteConditions | None = None
    #: Free text, no markdown (§10.1).
    notes: str | None = Field(default=None, max_length=4000)
    #: Locked against accidental moves in the editor (GP-FR-032).
    locked: bool = False
    z_order: int = 0
    #: Grid pitch assumed for legacy slots of this location (§9.2a, migration v0093).
    pitch_m: float = Field(default=DEFAULT_PITCH_M, ge=MIN_DIMENSION_M, le=MAX_DIMENSION_M)
    #: Permanent crop (asparagus, berry shrubs): excluded from crop rotation (GP-FR-137, W-013). Wins over
    #: ``rotation_enabled``.
    rotation_exempt: bool = False
    #: Per-bed crop-rotation switch (GP-FR-137 "je Beet einschaltbar", #2544), additive: ``None`` = the type default
    #: (off for ``planter``/``tent``/``shelf``, on for every other type), ``True`` = on, ``False`` = off.
    rotation_enabled: bool | None = None
    #: The bed's photos (REQ-053 GP-FR-051, WP 8.18): ids of ``location`` attachments of the site's tenant, newest
    #: first, without repeats. Written only by ``LocationPhotoService`` (never by an edit body, a plan batch or the
    #: plan's JSON file); presentation, so not part of the plan revision and never in the plan export.
    photo_refs: list[Annotated[str, Field(min_length=1, max_length=MAX_PHOTO_REF_LENGTH)]] = Field(
        default_factory=list, max_length=MAX_PHOTOS_PER_LOCATION
    )
    #: The photo shown for the bed; one of ``photo_refs`` or ``None`` (cleared when that photo is removed).
    cover_photo_ref: str | None = Field(default=None, min_length=1, max_length=MAX_PHOTO_REF_LENGTH)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_photos(self) -> Self:
        """No photo twice, and the cover is one of the bed's photos (WP 8.18)."""
        if len(set(self.photo_refs)) != len(self.photo_refs):
            raise ValueError("photo_refs must not repeat a reference.")
        if self.cover_photo_ref is not None and self.cover_photo_ref not in self.photo_refs:
            raise ValueError("cover_photo_ref must be one of photo_refs.")
        return self

    @field_validator("soil_profile", mode="before")
    @classmethod
    def _stored_profile_without_ec_method(cls, value: object) -> object:
        return with_legacy_ec_method(value)

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

    @model_validator(mode="after")
    def derive_orientation_from_aspect(self) -> Self:
        """GP-FR-017/168: a set ``site_conditions.aspect_deg`` derives ``orientation`` (8 compass sectors).

        Derived in the model, like ``area_m2`` from the geometry, so every write path - ``PATCH /locations``,
        ``PUT /locations``, the plan batch, the import - stores the same value without a call site to forget.
        Without an aspect the orientation is the manually maintained value and is never touched.
        """
        aspect = self.site_conditions.aspect_deg if self.site_conditions is not None else None
        if aspect is not None:
            self.orientation = orientation_from_aspect(aspect)
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
    # ── Garden-planning thresholds (REQ-053 GP-FR-164/166, WP 8.24) — ``None`` = the defaults ──
    #: Stored only once somebody sets them; a site edit that does not send them keeps the stored value.
    sun_class_thresholds: SunClassThresholds | None = None
    reach_thresholds: ReachThresholds | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @property
    def effective_sun_class_thresholds(self) -> SunClassThresholds:
        """The site's sun-class bounds, the RHS defaults where none are stored."""
        return self.sun_class_thresholds or SunClassThresholds()

    @property
    def effective_reach_thresholds(self) -> ReachThresholds:
        """The site's reach thresholds, 1.2 / 0.6 m and a 0.3 m path distance where none are stored."""
        return self.reach_thresholds or ReachThresholds()

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
