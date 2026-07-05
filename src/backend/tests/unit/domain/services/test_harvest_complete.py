"""Issue #367 Fix #14 — explicit 'Ernte abschließen' ends a plant's lifecycle
via the phase engine (TerminationType.HARVESTED), for both the single-plant and
the run-batch path. Creating harvest batches never auto-terminates (R14 / A1).
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import TerminationType
from app.common.exceptions import NotFoundError
from app.domain.engines.phase_transition_engine import PhaseTransitionEngine
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.harvest_service import HarvestService
from tests.conftest import wire_get_or_raise

TENANT = "tenant_a"


def _plant(key: str, *, tenant: str = TENANT, terminated: bool = False, removed: bool = False) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=tenant,
        instance_id=key.upper(),
        species_key="sp_tomato",
        planted_on=date(2026, 1, 1),
        current_phase_key="phase_flowering",
        removed_on=date(2026, 6, 1) if removed else None,
        termination_type=TerminationType.HARVESTED if terminated else None,
    )


def _service(*, plant_repo=None, run_repo=None, phase_engine=None) -> HarvestService:
    return HarvestService(
        repo=MagicMock(),
        ipm_service=MagicMock(),
        readiness_engine=None,
        quality_engine=None,
        plant_repo=plant_repo,
        run_repo=run_repo,
        phase_engine=phase_engine,
    )


class TestCompleteHarvestSinglePlant:
    def test_complete_terminates_via_phase_engine_as_harvested(self):
        plant_repo = MagicMock()
        plant_repo.get_by_key.return_value = _plant("plant_1")
        phase_engine = MagicMock()
        phase_engine.terminate.return_value = _plant("plant_1", terminated=True, removed=True)

        service = _service(plant_repo=plant_repo, phase_engine=phase_engine)
        result = service.complete_harvest("plant_1", tenant_key=TENANT, on_date=date(2026, 7, 5))

        phase_engine.terminate.assert_called_once_with("plant_1", TerminationType.HARVESTED, on_date=date(2026, 7, 5))
        assert result.termination_type == TerminationType.HARVESTED

    def test_already_terminated_plant_is_not_re_terminated(self):
        plant_repo = MagicMock()
        plant_repo.get_by_key.return_value = _plant("plant_1", terminated=True)
        phase_engine = MagicMock()

        service = _service(plant_repo=plant_repo, phase_engine=phase_engine)
        result = service.complete_harvest("plant_1", tenant_key=TENANT)

        phase_engine.terminate.assert_not_called()
        assert result.termination_type == TerminationType.HARVESTED

    def test_already_removed_plant_is_not_terminated(self):
        plant_repo = MagicMock()
        plant_repo.get_by_key.return_value = _plant("plant_1", removed=True)
        phase_engine = MagicMock()

        service = _service(plant_repo=plant_repo, phase_engine=phase_engine)
        service.complete_harvest("plant_1", tenant_key=TENANT)

        phase_engine.terminate.assert_not_called()

    def test_missing_plant_raises_not_found(self):
        plant_repo = MagicMock()
        plant_repo.get_by_key.return_value = None
        service = _service(plant_repo=plant_repo, phase_engine=MagicMock())

        with pytest.raises(NotFoundError):
            service.complete_harvest("ghost", tenant_key=TENANT)

    def test_cross_tenant_plant_raises_not_found(self):
        plant_repo = MagicMock()
        plant_repo.get_by_key.return_value = _plant("plant_1", tenant="other_tenant")
        phase_engine = MagicMock()
        service = _service(plant_repo=plant_repo, phase_engine=phase_engine)

        with pytest.raises(NotFoundError):
            service.complete_harvest("plant_1", tenant_key=TENANT)
        phase_engine.terminate.assert_not_called()

    def test_real_phase_engine_produces_terminal_state_and_closes_history(self):
        # End-to-end through the real engine: HARVESTED must set termination_type
        # + removed_on and close the open phase-history entry (no backward step).
        plant = _plant("plant_1")
        history = [
            PhaseHistory(
                _key="h1",
                plant_instance_key="plant_1",
                phase_key="phase_flowering",
                phase_name="flowering",
                entered_at=datetime(2026, 5, 1),
            )
        ]

        plant_repo = MagicMock()
        store = {"plant_1": plant}
        plant_repo.get_by_key.side_effect = lambda k: store.get(k)
        plant_repo.update.side_effect = lambda k, p: store.__setitem__(k, p) or p

        phase_repo = MagicMock()
        phase_repo.get_phase_history.return_value = history
        closed: dict = {}
        phase_repo.update_phase_history.side_effect = lambda k, h: closed.__setitem__(k, h)

        engine = PhaseTransitionEngine(phase_repo, plant_repo)
        service = _service(plant_repo=plant_repo, phase_engine=engine)

        result = service.complete_harvest("plant_1", tenant_key=TENANT, on_date=date(2026, 7, 5))

        assert result.termination_type == TerminationType.HARVESTED
        assert result.removed_on == date(2026, 7, 5)
        # The open history entry was closed (exited_at set).
        assert closed["h1"].exited_at is not None


class TestCompleteHarvestForRun:
    def _run_service(self, plants: list[PlantInstance], run_tenant: str = TENANT):
        run = MagicMock()
        run.tenant_key = run_tenant
        run.key = "run_1"
        run_repo = MagicMock()
        run_repo.get_by_key.return_value = run
        wire_get_or_raise(run_repo, "PlantingRun")
        run_repo.get_run_plants.return_value = [{"_key": p.key} for p in plants]

        store = {p.key: p for p in plants}
        plant_repo = MagicMock()
        plant_repo.get_by_key.side_effect = lambda k: store.get(k)

        phase_engine = MagicMock()
        service = _service(plant_repo=plant_repo, run_repo=run_repo, phase_engine=phase_engine)
        return service, phase_engine

    def test_terminates_only_active_instances(self):
        plants = [
            _plant("p_active_1"),
            _plant("p_terminated", terminated=True),
            _plant("p_removed", removed=True),
            _plant("p_active_2"),
        ]
        service, phase_engine = self._run_service(plants)

        result = service.complete_harvest_for_run("run_1", tenant_key=TENANT)

        assert result["completed_count"] == 2
        assert set(result["completed_keys"]) == {"p_active_1", "p_active_2"}
        terminated_keys = {call.args[0] for call in phase_engine.terminate.call_args_list}
        assert terminated_keys == {"p_active_1", "p_active_2"}
        for call in phase_engine.terminate.call_args_list:
            assert call.args[1] == TerminationType.HARVESTED

    def test_cross_tenant_run_raises_not_found(self):
        service, phase_engine = self._run_service([_plant("p1")], run_tenant="other_tenant")

        with pytest.raises(NotFoundError):
            service.complete_harvest_for_run("run_1", tenant_key=TENANT)
        phase_engine.terminate.assert_not_called()


class TestUnwiredGuards:
    def test_complete_harvest_without_engine_raises(self):
        service = _service()
        with pytest.raises(RuntimeError):
            service.complete_harvest("p1", tenant_key=TENANT)

    def test_complete_run_without_engine_raises(self):
        service = _service()
        with pytest.raises(RuntimeError):
            service.complete_harvest_for_run("run_1", tenant_key=TENANT)
