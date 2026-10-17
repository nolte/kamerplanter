"""Non-plantable objects of a garden plan (REQ-053 §20.4, §9.5, §9.8).

A ``GardenObject`` is a path, a tree, a water barrel, a fence — anything the
plan draws that is neither a location nor a slot. It belongs to its site
(``site_key``) and carries **no** ``tenant_key`` (E-01, #2107): like a location,
its tenant is its site's, and the service resolves ownership through
``location_ownership.require_owned_site`` (§22.3). Nothing is planted on it
(V-16); a task may hang off it (``has_task``).

``props`` is a discriminated union over ``object_type``: every class has its own
Pydantic model with the fields §9.5 / §9.8 / §20.4 name for it, so a
``water_source`` cannot be stored without its ``water_source_kind`` and a
``tree`` cannot carry a ``surface``. The discriminator inside ``props`` is the
object's ``object_type``; a client may omit it there (the spec's example does)
and the model fills it in, but a *mismatching* value is refused.

``geometry`` lives in the plan frame (§9.2) and its kind is restricted per
class (§9.5 "Geometrieformen"); ``bbox`` is derived from it (GP-FR-007).
``off_site = True`` marks scenery outside the garden boundary (the neighbour's
house, a tree behind the fence) and exempts the object from containment (V-03).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import (
    FoliageType,
    GardenObjectType,
    GeometryKind,
    LampKind,
    ObstacleOpacity,
    PathSurface,
    WaterSourceKind,
    WindowGlazing,
)
from app.domain.calculators.geometry_calculator import BoundingBox, bounding_box
from app.domain.models.geometry import MAX_DIMENSION_M, MIN_DIMENSION_M, Geometry, round_length

# ── Geometry kinds per class (REQ-053 §9.5, §9.8) ────────────────────────────

_AREA = frozenset({GeometryKind.RECT, GeometryKind.POLYGON})
_LINE = frozenset({GeometryKind.POLYLINE})

#: Which geometry kinds an object of each class may take (§9.5 column "Geometrieformen").
ALLOWED_GEOMETRY_KINDS: dict[GardenObjectType, frozenset[GeometryKind]] = {
    GardenObjectType.PATH: frozenset({GeometryKind.POLYLINE, GeometryKind.POLYGON}),
    GardenObjectType.LAWN: _AREA,
    GardenObjectType.TREE: frozenset({GeometryKind.CIRCLE}),
    GardenObjectType.SHRUB: frozenset({GeometryKind.CIRCLE, GeometryKind.POLYLINE}),
    GardenObjectType.BUILDING: _AREA,
    GardenObjectType.WALL: _LINE,
    GardenObjectType.FENCE: _LINE,
    GardenObjectType.TRELLIS: _LINE,
    GardenObjectType.WATER_SOURCE: frozenset({GeometryKind.POINT}),
    GardenObjectType.COMPOST: frozenset({GeometryKind.RECT, GeometryKind.CIRCLE}),
    GardenObjectType.STORAGE: frozenset({GeometryKind.RECT}),
    GardenObjectType.OTHER: frozenset(GeometryKind),
    # Indoor (§9.8): a window or door is a line in the wall, furniture a footprint, a lamp a point or fixture.
    GardenObjectType.WINDOW: _LINE,
    GardenObjectType.DOOR: _LINE,
    GardenObjectType.FURNITURE: frozenset({GeometryKind.RECT}),
    GardenObjectType.LAMP: frozenset({GeometryKind.POINT, GeometryKind.RECT}),
}

#: A point object (water source, lamp) is drawn as a circle of this fixed radius (§9.5
#: "circle r = 0,25 m fest"), so its ``bbox`` spans the drawn symbol, not the bare point.
POINT_OBJECT_RADIUS_M = 0.25

#: A height above ground in metres, bounded like a plan dimension (V-01).
_HeightM = Annotated[float, Field(ge=MIN_DIMENSION_M, le=MAX_DIMENSION_M)]

#: A sill may sit at floor level (a French window), so zero is allowed there.
_SillHeightM = Annotated[float, Field(ge=0, le=MAX_DIMENSION_M)]


# ── Props per class ───────────────────────────────────────────────────────────


class _PropsBase(BaseModel):
    """Unknown keys are an error: a ``surface`` on a tree is a client defect, not data."""

    model_config = {"extra": "forbid"}


class PathProps(_PropsBase):
    object_type: Literal[GardenObjectType.PATH] = GardenObjectType.PATH
    surface: PathSurface | None = None


class LawnProps(_PropsBase):
    object_type: Literal[GardenObjectType.LAWN] = GardenObjectType.LAWN


class TreeProps(_PropsBase):
    """§9.5 / §20.4: crown radius is the drawn circle; height and foliage prepare the shade model (§29)."""

    object_type: Literal[GardenObjectType.TREE] = GardenObjectType.TREE
    species_label: str | None = Field(default=None, max_length=200)
    crown_radius_m: Annotated[float, Field(ge=MIN_DIMENSION_M, le=MAX_DIMENSION_M)]
    height_m: _HeightM | None = None
    crown_base_height_m: _HeightM | None = None
    foliage: FoliageType | None = None


class ShrubProps(_PropsBase):
    """A shrub or hedge is a wind and light obstacle like a fence (GP-FR-163)."""

    object_type: Literal[GardenObjectType.SHRUB] = GardenObjectType.SHRUB
    height_m: _HeightM | None = None
    opacity: ObstacleOpacity | None = None


class BuildingProps(_PropsBase):
    object_type: Literal[GardenObjectType.BUILDING] = GardenObjectType.BUILDING
    #: Eaves height.
    height_m: _HeightM | None = None
    ridge_height_m: _HeightM | None = None


class WallProps(_PropsBase):
    object_type: Literal[GardenObjectType.WALL] = GardenObjectType.WALL
    height_m: _HeightM | None = None
    opacity: ObstacleOpacity | None = None


class FenceProps(_PropsBase):
    object_type: Literal[GardenObjectType.FENCE] = GardenObjectType.FENCE
    height_m: _HeightM | None = None
    opacity: ObstacleOpacity | None = None


class TrellisProps(_PropsBase):
    """Offered in the planting dialog when ``Species.support_required`` (W-005)."""

    object_type: Literal[GardenObjectType.TRELLIS] = GardenObjectType.TRELLIS
    height_m: _HeightM


class WaterSourceProps(_PropsBase):
    object_type: Literal[GardenObjectType.WATER_SOURCE] = GardenObjectType.WATER_SOURCE
    water_source_kind: WaterSourceKind
    capacity_liters: float | None = Field(default=None, gt=0)
    last_refilled_at: datetime | None = None


class CompostProps(_PropsBase):
    object_type: Literal[GardenObjectType.COMPOST] = GardenObjectType.COMPOST


class StorageProps(_PropsBase):
    object_type: Literal[GardenObjectType.STORAGE] = GardenObjectType.STORAGE


class OtherProps(_PropsBase):
    object_type: Literal[GardenObjectType.OTHER] = GardenObjectType.OTHER


class WindowProps(_PropsBase):
    """§9.8: the orientation is derived from the wall and ``north_angle_deg``, never stored."""

    object_type: Literal[GardenObjectType.WINDOW] = GardenObjectType.WINDOW
    sill_height_m: _SillHeightM | None = None
    glazing: WindowGlazing | None = None


class DoorProps(_PropsBase):
    """§9.8 names ``swing`` without a value set; held as bounded free text until the spec fixes one."""

    object_type: Literal[GardenObjectType.DOOR] = GardenObjectType.DOOR
    swing: str | None = Field(default=None, max_length=50)


class FurnitureProps(_PropsBase):
    object_type: Literal[GardenObjectType.FURNITURE] = GardenObjectType.FURNITURE


class LampProps(_PropsBase):
    """§9.8: preparation for a light distribution, no calculation. ``ppfd_ref`` is a reference PPFD in µmol/m²/s."""

    object_type: Literal[GardenObjectType.LAMP] = GardenObjectType.LAMP
    kind: LampKind
    height_m: _HeightM
    ppfd_ref: float | None = Field(default=None, ge=0)


GardenObjectProps = Annotated[
    PathProps
    | LawnProps
    | TreeProps
    | ShrubProps
    | BuildingProps
    | WallProps
    | FenceProps
    | TrellisProps
    | WaterSourceProps
    | CompostProps
    | StorageProps
    | OtherProps
    | WindowProps
    | DoorProps
    | FurnitureProps
    | LampProps,
    Field(discriminator="object_type"),
]

#: ``object_type`` → its props model, for the service and for tests.
PROPS_BY_TYPE: dict[GardenObjectType, type[_PropsBase]] = {
    GardenObjectType.PATH: PathProps,
    GardenObjectType.LAWN: LawnProps,
    GardenObjectType.TREE: TreeProps,
    GardenObjectType.SHRUB: ShrubProps,
    GardenObjectType.BUILDING: BuildingProps,
    GardenObjectType.WALL: WallProps,
    GardenObjectType.FENCE: FenceProps,
    GardenObjectType.TRELLIS: TrellisProps,
    GardenObjectType.WATER_SOURCE: WaterSourceProps,
    GardenObjectType.COMPOST: CompostProps,
    GardenObjectType.STORAGE: StorageProps,
    GardenObjectType.OTHER: OtherProps,
    GardenObjectType.WINDOW: WindowProps,
    GardenObjectType.DOOR: DoorProps,
    GardenObjectType.FURNITURE: FurnitureProps,
    GardenObjectType.LAMP: LampProps,
}


# ── The object ────────────────────────────────────────────────────────────────


def fill_props_discriminator(data: Any) -> Any:
    """Let ``props`` omit its ``object_type`` (the spec's example does) — the object's value is it."""
    if not isinstance(data, dict):
        return data
    props = data.get("props")
    object_type = data.get("object_type")
    if isinstance(props, dict) and object_type is not None and "object_type" not in props:
        data = {**data, "props": {**props, "object_type": object_type}}
    return data


class GardenObject(BaseModel):
    """A non-plantable object on a site's plan (REQ-053 §20.4). No ``tenant_key`` (E-01)."""

    key: str | None = Field(default=None, alias="_key")
    site_key: str = ""
    #: The area the object lies in (a path inside a greenhouse); containment is checked by the service (V-03).
    parent_location_key: str | None = None
    object_type: GardenObjectType
    #: Shown on the plan; required for ``other`` (§9.5), optional elsewhere.
    label: str = Field(default="", max_length=200)
    geometry: Geometry
    #: Derived from ``geometry`` in the plan frame (GP-FR-007).
    bbox: BoundingBox | None = None
    props: GardenObjectProps
    #: Scenery outside the boundary — exempt from V-03, drawn grey, available to the shade model (§9.5).
    off_site: bool = False
    locked: bool = False
    z_order: int = 0
    notes: str | None = Field(default=None, max_length=4000)
    #: Account key; account erasure handles it in WP 4.1.
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def fill_props_discriminator(cls, data: Any) -> Any:
        return fill_props_discriminator(data)

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        if self.props.object_type is not self.object_type:
            raise ValueError(f"props are for {self.props.object_type}, the object is a {self.object_type}.")
        allowed = ALLOWED_GEOMETRY_KINDS[self.object_type]
        if self.geometry.kind not in allowed:
            raise ValueError(
                f"A {self.object_type} may be drawn as {', '.join(sorted(allowed))}, not as {self.geometry.kind}."
            )
        if isinstance(self.props, TreeProps) and self.geometry.kind is GeometryKind.CIRCLE:
            # The drawn circle is the crown (§9.5): one source of the size, overwritten like ``area_m2`` (GP-ACC-035).
            self.props.crown_radius_m = self.geometry.radius_m
        if self.object_type is GardenObjectType.OTHER and not self.label:
            raise ValueError("An object of type 'other' needs a label.")
        min_x, min_y, max_x, max_y = bounding_box(self.geometry)
        if self.geometry.kind is GeometryKind.POINT:
            r = POINT_OBJECT_RADIUS_M
            min_x, min_y, max_x, max_y = min_x - r, min_y - r, max_x + r, max_y + r
        self.bbox = (round_length(min_x), round_length(min_y), round_length(max_x), round_length(max_y))
        return self
