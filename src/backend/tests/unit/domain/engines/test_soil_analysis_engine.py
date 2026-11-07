"""WP 8.7 (#2650) — what an analysis writes into the bed profile and how the series read: per method, no conversion."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.domain.engines.soil_analysis_engine import (
    LEGACY_HAND_AT,
    AnalysisEvent,
    build_series,
    derive_profile,
    liming_hint,
    method_of,
    normal_unit,
    profile_values,
    read_instant,
    writes_the_soil_profile,
)
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


def _fields(measurements, at=T0) -> dict:  # type: ignore[no-untyped-def]
    """The profile one analysis derives on an empty bed, without the bookkeeping."""
    derived = derive_profile({}, [AnalysisEvent("e", at, measurements)])
    return {k: v for k, v in derived.items() if k != "hand_values"}


class TestProfileValues:
    def test_the_values_land_as_measured_with_their_methods(self) -> None:
        fields = _fields(
            [
                _m("ph", 6.4, "pH", ph_method="cacl2"),
                _m("ec", 1.1, "mS/cm", ec_method="ratio_1_5"),
                _m("humus", 3.2, "%"),
                _m("caco3", 0.5, "%"),
                _m("p", 12, "mg_per_100g"),  # no profile field for it
            ]
        )

        assert fields == {
            "ph": 6.4,
            "ph_method": "cacl2",
            "ec_ms_cm": 1.1,
            "ec_method": "ratio_1_5",
            "humus_percent": 3.2,
            "caco3_percent": 0.5,
            "last_analysis_at": T0,
        }

    def test_a_new_ph_never_keeps_the_method_of_the_old_one(self) -> None:
        derived = derive_profile({"ph": 5.0, "ph_method": "cacl2"}, [AnalysisEvent("e", T0, [_m("ph", 6.4, "pH")])])

        assert derived["ph"] == 6.4 and derived["ph_method"] is None

    def test_a_value_in_another_unit_is_left_out_not_converted(self) -> None:
        assert profile_values([_m("ec", 1100, "uS/cm", ec_method="sensor"), _m("humus", 0.03, "fraction")]) == {}

    def test_ds_per_m_is_the_same_number_as_ms_per_cm(self) -> None:
        assert _fields([_m("ec", 1.1, " dS/m ", ec_method="saturated_paste")])["ec_ms_cm"] == 1.1
        assert normal_unit("dS/m") == normal_unit("MS/CM ") == "ms/cm"

    def test_an_analysis_without_a_profile_value_changes_nothing(self) -> None:
        assert derive_profile({}, [AnalysisEvent("e", T0, [_m("p", 12, "mg_per_100g")])]) == {}
        assert profile_values(None) == {}

    def test_an_older_analysis_does_not_replace_a_newer_value(self) -> None:
        analyses = [
            AnalysisEvent("new", T0, [_m("ph", 6.4, "pH")]),
            AnalysisEvent("old", T0 - timedelta(days=200), [_m("ph", 5.1, "pH"), _m("humus", 3.0, "%")]),
        ]

        derived = derive_profile({}, analyses)

        assert (derived["ph"], derived["humus_percent"], derived["last_analysis_at"]) == (6.4, 3.0, T0)

    def test_one_predicate_says_which_events_feed_the_profile(self) -> None:
        assert writes_the_soil_profile("soil_analysis", [_m("ph", 6.4, "pH")]) is True
        assert writes_the_soil_profile("soil_analysis", []) is False
        assert writes_the_soil_profile("watering", [_m("ph", 6.4, "pH")]) is False


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


class TestOldDocumentsStayReadable:
    """Data-loss guard (WP 8.7): a document older than ``ec_method`` neither fails to load nor is refused."""

    def test_a_stored_bed_with_a_conductivity_and_no_method_still_loads_as_unknown(self) -> None:
        from app.domain.models.site import Location

        location = Location(
            _key="L1", site_key="S1", name="Bed", area_m2=1.0, soil_profile={"ec_ms_cm": 1.4, "drainage": "poor"}
        )

        assert location.soil_profile is not None
        assert (location.soil_profile.ec_ms_cm, location.soil_profile.ec_method) == (1.4, "unknown")
        # counter-case: a method that is stated stays what it is
        stated = Location(
            _key="L2", site_key="S1", name="Bed", area_m2=1.0, soil_profile={"ec_ms_cm": 1.4, "ec_method": "sensor"}
        )
        assert stated.soil_profile is not None and stated.soil_profile.ec_method == "sensor"

    def test_a_request_is_still_refused(self) -> None:
        with pytest.raises(ValidationError, match="ec_method"):
            SoilProfile(ec_ms_cm=1.4)

    def test_an_old_backup_or_import_snapshot_is_read_not_refused(self) -> None:
        from app.domain.services.garden_plan_import_service import GardenPlanImportService

        document = {
            "schema_version": "1",
            "exported_at": "2026-03-01T09:00:00Z",
            "site": {"name": "Garden", "type": "outdoor"},
            "locations": [
                {"key": "bed_1", "name": "Bed", "location_type_key": "bed", "soil_profile": {"ec_ms_cm": 1.4}}
            ],
        }

        parsed = GardenPlanImportService._read_document(document)

        profile = parsed.locations[0].soil_profile
        assert profile is not None and profile.ec_method == "unknown"
        assert "ec_method" not in document["locations"][0]["soil_profile"]  # the caller's document is not changed


class TestLimingHint:
    """WP 8.8 (#2651): "liming likely" is a text from method + texture + a stated target - never an amount."""

    @staticmethod
    def _profile(**overrides) -> SoilProfile:  # type: ignore[no-untyped-def]
        base = {
            "growing_medium_kind": "native_soil",
            "soil_texture": "loam",
            "ph": 5.6,
            "ph_method": "cacl2",
            "target_ph": 6.2,
        }
        return SoilProfile.model_validate({**base, **overrides})

    def test_a_cacl2_ph_below_the_stated_target_on_known_soil_is_likely(self) -> None:
        hint = liming_hint(self._profile())
        assert (hint.status, hint.reason) == ("likely", "below_target")

    @pytest.mark.parametrize("ph", [6.2, 6.8])
    def test_a_ph_at_or_above_the_target_is_not_indicated(self, ph: float) -> None:
        hint = liming_hint(self._profile(ph=ph))
        assert (hint.status, hint.reason) == ("not_indicated", "at_or_above_target")

    @pytest.mark.parametrize(
        ("overrides", "reason"),
        [
            ({"ph": None, "ph_method": None}, "no_ph"),
            ({"growing_medium_kind": "raised_bed_mix"}, "not_native_soil"),
            ({"growing_medium_kind": None}, "not_native_soil"),
            # a pH by water or by probe is never converted to CaCl2 - even one far below the target
            ({"ph_method": "h2o", "ph": 4.0}, "ph_method_not_cacl2"),
            ({"ph_method": "probe_unknown", "ph": 4.0}, "ph_method_not_cacl2"),
            ({"ph_method": None, "ph": 4.0}, "ph_method_not_cacl2"),
            ({"soil_texture": "unknown"}, "texture_unknown"),
            # no target is derived from the texture ("stays null" item 17)
            ({"target_ph": None, "ph": 4.0}, "no_target_ph"),
        ],
    )
    def test_without_every_precondition_nothing_is_assessed(self, overrides: dict, reason: str) -> None:
        hint = liming_hint(self._profile(**overrides))
        assert (hint.status, hint.reason) == ("not_assessable", reason)

    def test_no_profile_is_no_ph(self) -> None:
        assert liming_hint(None).reason == "no_ph"


class TestFollowUps2706:
    """#2706: unit-split series, per-analysis method changes, the shallowest depth, tolerant instants, re-derivation."""

    def test_two_units_of_one_method_are_two_series(self) -> None:
        events = [
            AnalysisEvent("e1", T0, [_m("ec", 1100, "uS/cm", ec_method="sensor")]),
            AnalysisEvent("e2", T0 + timedelta(days=30), [_m("ec", 1.1, "mS/cm", ec_method="sensor")]),
        ]

        series, changes = build_series(events, "ec")

        assert [(s.method, s.unit, [p.value for p in s.points]) for s in series] == [
            ("sensor", "mS/cm", [1.1]),
            ("sensor", "uS/cm", [1100.0]),
        ]
        assert changes == []  # the same method: no method change, only another unit

    def test_spellings_of_one_unit_are_one_series_reported_normalised(self) -> None:
        events = [
            AnalysisEvent("e1", T0, [_m("ec", 1.0, "mS/cm", ec_method="sensor")]),
            AnalysisEvent("e2", T0 + timedelta(days=1), [_m("ec", 1.1, " ms/cm", ec_method="sensor")]),
            AnalysisEvent("e3", T0 + timedelta(days=2), [_m("ec", 1.2, "dS/m", ec_method="sensor")]),
            AnalysisEvent("e4", T0 + timedelta(days=3), [_m("ph", 6.1, "PH")]),
        ]

        series, _ = build_series(events)

        assert [(s.parameter, s.unit, len(s.points)) for s in series] == [("ec", "mS/cm", 3), ("ph", "pH", 1)]

    def test_a_method_change_at_the_same_instant_is_marked(self) -> None:
        events = [
            AnalysisEvent("e1", T0, [_m("ph", 6.0, "pH", ph_method="cacl2")]),
            AnalysisEvent("e2", T0, [_m("ph", 6.6, "pH", ph_method="h2o")]),
        ]

        _, changes = build_series(events, "ph")

        assert [(c.from_method, c.to_method, c.at) for c in changes] == [("cacl2", "h2o", T0)]

    def test_the_mark_does_not_depend_on_the_order_inside_an_analysis(self) -> None:
        first = [_m("ph", 6.4, "pH", ph_method="h2o"), _m("ph", 6.0, "pH", ph_method="cacl2")]
        events = [
            AnalysisEvent("e1", T0, first),
            AnalysisEvent("e2", T0 + timedelta(days=30), [_m("ph", 6.2, "pH", ph_method="cacl2")]),
        ]

        assert build_series(events, "ph")[1] == []  # cacl2 continues; listing h2o first must not invent a change
        moved = [AnalysisEvent("e1", T0, first), AnalysisEvent("e2", T0 + timedelta(days=30), [_m("ph", 6.2, "pH")])]
        assert [(c.from_method, c.to_method) for c in build_series(moved, "ph")[1]] == [
            ("cacl2", "unknown"),
            ("h2o", "unknown"),
        ]

    def test_the_shallowest_sample_depth_wins_in_the_profile(self) -> None:
        values = profile_values(
            [_m("ph", 6.0, "pH", sample_depth_cm=30), _m("ph", 6.6, "pH", sample_depth_cm=10), _m("ph", 7.0, "pH")]
        )

        assert values["ph"]["ph"] == 6.6

    def test_an_unreadable_stored_instant_reads_as_missing(self) -> None:
        assert read_instant("not a date") is None and read_instant(None) is None
        assert read_instant("2026-03-01T09:00:00") == T0  # naive text is UTC
        # a naive performed_at reads as UTC: it ties with the aware one, the one listed first wins
        derived = derive_profile(
            {}, [AnalysisEvent("a", T0.replace(tzinfo=None), [_m("ph", 6.0, "pH")]), AnalysisEvent("b", T0, [])]
        )
        assert derived["last_analysis_at"] == T0

    def test_the_profile_is_derived_from_the_newest_analysis_per_parameter_and_keeps_hand_fields(self) -> None:
        current = {
            "drainage": "good",
            "target_ph": 6.5,
            "ph": 9.9,
            "humus_percent": 8.0,
            "last_analysis_at": "x",
            "hand_values": {},
        }
        analyses = [
            AnalysisEvent("old", T0, [_m("ph", 6.0, "pH", ph_method="h2o"), _m("humus", 3.0, "%")]),
            AnalysisEvent("new", T0 + timedelta(days=10), [_m("ph", 6.4, "pH", ph_method="cacl2")]),
        ]

        derived = derive_profile(current, analyses)

        assert derived == {
            "drainage": "good",
            "target_ph": 6.5,
            "ph": 6.4,
            "ph_method": "cacl2",
            "humus_percent": 3.0,
            "last_analysis_at": T0 + timedelta(days=10),
            "hand_values": {},
        }

    def test_without_an_analysis_the_measured_fields_and_the_instant_are_cleared(self) -> None:
        current = {
            "drainage": "good",
            "ph": 6.4,
            "ph_method": "cacl2",
            "ec_ms_cm": 1.0,
            "ec_method": "sensor",
            "hand_values": {},
        }

        assert derive_profile({**current, "last_analysis_at": T0}, []) == {"drainage": "good", "hand_values": {}}


def _hand(value, at, method=None) -> dict:  # type: ignore[no-untyped-def]
    return {"value": value, "method": method, "at": at.isoformat()}


class TestNewestObservationWins:
    """#2706 re-review: per field the newer of the hand entry and the newest open analysis wins; a tie is the hand's."""

    def test_voiding_the_newer_analysis_returns_to_the_hand_value_not_the_older_analysis(self) -> None:  # M3
        hand = {"ph": _hand(6.5, T0, "h2o")}
        older = AnalysisEvent("A", T0 - timedelta(days=30), [_m("ph", 6.0, "pH", ph_method="cacl2")])
        newer = AnalysisEvent("N", T0 + timedelta(days=30), [_m("ph", 6.9, "pH", ph_method="cacl2")])

        with_n = derive_profile({"ph": 6.9, "hand_values": hand}, [newer, older])
        after_void = derive_profile(with_n, [older])

        assert (with_n["ph"], with_n["last_analysis_at"]) == (6.9, T0 + timedelta(days=30))
        assert (after_void["ph"], after_void["ph_method"], "last_analysis_at" in after_void) == (6.5, "h2o", False)

    def test_a_value_cleared_by_hand_stays_cleared_against_older_analyses(self) -> None:  # M4
        current = {"humus_percent": 3.0, "hand_values": {"ph": _hand(None, T0)}}
        older = AnalysisEvent("A", T0 - timedelta(days=30), [_m("ph", 6.0, "pH")])
        humus = AnalysisEvent("H", T0 + timedelta(days=1), [_m("humus", 3.0, "%")])

        derived = derive_profile(current, [humus, older])

        assert "ph" not in derived and derived["humus_percent"] == 3.0

    def test_the_times_are_per_field(self) -> None:  # L2
        hand = {"ph": _hand(6.5, T0), "humus_percent": _hand(4.0, T0 + timedelta(days=20))}
        between = AnalysisEvent("B", T0 + timedelta(days=10), [_m("ph", 6.9, "pH"), _m("humus", 3.0, "%")])

        derived = derive_profile({"hand_values": hand}, [between])

        assert (derived["ph"], derived["humus_percent"]) == (6.9, 4.0)  # the later humus edit protects only humus

    def test_a_tie_goes_to_the_hand_entry(self) -> None:
        derived = derive_profile(
            {"hand_values": {"ph": _hand(6.5, T0)}}, [AnalysisEvent("A", T0, [_m("ph", 6.0, "pH")])]
        )

        assert derived["ph"] == 6.5 and "last_analysis_at" not in derived

    def test_a_row_from_before_the_entries_classifies_its_values(self) -> None:
        voided = AnalysisEvent("voided", T0, [_m("ph", 9.9, "pH")])
        current = {"ph": 9.9, "humus_percent": 4.0}

        derived = derive_profile(current, [], history=[voided])

        # 9.9 was the analysis's and goes with it; 4.0 becomes a hand entry at the oldest instant
        assert "ph" not in derived and derived["humus_percent"] == 4.0
        assert derived["hand_values"]["humus_percent"]["at"] == LEGACY_HAND_AT == datetime.min.replace(tzinfo=UTC)
        later = derive_profile(derived, [AnalysisEvent("H", T0 - timedelta(days=900), [_m("humus", 2.0, "%")])])
        assert later["humus_percent"] == 2.0  # any open analysis supersedes a classified legacy value


def test_an_unknown_unit_is_reported_in_the_spelling_of_its_oldest_measurement() -> None:
    events = [
        AnalysisEvent("e2", T0 + timedelta(days=1), [_m("p", 13, "MG_PER_L ")]),
        AnalysisEvent("e1", T0, [_m("p", 12, " mg_per_L")]),
    ]

    series, _ = build_series(events, "p")

    assert [(s.unit, len(s.points)) for s in series] == [("mg_per_L", 2)]  # grouped on the key, never lower-cased
