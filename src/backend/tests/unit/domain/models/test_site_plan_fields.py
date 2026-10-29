"""REQ-053 WP 1.7 (#2326) — ``Site.plan``, the plan fields of ``Location`` and ``Slot``.

V-01 (``geometry.invalid``) on every carrier: a geometry the value type refuses is
refused through the carrier too, with the carrier's field in the error location.
GP-ACC-035: a geometry overwrites ``area_m2`` and yields ``bbox``; a location
without one keeps its manual area and stays valid (the catch-up window of #2323).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.enums import BedStatus, GeometrySource, SlotRole, SoilTexture, SunExposure
from app.domain.models.geometry import GeometryFrame, parse_geometry
from app.domain.models.site import (
    DEFAULT_ADJACENCY_FACTOR,
    DEFAULT_GRID_M,
    DEFAULT_PITCH_M,
    Location,
    Site,
    SitePlan,
    Slot,
    SoilProfile,
)

_RECT = {"kind": "rect", "origin": [1.0, 1.0], "width_m": 2.0, "length_m": 1.0, "rotation_deg": 90.0}
_BOUNDARY = {"kind": "polygon", "points": [[0, 0], [10, 0], [10, 6], [0, 6]]}


def _errors(exc: ValidationError) -> list[tuple[tuple, str]]:
    return [(tuple(e["loc"]), e["type"]) for e in exc.errors()]


class TestSitePlan:
    def test_a_site_without_a_plan_is_the_legacy_site(self) -> None:
        site = Site(name="Garten")
        assert site.plan is None
        assert site.total_area_m2 == 0.0

    def test_defaults_follow_the_spec(self) -> None:
        plan = SitePlan()
        assert (plan.north_angle_deg, plan.default_grid_m, plan.adjacency_factor, plan.plan_revision) == (
            0.0,
            DEFAULT_GRID_M,
            DEFAULT_ADJACENCY_FACTOR,
            0,
        )
        assert (DEFAULT_GRID_M, DEFAULT_ADJACENCY_FACTOR) == (0.10, 1.5)

    def test_total_area_is_derived_from_the_boundary(self) -> None:
        """GP-ACC-001: a 10 × 6 m boundary makes ``total_area_m2 = 60.0`` whatever the body said."""
        site = Site(name="Garten", total_area_m2=12.0, plan={"boundary": _BOUNDARY})
        assert site.total_area_m2 == 60.0

    def test_total_area_stays_manual_without_a_boundary(self) -> None:
        assert Site(name="Garten", total_area_m2=12.0, plan={}).total_area_m2 == 12.0

    def test_boundary_v01_is_enforced_through_the_site(self) -> None:
        with pytest.raises(ValidationError) as exc:
            Site(name="Garten", plan={"boundary": {"kind": "polygon", "points": [[0, 0], [1000.5, 0], [1, 1]]}})
        assert any(loc[:2] == ("plan", "boundary") for loc, _ in _errors(exc.value))

    def test_boundary_must_be_rect_or_polygon(self) -> None:
        with pytest.raises(ValidationError, match="rect or polygon"):
            SitePlan(boundary={"kind": "circle", "origin": [5, 5], "radius_m": 3})

    @pytest.mark.parametrize("angle", [-0.1, 360.0, 400.0])
    def test_north_angle_outside_the_compass_is_refused(self, angle: float) -> None:
        with pytest.raises(ValidationError, match="north_angle_deg"):
            SitePlan(north_angle_deg=angle)

    def test_north_angle_rounds_to_the_storage_precision(self) -> None:
        assert SitePlan(north_angle_deg=15.0004).north_angle_deg == 15.0
        assert SitePlan(north_angle_deg=359.9999).north_angle_deg == 0.0

    def test_plan_round_trips_through_a_document(self) -> None:
        site = Site(name="Garten", plan={"boundary": _BOUNDARY, "north_angle_deg": 15, "plan_revision": 42})
        doc = site.model_dump(by_alias=True, mode="json")
        assert doc["plan"]["boundary"]["kind"] == "polygon"
        assert Site.model_validate(doc) == site


class TestLocationGeometry:
    def test_a_location_without_geometry_stays_valid_and_unplaced(self) -> None:
        """GP-ACC-035 / #2323: the catch-up window leaves ``geometry = None``; the manual area survives."""
        loc = Location(name="Beet", area_m2=3.5)
        assert (loc.geometry, loc.bbox, loc.area_m2) == (None, None, 3.5)

    def test_a_geometry_overwrites_the_area_and_yields_the_bbox(self) -> None:
        """GP-ACC-035 with the §20.1 worked example: 2 × 1 m at (1, 1) rotated 90° → bbox [0, 1, 1, 3]."""
        loc = Location(name="Beet", area_m2=99.0, geometry=_RECT)
        assert loc.area_m2 == 2.0
        assert loc.bbox == (0.0, 1.0, 1.0, 3.0)

    def test_a_circle_bed_is_an_area(self) -> None:
        loc = Location(name="Kübel", area_m2=0, geometry={"kind": "circle", "origin": [2, 2], "radius_m": 0.5})
        assert loc.area_m2 == pytest.approx(0.785, abs=0.001)
        assert loc.bbox == (1.5, 1.5, 2.5, 2.5)

    @pytest.mark.parametrize(
        "geometry",
        [
            {"kind": "point", "origin": [1, 1]},
            {"kind": "polyline", "points": [[0, 0], [1, 1]], "width_m": 0.5},
        ],
    )
    def test_a_location_geometry_must_enclose_an_area(self, geometry: dict) -> None:
        with pytest.raises(ValidationError, match="enclose an area"):
            Location(name="Beet", area_m2=1.0, geometry=geometry)

    @pytest.mark.parametrize(
        "geometry",
        [
            {"kind": "rect", "origin": [0, 0], "width_m": 0.0, "length_m": 1.0},
            {"kind": "rect", "origin": [-1, 0], "width_m": 1.0, "length_m": 1.0},
            {"kind": "rect", "origin": [0, 0], "width_m": 1.0, "length_m": 1.0, "rotation_deg": 360},
            {"kind": "polygon", "points": [[0, 0], [1, 0]]},
            {"kind": "circle", "origin": [0, 0], "radius_m": 1, "rotation_deg": 0},
            {"kind": "trapezoid", "origin": [0, 0]},
        ],
    )
    def test_v01_is_enforced_through_the_location(self, geometry: dict) -> None:
        with pytest.raises(ValidationError) as exc:
            Location(name="Beet", area_m2=1.0, geometry=geometry)
        assert all(loc[0] == "geometry" for loc, _ in _errors(exc.value))

    def test_a_stored_document_is_re_derived_on_read(self) -> None:
        """A document whose stored ``area_m2`` drifted from its geometry reads back consistent."""
        loc = Location.model_validate({"_key": "l1", "name": "Beet", "area_m2": 7.0, "geometry": _RECT, "bbox": None})
        assert (loc.area_m2, loc.bbox) == (2.0, (0.0, 1.0, 1.0, 3.0))

    def test_a_stored_legacy_dimensions_triple_is_still_ignored(self) -> None:
        loc = Location.model_validate({"name": "Tent", "area_m2": 1.0, "dimensions": [1.2, 1.2, 2.0]})
        assert not hasattr(loc, "dimensions")


