"""The bed template: a reusable bed shape that "Place from template" copies into a plan (REQ-053 §20.12; WP 7.8, #2474).

A template is **master data with two owners**: a tenant's own template carries that tenant's ``tenant_key``; a
*system* template (the standard sizes of GP-FR-045, shipped by migration v0101 under a fixed ``_key``) carries
``tenant_key = None`` and is read by every tenant (the ``null`` global marker of §20.12 - not the empty string,
which §20.13 names as the leak of #706/#1397). A tenant can neither write nor delete a global template; only a
platform admin can (§21.8 "Beetvorlage").

``default_geometry`` is expressed in the **bed frame** (§9.2, V-01) and turned by its own ``rotation_deg``. Its
anchor - the centre of a circle, the first vertex of a polygon, the lower-left corner of a rectangle - is
*conventionally* at the origin (the system templates of v0101 and the editor's "save as template" write it there),
but nothing here requires it: an anchor stored elsewhere is accepted and has no effect, because placing a template
(WP 7.9, ``template_placement_calculator.place_geometry``) puts the anchor at the clicked point - a rectangle's or
circle's stored ``origin`` is replaced, a polygon is shifted by its first vertex - and turns the shape by the
requested angle on top.

**Agronomic values (E-10).** ``default_layout`` and ``soil_profile_defaults`` are stored exactly as the author
sent them; the system templates carry ``null`` for both - no spacing or soil value is invented for them.

**What a template never carries.** No reference to another tenant's data: ``soil_profile_defaults`` holds the
soil *axes* (medium, texture, drainage, water regime, conditions) and neither a ``substrate_key`` (a reference)
nor a measurement (a state of one bed) nor a free-text note (which could name a person). ``created_by`` is the
account that created a tenant template; it is erased with the account (GP-NFR-055) and never shown in a response.

``recurring_task_templates`` is a list of ``task_templates`` keys, **stored only**: placing a template copies
nothing from it (operator decision of 2026-10-19, #2466 item 9). The service resolves every key under the tenant
(GP-NFR-058) so a foreign key cannot be parked here; a system template, which every tenant reads, admits global
task templates only (#2529).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.common.enums import GrowingMediumKind, SiteWaterRegime, SoilConditionFlag, SoilDrainage, SoilTexture
from app.domain.calculators.geometry_calculator import validate_geometry
from app.domain.models.geometry import AREA_KINDS, BedFrameGeometry
from app.domain.models.site import SoilProfile

#: GP-FR-043: the height of a raised bed or planter, in metres.
MIN_TEMPLATE_HEIGHT_M = 0.1
MAX_TEMPLATE_HEIGHT_M = 1.5
#: §20.12 ``default_layout``: spacings in centimetres, the same range a planting layout accepts.
MIN_SPACING_CM = 5.0
MAX_SPACING_CM = 1500.0
#: ``recurring_task_templates[]``: a template brings a handful of tasks, not a calendar.
MAX_RECURRING_TASK_TEMPLATES = 20
#: A tenant's catalogue is bounded like every other list (GP-NFR-017 style): the list route pages inside this.
MAX_TEMPLATES_PER_TENANT = 200
#: 422 when ``location_type_key`` names a type that is no bed type - on a template write and when placing one.
ERROR_NOT_A_BED_TYPE = "bed_template.not_a_bed_type"

#: A stored key of another document: a short non-empty string (the database decides what exists).
TaskTemplateKey = Annotated[str, StringConstraints(min_length=1, max_length=200)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DefaultLayout(_Strict):
    """The default spacing of a template (§20.12). ``null`` = not stated (E-10)."""

    row_spacing_cm: float | None = Field(default=None, ge=MIN_SPACING_CM, le=MAX_SPACING_CM)
    spacing_cm: float | None = Field(default=None, ge=MIN_SPACING_CM, le=MAX_SPACING_CM)


class SoilProfileDefaults(_Strict):
    """The soil axes a template pre-fills on a placed bed (GP-FR-044 "Bodenprofil-Vorgabe").

    A subset of :class:`~app.domain.models.site.SoilProfile` on purpose: the axes describe *what kind of bed
    this is*; ``substrate_key`` is a reference, the measurements and ``rotation_reset_at`` are the state of one
    bed, and ``notes`` is free text. Each of those stays with the placed bed.
    """

    growing_medium_kind: GrowingMediumKind | None = None
    soil_texture: SoilTexture = SoilTexture.UNKNOWN
    drainage: SoilDrainage = SoilDrainage.UNKNOWN
    site_water_regime: SiteWaterRegime = SiteWaterRegime.UNKNOWN
    conditions: list[SoilConditionFlag] = Field(default_factory=list)

    @field_validator("conditions")
    @classmethod
    def validate_conditions_unique(cls, value: list[SoilConditionFlag]) -> list[SoilConditionFlag]:
        if len(set(value)) != len(value):
            raise ValueError("conditions must not repeat a flag")
        return value

    def to_soil_profile(self) -> SoilProfile:
        """The copy a placed bed receives (every field a plain value, nothing shared with the template)."""
        return SoilProfile(
            growing_medium_kind=self.growing_medium_kind,
            soil_texture=self.soil_texture,
            drainage=self.drainage,
            site_water_regime=self.site_water_regime,
            conditions=list(self.conditions),
        )


def _check_default_geometry(geometry: BedFrameGeometry) -> BedFrameGeometry:
    """A bed encloses an area (rect, circle, polygon) and a polygon does not cross itself (V-02)."""
    if geometry.kind not in AREA_KINDS:
        raise ValueError(f"default_geometry must enclose an area (rect, circle, polygon), got {geometry.kind}.")
    problems = validate_geometry(geometry)
    if problems:
        raise ValueError(problems[0])
    return geometry


def _check_unique_task_templates(value: list[TaskTemplateKey]) -> list[TaskTemplateKey]:
    if len(set(value)) != len(value):
        raise ValueError("recurring_task_templates must not repeat a key")
    return value


class BedTemplate(BaseModel):
    """A stored ``bed_templates`` document (§20.12)."""

    model_config = ConfigDict(populate_by_name=True)

    key: str | None = Field(default=None, alias="_key")
    #: ``None`` = a system (global) template; otherwise the owning tenant (E-01).
    tenant_key: str | None = None
    name: str = Field(min_length=1, max_length=200)
    #: A ``location_types`` row; it decides what the placed bed is (bed, raised bed, planter ...).
    location_type_key: str = Field(min_length=1, max_length=200)
    default_geometry: BedFrameGeometry
    height_m: float | None = Field(default=None, ge=MIN_TEMPLATE_HEIGHT_M, le=MAX_TEMPLATE_HEIGHT_M)
    default_layout: DefaultLayout = Field(default_factory=DefaultLayout)
    soil_profile_defaults: SoilProfileDefaults | None = None
    #: ``task_templates`` keys, stored only (see the module docstring).
    recurring_task_templates: list[TaskTemplateKey] = Field(
        default_factory=list, max_length=MAX_RECURRING_TASK_TEMPLATES
    )
    #: Account key of the author of a tenant template; erased with the account, never in a response.
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("A template needs a name.")
        return stripped

    @field_validator("default_geometry")
    @classmethod
    def validate_default_geometry(cls, value: BedFrameGeometry) -> BedFrameGeometry:
        return _check_default_geometry(value)

    @field_validator("recurring_task_templates")
    @classmethod
    def validate_task_templates_unique(cls, value: list[TaskTemplateKey]) -> list[TaskTemplateKey]:
        return _check_unique_task_templates(value)

    @property
    def is_system(self) -> bool:
        """Whether this is a global template (``tenant_key`` is ``null``, §20.12)."""
        return self.tenant_key is None


class BedTemplateInput(_Strict):
    """``POST /bed-templates``: what a client sends. ``tenant_key`` and ``created_by`` are the caller's, never sent."""

    name: str = Field(min_length=1, max_length=200)
    location_type_key: str = Field(min_length=1, max_length=200)
    default_geometry: BedFrameGeometry
    height_m: float | None = Field(default=None, ge=MIN_TEMPLATE_HEIGHT_M, le=MAX_TEMPLATE_HEIGHT_M)
    default_layout: DefaultLayout = Field(default_factory=DefaultLayout)
    soil_profile_defaults: SoilProfileDefaults | None = None
    recurring_task_templates: list[TaskTemplateKey] = Field(
        default_factory=list, max_length=MAX_RECURRING_TASK_TEMPLATES
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("A template needs a name.")
        return stripped

    @field_validator("default_geometry")
    @classmethod
    def validate_default_geometry(cls, value: BedFrameGeometry) -> BedFrameGeometry:
        return _check_default_geometry(value)

    @field_validator("recurring_task_templates")
    @classmethod
    def validate_task_templates_unique(cls, value: list[TaskTemplateKey]) -> list[TaskTemplateKey]:
        return _check_unique_task_templates(value)


class BedTemplatePatch(_Strict):
    """``PATCH /bed-templates/{key}``: only the fields present change; ``null`` clears ``height_m`` and
    ``soil_profile_defaults`` (the two optional ones) and is refused on the others."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    location_type_key: str | None = Field(default=None, min_length=1, max_length=200)
    default_geometry: BedFrameGeometry | None = None
    height_m: float | None = Field(default=None, ge=MIN_TEMPLATE_HEIGHT_M, le=MAX_TEMPLATE_HEIGHT_M)
    default_layout: DefaultLayout | None = None
    soil_profile_defaults: SoilProfileDefaults | None = None
    recurring_task_templates: list[TaskTemplateKey] | None = Field(
        default=None, max_length=MAX_RECURRING_TASK_TEMPLATES
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("A template needs a name.")
        return stripped

    @field_validator("default_geometry")
    @classmethod
    def validate_default_geometry(cls, value: BedFrameGeometry | None) -> BedFrameGeometry | None:
        return None if value is None else _check_default_geometry(value)

    @field_validator("recurring_task_templates")
    @classmethod
    def validate_task_templates_unique(cls, value: list[TaskTemplateKey] | None) -> list[TaskTemplateKey] | None:
        return None if value is None else _check_unique_task_templates(value)

    @model_validator(mode="after")
    def refuse_clearing_a_required_field(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("A PATCH needs at least one field.")
        for name in ("name", "location_type_key", "default_geometry", "default_layout", "recurring_task_templates"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be cleared.")
        return self
