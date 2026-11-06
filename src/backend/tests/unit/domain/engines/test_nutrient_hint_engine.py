"""WP 8.10 (#2653) — the nutrient hint of a bed by the rule table of REQ-053 §15.3 (GP-FR-125, W-010).

Review acceptance "nutrient hint": a missing ``nutrient_demand`` is ``insufficient_data``; thresholds without a
source give ``insufficient_data`` only (E-10) - and, as the counter-test against an inert engine, a configuration
with an activated, sourced test threshold reaches every other state; a legume preceding crop is a flag without an N
amount; P or K class D/E withholds compost and P. The test thresholds below are **test values, not agronomy**.
"""

from __future__ import annotations

import ast
import dataclasses
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.common.enums import EcMethod, GrowingMediumKind, NutrientDemand
from app.domain.engines import nutrient_hint_engine
from app.domain.engines.nutrient_hint_engine import (
    DEFAULT_CONFIG,
    NutrientHintConfig,
    NutrientHintInputs,
    SourcedClasses,
    SourcedFlag,
    SourcedThreshold,
    assess,
    is_n_binding_mulch,
    is_n_input_amendment,
    lab_content_classes,
    strongest_demand,
)
from app.domain.engines.soil_salinity_hint import SoilSalinityConfig
from app.domain.engines.task_completion_engine import NUTRIENT_MATERIALS
from app.domain.models.nutrient_hint import NUTRIENT_HINT_REASONS, NUTRIENT_HINT_STATES, NutrientHint
from app.domain.models.site import SoilProfile

NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
HEAVY = NutrientDemand.HEAVY_FEEDER
LIGHT = NutrientDemand.LIGHT_FEEDER
TEST_SOURCE = "test threshold, not agronomy"


def _sourced(check: float, likely: float, *, demand: NutrientDemand = HEAVY) -> NutrientHintConfig:
    """A configuration with a sourced feeding-age threshold for one feeder level (the activated test threshold)."""
    nulls = {each: SourcedThreshold() for each in NutrientDemand}
    return NutrientHintConfig(
        check_after_days={**nulls, demand: SourcedThreshold(check, TEST_SOURCE)},
        likely_deficit_after_days={**nulls, demand: SourcedThreshold(likely, TEST_SOURCE)},
    )


ACTIVE = _sourced(30, 60)
LOW = SourcedClasses(frozenset({"A", "B"}), TEST_SOURCE, lab="test lab", year=2026, region="test region")
CLASSES = NutrientHintConfig(low_content_classes=LOW)
BARK = dataclasses.replace(ACTIVE, bark_mulch_binding=SourcedFlag(True, "bark source"))


def _inputs(**overrides: object) -> NutrientHintInputs:
    base: dict[str, object] = {
        "now": NOW,
        "growing_medium_kind": GrowingMediumKind.NATIVE_SOIL,
        "species_demands": (HEAVY,),
        "last_nutrient_input_at": NOW - timedelta(days=10),
    }
    return NutrientHintInputs(**{**base, **overrides})  # type: ignore[arg-type]


def _fed(days: float) -> NutrientHintInputs:
    return _inputs(last_nutrient_input_at=NOW - timedelta(days=days))


