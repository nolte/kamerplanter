"""Data-integrity + model round-trip tests for the lifecycle_overrides backfill.

`flowering_strategy` and `cultivation_cycle_type` are seeded from
``species.yaml/lifecycle_overrides`` (the authoritative source consulted by
``seed_data.py`` and preserved by ``seed_plant_info(_extended).py``). These
DB-less tests assert the backfilled values are valid enums, are internally
consistent, and round-trip through :class:`LifecycleConfig` — including the
biennial↔vernalization invariant.
"""

from app.common.enums import CycleType, FloweringStrategy, GrowthDeterminacy
from app.domain.models.lifecycle import LifecycleConfig
from app.migrations.yaml_loader import load_yaml

_OVERRIDES: dict[str, dict] = load_yaml("species.yaml").get("lifecycle_overrides", {})


class TestOverrideDataIntegrity:
    def test_overrides_present(self):
        assert len(_OVERRIDES) > 100, "backfill should populate the override map"

    def test_all_values_are_valid_enums(self):
        for name, entry in _OVERRIDES.items():
            assert set(entry).issubset(
                {
                    "cultivation_cycle_type",
                    "flowering_strategy",
                    "growth_determinacy",
                    "cultivation_flexible",
                }
            ), name
            if "flowering_strategy" in entry:
                FloweringStrategy(entry["flowering_strategy"])  # raises on typo
            if "cultivation_cycle_type" in entry:
                CycleType(entry["cultivation_cycle_type"])
            if "growth_determinacy" in entry:
                GrowthDeterminacy(entry["growth_determinacy"])  # raises on typo
            if "cultivation_flexible" in entry:
                assert isinstance(entry["cultivation_flexible"], bool), name

    def test_biennial_cultivation_implies_monocarpic(self):
        # A crop grown as a biennial flowers once in year two, then dies.
        for name, entry in _OVERRIDES.items():
            if entry.get("cultivation_cycle_type") == "biennial":
                assert entry.get("flowering_strategy") == "monocarpic", name

    def test_known_monocarpic_species(self):
        # Bromeliad rosette (semelparous) + a classic biennial vegetable.
        assert _OVERRIDES["Aechmea fasciata"]["flowering_strategy"] == "monocarpic"
        assert _OVERRIDES["Daucus carota"]["flowering_strategy"] == "monocarpic"

    def test_known_polycarpic_species(self):
        assert _OVERRIDES["Lavandula angustifolia"]["flowering_strategy"] == "polycarpic"


class TestCultivationFlexibleFlag:
    """ADR-006 E6 (#615): the facultative-cultivation capability flag."""

    # Documented facultative cohort — each backed by Steckbrief evidence in
    # species.yaml (inline comment) / spec/knowledge/plants/*.md.
    _EXPECTED_FLEXIBLE = frozenset(
        {
            "Solanum lycopersicum",
            "Capsicum annuum",
            "Solanum melongena",
            "Physalis peruviana",
            "Pelargonium zonale",
            "Ocimum basilicum",
            "Petunia x hybrida",
            "Verbena x hybrida",
            "Viola x wittrockiana",
            "Fragaria x ananassa",
            "Begonia semperflorens",
            "Impatiens walleriana",
        }
    )

    def _flagged(self) -> set[str]:
        return {name for name, ov in _OVERRIDES.items() if ov.get("cultivation_flexible") is True}

    def test_documented_cohort_is_flagged(self):
        flagged = self._flagged()
        for name in self._EXPECTED_FLEXIBLE:
            assert name in flagged, f"{name} should be cultivation_flexible"

    def test_flag_is_only_ever_true(self):
        # The flag is additive: it is only ever set true; absence means the
        # model default (false). No entry should carry an explicit false.
        for name, ov in _OVERRIDES.items():
            if "cultivation_flexible" in ov:
                assert ov["cultivation_flexible"] is True, name

    def test_strict_annuals_are_not_flagged(self):
        # Potato and nasturtium are botanically perennial but grown strictly as
        # annuals (no standing-plant overwintering choice) — must NOT be flagged.
        flagged = self._flagged()
        assert "Solanum tuberosum" not in flagged
        assert "Tropaeolum majus" not in flagged


class TestOverrideRoundTripThroughModel:
    def test_monocarpic_perennial_round_trip(self):
        ov = _OVERRIDES["Aechmea fasciata"]
        lc = LifecycleConfig(
            cycle_type=CycleType.PERENNIAL,
            flowering_strategy=FloweringStrategy(ov["flowering_strategy"]),
        )
        assert lc.flowering_strategy == FloweringStrategy.MONOCARPIC

    def test_biennial_round_trip_holds_vernalization_invariant(self):
        # Daucus carota is loaded as a biennial via the plant_info lifecycle_config;
        # the loader must set vernalization_required, or the model rejects it.
        ov = _OVERRIDES["Daucus carota"]
        lc = LifecycleConfig(
            cycle_type=CycleType.BIENNIAL,
            vernalization_required=True,
            flowering_strategy=FloweringStrategy(ov["flowering_strategy"]),
        )
        assert lc.cycle_type == CycleType.BIENNIAL
        assert lc.flowering_strategy == FloweringStrategy.MONOCARPIC

    def test_tender_perennial_grown_as_annual_round_trip(self):
        ov = _OVERRIDES["Solanum lycopersicum"]
        lc = LifecycleConfig(
            cycle_type=CycleType.PERENNIAL,
            cultivation_cycle_type=CycleType(ov["cultivation_cycle_type"]),
            flowering_strategy=FloweringStrategy(ov["flowering_strategy"]),
        )
        assert lc.cultivation_cycle_type == CycleType.ANNUAL
        assert lc.flowering_strategy == FloweringStrategy.POLYCARPIC
