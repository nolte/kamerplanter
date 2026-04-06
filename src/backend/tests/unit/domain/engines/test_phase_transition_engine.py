"""Tests for PhaseTransitionEngine — perennial cycle restart support."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import CycleType
from app.common.exceptions import PhaseTransitionError
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance


def _make_phase(
    key: str,
    name: str,
    sequence_order: int,
    lifecycle_key: str = "lc-1",
    *,
    is_terminal: bool = False,
    allows_harvest: bool = False,
    is_recurring: bool = False,
) -> GrowthPhase:
    return GrowthPhase(
        key=key,
        name=name,
        sequence_order=sequence_order,
        lifecycle_key=lifecycle_key,
        typical_duration_days=30,
        is_terminal=is_terminal,
        allows_harvest=allows_harvest,
        is_recurring=is_recurring,
    )


def _make_lifecycle(
    key: str = "lc-1",
    cycle_type: CycleType = CycleType.PERENNIAL,
    cycle_restart_phase_order: int | None = 1,
) -> LifecycleConfig:
    return LifecycleConfig(
        key=key,
        cycle_type=cycle_type,
        cycle_restart_phase_order=cycle_restart_phase_order,
    )


def _make_plant(
    key: str = "plant-1",
    current_phase_key: str | None = None,
) -> PlantInstance:
    plant = MagicMock(spec=PlantInstance)
    plant.key = key
    plant.current_phase_key = current_phase_key
    plant.current_phase_started_at = datetime(2025, 1, 1, tzinfo=UTC)
    return plant


class TestPerennialCycleRestart:
    """Test perennial cycle restart transitions."""

    def setup_method(self) -> None:
        self.phase_repo = MagicMock()
        self.plant_repo = MagicMock()
        self.engine = PhaseTransitionEngine(self.phase_repo, self.plant_repo)

        # Perennial phases: dormancy(1) -> sprouting(2) -> vegetative(3) -> flowering(4) -> senescence(5, terminal)
        self.dormancy = _make_phase("ph-1", "dormancy", 1, is_recurring=True)
        self.sprouting = _make_phase("ph-2", "sprouting", 2, is_recurring=True)
        self.vegetative = _make_phase("ph-3", "vegetative", 3, is_recurring=True)
        self.flowering = _make_phase("ph-4", "flowering", 4, is_recurring=True)
        self.senescence = _make_phase("ph-5", "senescence", 5, is_terminal=True, is_recurring=True)

        self.lifecycle = _make_lifecycle(cycle_restart_phase_order=1)

    def test_perennial_cycle_restart_allowed_without_force(self) -> None:
        """Transition from terminal phase back to restart phase is allowed for perennials."""
        plant = _make_plant(current_phase_key="ph-5")
        self.plant_repo.get_by_key.return_value = plant
        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-5": self.senescence,
            "ph-1": self.dormancy,
        }.get(k)
        self.phase_repo.get_lifecycle_by_key.return_value = self.lifecycle
        self.phase_repo.get_transition_rules.return_value = []

        warnings = self.engine.validate_transition("plant-1", "ph-1")

        assert len(warnings) == 1
        assert "Perennial cycle restart" in warnings[0]

    def test_annual_cycle_restart_blocked(self) -> None:
        """Backward transition is blocked for annuals (no cycle restart)."""
        plant = _make_plant(current_phase_key="ph-5")
        self.plant_repo.get_by_key.return_value = plant

        annual_senescence = _make_phase(
            "ph-5",
            "senescence",
            5,
            lifecycle_key="lc-annual",
            is_terminal=True,
        )
        annual_dormancy = _make_phase("ph-1", "dormancy", 1, lifecycle_key="lc-annual")
        annual_lifecycle = _make_lifecycle(
            key="lc-annual",
            cycle_type=CycleType.ANNUAL,
            cycle_restart_phase_order=None,
        )

        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-5": annual_senescence,
            "ph-1": annual_dormancy,
        }.get(k)
        self.phase_repo.get_lifecycle_by_key.return_value = annual_lifecycle

        with pytest.raises(PhaseTransitionError, match="Backward transition not allowed"):
            self.engine.validate_transition("plant-1", "ph-1")

    def test_backward_transition_to_non_restart_phase_blocked(self) -> None:
        """Backward transition to a phase other than the restart phase is still blocked."""
        plant = _make_plant(current_phase_key="ph-5")
        self.plant_repo.get_by_key.return_value = plant
        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-5": self.senescence,
            "ph-3": self.vegetative,
        }.get(k)
        self.phase_repo.get_lifecycle_by_key.return_value = self.lifecycle

        with pytest.raises(PhaseTransitionError, match="Backward transition not allowed"):
            self.engine.validate_transition("plant-1", "ph-3")

    def test_cycle_number_incremented_on_restart(self) -> None:
        """Cycle number is incremented when executing a perennial cycle restart."""
        plant = _make_plant(current_phase_key="ph-5")
        self.plant_repo.get_by_key.return_value = plant
        self.plant_repo.update.return_value = plant

        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-5": self.senescence,
            "ph-1": self.dormancy,
        }.get(k)
        self.phase_repo.get_lifecycle_by_key.return_value = self.lifecycle
        self.phase_repo.get_transition_rules.return_value = []

        # Existing history from cycle 1
        existing_history = [
            PhaseHistory(
                key="h-1",
                plant_instance_key="plant-1",
                phase_key="ph-5",
                phase_name="senescence",
                entered_at=datetime(2025, 6, 1, tzinfo=UTC),
                cycle_number=1,
            ),
        ]
        self.phase_repo.get_phase_history.return_value = existing_history

        self.engine.execute_transition("plant-1", "ph-1", reason="seasonal_restart")

        # Verify new history entry has cycle_number=2
        create_call = self.phase_repo.create_phase_history.call_args[0][0]
        assert create_call.cycle_number == 2
        assert create_call.phase_name == "dormancy"

    def test_cycle_number_not_incremented_on_forward_transition(self) -> None:
        """Cycle number stays the same during normal forward transitions."""
        plant = _make_plant(current_phase_key="ph-1")
        self.plant_repo.get_by_key.return_value = plant
        self.plant_repo.update.return_value = plant

        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-1": self.dormancy,
            "ph-2": self.sprouting,
        }.get(k)
        self.phase_repo.get_transition_rules.return_value = []

        existing_history = [
            PhaseHistory(
                key="h-1",
                plant_instance_key="plant-1",
                phase_key="ph-1",
                phase_name="dormancy",
                entered_at=datetime(2025, 1, 1, tzinfo=UTC),
                cycle_number=2,
            ),
        ]
        self.phase_repo.get_phase_history.return_value = existing_history

        self.engine.execute_transition("plant-1", "ph-2", reason="manual")

        create_call = self.phase_repo.create_phase_history.call_args[0][0]
        assert create_call.cycle_number == 2
        assert create_call.phase_name == "sprouting"

    def test_non_terminal_phase_backward_transition_blocked(self) -> None:
        """Backward transition from a non-terminal phase is blocked even for perennials."""
        plant = _make_plant(current_phase_key="ph-3")
        self.plant_repo.get_by_key.return_value = plant
        self.phase_repo.get_phase_by_key.side_effect = lambda k: {
            "ph-3": self.vegetative,
            "ph-1": self.dormancy,
        }.get(k)
        # vegetative is not terminal, so _is_perennial_cycle_restart returns False
        self.phase_repo.get_lifecycle_by_key.return_value = self.lifecycle

        with pytest.raises(PhaseTransitionError, match="Backward transition not allowed"):
            self.engine.validate_transition("plant-1", "ph-1")


class TestGetCurrentPhasePerennial:
    """Test PhaseService.get_current_phase returns perennial metadata."""

    def test_returns_cycle_type_and_harvest_info(self) -> None:
        from app.domain.services.phase_service import PhaseService

        phase_repo = MagicMock()
        plant_repo = MagicMock()
        service = PhaseService(phase_repo, plant_repo)

        plant = MagicMock()
        plant.current_phase_key = "ph-3"
        plant.current_phase_started_at = datetime(2025, 6, 1, tzinfo=UTC)
        plant_repo.get_by_key.return_value = plant

        active_history = PhaseHistory(
            key="h-1",
            plant_instance_key="plant-1",
            phase_key="ph-3",
            phase_name="vegetative",
            entered_at=datetime(2025, 6, 1, tzinfo=UTC),
            cycle_number=2,
        )
        phase_repo.get_phase_history.return_value = [active_history]

        veg_phase = _make_phase("ph-3", "vegetative", 3)
        phase_repo.get_phase_by_key.return_value = veg_phase
        phase_repo.get_transition_rules.return_value = []

        lifecycle = _make_lifecycle(cycle_type=CycleType.PERENNIAL)
        phase_repo.get_lifecycle_by_key.return_value = lifecycle

        # Phases: no harvest phase
        phases = [
            _make_phase("ph-1", "dormancy", 1, is_recurring=True),
            _make_phase("ph-3", "vegetative", 3, is_recurring=True),
            _make_phase("ph-5", "senescence", 5, is_terminal=True, is_recurring=True),
        ]
        phase_repo.get_phases_by_lifecycle.return_value = phases

        result = service.get_current_phase("plant-1")

        assert result["cycle_type"] == "perennial"
        assert result["cycle_number"] == 2
        assert result["has_harvest_phase"] is False

    def test_returns_has_harvest_phase_true(self) -> None:
        from app.domain.services.phase_service import PhaseService

        phase_repo = MagicMock()
        plant_repo = MagicMock()
        service = PhaseService(phase_repo, plant_repo)

        plant = MagicMock()
        plant.current_phase_key = "ph-2"
        plant.current_phase_started_at = datetime(2025, 6, 1, tzinfo=UTC)
        plant_repo.get_by_key.return_value = plant

        active_history = PhaseHistory(
            key="h-1",
            plant_instance_key="plant-1",
            phase_key="ph-2",
            phase_name="vegetative",
            entered_at=datetime(2025, 6, 1, tzinfo=UTC),
            cycle_number=1,
        )
        phase_repo.get_phase_history.return_value = [active_history]

        veg_phase = _make_phase("ph-2", "vegetative", 2, lifecycle_key="lc-annual")
        phase_repo.get_phase_by_key.return_value = veg_phase
        phase_repo.get_transition_rules.return_value = []

        lifecycle = _make_lifecycle(key="lc-annual", cycle_type=CycleType.ANNUAL, cycle_restart_phase_order=None)
        phase_repo.get_lifecycle_by_key.return_value = lifecycle

        phases = [
            _make_phase("ph-1", "seedling", 1, lifecycle_key="lc-annual"),
            _make_phase("ph-2", "vegetative", 2, lifecycle_key="lc-annual"),
            _make_phase("ph-3", "harvest", 3, lifecycle_key="lc-annual", allows_harvest=True, is_terminal=True),
        ]
        phase_repo.get_phases_by_lifecycle.return_value = phases

        result = service.get_current_phase("plant-1")

        assert result["cycle_type"] == "annual"
        assert result["cycle_number"] == 1
        assert result["has_harvest_phase"] is True