class TestNoSourceNoState:
    """E-10: the shipped configuration has no active threshold, so every bed is ``insufficient_data``."""

    def test_the_default_configuration_has_no_active_rule(self) -> None:
        assert DEFAULT_CONFIG.active_rules() == ()

    @pytest.mark.parametrize(
        "inputs",
        [
            _fed(0),
            _fed(500),
            _inputs(last_nutrient_input_at=None),
            _inputs(content_classes={"p": "A", "k": "A"}),
            _inputs(content_classes={"p": "E"}, preceding_nitrogen_fixing=True),
            _inputs(last_n_binding_mulch_at=NOW - timedelta(days=1)),
        ],
    )
    def test_without_a_source_every_bed_is_insufficient_data(self, inputs: NutrientHintInputs) -> None:
        hint = assess(inputs)
        assert hint.state == "insufficient_data"
        assert hint.reasons[0] == "thresholds_without_source"
        assert hint.sources == ()

    def test_a_value_without_its_source_takes_no_part(self) -> None:
        nulls = {each: SourcedThreshold() for each in NutrientDemand}
        for source in (None, "", "   "):
            config = NutrientHintConfig(
                check_after_days={**nulls, HEAVY: SourcedThreshold(1, source)},
                likely_deficit_after_days={**nulls, HEAVY: SourcedThreshold(2, source)},
                low_content_classes=SourcedClasses(frozenset({"A"}), source, lab="lab", year=2026, region="BY"),
            )
            assert config.active_rules() == ()
            assert assess(_fed(500), config).state == "insufficient_data"
        # counter-case: the same values with a source decide the state
        assert assess(_fed(500), _sourced(1, 2)).state == "likely_deficit"

    def test_class_bounds_need_lab_year_and_region_next_to_the_source(self) -> None:
        """R-007: class bounds vary by lab, year and federal state - a bare source is not enough."""
        for partial in (
            SourcedClasses(frozenset({"A"}), TEST_SOURCE),
            SourcedClasses(frozenset({"A"}), TEST_SOURCE, lab="lab", year=2026),
            SourcedClasses(frozenset({"A"}), TEST_SOURCE, lab="lab", region="BY"),
            SourcedClasses(frozenset({"A"}), TEST_SOURCE, year=2026, region="BY"),
        ):
            config = NutrientHintConfig(low_content_classes=partial)
            assert config.active_rules() == ()
            assert assess(_inputs(content_classes={"p": "A"}), config).state == "insufficient_data"
        hint = assess(_inputs(content_classes={"p": "A"}), CLASSES)
        assert hint.state == "likely_deficit" and hint.sources == (f"{TEST_SOURCE} (test lab, 2026, test region)",)

    def test_a_source_without_a_value_takes_no_part(self) -> None:
        nulls = {each: SourcedThreshold() for each in NutrientDemand}
        config = NutrientHintConfig(check_after_days={**nulls, HEAVY: SourcedThreshold(None, TEST_SOURCE)})
        assert assess(_fed(500), config).state == "insufficient_data"


class TestPreconditions:
    def test_a_missing_nutrient_demand_is_insufficient_data(self) -> None:
        hint = assess(_inputs(species_demands=(None, None)), ACTIVE)
        assert (hint.state, hint.reasons[0]) == ("insufficient_data", "demand_unknown")

    def test_plants_whose_species_the_tenant_cannot_read_are_named_as_such(self) -> None:
        hint = assess(_inputs(species_demands=(None, None), unreadable_species=2), ACTIVE)
        assert (hint.state, hint.reasons[0]) == ("insufficient_data", "species_not_readable")
        # counter-case: one readable species without a feeder level is "demand_unknown", not "not readable"
        assert assess(_inputs(species_demands=(None, None), unreadable_species=1), ACTIVE).reasons[0] == (
            "demand_unknown"
        )

    def test_a_bed_without_plants_is_insufficient_data(self) -> None:
        hint = assess(_inputs(species_demands=()), ACTIVE)
        assert (hint.state, hint.reasons[0]) == ("insufficient_data", "no_current_crop")

    def test_a_mineral_substrate_bed_is_left_to_the_nutrient_solution_logic(self) -> None:
        hint = assess(_inputs(growing_medium_kind=GrowingMediumKind.MINERAL_SUBSTRATE), ACTIVE)
        assert (hint.state, hint.reasons[0]) == ("insufficient_data", "substrate_bed")
        # counter-case: a raised-bed mix and an unknown filling are assessed
        assert assess(_inputs(growing_medium_kind=GrowingMediumKind.RAISED_BED_MIX), ACTIVE).state == "ok"
        assert assess(_inputs(growing_medium_kind=None), ACTIVE).state == "ok"

    def test_a_threshold_of_another_feeder_level_does_not_apply(self) -> None:
        hint = assess(_inputs(species_demands=(LIGHT,), last_nutrient_input_at=NOW - timedelta(days=500)), ACTIVE)
        assert (hint.state, hint.reasons[0]) == ("insufficient_data", "thresholds_without_source")