class TestLocationPlanningFields:
    def test_defaults(self) -> None:
        loc = Location(name="Beet", area_m2=1.0)
        assert loc.bed_status is BedStatus.ACTIVE
        assert loc.sun_exposure is SunExposure.UNKNOWN
        assert (loc.locked, loc.z_order, loc.rotation_exempt) == (False, 0, False)
        assert loc.pitch_m == DEFAULT_PITCH_M == 0.30
        assert (loc.soil_profile, loc.notes, loc.description, loc.height_m, loc.irrigation_zone_key) == (
            None,
            None,
            None,
            None,
            None,
        )

    def test_sun_exposure_has_five_values_including_deep_shade(self) -> None:
        assert {e.value for e in SunExposure} == {"full_sun", "partial_shade", "shade", "deep_shade", "unknown"}

    @pytest.mark.parametrize("height", [0.0, 0.001, 1000.5])
    def test_height_is_bounded_like_a_dimension(self, height: float) -> None:
        with pytest.raises(ValidationError, match="height_m"):
            Location(name="Hochbeet", area_m2=1.0, height_m=height)

    def test_height_in_range(self) -> None:
        assert Location(name="Hochbeet", area_m2=1.0, height_m=0.8).height_m == 0.8

    def test_soil_profile_v1_fields(self) -> None:
        loc = Location(
            name="Beet",
            area_m2=1.0,
            soil_profile={
                "growing_medium_kind": "raised_bed_mix",
                "soil_texture": "loam",
                "conditions": ["compacted", "stony"],
                "substrate_key": "sub_1",
                "ph": 6.8,
                "ph_method": "cacl2",
                "humus_percent": 8.0,
            },
        )
        assert loc.soil_profile is not None
        assert loc.soil_profile.soil_texture is SoilTexture.LOAM
        assert loc.soil_profile.drainage.value == "unknown"
        assert loc.soil_profile.site_water_regime.value == "unknown"

    def test_soil_profile_refuses_an_impossible_ph_and_a_repeated_flag(self) -> None:
        with pytest.raises(ValidationError, match="ph"):
            SoilProfile(ph=14.5)
        with pytest.raises(ValidationError, match="repeat"):
            SoilProfile(conditions=["stony", "stony"])

    def test_notes_are_bounded(self) -> None:
        with pytest.raises(ValidationError, match="notes"):
            Location(name="Beet", area_m2=1.0, notes="x" * 4001)


