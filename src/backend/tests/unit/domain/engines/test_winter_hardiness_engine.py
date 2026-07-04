import pytest

from app.common.enums import FrostTolerance, HardinessRating, WinterAction, WinterHardinessLight
from app.common.exceptions import WinterPathViolationError
from app.domain.engines.winter_hardiness_engine import (
    derive_winter_path,
    evaluate_winter_hardiness,
    map_frost_sensitivity,
    parse_zone,
    validate_d5_invariant,
)
from app.domain.models.overwintering_profile import OverwinteringProfile


class TestZoneParsing:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("7b", 7.5), ("8a", 8.0), ("7", 7.0), ("USDA 6b", 6.5), ("z10", 10.0), (None, None), ("", None)],
    )
    def test_parse_zone(self, raw, expected) -> None:
        assert parse_zone(raw) == expected


class TestFrostSensitivityMapping:
    @pytest.mark.parametrize(
        ("frost", "mapped"),
        [
            (FrostTolerance.VERY_HARDY, "hardy"),
            (FrostTolerance.HARDY, "hardy"),
            (FrostTolerance.MODERATE, "half_hardy"),
            (FrostTolerance.SENSITIVE, "tender"),
            (None, None),
        ],
    )
    def test_map(self, frost, mapped) -> None:
        assert map_frost_sensitivity(frost) == mapped


class TestEvaluateWinterHardiness:
    def test_green_hardy_zone_covered(self) -> None:
        assert evaluate_winter_hardiness(FrostTolerance.VERY_HARDY, "6a", "7a") == WinterHardinessLight.GREEN

    def test_yellow_half_hardy(self) -> None:
        assert evaluate_winter_hardiness(FrostTolerance.MODERATE, "6a", "8a") == WinterHardinessLight.YELLOW

    def test_yellow_marginal_zone_gap(self) -> None:
        # site exactly one zone colder than required → yellow (delta == -1)
        assert evaluate_winter_hardiness(FrostTolerance.HARDY, "8a", "7a") == WinterHardinessLight.YELLOW

    def test_red_tender(self) -> None:
        assert evaluate_winter_hardiness(FrostTolerance.SENSITIVE, "9a", "8a") == WinterHardinessLight.RED

    def test_red_large_zone_gap(self) -> None:
        # site more than one zone too cold → red (delta < -1)
        assert evaluate_winter_hardiness(FrostTolerance.HARDY, "8a", "6a") == WinterHardinessLight.RED

    def test_no_zone_info_uses_frost_sensitivity(self) -> None:
        assert evaluate_winter_hardiness(FrostTolerance.HARDY, None, None) == WinterHardinessLight.GREEN
        assert evaluate_winter_hardiness(FrostTolerance.MODERATE, None, None) == WinterHardinessLight.YELLOW
        assert evaluate_winter_hardiness(FrostTolerance.SENSITIVE, None, None) == WinterHardinessLight.RED

    def test_no_info_at_all_defaults_yellow(self) -> None:
        assert evaluate_winter_hardiness(None, None, None) == WinterHardinessLight.YELLOW


class TestDeriveWinterPath:
    def test_green_and_yellow_path_a(self) -> None:
        assert derive_winter_path(WinterHardinessLight.GREEN) == "A"
        assert derive_winter_path(WinterHardinessLight.YELLOW) == "A"

    def test_red_path_b(self) -> None:
        assert derive_winter_path(WinterHardinessLight.RED) == "B"


class TestD5Invariant:
    def _profile(self, rating: HardinessRating, action: WinterAction) -> OverwinteringProfile:
        return OverwinteringProfile(
            plant_key="p1",
            hardiness_rating=rating,
            winter_action=action,
            winter_action_month=10,
        )

    def test_path_a_allows_in_situ_action(self) -> None:
        profile = self._profile(HardinessRating.NEEDS_PROTECTION, WinterAction.MULCH)
        validate_d5_invariant(profile, WinterHardinessLight.YELLOW)  # no raise

    def test_path_a_rejects_move_indoors(self) -> None:
        profile = self._profile(HardinessRating.HARDY, WinterAction.MOVE_INDOORS)
        with pytest.raises(WinterPathViolationError):
            validate_d5_invariant(profile, WinterHardinessLight.GREEN)

    def test_path_b_allows_relocation(self) -> None:
        profile = self._profile(HardinessRating.DIG_AND_STORE, WinterAction.DIG_STORE)
        validate_d5_invariant(profile, WinterHardinessLight.RED)  # no raise

    def test_path_b_rejects_mulch(self) -> None:
        profile = self._profile(HardinessRating.FROST_FREE, WinterAction.MULCH)
        with pytest.raises(WinterPathViolationError):
            validate_d5_invariant(profile, WinterHardinessLight.RED)