class TestActivatedThresholdReachesEveryState:
    """The counter-test against an inert engine: a sourced test threshold reaches ok, check and likely_deficit."""

    def test_recently_fed_is_ok(self) -> None:
        hint = assess(_fed(10), ACTIVE)
        assert (hint.state, hint.confidence, hint.reasons) == ("ok", "medium", ("fed_recently",))
        assert hint.sources == (TEST_SOURCE,)

    def test_past_the_check_threshold_is_check(self) -> None:
        hint = assess(_fed(45), ACTIVE)
        assert (hint.state, hint.reasons) == ("check", ("feeding_due",))

    def test_past_the_deficit_threshold_is_likely_deficit(self) -> None:
        hint = assess(_fed(90), ACTIVE)
        assert (hint.state, hint.confidence, hint.reasons) == ("likely_deficit", "medium", ("feeding_overdue",))

    def test_the_threshold_itself_is_not_yet_past(self) -> None:
        assert assess(_fed(30), ACTIVE).state == "ok"
        assert assess(_fed(60), ACTIVE).state == "check"

    def test_no_recorded_input_is_at_most_check_with_low_confidence(self) -> None:
        hint = assess(_inputs(last_nutrient_input_at=None), ACTIVE)
        assert (hint.state, hint.confidence, hint.reasons) == ("check", "low", ("no_feeding_recorded",))

    def test_every_state_is_reachable(self) -> None:
        reached = {
            assess(_fed(10), ACTIVE).state,
            assess(_fed(45), ACTIVE).state,
            assess(_fed(90), ACTIVE).state,
            assess(_fed(90)).state,
        }
        assert reached == set(NUTRIENT_HINT_STATES)

    def test_a_mixed_bed_is_judged_by_its_hungriest_stated_crop(self) -> None:
        hint = assess(
            _inputs(species_demands=(LIGHT, None, HEAVY), last_nutrient_input_at=NOW - timedelta(days=90)), ACTIVE
        )
        assert hint.state == "likely_deficit"
        assert "demand_partly_unknown" in hint.reasons and hint.confidence == "low"


class TestLabClasses:
    def test_a_low_lab_class_makes_a_deficit_likely_with_high_confidence(self) -> None:
        hint = assess(_inputs(content_classes={"k": "A", "p": "C"}), CLASSES)
        assert (hint.state, hint.confidence, hint.reasons) == ("likely_deficit", "high", ("k_class_low",))

    def test_sufficient_classes_are_ok(self) -> None:
        hint = assess(_inputs(content_classes={"p": "C", "k": "C"}), CLASSES)
        assert (hint.state, hint.reasons) == ("ok", ("content_classes_sufficient",))

    def test_the_worse_of_two_rules_wins(self) -> None:
        config = dataclasses.replace(ACTIVE, low_content_classes=LOW)
        hint = assess(_inputs(content_classes={"p": "B"}, last_nutrient_input_at=NOW - timedelta(days=1)), config)
        assert (hint.state, hint.reasons) == ("likely_deficit", ("p_class_low",))

    def test_only_a_lab_class_is_read(self) -> None:
        cal = {"source": "lab", "extraction_method": "cal"}
        analyses = [
            [{"parameter": "p", "value": 3, "source": "test_kit", "extraction_method": "cal", "content_class": "A"}],
            [
                {"parameter": "p", "value": 9, **cal, "content_class": "D"},
                {"parameter": "k", "value": 9, **cal, "content_class": "B"},
                {"parameter": "mg", "value": 9, **cal, "content_class": "A"},
            ],
            [{"parameter": "k", "value": 1, **cal, "content_class": "E"}],
        ]
        # newest first: the test-kit class is skipped, the newest lab class per parameter wins, Mg stays out
        assert lab_content_classes(analyses) == {"p": "D", "k": "B"}
        assert lab_content_classes([[{"parameter": "p", "value": 3, **cal}]]) == {}

    @pytest.mark.parametrize("method", ["ammonium_acetate", "olsen", None])
    def test_a_lab_class_by_another_method_than_cal_is_not_read(self, method: str | None) -> None:
        other = [[{"parameter": "p", "value": 40, "source": "lab", "extraction_method": method, "content_class": "E"}]]
        classes = lab_content_classes(other)
        assert classes == {}
        hint = assess(_inputs(content_classes=classes), CLASSES)
        assert hint.compost_and_p_withheld is False and hint.state == "insufficient_data"


