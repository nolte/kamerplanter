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
            assert set(entry).issubset({"cultivation_cycle_type", "flowering_strategy", "growth_determinacy"}), name
            if "flowering_strategy" in entry:
                FloweringStrategy(entry["flowering_strategy"])  # raises on typo
            if "cultivation_cycle_type" in entry:
                CycleType(entry["cultivation_cycle_type"])
            if "growth_determinacy" in entry:
                GrowthDeterminacy(entry["growth_determinacy"])  # raises on typo

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
