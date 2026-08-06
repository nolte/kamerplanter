"""Tests for lifecycle termination on plant removal (REQ-003 E5).

``remove_plant`` optionally classifies how a lifecycle ended. An unplanned
``died`` freezes the current growth phase (no senescence transition) and records
the cause; the planned ends (``harvested``/``senesced``) and a ``cancelled``
abort only stamp ``termination_type``. A cause without ``died`` is rejected (422).
In every case the plant's open tasks — including the CARE_REMINDER-category tasks
that surface care reminders (REQ-022) — are cancelled.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import TaskCategory, TerminationCause, TerminationType
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.task import Task
from app.domain.services.plant_instance_service import PlantInstanceService


def _plant(tenant_key: str = "tenant-a") -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        tenant_key=tenant_key,
        instance_id="P-1",
        species_key="sp-1",
        planted_on=date(2025, 1, 1),
        current_phase_key="ph-veg",
        current_phase_started_at=datetime(2025, 5, 1, tzinfo=UTC),
    )


def _open_history() -> PhaseHistory:
    return PhaseHistory(
        key="h-1",
        plant_instance_key="plant-1",
        phase_key="ph-veg",
        phase_name="vegetative",
        entered_at=datetime(2025, 5, 1, tzinfo=UTC),
        exited_at=None,
        cycle_number=1,
    )


def _care_task() -> Task:
    return Task(
        _key="care-1",
        name="P-1 — watering",
        category=TaskCategory.CARE_REMINDER,
        entity_key="plant-1",
        entity_type="plant_instance",
        status="pending",
    )


class TestTermination:
    def setup_method(self) -> None:
        self.plant_repo = MagicMock()
        self.site_repo = MagicMock()
        self.rotation = MagicMock()
        self.companion = MagicMock()
        self.phase_repo = MagicMock()
        self.task_repo = MagicMock()

        self.plant = _plant()
        self.plant_repo.get_or_raise.return_value = self.plant
        self.plant_repo.get_by_key.return_value = self.plant
        self.plant_repo.update.side_effect = lambda _key, p: p
        self.task_repo.get_tasks_for_plant.return_value = [_care_task()]

    def _service(self, *, with_phase_repo: bool = True) -> PlantInstanceService:
        return PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            phase_repo=self.phase_repo if with_phase_repo else None,
            task_repo=self.task_repo,
        )

    def test_died_freezes_phase_sets_cause_and_cancels_reminders(self) -> None:
        self.phase_repo.get_phase_history.return_value = [_open_history()]
        service = self._service()

        result = service.remove_plant(
            "plant-1",
            termination_type=TerminationType.DIED,
            termination_cause=TerminationCause.DISEASE,
        )

        assert result.termination_type == TerminationType.DIED
        assert result.termination_cause == TerminationCause.DISEASE
        assert result.removed_on is not None
        # Phase frozen: the open history entry is closed in place (no new phase).
        self.phase_repo.update_phase_history.assert_called_once()
        closed = self.phase_repo.update_phase_history.call_args[0][1]
        assert closed.exited_at is not None
        self.phase_repo.create_phase_history.assert_not_called()
        # The care reminder (a CARE_REMINDER task) is cancelled alongside plain tasks.
        deleted = {c.args[0] for c in self.task_repo.delete_task.call_args_list}
        assert "care-1" in deleted
        # The task lookup is bound to the plant's tenant (#927).
        assert self.task_repo.get_tasks_for_plant.call_args.kwargs["tenant_key"] == "tenant-a"

    def test_a_tenantless_plant_does_not_trigger_an_unscoped_task_sweep(self) -> None:
        """Fail closed: no tenant, no task lookup at all (#927).

        The task cascade reads a tenant-scoped repository query. A plant whose
        tenant cannot be established must therefore leave its tasks alone rather
        than have the service fall back to a scan across every tenant.
        """
        tenantless = _plant(tenant_key="")
        self.plant_repo.get_or_raise.return_value = tenantless
        self.plant_repo.get_by_key.return_value = tenantless
        service = self._service()

        service.remove_plant("plant-1", termination_type=TerminationType.HARVESTED)

        self.task_repo.get_tasks_for_plant.assert_not_called()
        self.task_repo.delete_task.assert_not_called()

    def test_harvested_does_not_freeze_into_died_semantics(self) -> None:
        service = self._service()

        result = service.remove_plant("plant-1", termination_type=TerminationType.HARVESTED)

        assert result.termination_type == TerminationType.HARVESTED
        assert result.termination_cause is None
        assert result.removed_on is not None
        # No phase freeze / no history mutation for a planned end.
        self.phase_repo.get_phase_history.assert_not_called()
        self.phase_repo.update_phase_history.assert_not_called()

    def test_cancelled_only_stamps_type(self) -> None:
        service = self._service()

        result = service.remove_plant("plant-1", termination_type=TerminationType.CANCELLED)

        assert result.termination_type == TerminationType.CANCELLED
        assert result.termination_cause is None
        self.phase_repo.update_phase_history.assert_not_called()

    def test_cause_without_died_is_rejected(self) -> None:
        service = self._service()

        with pytest.raises(ValidationError):
            service.remove_plant(
                "plant-1",
                termination_type=TerminationType.HARVESTED,
                termination_cause=TerminationCause.PEST,
            )

    def test_cause_without_any_type_is_rejected(self) -> None:
        service = self._service()

        with pytest.raises(ValidationError):
            service.remove_plant("plant-1", termination_cause=TerminationCause.FROST)

    def test_plain_removal_is_backward_compatible(self) -> None:
        service = self._service()

        result = service.remove_plant("plant-1")

        assert result.termination_type is None
        assert result.termination_cause is None
        assert result.removed_on is not None
        # Plain removal never touches the phase history.
        self.phase_repo.update_phase_history.assert_not_called()

    def test_cross_tenant_removal_is_rejected(self) -> None:
        """SEC-001: passing a foreign tenant_key re-verifies ownership in the
        service and refuses the removal (cross-tenant → NotFound), independent of
        any router-level pre-check."""
        self.plant.tenant_key = "tenant-a"
        service = self._service()

        with pytest.raises(NotFoundError):
            service.remove_plant(
                "plant-1",
                termination_type=TerminationType.DIED,
                termination_cause=TerminationCause.PEST,
                tenant_key="tenant-b",
            )

    def test_died_without_phase_repo_still_records_loss(self) -> None:
        """Without a phase repository the loss is still recorded (no freeze possible)."""
        service = self._service(with_phase_repo=False)

        result = service.remove_plant(
            "plant-1",
            termination_type=TerminationType.DIED,
            termination_cause=TerminationCause.DROUGHT,
        )

        assert result.termination_type == TerminationType.DIED
        assert result.termination_cause == TerminationCause.DROUGHT
        assert result.removed_on is not None