class TestClassDOrEWithholdsCompostAndP:
    @pytest.mark.parametrize("classes", [{"p": "D"}, {"k": "E"}, {"p": "E", "k": "A"}])
    def test_p_or_k_class_d_or_e_withholds_compost_and_p(self, classes: dict[str, str]) -> None:
        for config in (DEFAULT_CONFIG, ACTIVE, CLASSES):
            hint = assess(_inputs(content_classes=classes), config)
            assert hint.compost_and_p_withheld is True
            assert "p_or_k_class_high" in hint.reasons

    def test_the_d_e_rule_is_active_by_default_and_names_its_source(self) -> None:
        hint = assess(_inputs(content_classes={"p": "D"}))
        assert hint.withheld_source is not None and "R-006" in hint.withheld_source
        assert "LWG" in hint.withheld_source and "Hessisches Landeslabor" in hint.withheld_source
        assert assess(_inputs(content_classes={"p": "C"})).withheld_source is None

    def test_p_e_with_k_a_stays_conservative(self) -> None:
        """P very high, K very low: the K deficit is reported, but compost and P stay withheld."""
        hint = assess(_inputs(content_classes={"p": "E", "k": "A"}), CLASSES)
        assert (hint.state, hint.compost_and_p_withheld) == ("likely_deficit", True)
        assert hint.reasons[0] == "k_class_low" and "p_class_low" not in hint.reasons

    def test_class_c_withholds_nothing(self) -> None:
        hint = assess(_inputs(content_classes={"p": "C", "k": "B"}), CLASSES)
        assert hint.compost_and_p_withheld is False and "p_or_k_class_high" not in hint.reasons

    def test_no_reason_code_points_to_compost_or_phosphorus(self) -> None:
        # The hint has no remedy codes at all: nothing it says can recommend compost or a P fertiliser.
        assert not [code for code in NUTRIENT_HINT_REASONS if "compost" in code or "phosph" in code]


class TestPrecedingNitrogenFixer:
    def test_a_legume_preceding_crop_is_a_flag_without_an_amount(self) -> None:
        for config in (DEFAULT_CONFIG, ACTIVE):
            hint = assess(_inputs(preceding_nitrogen_fixing=True), config)
            assert "preceding_nitrogen_fixer" in hint.reasons
            assert all(not isinstance(value, (int, float)) or isinstance(value, bool) for value in _values(hint))

    def test_without_a_sourced_relief_the_flag_changes_no_state(self) -> None:
        assert assess(
            _inputs(preceding_nitrogen_fixing=True, last_nutrient_input_at=NOW - timedelta(days=90)), ACTIVE
        ).state == ("likely_deficit")

    def test_a_sourced_relief_lowers_a_feeding_deficit_to_check(self) -> None:
        config = dataclasses.replace(ACTIVE, nitrogen_fixer_relief=SourcedFlag(True, "relief source"))
        hint = assess(_inputs(preceding_nitrogen_fixing=True, last_nutrient_input_at=NOW - timedelta(days=90)), config)
        assert (hint.state, hint.confidence) == ("check", "low")
        assert hint.sources == (TEST_SOURCE, "relief source")
        # counter-case: a deficit from a lab class is not softened by the preceding crop
        both = dataclasses.replace(config, low_content_classes=LOW)
        lab = assess(_inputs(preceding_nitrogen_fixing=True, content_classes={"k": "A"}), both)
        assert lab.state == "likely_deficit"


