"""REQ-053 §20.4 (WP 1.7, #2326) — ``GardenObject`` and its ``props`` union.

Every object class has exactly one props model, selected by ``object_type``;
the geometry kind is restricted per class (§9.5); ``bbox`` is derived; and the
model carries no ``tenant_key`` (E-01).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.enums import GardenObjectType, GeometryKind
from app.domain.models.garden_object import (
    ALLOWED_GEOMETRY_KINDS,
    POINT_OBJECT_RADIUS_M,
    PROPS_BY_TYPE,
    GardenObject,
    TreeProps,
    WaterSourceProps,
)

_POINT = {"kind": "point", "origin": [9.7, 0.4]}
_CIRCLE = {"kind": "circle", "origin": [3.0, 3.0], "radius_m": 2.0}
_LINE = {"kind": "polyline", "points": [[0, 5], [12, 5]], "width_m": 0.8}
_RECT = {"kind": "rect", "origin": [0, 0], "width_m": 4, "length_m": 3}

#: One valid ``(geometry, props)`` per class — the fixture every class test is built from.
_VALID: dict[GardenObjectType, tuple[dict, dict]] = {
    GardenObjectType.PATH: (_LINE, {"surface": "gravel"}),
    GardenObjectType.LAWN: (_RECT, {}),
    GardenObjectType.TREE: (_CIRCLE, {"crown_radius_m": 2.0, "foliage": "deciduous"}),
    GardenObjectType.SHRUB: (_CIRCLE, {"height_m": 1.5, "opacity": "semi"}),
    GardenObjectType.BUILDING: (_RECT, {"height_m": 3.0, "ridge_height_m": 6.0}),
    GardenObjectType.WALL: (_LINE, {"height_m": 1.8, "opacity": "opaque"}),
    GardenObjectType.FENCE: (_LINE, {"opacity": "open"}),
    GardenObjectType.TRELLIS: (_LINE, {"height_m": 1.8}),
    GardenObjectType.WATER_SOURCE: (_POINT, {"water_source_kind": "rain_barrel", "capacity_liters": 300}),
    GardenObjectType.COMPOST: (_RECT, {}),
    GardenObjectType.STORAGE: (_RECT, {}),
    GardenObjectType.OTHER: (_POINT, {}),
    GardenObjectType.WINDOW: (_LINE, {"sill_height_m": 0.9, "glazing": "double"}),
    GardenObjectType.DOOR: (_LINE, {"swing": "inward"}),
    GardenObjectType.FURNITURE: (_RECT, {}),
    GardenObjectType.LAMP: (_POINT, {"kind": "grow_light", "height_m": 1.2, "ppfd_ref": 400}),
}


def _object(object_type: GardenObjectType, **overrides) -> GardenObject:
    geometry, props = _VALID[object_type]
    data = {"site_key": "site_1", "object_type": object_type, "label": "x", "geometry": geometry, "props": props}
    data.update(overrides)
    return GardenObject(**data)


class TestTheUnionCoversEveryClass:
    def test_every_object_type_has_a_props_model_and_an_allowed_kind_set(self) -> None:
        assert set(PROPS_BY_TYPE) == set(GardenObjectType) == set(ALLOWED_GEOMETRY_KINDS) == set(_VALID)

    @pytest.mark.parametrize("object_type", list(GardenObjectType))
    def test_a_valid_object_of_each_class_selects_its_props_model(self, object_type: GardenObjectType) -> None:
        obj = _object(object_type)
        assert type(obj.props) is PROPS_BY_TYPE[object_type]
        assert obj.props.object_type is object_type

    @pytest.mark.parametrize("object_type", list(GardenObjectType))
    def test_a_stored_document_round_trips(self, object_type: GardenObjectType) -> None:
        obj = _object(object_type)
        doc = obj.model_dump(by_alias=True, mode="json")
        assert doc["props"]["object_type"] == object_type.value
        assert GardenObject.model_validate(doc) == obj

    def test_the_spec_example_validates(self) -> None:
        """§20.4 verbatim: ``props`` without a discriminator, ``bbox`` spanning the drawn 0.25 m symbol."""
        obj = GardenObject.model_validate(
            {
                "_key": "go_91ab",
                "site_key": "site_7f3a",
                "parent_location_key": None,
                "object_type": "water_source",
                "label": "Regentonne Ost",
                "geometry": {"kind": "point", "origin": [9.7, 0.4]},
                "props": {"water_source_kind": "rain_barrel", "capacity_liters": 300, "last_refilled_at": None},
                "locked": False,
                "z_order": 5,
                "notes": "",
                "created_by": "u_sabine",
            }
        )
        assert isinstance(obj.props, WaterSourceProps)
        assert obj.bbox == (9.45, 0.15, 9.95, 0.65)
        assert POINT_OBJECT_RADIUS_M == 0.25
        assert obj.off_site is False


class TestConsistency:
    def test_props_of_another_class_are_refused(self) -> None:
        with pytest.raises(ValidationError, match="props are for"):
            _object(GardenObjectType.TREE, props={"object_type": "path", "surface": "gravel"})

    def test_a_field_of_another_class_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden|Extra inputs"):
            _object(GardenObjectType.PATH, props={"surface": "gravel", "crown_radius_m": 1})

    def test_required_props_are_required(self) -> None:
        with pytest.raises(ValidationError, match="water_source_kind"):
            _object(GardenObjectType.WATER_SOURCE, props={})
        with pytest.raises(ValidationError, match="crown_radius_m"):
            _object(GardenObjectType.TREE, props={})
        assert TreeProps.model_fields["crown_radius_m"].is_required()

    @pytest.mark.parametrize(
        ("object_type", "geometry"),
        [
            (GardenObjectType.TREE, _RECT),
            (GardenObjectType.WATER_SOURCE, _CIRCLE),
            (GardenObjectType.FENCE, _RECT),
            (GardenObjectType.STORAGE, _CIRCLE),
            (GardenObjectType.FURNITURE, _POINT),
        ],
    )
    def test_the_geometry_kind_is_restricted_per_class(self, object_type: GardenObjectType, geometry: dict) -> None:
        with pytest.raises(ValidationError, match="may be drawn as"):
            _object(object_type, geometry=geometry)

    def test_other_takes_any_kind_but_needs_a_label(self) -> None:
        assert ALLOWED_GEOMETRY_KINDS[GardenObjectType.OTHER] == frozenset(GeometryKind)
        with pytest.raises(ValidationError, match="needs a label"):
            _object(GardenObjectType.OTHER, label="  ")

    @pytest.mark.parametrize(
        "geometry",
        [
            {"kind": "circle", "origin": [3, 3], "radius_m": 0},
            {"kind": "circle", "origin": [-1, 3], "radius_m": 1},
            {"kind": "circle", "origin": [3, 3], "radius_m": 1, "rotation_deg": 10},
        ],
    )
    def test_v01_is_enforced_through_the_object(self, geometry: dict) -> None:
        with pytest.raises(ValidationError) as exc:
            _object(GardenObjectType.TREE, geometry=geometry)
        assert all(tuple(e["loc"])[0] == "geometry" for e in exc.value.errors())

    def test_bbox_is_derived_in_the_plan_frame(self) -> None:
        obj = _object(GardenObjectType.TREE)
        assert obj.bbox == (1.0, 1.0, 5.0, 5.0)
        line = _object(GardenObjectType.FENCE)  # the stroke (± width_m / 2 = 0.4) is part of what is drawn
        assert line.bbox == (-0.4, 4.6, 12.4, 5.4)

    def test_off_site_and_no_tenant(self) -> None:
        obj = _object(GardenObjectType.BUILDING, off_site=True)
        assert obj.off_site is True
        assert "tenant_key" not in GardenObject.model_fields


class TestReviewFollowUps:
    def test_the_drawn_circle_overwrites_the_crown_radius(self) -> None:
        tree = _object(GardenObjectType.TREE, props={"crown_radius_m": 9.0})

        assert tree.props.crown_radius_m == 2.0  # type: ignore[union-attr]

    def test_a_window_sill_may_sit_at_floor_level(self) -> None:
        window = _object(GardenObjectType.WINDOW, props={"sill_height_m": 0})

        assert window.props.sill_height_m == 0  # type: ignore[union-attr]

    def test_the_create_schema_rejects_foreign_props_at_the_request(self) -> None:
        from app.api.v1.garden_objects.schemas import GardenObjectCreate

        with pytest.raises(ValidationError):
            GardenObjectCreate(object_type="tree", geometry=_CIRCLE, props={"surface": "gravel"})
        ok = GardenObjectCreate(object_type="tree", geometry=_CIRCLE, props={"crown_radius_m": 2.0})
        assert ok.props.object_type is GardenObjectType.TREE

    def test_the_response_keeps_account_keys_server_side(self) -> None:
        from app.api.v1.garden_objects.schemas import garden_object_to_response

        response = garden_object_to_response(_object(GardenObjectType.LAWN, created_by="acct_1"))

        assert "created_by" not in response.model_dump()