class TestSlotGeometry:
    def test_a_slot_without_geometry_is_unplaced(self) -> None:
        slot = Slot(slot_id="BEET_1")
        assert slot.geometry is None
        assert slot.slot_role is SlotRole.POSITION
        assert (slot.row_index, slot.sequence, slot.geometry_source) == (None, None, None)

    def test_a_position_is_a_bed_frame_point_and_may_be_negative(self) -> None:
        """§9.2: the bed frame has its origin at the bed's anchor, so a circular bed's slots sit left of it."""
        slot = Slot(slot_id="BEET_1", geometry={"kind": "point", "origin": [-0.3, 0.3]})
        assert slot.geometry is not None
        assert slot.geometry.origin == (-0.3, 0.3)

    def test_the_bed_frame_does_not_depend_on_the_caller_s_context(self) -> None:
        """A slot read from the database (no validation context) must accept what the migration stored."""
        stored = parse_geometry({"kind": "point", "origin": [-1.0, -1.0]}, frame=GeometryFrame.BED)
        doc = {"_key": "s1", "slot_id": "BEET_1", "geometry": stored.model_dump(mode="json")}
        assert Slot.model_validate(doc).geometry == stored

    def test_v01_is_enforced_through_the_slot(self) -> None:
        """GP-ACC-058 (slot point at x = -1000.5 is refused; the frame itself is covered by the neighbours)."""
        with pytest.raises(ValidationError) as exc:
            Slot(slot_id="BEET_1", geometry={"kind": "point", "origin": [-1000.5, 0]})
        assert all(loc[0] == "geometry" for loc, _ in _errors(exc.value))
        with pytest.raises(ValidationError):
            Slot(slot_id="BEET_1", slot_role="zone", geometry={"kind": "polygon", "points": [[0, 0], [1, 0]]})

    @pytest.mark.parametrize(
        ("role", "geometry"),
        [
            ("position", {"kind": "polyline", "points": [[0, 0], [1, 0]], "width_m": 0.1}),
            ("row", {"kind": "point", "origin": [0, 0]}),
            ("zone", {"kind": "polyline", "points": [[0, 0], [1, 0]], "width_m": 0.1}),
            ("zone", {"kind": "rect", "origin": [0, 0], "width_m": 1, "length_m": 1}),
        ],
    )
    def test_the_geometry_kind_follows_the_slot_role(self, role: str, geometry: dict) -> None:
        with pytest.raises(ValidationError, match="needs a"):
            Slot(slot_id="BEET_1", slot_role=role, geometry=geometry)

    def test_a_row_is_a_polyline_and_a_zone_a_polygon(self) -> None:
        row = Slot(
            slot_id="BEET_R1",
            slot_role="row",
            geometry={"kind": "polyline", "points": [[0, 0.3], [2, 0.3]], "width_m": 0.1},
        )
        zone = Slot(
            slot_id="BEET_Z1", slot_role="zone", geometry={"kind": "polygon", "points": [[0, 0], [1, 0], [1, 1]]}
        )
        assert (row.geometry.kind.value, zone.geometry.kind.value) == ("polyline", "polygon")  # type: ignore[union-attr]

    def test_the_migrated_grid_fields_read_back(self) -> None:
        """What v0093 wrote for a 3 × 3 tent (§9.2a): middle slot at (0.30, 0.30), row 1, sequence 5."""
        doc = {
            "_key": "s5",
            "slot_id": "TENT01_B2",
            "geometry": {"kind": "point", "origin": [0.3, 0.3]},
            "row_index": 1,
            "sequence": 5,
            "geometry_source": "migrated_grid",
            "position": [1, 1],
        }
        slot = Slot.model_validate(doc)
        assert (slot.row_index, slot.sequence, slot.geometry_source) == (1, 5, GeometrySource.MIGRATED_GRID)
        assert not hasattr(slot, "position")

    def test_planning_fields_are_bounded(self) -> None:
        with pytest.raises(ValidationError, match="container_volume_l"):
            Slot(slot_id="BEET_1", container_volume_l=0)
        with pytest.raises(ValidationError, match="sequence"):
            Slot(slot_id="BEET_1", sequence=0)
        with pytest.raises(ValidationError, match="row_index"):
            Slot(slot_id="BEET_1", row_index=-1)
        slot = Slot(slot_id="BEET_1", container_volume_l=11, planned_spacing_cm=30, sown_at="2026-04-01")
        assert slot.sown_at is not None and slot.sown_at.isoformat() == "2026-04-01"