class TestStandingNitrogenFixer:
    def test_a_standing_legume_is_a_flag_of_its_own_without_a_state(self) -> None:
        hint = assess(_inputs(standing_nitrogen_fixing=True), ACTIVE)
        assert hint.state == "ok" and "standing_nitrogen_fixer" in hint.reasons
        assert "preceding_nitrogen_fixer" not in hint.reasons


class TestBarkMulch:
    def test_without_a_source_bark_mulch_is_a_reason_only(self) -> None:
        hint = assess(_inputs(last_n_binding_mulch_at=NOW - timedelta(days=2)), ACTIVE)
        assert (hint.state, hint.confidence) == ("ok", "medium")
        assert "bark_mulch_n_binding" in hint.reasons

    def test_a_sourced_flag_turns_an_ok_of_the_feeding_age_into_check(self) -> None:
        hint = assess(_inputs(last_n_binding_mulch_at=NOW - timedelta(days=2)), BARK)
        assert (hint.state, hint.confidence) == ("check", "low")
        assert hint.sources == (TEST_SOURCE, "bark source")

    def test_an_ok_of_a_lab_class_is_never_raised(self) -> None:
        config = dataclasses.replace(CLASSES, bark_mulch_binding=SourcedFlag(True, "bark source"))
        hint = assess(_inputs(content_classes={"p": "C"}, last_n_binding_mulch_at=NOW - timedelta(days=2)), config)
        assert hint.state == "ok" and "bark_mulch_n_binding" in hint.reasons

    def test_bark_mulch_before_the_last_input_is_no_flag(self) -> None:
        hint = assess(_inputs(last_n_binding_mulch_at=NOW - timedelta(days=20)), BARK)
        assert hint.state == "ok" and "bark_mulch_n_binding" not in hint.reasons

    def test_bark_mulch_alone_produces_no_state(self) -> None:
        hint = assess(
            _inputs(last_n_binding_mulch_at=NOW - timedelta(days=2)),
            dataclasses.replace(DEFAULT_CONFIG, bark_mulch_binding=SourcedFlag(True, "bark source")),
        )
        assert hint.state == "insufficient_data" and "bark_mulch_n_binding" in hint.reasons

    def test_only_bark_mulch_binds(self) -> None:
        assert is_n_binding_mulch("bark_mulch") and is_n_binding_mulch(" Bark_Mulch ")
        assert not any(is_n_binding_mulch(each) for each in ("straw", "compost", None, ""))


