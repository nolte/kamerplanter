"""Tests for CyclicLifecycleEngine (REQ-003 D1/D4/D6/D10)."""

from app.common.enums import CycleType, FloweringStrategy, MaturityStage
from app.domain.engines.cyclic_lifecycle_engine import CyclicLifecycleEngine
from app.domain.models.lifecycle import LifecycleConfig


def _lc(**kw) -> LifecycleConfig:
    return LifecycleConfig(**kw)


def _biennial(**kw) -> LifecycleConfig:
    # the model validator requires vernalization for biennials
    return LifecycleConfig(cycle_type=CycleType.BIENNIAL, vernalization_required=True, **kw)


class TestMaxSeasons:
    def setup_method(self) -> None:
        self.engine = CyclicLifecycleEngine()

    def test_biennial_defaults_to_two_seasons(self) -> None:
        assert self.engine.effective_max_seasons(_biennial()) == 2

    def test_explicit_max_seasons_wins(self) -> None:
        assert self.engine.effective_max_seasons(_lc(cycle_type=CycleType.PERENNIAL, max_seasons=5)) == 5

    def test_perennial_unbounded(self) -> None:
        assert self.engine.effective_max_seasons(_lc(cycle_type=CycleType.PERENNIAL)) is None


class TestMaturityStage:
    def setup_method(self) -> None:
        self.engine = CyclicLifecycleEngine()
        self.lc = _lc(cycle_type=CycleType.PERENNIAL, first_bearing_year=3, expected_productive_years=10)

    def test_juvenile_below_first_bearing(self) -> None:
        assert self.engine.get_maturity_stage(self.lc, 2) == MaturityStage.JUVENILE
        assert self.engine.skips_reproductive_phases(self.lc, 2) is True

    def test_productive_in_span(self) -> None:
        assert self.engine.get_maturity_stage(self.lc, 5) == MaturityStage.PRODUCTIVE
        assert self.engine.skips_reproductive_phases(self.lc, 5) is False

    def test_declining_past_span(self) -> None:
        assert self.engine.get_maturity_stage(self.lc, 14) == MaturityStage.DECLINING

    def test_productive_when_no_bearing_info(self) -> None:
        assert self.engine.get_maturity_stage(_lc(cycle_type=CycleType.PERENNIAL), 1) == MaturityStage.PRODUCTIVE


class TestShouldRestartCycle:
    def setup_method(self) -> None:
        self.engine = CyclicLifecycleEngine()

    def test_perennial_restarts(self) -> None:
        restart, reason = self.engine.should_restart_cycle(
            _lc(cycle_type=CycleType.PERENNIAL), current_season_number=3, current_phase_name="senescence"
        )
        assert restart is True
        assert "restart" in reason.lower()

    def test_biennial_terminal_after_second_season(self) -> None:
        restart, reason = self.engine.should_restart_cycle(
            _biennial(), current_season_number=2, current_phase_name="ripening"
        )
        assert restart is False
        assert "terminal" in reason.lower()

    def test_monocarpic_terminal_after_flowering(self) -> None:
        lc = _lc(cycle_type=CycleType.PERENNIAL, flowering_strategy=FloweringStrategy.MONOCARPIC)
        restart, reason = self.engine.should_restart_cycle(lc, current_season_number=8, current_phase_name="flowering")
        assert restart is False
        assert "monocarp" in reason.lower()

    def test_monocarpic_via_extended_phase_name(self) -> None:
        # bract_coloring maps to flowering (D8) — a bromeliad's terminal bloom
        lc = _lc(cycle_type=CycleType.PERENNIAL, flowering_strategy=FloweringStrategy.MONOCARPIC)
        restart, _ = self.engine.should_restart_cycle(lc, current_season_number=8, current_phase_name="bract_coloring")
        assert restart is False

    def test_annual_never_restarts(self) -> None:
        restart, _ = self.engine.should_restart_cycle(
            _lc(cycle_type=CycleType.ANNUAL), current_season_number=1, current_phase_name="senescence"
        )
        assert restart is False
