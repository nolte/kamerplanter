"""REQ-037 — unit tests for the crop-coefficient (Kc) resolution cascade."""

from app.common.enums import PlantCategory
from app.domain.calculators.crop_coefficient import GLOBAL_DEFAULT_KC, KC_DEFAULTS, resolve_kc


class TestResolveKcCascade:
    def test_phase_wins_over_everything(self):
        kc, source = resolve_kc(
            phase_kc=1.1,
            species_kc=0.9,
            plant_category=PlantCategory.OUTDOOR_VEGETABLE,
        )
        assert kc == 1.1
        assert source == "phase"

    def test_species_wins_over_category(self):
        kc, source = resolve_kc(species_kc=0.85, plant_category=PlantCategory.OUTDOOR_VEGETABLE)
        assert kc == 0.85
        assert source == "species"

    def test_category_default_applies(self):
        kc, source = resolve_kc(plant_category=PlantCategory.OUTDOOR_VEGETABLE)
        assert kc == KC_DEFAULTS[PlantCategory.OUTDOOR_VEGETABLE]
        assert source == "category_default"

    def test_global_default_when_nothing_resolves(self):
        kc, source = resolve_kc()
        assert kc == GLOBAL_DEFAULT_KC
        assert source == "global_default"

    def test_unmapped_category_falls_through_to_global(self):
        # Every PlantCategory is mapped, but a None category must fall through.
        kc, source = resolve_kc(plant_category=None)
        assert source == "global_default"

    def test_phase_kc_is_clamped_to_range(self):
        kc, source = resolve_kc(phase_kc=9.9)
        assert kc == 1.5  # clamped to FAO-56 upper bound
        assert source == "phase"

    def test_low_phase_kc_is_clamped(self):
        kc, _ = resolve_kc(phase_kc=0.0)
        assert kc == 0.1
