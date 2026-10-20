"""REQ-053 WP 7.8 (#2474) - the bed template model: shapes, bounds, what a template must never carry."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.enums import GrowingMediumKind, SoilDrainage
from app.domain.models.bed_template import (
    BedTemplate,
    BedTemplateInput,
    BedTemplatePatch,
    DefaultLayout,
    SoilProfileDefaults,
)

_RECT = {"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0}


def _template(**overrides) -> BedTemplate:
    return BedTemplate(**{"name": "Bed", "location_type_key": "bed", "default_geometry": _RECT, **overrides})


class TestTheStoredTemplate:
    def test_a_minimal_template_is_global_until_it_names_a_tenant(self) -> None:
        assert _template().is_system is True
        assert _template(tenant_key="ten_a").is_system is False

    def test_the_name_is_stripped_and_not_blank(self) -> None:
        assert _template(name="  Herb bed ").name == "Herb bed"
        with pytest.raises(ValidationError):
            _template(name="   ")

    @pytest.mark.parametrize("height", [0.09, 1.51, 0, -1])
    def test_the_height_is_bounded_by_gp_fr_043(self, height: float) -> None:
        with pytest.raises(ValidationError):
            _template(height_m=height)

    @pytest.mark.parametrize("height", [0.1, 0.8, 1.5])
    def test_the_height_bounds_are_inclusive(self, height: float) -> None:
        assert _template(height_m=height).height_m == height

    @pytest.mark.parametrize("value", [4.9, 1500.1, 0])
    def test_a_spacing_outside_5_to_1500_cm_is_refused(self, value: float) -> None:
        with pytest.raises(ValidationError):
            DefaultLayout(row_spacing_cm=value)
        with pytest.raises(ValidationError):
            DefaultLayout(spacing_cm=value)

    def test_the_spacing_bounds_are_inclusive_and_null_is_not_stated(self) -> None:
        assert DefaultLayout(row_spacing_cm=5, spacing_cm=1500).spacing_cm == 1500
        assert DefaultLayout().model_dump() == {"row_spacing_cm": None, "spacing_cm": None}

    def test_the_geometry_lives_in_the_bed_frame_so_it_may_reach_below_zero(self) -> None:
        polygon = {"kind": "polygon", "points": [[0, 0], [2, 0], [2, 1], [-0.5, 1]], "rotation_deg": 0}
        assert _template(default_geometry=polygon).default_geometry.kind == "polygon"

    @pytest.mark.parametrize(
        "geometry",
        [
            {"kind": "point", "origin": [0, 0]},
            {"kind": "polyline", "points": [[0, 0], [1, 1]], "width_m": 0.2},
        ],
        ids=["point", "polyline"],
    )
    def test_a_shape_that_encloses_no_area_is_no_bed(self, geometry: dict) -> None:
        with pytest.raises(ValidationError):
            _template(default_geometry=geometry)

    def test_a_polygon_that_crosses_itself_is_refused(self) -> None:
        bow_tie = {"kind": "polygon", "points": [[0, 0], [2, 2], [2, 0], [0, 2]], "rotation_deg": 0}
        with pytest.raises(ValidationError):
            _template(default_geometry=bow_tie)

    def test_a_dimension_outside_v01_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            _template(default_geometry={**_RECT, "width_m": 0.001})

    def test_task_template_keys_must_not_repeat_and_are_capped(self) -> None:
        with pytest.raises(ValidationError):
            _template(recurring_task_templates=["a", "a"])
        with pytest.raises(ValidationError):
            _template(recurring_task_templates=[f"t{i}" for i in range(21)])


class TestWhatATemplateNeverCarries:
    def test_the_soil_defaults_hold_the_axes_and_nothing_else(self) -> None:
        for forbidden in ("substrate_key", "ph", "ec_ms_cm", "humus_percent", "rotation_reset_at", "notes"):
            with pytest.raises(ValidationError):
                SoilProfileDefaults(**{forbidden: "x"})

    def test_the_soil_defaults_become_a_soil_profile_copy(self) -> None:
        defaults = SoilProfileDefaults(growing_medium_kind=GrowingMediumKind.RAISED_BED_MIX, drainage=SoilDrainage.GOOD)

        profile = defaults.to_soil_profile()

        assert (profile.growing_medium_kind, profile.drainage) == (GrowingMediumKind.RAISED_BED_MIX, SoilDrainage.GOOD)
        assert profile.substrate_key is None and profile.ph is None

    def test_a_body_cannot_name_its_tenant_or_author(self) -> None:
        for field in ("tenant_key", "created_by"):
            with pytest.raises(ValidationError):
                BedTemplateInput(name="x", location_type_key="bed", default_geometry=_RECT, **{field: "x"})
            with pytest.raises(ValidationError):
                BedTemplatePatch(**{field: "x"})


class TestThePatch:
    def test_it_needs_a_field(self) -> None:
        with pytest.raises(ValidationError):
            BedTemplatePatch()

    def test_null_clears_the_optional_fields_only(self) -> None:
        assert BedTemplatePatch(height_m=None).model_fields_set == {"height_m"}
        assert BedTemplatePatch(soil_profile_defaults=None).model_fields_set == {"soil_profile_defaults"}
        for required in ("name", "location_type_key", "default_geometry", "default_layout", "recurring_task_templates"):
            with pytest.raises(ValidationError):
                BedTemplatePatch(**{required: None})
