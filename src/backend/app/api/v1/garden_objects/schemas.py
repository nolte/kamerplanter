"""Request/response schemas of garden objects (REQ-053 §20.4, §21.2).

Schemas only (WP 1.7, #2326): the routes arrive with WP 1.9 (GardenObject CRUD)
and the plan batch (WP 1.8). ``site_key`` is deliberately absent from the create
body — T-01 (§22.3): it always comes from the path or the stored document, never
from the request.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums import GardenObjectType
from app.domain.models.garden_object import (
    GardenObject,
    GardenObjectProps,
    fill_props_discriminator,
)
from app.domain.models.geometry import Geometry


class GardenObjectCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "object_type": "tree",
                    "label": "Apple tree",
                    "geometry": {"kind": "circle", "origin": [3.0, 3.0], "radius_m": 2.0},
                    "props": {"crown_radius_m": 2.0, "foliage": "deciduous"},
                }
            ]
        }
    )

    object_type: GardenObjectType
    label: str = Field(default="", max_length=200)
    geometry: Geometry
    #: Typed by ``object_type``; the discriminator inside may be omitted (filled before validation),
    #: so a malformed or foreign-class prop is a 422 at the request, not a 500 in the service.
    props: GardenObjectProps
    parent_location_key: str | None = None
    off_site: bool = False
    locked: bool = False
    z_order: int = 0
    notes: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="before")
    @classmethod
    def fill_props_discriminator(cls, data: Any) -> Any:
        return fill_props_discriminator(data)


class GardenObjectResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "go_1",
                    "site_key": "site_1",
                    "object_type": "water_source",
                    "label": "Rain barrel",
                    "geometry": {"kind": "point", "origin": [9.7, 0.4]},
                    "props": {"object_type": "water_source", "water_source_kind": "rain_barrel"},
                }
            ]
        }
    )

    key: str
    site_key: str
    parent_location_key: str | None = None
    object_type: GardenObjectType
    label: str = ""
    geometry: Geometry
    #: ``[min_x, min_y, max_x, max_y]`` in the plan frame (GP-FR-007), derived.
    bbox: tuple[float, float, float, float] | None = None
    props: GardenObjectProps
    off_site: bool = False
    locked: bool = False
    z_order: int = 0
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def garden_object_to_response(garden_object: GardenObject) -> GardenObjectResponse:
    """The response of a stored object; ``created_by`` stays server-side (an account key, §26)."""
    return GardenObjectResponse(
        key=garden_object.key or "",
        site_key=garden_object.site_key,
        parent_location_key=garden_object.parent_location_key,
        object_type=garden_object.object_type,
        label=garden_object.label,
        geometry=garden_object.geometry,
        bbox=garden_object.bbox,
        props=garden_object.props,
        off_site=garden_object.off_site,
        locked=garden_object.locked,
        z_order=garden_object.z_order,
        notes=garden_object.notes,
        created_at=garden_object.created_at,
        updated_at=garden_object.updated_at,
    )
