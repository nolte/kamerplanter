"""Unit tests for the phase auto-transition Celery task (REQ-003).

The task module imports its dependency getters at module level, so the mock
``app.common.dependencies`` module is installed before the task module is
imported. Collaborators are doubled with ``MagicMock``. Tests assert the
result dict and which phase-service methods are invoked.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _task_module(monkeypatch):
    """Import the task module once, then patch its module-level getters.

    The task module captures ``get_phase_service`` / ``get_plant_repo`` at
    import time, so the bindings are overridden directly on the module.
    """
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_phase_service = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_plant_repo = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.phase_transitions as module

    monkeypatch.setattr(module, "get_phase_service", mock_deps.get_phase_service)
    monkeypatch.setattr(module, "get_plant_repo", mock_deps.get_plant_repo)

    deps = SimpleNamespace(
        get_phase_service=mock_deps.get_phase_service,
        get_plant_repo=mock_deps.get_plant_repo,
    )
    yield module, deps


def _plant(**overrides):
    data = {"key": "plant_1", "removed_on": None, "current_phase_key": "phase_veg"}
    data.update(overrides)
    return SimpleNamespace(**data)


class TestCheckAutoTransitions:
    def test_no_plants(self, _task_module):
        module, deps = _task_module
        deps.get_plant_repo.return_value.get_all.return_value = ([], 0)
        deps.get_phase_service.return_value = MagicMock()

        result = module.check_auto_transitions()

        assert result == {"transitioned": 0, "errors": 0, "checked": 0}

    def test_skips_removed_and_phaseless_plants(self, _task_module):
        module, deps = _task_module
        plants = [_plant(removed_on="2026-01-01"), _plant(current_phase_key=None)]
        deps.get_plant_repo.return_value.get_all.return_value = (plants, 2)
        phase_service = MagicMock()
        deps.get_phase_service.return_value = phase_service

        result = module.check_auto_transitions()

        assert result == {"transitioned": 0, "errors": 0, "checked": 2}
        phase_service.transition_phase.assert_not_called()

    def test_transitions_when_time_rule_met(self, _task_module):
        module, deps = _task_module
        deps.get_plant_repo.return_value.get_all.return_value = ([_plant()], 1)

        phase_service = MagicMock()
        phase_service.get_current_phase.return_value = {"days_in_phase": 30}
        phase_service.get_transition_rules.return_value = [
            SimpleNamespace(
                trigger_type="time_based",
                auto_transition_after_days=28,
                to_phase_key="phase_flower",
            )
        ]
        deps.get_phase_service.return_value = phase_service

        result = module.check_auto_transitions()

        assert result == {"transitioned": 1, "errors": 0, "checked": 1}
        phase_service.transition_phase.assert_called_once_with("plant_1", "phase_flower", reason="auto_time_based")

    def test_no_transition_when_days_below_threshold(self, _task_module):
        module, deps = _task_module
        deps.get_plant_repo.return_value.get_all.return_value = ([_plant()], 1)

        phase_service = MagicMock()
        phase_service.get_current_phase.return_value = {"days_in_phase": 10}
        phase_service.get_transition_rules.return_value = [
            SimpleNamespace(
                trigger_type="time_based",
                auto_transition_after_days=28,
                to_phase_key="phase_flower",
            )
        ]
        deps.get_phase_service.return_value = phase_service

        result = module.check_auto_transitions()

        assert result == {"transitioned": 0, "errors": 0, "checked": 1}
        phase_service.transition_phase.assert_not_called()

    def test_counts_error_without_crashing(self, _task_module):
        module, deps = _task_module
        deps.get_plant_repo.return_value.get_all.return_value = ([_plant()], 1)

        phase_service = MagicMock()
        phase_service.get_current_phase.side_effect = RuntimeError("lookup failed")
        deps.get_phase_service.return_value = phase_service

        result = module.check_auto_transitions()

        assert result == {"transitioned": 0, "errors": 1, "checked": 1}
