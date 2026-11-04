"""WP 8.7 (#2650) — what an analysis writes into the bed profile and how the series read: per method, no conversion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domain.engines.soil_analysis_engine import AnalysisEvent, build_series, is_newer, method_of, profile_patch
from app.domain.models.care_event import CareEventInput, Measurement
from app.domain.models.site import SoilProfile

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)


def _m(parameter: str, value: float, unit: str, **extra) -> dict:  # type: ignore[no-untyped-def]
    return {"parameter": parameter, "value": value, "unit": unit, "source": "lab", **extra}


class TestMeasurementRules:
    @staticmethod
    def _event(category: str, measurement: dict) -> CareEventInput:
        return CareEventInput(
            location_key="L1",
            category=category,
            summary="x",
            performed_at=datetime.now(UTC),
            measurements=[measurement],
        )

    def test_a_conductivity_of_a_soil_analysis_without_its_method_is_refused(self) -> None:
        bare = {"parameter": "ec", "value": 1.2, "unit": "mS/cm"}
        with pytest.raises(ValidationError, match="ec_method"):
            self._event("soil_analysis", bare)
        # counter-cases: with the method it is accepted; a nutrient-solution ec_check has no soil extraction method
        assert self._event("soil_analysis", {**bare, "ec_method": "ratio_1_5"}).measurements
        assert self._event("ec_check", bare).measurements

    @pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
    def test_a_value_that_is_no_number_is_refused(self, value: float) -> None:
        with pytest.raises(ValidationError):
            Measurement(parameter="ec", value=value, unit="mS/cm", ec_method="sensor")

    def test_a_content_class_is_taken_over_only_from_a_lab_result_by_cal(self) -> None:
        taken = Measurement(
            parameter="p", value=12, unit="mg_per_100g", source="lab", extraction_method="cal", content_class="C"
        )
        assert taken.content_class == "C"
        for source, method in (("test_kit", "cal"), ("lab", "ammonium_acetate"), ("sensor", None), ("lab", None)):
            with pytest.raises(ValidationError, match="content class"):
                Measurement(
                    parameter="p",
                    value=12,
                    unit="mg_per_100g",
                    source=source,
                    extraction_method=method,
                    content_class="C",
                )

    def test_a_content_class_exists_for_p_k_and_mg_only(self) -> None:
        with pytest.raises(ValidationError, match="content class"):
            Measurement(parameter="ph", value=6.5, unit="pH", source="lab", extraction_method="cal", content_class="C")

    def test_the_methods_belong_to_their_parameters(self) -> None:
        with pytest.raises(ValidationError):
            Measurement(parameter="ph", value=6.5, unit="pH", ec_method="ratio_1_5")
        with pytest.raises(ValidationError):
            Measurement(parameter="humus", value=3, unit="%", ph_method="cacl2")

    @pytest.mark.parametrize(("parameter", "value"), [("ph", 14.5), ("ph", -1), ("humus", 120), ("caco3", -0.1)])
    def test_a_value_outside_its_possible_range_is_refused(self, parameter: str, value: float) -> None:
        with pytest.raises(ValidationError, match="range"):
            Measurement(parameter=parameter, value=value, unit="%")


class TestProfileFields:
    def test_a_conductivity_in_the_profile_needs_its_method(self) -> None:
        with pytest.raises(ValidationError, match="ec_method"):
            SoilProfile(ec_ms_cm=1.4)
        assert SoilProfile(ec_ms_cm=1.4, ec_method="sensor").ec_method == "sensor"
        assert SoilProfile().ec_method is None  # no value, no method needed

    def test_the_api_schema_carries_the_new_fields_and_the_same_rule(self) -> None:
        from app.api.v1.locations.schemas import SoilProfileSchema

        with pytest.raises(ValidationError, match="ec_method"):
            SoilProfileSchema(ec_ms_cm=1.4)
        schema = SoilProfileSchema(ec_ms_cm=1.4, ec_method="ratio_1_5", caco3_percent=2.0, stone_content_class="few")
        assert (schema.ec_method, schema.caco3_percent, schema.stone_content_class) == ("ratio_1_5", 2.0, "few")

    def test_the_v2_fields_are_fields_only_and_nothing_derives_target_ph(self) -> None:
        profile = SoilProfile(soil_texture="clay")

        assert profile.target_ph is None and profile.stone_content_class == "unknown" and profile.caco3_percent is None


class TestProfilePatch:
    def test_the_values_land_as_measured_with_their_methods(self) -> None:
        patch = profile_patch(
            [
                _m("ph", 6.4, "pH", ph_method="cacl2"),
                _m("ec", 1.1, "mS/cm", ec_method="ratio_1_5"),
                _m("humus", 3.2, "%"),
                _m("caco3", 0.5, "%"),
                _m("p", 12, "mg_per_100g"),  # no profile field for it
            ],
            T0,
        )

        assert patch is not None
        assert patch.fields == {
            "ph": 6.4,
            "ph_method": "cacl2",
            "ec_ms_cm": 1.1,
            "ec_method": "ratio_1_5",
            "humus_percent": 3.2,
            "caco3_percent": 0.5,
            "last_analysis_at": T0,
        }

    def test_a_new_ph_never_keeps_the_method_of_the_old_one(self) -> None:
        patch = profile_patch([_m("ph", 6.4, "pH")], T0)

        assert patch is not None and patch.fields["ph_method"] is None

    def test_a_value_in_another_unit_is_left_out_not_converted(self) -> None:
        patch = profile_patch([_m("ec", 1100, "uS/cm", ec_method="sensor"), _m("humus", 0.03, "fraction")], T0)

        assert patch is None

    def test_ds_per_m_is_the_same_number_as_ms_per_cm(self) -> None:
        patch = profile_patch([_m("ec", 1.1, "dS/m", ec_method="saturated_paste")], T0)

        assert patch is not None and patch.fields["ec_ms_cm"] == 1.1

    def test_an_analysis_without_a_profile_value_changes_nothing(self) -> None:
        assert profile_patch([_m("p", 12, "mg_per_100g"), _m("k", 20, "mg_per_100g")], T0) is None
        assert profile_patch(None, T0) is None

    def test_only_an_analysis_that_is_not_older_may_write(self) -> None:
        assert is_newer(T0, None) is True
        assert is_newer(T0, T0 - timedelta(days=1)) is True
        assert is_newer(T0 - timedelta(days=1), T0) is False
        # the same instant: the latest write wins, so the correction of the newest analysis refreshes the profile
        assert is_newer(T0, T0) is True


class TestSeries:
    @staticmethod
    def _events() -> list[AnalysisEvent]:
        return [
            AnalysisEvent(
                "e1", T0, [_m("ec", 0.8, "mS/cm", ec_method="ratio_1_5"), _m("ph", 6.1, "pH", ph_method="cacl2")]
            ),
            AnalysisEvent(
                "e2",
                T0 + timedelta(days=90),
                [_m("ec", 2.4, "mS/cm", ec_method="saturated_paste"), _m("ph", 6.4, "pH", ph_method="cacl2")],
            ),
            AnalysisEvent("e3", T0 + timedelta(days=180), [_m("ec", 0.9, "mS/cm", ec_method="ratio_1_5")]),
        ]

    def test_two_methods_are_two_series_and_never_merged(self) -> None:
        series, _ = build_series(self._events(), "ec")

        assert [(s.parameter, s.method, [p.event_key for p in s.points]) for s in series] == [
            ("ec", "ratio_1_5", ["e1", "e3"]),
            ("ec", "saturated_paste", ["e2"]),
        ]
        assert [p.value for p in series[0].points] == [0.8, 0.9]  # as measured, no conversion

    def test_a_change_of_method_is_marked_where_it_happens(self) -> None:
        _, changes = build_series(self._events())

        assert [(c.parameter, c.from_method, c.to_method, c.at) for c in changes] == [
            ("ec", "ratio_1_5", "saturated_paste", T0 + timedelta(days=90)),
            ("ec", "saturated_paste", "ratio_1_5", T0 + timedelta(days=180)),
        ]
        # counter-case: ph kept one method and so has no change
        assert not [c for c in changes if c.parameter == "ph"]

    def test_the_parameter_filter_leaves_the_others_out(self) -> None:
        series, changes = build_series(self._events(), "ph")

        assert {s.parameter for s in series} == {"ph"} and changes == []

    def test_a_missing_method_is_unknown_and_its_own_series(self) -> None:
        series, _ = build_series([AnalysisEvent("e1", T0, [_m("humus", 3.0, "%")])])

        assert [(s.parameter, s.method) for s in series] == [("humus", "unknown")]
        assert method_of(_m("ph", 6.4, "pH")) == "unknown"

    def test_the_order_of_the_input_does_not_matter(self) -> None:
        shuffled = list(reversed(self._events()))

        assert build_series(shuffled)[1] == build_series(self._events())[1]


def test_two_methods_inside_one_analysis_are_no_method_change() -> None:
    events = [
        AnalysisEvent("e1", T0, [_m("ph", 6.0, "pH", ph_method="cacl2"), _m("ph", 6.4, "pH", ph_method="h2o")]),
        AnalysisEvent("e2", T0 + timedelta(days=30), [_m("ph", 6.2, "pH", ph_method="cacl2")]),
    ]

    series, changes = build_series(events, "ph")

    assert {s.method for s in series} == {"cacl2", "h2o"}
    assert changes == []
