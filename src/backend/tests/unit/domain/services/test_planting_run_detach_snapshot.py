"""REQ-013 v2.1-v2.3 detach-snapshot + run-membership-guard scaffolding tests."""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import KamerplanterError


class TestRunMembershipGuard:
    """REQ-013 v2.1 W-003 — phase change on run-owned plant returns 409."""

    def _service_with_runs(self, runs):
        from app.domain.services.planting_run_service import PlantingRunService

        run_repo = MagicMock()
        run_repo.get_runs_for_plant.return_value = runs
        return PlantingRunService(
            run_repo=run_repo,
            plant_repo=MagicMock(),
            engine=MagicMock(),
            phase_repo=MagicMock(),
        )

    def test_no_runs_passes_silently(self):
        svc = self._service_with_runs([])
        # Should not raise.
        svc.assert_plant_not_run_owned("plant-1")

    def test_completed_run_does_not_block(self):
        svc = self._service_with_runs([MagicMock(key="run-1", status="completed")])
        svc.assert_plant_not_run_owned("plant-1")

    @pytest.mark.parametrize("status", ["planned", "active", "harvesting"])
    def test_active_run_raises_409_with_phase_run_owned_error_code(self, status):
        svc = self._service_with_runs([MagicMock(key="run-1", status=status)])
        with pytest.raises(KamerplanterError) as exc:
            svc.assert_plant_not_run_owned("plant-1")
        assert exc.value.status_code == 409
        assert exc.value.error_code == "phase.run_owned"
        assert "run-1" in exc.value.message