class TestSaltLimit:
    """E-17 variant A (#2654): soil EC is a salt-limit hint ``check_salt_content`` - never a dose, never a state."""

    SALT = SoilSalinityConfig(threshold_ms_cm=2.0, ec_method=EcMethod.SATURATED_PASTE, source=TEST_SOURCE)
    SALTY = SoilProfile(
        growing_medium_kind=GrowingMediumKind.NATIVE_SOIL, ec_ms_cm=3.0, ec_method=EcMethod.SATURATED_PASTE
    )

    def test_the_default_configuration_gives_no_salt_reason(self) -> None:
        hint = assess(_inputs(soil_profile=self.SALTY))
        assert "check_salt_content" not in hint.reasons

    def test_above_a_sourced_threshold_of_the_same_method_gives_the_reason(self) -> None:
        config = NutrientHintConfig(soil_salinity=self.SALT)
        hint = assess(_inputs(soil_profile=self.SALTY), config)
        assert "check_salt_content" in hint.reasons
        assert config.active_rules() == ("soil_salinity",)

    def test_another_method_gives_no_reason(self) -> None:
        profile = SoilProfile(ec_ms_cm=3.0, ec_method=EcMethod.RATIO_1_5)
        hint = assess(_inputs(soil_profile=profile), NutrientHintConfig(soil_salinity=self.SALT))
        assert "check_salt_content" not in hint.reasons

    def test_a_threshold_without_a_source_gives_no_reason(self) -> None:
        unsourced = SoilSalinityConfig(threshold_ms_cm=2.0, ec_method=EcMethod.SATURATED_PASTE, source=None)
        hint = assess(_inputs(soil_profile=self.SALTY), NutrientHintConfig(soil_salinity=unsourced))
        assert "check_salt_content" not in hint.reasons

    def test_the_reason_never_changes_an_ok(self) -> None:
        config = dataclasses.replace(ACTIVE, soil_salinity=self.SALT)
        plain = assess(_fed(10), ACTIVE)
        salty = assess(_inputs(soil_profile=self.SALTY), config)
        assert plain.state == salty.state == "ok"
        assert plain.confidence == salty.confidence
        assert plain.sources == salty.sources
        assert "check_salt_content" in salty.reasons

    def test_the_reason_never_produces_a_state_on_its_own(self) -> None:
        hint = assess(_inputs(soil_profile=self.SALTY), NutrientHintConfig(soil_salinity=self.SALT))
        assert hint.state == "insufficient_data"
        assert hint.reasons[0] == "thresholds_without_source"

    def test_a_mineral_substrate_bed_gets_no_soil_salt_reason(self) -> None:
        substrate = SoilProfile(
            growing_medium_kind=GrowingMediumKind.MINERAL_SUBSTRATE, ec_ms_cm=3.0, ec_method=EcMethod.SATURATED_PASTE
        )
        hint = assess(
            _inputs(growing_medium_kind=GrowingMediumKind.MINERAL_SUBSTRATE, soil_profile=substrate),
            NutrientHintConfig(soil_salinity=self.SALT),
        )
        assert hint.reasons == ("substrate_bed",)


class TestNInputs:
    def test_compost_is_no_n_input_but_manure_and_horn_shavings_are(self) -> None:
        """R-005: compost is no N supplier; W-007 (its feeding event for the balance) stays untouched."""
        assert is_n_input_amendment("manure") and is_n_input_amendment("horn_shavings")
        assert not any(is_n_input_amendment(each) for each in ("compost", "sand", None))
        assert "compost" in NUTRIENT_MATERIALS


class TestConfigValidation:
    def test_an_active_r1_threshold_beyond_the_read_window_is_refused(self) -> None:
        with pytest.raises(ValueError, match="read_window_days"):
            _sourced(30, 400)
        with pytest.raises(ValueError, match="read_window_days"):
            dataclasses.replace(_sourced(30, 60), read_window_days=45)
        with pytest.raises(ValueError, match="read_window_days"):
            _sourced(0, 60)
        # counter-cases: on the window itself, and an inactive value beyond it, are accepted
        assert _sourced(30, 365).active_rules()
        nulls = {each: SourcedThreshold() for each in NutrientDemand}
        assert NutrientHintConfig(check_after_days={**nulls, HEAVY: SourcedThreshold(9999, None)}).active_rules() == ()

    def test_the_read_window_is_positive(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            NutrientHintConfig(read_window_days=0)


def test_strongest_demand_never_invents_one() -> None:
    assert strongest_demand([None, None]) is None
    assert strongest_demand([LIGHT, NutrientDemand.MEDIUM_FEEDER]) is NutrientDemand.MEDIUM_FEEDER


def _values(hint: NutrientHint) -> list[object]:
    return [getattr(hint, name.name) for name in dataclasses.fields(hint)]


def test_the_engine_holds_no_agronomic_number() -> None:
    """Static: the module names no day count, class limit or N amount of its own - those are configuration."""
    tree = ast.parse(Path(nutrient_hint_engine.__file__).read_text(encoding="utf-8"))
    numbers = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    }
    # 0 / 1 / 2 are the severity ranks and the "or 0" of an inactive value; 86400 turns seconds into days.
    assert numbers <= {0, 1, 2, 86400}, numbers
