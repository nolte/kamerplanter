"""``SiteConditions`` (REQ-053 section 10.2, WP 3.9): defaults, bounds, and the frost-risk copy."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.enums import AccessSide, FrostRisk, HeatRetention, SiteFlag, SunProfileSource, SunWindow, WindExposure
from app.domain.models.site import Location, Microclimate, SiteConditions, SunProfile


def _filled() -> SiteConditions:
    """Every field away from its default, so a copy that forgets one is visible."""
    return SiteConditions(
        sun_profile=SunProfile(
            sun_window=SunWindow.AFTERNOON,
            direct_sun_hours_summer=5.5,
            foliage_shade_in_summer=True,
            source=SunProfileSource.COMPUTED,
        ),
        microclimate=Microclimate(frost_risk=FrostRisk.NORMAL, cold_air_pocket=True, heat_retention=HeatRetention.WALL),
        wind_exposure=WindExposure.EXPOSED,
        slope_deg=12.5,
        aspect_deg=190.0,
        access_sides=[AccessSide.NORTH, AccessSide.WEST],
        flags=[SiteFlag.ROOT_COMPETITION],
    )


class TestDefaults:
    def test_everything_is_optional_and_unknown(self) -> None:
        conditions = SiteConditions()

        assert conditions.sun_profile.sun_window is SunWindow.UNKNOWN
        assert conditions.microclimate.frost_risk is FrostRisk.UNKNOWN
        assert conditions.microclimate.heat_retention is HeatRetention.UNKNOWN
        assert conditions.wind_exposure is WindExposure.UNKNOWN
        assert (conditions.slope_deg, conditions.aspect_deg) == (None, None)
        assert conditions.access_sides == [] and conditions.flags == []

    def test_a_location_carries_none_until_somebody_enters_something(self) -> None:
        assert Location(name="Beet", site_key="s", area_m2=1.0).site_conditions is None


class TestBounds:
    @pytest.mark.parametrize(
        "bad",
        [
            {"slope_deg": -1},
            {"slope_deg": 91},
            {"aspect_deg": 360},
            {"aspect_deg": -0.1},
            {"sun_profile": {"direct_sun_hours_summer": 25}},
            {"sun_profile": {"direct_sun_hours_summer": -1}},
            {"access_sides": ["N", "N"]},
            {"flags": ["root_competition", "root_competition"]},
            {"wind_exposure": "gale"},
        ],
    )
    def test_a_value_outside_the_vocabulary_is_refused(self, bad: dict[str, object]) -> None:
        with pytest.raises(ValidationError):
            SiteConditions.model_validate(bad)

    def test_the_edges_are_accepted(self) -> None:
        conditions = SiteConditions.model_validate(
            {"slope_deg": 90, "aspect_deg": 359.9, "sun_profile": {"direct_sun_hours_summer": 24}}
        )

        assert (conditions.slope_deg, conditions.aspect_deg) == (90, 359.9)


class TestWithFrostRisk:
    def test_only_the_risk_changes(self) -> None:
        original = _filled()

        changed = original.with_frost_risk(FrostRisk.HIGH)

        assert changed.microclimate.frost_risk is FrostRisk.HIGH
        expected = original.model_dump()
        expected["microclimate"]["frost_risk"] = FrostRisk.HIGH
        assert changed.model_dump() == expected

    def test_the_original_is_not_touched(self) -> None:
        original = _filled()

        original.with_frost_risk(FrostRisk.LOW)

        assert original.microclimate.frost_risk is FrostRisk.NORMAL

    def test_a_field_added_later_is_carried_too(self) -> None:
        """The copy walks ``model_fields``: a field nobody remembered to list is not silently reset."""
        assert set(_filled().with_frost_risk(FrostRisk.UNKNOWN).model_dump()) == set(SiteConditions.model_fields)

    def test_the_lists_are_not_shared_with_the_original(self) -> None:
        original = _filled()

        changed = original.with_frost_risk(FrostRisk.HIGH)
        changed.access_sides.append(AccessSide.EAST)

        assert original.access_sides == [AccessSide.NORTH, AccessSide.WEST]
