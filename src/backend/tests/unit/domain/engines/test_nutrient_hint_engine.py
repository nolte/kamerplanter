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

from app.common.enums import GrowingMediumKind, NutrientDemand
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
    lab_content_classes,
    strongest_demand,
)
from app.domain.models.nutrient_hint import NUTRIENT_HINT_REASONS, NUTRIENT_HINT_STATES, NutrientHint

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
CLASSES = NutrientHintConfig(low_content_classes=SourcedClasses(frozenset({"A", "B"}), TEST_SOURCE))


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
                low_content_classes=SourcedClasses(frozenset({"A"}), source),
            )
            assert config.active_rules() == ()
            assert assess(_fed(500), config).state == "insufficient_data"
        # counter-case: the same values with a source decide the state
        assert assess(_fed(500), _sourced(1, 2)).state == "likely_deficit"

    def test_a_source_without_a_value_takes_no_part(self) -> None:
        nulls = {each: SourcedThreshold() for each in NutrientDemand}
        config = NutrientHintConfig(check_after_days={**nulls, HEAVY: SourcedThreshold(None, TEST_SOURCE)})
        assert assess(_fed(500), config).state == "insufficient_data"


class TestPreconditions:
    def test_a_missing_nutrient_demand_is_insufficient_data(self) -> None:
        hint = assess(_inputs(species_demands=(None, None)), ACTIVE)
        assert (hint.state, hint.reasons[0]) == ("insufficient_data", "demand_unknown")

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
        config = dataclasses.replace(ACTIVE, low_content_classes=CLASSES.low_content_classes)
        hint = assess(_inputs(content_classes={"p": "B"}, last_nutrient_input_at=NOW - timedelta(days=1)), config)
        assert (hint.state, hint.reasons) == ("likely_deficit", ("p_class_low",))

    def test_only_a_lab_class_is_read(self) -> None:
        analyses = [
            [{"parameter": "p", "value": 3, "source": "test_kit", "content_class": "A"}],
            [
                {"parameter": "p", "value": 9, "source": "lab", "content_class": "D"},
                {"parameter": "k", "value": 9, "source": "lab", "content_class": "B"},
                {"parameter": "mg", "value": 9, "source": "lab", "content_class": "A"},
            ],
            [{"parameter": "k", "value": 1, "source": "lab", "content_class": "E"}],
        ]
        # newest first: the test-kit class is skipped, the newest lab class per parameter wins, Mg stays out
        assert lab_content_classes(analyses) == {"p": "D", "k": "B"}
        assert lab_content_classes([[{"parameter": "p", "value": 3, "source": "lab"}]]) == {}


class TestClassDOrEWithholdsCompostAndP:
    @pytest.mark.parametrize("classes", [{"p": "D"}, {"k": "E"}, {"p": "E", "k": "A"}])
    def test_p_or_k_class_d_or_e_withholds_compost_and_p(self, classes: dict[str, str]) -> None:
        for config in (DEFAULT_CONFIG, ACTIVE, CLASSES):
            hint = assess(_inputs(content_classes=classes), config)
            assert hint.compost_and_p_withheld is True
            assert "p_or_k_class_high" in hint.reasons

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
        both = dataclasses.replace(config, low_content_classes=CLASSES.low_content_classes)
        lab = assess(_inputs(preceding_nitrogen_fixing=True, content_classes={"k": "A"}), both)
        assert lab.state == "likely_deficit"


class TestBarkMulch:
    def test_bark_mulch_after_the_last_input_turns_ok_into_check(self) -> None:
        hint = assess(_inputs(last_n_binding_mulch_at=NOW - timedelta(days=2)), ACTIVE)
        assert (hint.state, hint.confidence) == ("check", "low")
        assert "bark_mulch_n_binding" in hint.reasons

    def test_bark_mulch_before_the_last_input_is_no_flag(self) -> None:
        hint = assess(_inputs(last_n_binding_mulch_at=NOW - timedelta(days=20)), ACTIVE)
        assert hint.state == "ok" and "bark_mulch_n_binding" not in hint.reasons

    def test_bark_mulch_alone_produces_no_state(self) -> None:
        hint = assess(_inputs(last_n_binding_mulch_at=NOW - timedelta(days=2)))
        assert hint.state == "insufficient_data" and "bark_mulch_n_binding" in hint.reasons

    def test_only_bark_mulch_binds(self) -> None:
        assert is_n_binding_mulch("bark_mulch") and is_n_binding_mulch(" Bark_Mulch ")
        assert not any(is_n_binding_mulch(each) for each in ("straw", "compost", None, ""))


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
