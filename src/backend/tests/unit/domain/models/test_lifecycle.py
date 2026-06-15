import pytest
from pydantic import ValidationError

from app.common.enums import CycleType, FloweringStrategy
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig


class TestLifecycleConfig:
    def test_valid_annual(self):
        lc = LifecycleConfig(cycle_type=CycleType.ANNUAL)
        assert lc.dormancy_required is False

    def test_biennial_requires_vernalization(self):
        with pytest.raises(ValidationError, match="vernalization_required"):
            LifecycleConfig(cycle_type=CycleType.BIENNIAL, vernalization_required=False)

    def test_biennial_with_vernalization(self):
        lc = LifecycleConfig(cycle_type=CycleType.BIENNIAL, vernalization_required=True)
        assert lc.vernalization_required is True

    def test_perennial_with_dormancy(self):
        lc = LifecycleConfig(cycle_type=CycleType.PERENNIAL, dormancy_required=True)
        assert lc.dormancy_required is True


class TestGrowthPhase:
    def test_valid_phase(self):
        p = GrowthPhase(name="seedling", typical_duration_days=14, sequence_order=0)
        assert p.name == "seedling"

    def test_negative_duration(self):
        with pytest.raises(ValidationError):
            GrowthPhase(name="test", typical_duration_days=0, sequence_order=0)

    def test_terminal_phase(self):
        p = GrowthPhase(
            name="harvest",
            typical_duration_days=7,
            sequence_order=5,
            is_terminal=True,
            allows_harvest=True,
        )
        assert p.is_terminal is True
        assert p.allows_harvest is True


class TestLifecycleCultivationAndFlowering:
    """Plan WP-3 / WP-4 — cultivation lifespan split and flowering strategy."""

    def test_defaults_are_none(self):
        lc = LifecycleConfig(cycle_type=CycleType.ANNUAL)
        assert lc.cultivation_cycle_type is None
        assert lc.flowering_strategy is None

    def test_tender_perennial_split(self):
        # Tomato: botanically perennial, grown as an annual.
        lc = LifecycleConfig(
            cycle_type=CycleType.PERENNIAL,
            cultivation_cycle_type=CycleType.ANNUAL,
            flowering_strategy=FloweringStrategy.POLYCARPIC,
        )
        assert lc.cycle_type == CycleType.PERENNIAL
        assert lc.cultivation_cycle_type == CycleType.ANNUAL
        assert lc.flowering_strategy == FloweringStrategy.POLYCARPIC

    def test_monocarpic_value(self):
        lc = LifecycleConfig(cycle_type=CycleType.PERENNIAL, flowering_strategy="monocarpic")
        assert lc.flowering_strategy == FloweringStrategy.MONOCARPIC

    def test_invalid_flowering_strategy_rejected(self):
        with pytest.raises(ValidationError):
            LifecycleConfig(cycle_type=CycleType.ANNUAL, flowering_strategy="biannual")
