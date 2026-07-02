"""Tests for the #305 lifecycle-engine core: E3 controlled reversion + E5
termination/phase-freeze, plus the new model fields."""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import (
    GrowthDeterminacy,
    TerminationCause,
    TerminationType,
    TransitionTriggerType,
)
from app.common.exceptions import PhaseTransitionError
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import PhaseHistory, PhaseTransitionRule
from app.domain.models.plant_instance import PlantInstance


def _phase(key: str, name: str, order: int) -> GrowthPhase:
    return GrowthPhase(key=key, name=name, sequence_order=order, lifecycle_key="lc-1", typical_duration_days=30)


def _plant(current_phase_key: str) -> PlantInstance:
    return PlantInstance(
        instance_id="p-1",
        species_key="sp-1",
        planted_on=date(2025, 1, 1),
        current_phase_key=current_phase_key,
        current_phase_started_at=datetime(2025, 3, 1, tzinfo=UTC),
    )


class TestControlledReversion:
    """E3: flowering → vegetative allowed only via an is_reversion rule."""

    def setup_method(self) -> None:
        self.phase_repo = MagicMock()
        self.plant_repo = MagicMock()
        self.engine = PhaseTransitionEngine(self.phase_repo, self.plant_repo)
        self.veg = _phase("ph-veg", "vegetative", 3)
        self.flower = _phase("ph-flr", "flowering", 4)
        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-veg": self.veg,
            "ph-flr": self.flower,
        }.get(k)

    def test_backward_without_reversion_rule_is_blocked(self) -> None:
        self.plant_repo.get_by_key.return_value = _plant("ph-flr")
        self.phase_repo.get_transition_rules.return_value = []
        with pytest.raises(PhaseTransitionError, match="Backward transition not allowed"):
            self.engine.validate_transition("p-1", "ph-veg")

    def test_reversion_rule_allows_backward_with_warning(self) -> None:
        self.plant_repo.get_by_key.return_value = _plant("ph-flr")
        self.phase_repo.get_transition_rules.return_value = [
            PhaseTransitionRule(from_phase_key="ph-flr", to_phase_key="ph-veg", is_reversion=True)
        ]
        warnings = self.engine.validate_transition("p-1", "ph-veg")
        assert any("Controlled reversion" in w for w in warnings)

    def test_execute_reversion_increments_count(self) -> None:
        plant = _plant("ph-flr")
        self.plant_repo.get_by_key.return_value = plant
        self.plant_repo.update.side_effect = lambda _k, p: p
        self.phase_repo.get_phase_history.return_value = []
        self.phase_repo.get_transition_rules.return_value = [
            PhaseTransitionRule(from_phase_key="ph-flr", to_phase_key="ph-veg", is_reversion=True)
        ]
        result = self.engine.execute_transition("p-1", "ph-veg", reason="re-veg")
        assert result.reversion_count == 1
        assert result.current_phase_key == "ph-veg"


class TestTermination:
    """E5: terminate distinguishes planned end from unplanned loss and freezes the phase."""

    def setup_method(self) -> None:
        self.phase_repo = MagicMock()
        self.plant_repo = MagicMock()
        self.engine = PhaseTransitionEngine(self.phase_repo, self.plant_repo)
        self.plant_repo.update.side_effect = lambda _k, p: p

    def test_died_freezes_open_phase_and_sets_cause(self) -> None:
        plant = _plant("ph-flr")
        self.plant_repo.get_by_key.return_value = plant
        open_hist = PhaseHistory(
            key="h-1",
            plant_instance_key="p-1",
            phase_key="ph-flr",
            phase_name="flowering",
            entered_at=datetime(2025, 3, 1, tzinfo=UTC),
        )
        self.phase_repo.get_phase_history.return_value = [open_hist]

        result = self.engine.terminate("p-1", TerminationType.DIED, termination_cause=TerminationCause.DISEASE)

        assert result.termination_type == TerminationType.DIED
        assert result.termination_cause == TerminationCause.DISEASE
        assert result.removed_on is not None
        # the open phase-history entry was closed (frozen), no senescence transition created
        self.phase_repo.update_phase_history.assert_called_once()
        self.phase_repo.create_phase_history.assert_not_called()

    def test_cause_without_died_is_rejected(self) -> None:
        self.plant_repo.get_by_key.return_value = _plant("ph-flr")
        self.phase_repo.get_phase_history.return_value = []
        with pytest.raises(PhaseTransitionError, match="only valid for termination_type='died'"):
            self.engine.terminate("p-1", TerminationType.HARVESTED, termination_cause=TerminationCause.DISEASE)

    def test_harvested_is_planned_end(self) -> None:
        self.plant_repo.get_by_key.return_value = _plant("ph-rip")
        self.phase_repo.get_phase_history.return_value = []
        result = self.engine.terminate("p-1", TerminationType.HARVESTED)
        assert result.termination_type == TerminationType.HARVESTED
        assert result.termination_cause is None


class TestNewModelFields:
    """F: the new enum-backed model fields accept the documented values."""

    def test_lifecycle_growth_determinacy(self) -> None:
        lc = LifecycleConfig(growth_determinacy=GrowthDeterminacy.INDETERMINATE)
        assert lc.growth_determinacy is GrowthDeterminacy.INDETERMINATE
        assert LifecycleConfig().growth_determinacy is None  # defaults to determinate

    def test_transition_rule_flags(self) -> None:
        rule = PhaseTransitionRule(
            from_phase_key="a",
            to_phase_key="b",
            trigger_type=TransitionTriggerType.PHOTOPERIOD_BASED,
            is_reversion=True,
            is_premature=True,
            priority=5,
        )
        assert rule.trigger_type is TransitionTriggerType.PHOTOPERIOD_BASED
        assert rule.is_reversion and rule.is_premature
        assert rule.priority == 5

    def test_plant_instance_termination_defaults(self) -> None:
        plant = PlantInstance(instance_id="p", species_key="s", planted_on=date(2025, 1, 1))
        assert plant.termination_type is None
        assert plant.reversion_count == 0
