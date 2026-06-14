"""Unit tests for the dormancy-trigger Celery task (REQ-022 Überwinterung).

The task module imports its dependency getters and ``DormancyTrigger`` at
module level, so the mock ``app.common.dependencies`` module is installed
before import and ``DormancyTrigger`` is patched on the module per test.
Tests assert the result dict and the phase-transition side effect.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _task_module(monkeypatch):
    """Import the task module once, then patch its module-level getters.

    ``get_phase_service`` is imported lazily inside the function body, so it is
    left on the mock dependencies module; the module-level getters are
    overridden directly on the task module.
    """
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_plant_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_species_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_lifecycle_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_phase_sequence_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_phase_service = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.dormancy_checks as module

    monkeypatch.setattr(module, "get_plant_repo", mock_deps.get_plant_repo)
    monkeypatch.setattr(module, "get_species_repo", mock_deps.get_species_repo)
    monkeypatch.setattr(module, "get_lifecycle_repo", mock_deps.get_lifecycle_repo)
    monkeypatch.setattr(module, "get_phase_sequence_repo", mock_deps.get_phase_sequence_repo)

    yield module, mock_deps


def _plant(**overrides):
    data = {
        "key": "plant_1",
        "removed_on": None,
        "current_phase_key": "phase_veg",
        "species_key": "species_1",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class TestCheckDormancyTriggers:
    def test_no_plants(self, _task_module):
        module, deps = _task_module
        deps.get_plant_repo.return_value.get_all.return_value = ([], 0)

        with patch.object(module, "DormancyTrigger"):
            result = module.check_dormancy_triggers(current_temp_c=5.0, day_length_hours=9.0)

        assert result == {"triggered": 0}

    def test_skips_plant_already_dormant(self, _task_module):
        module, deps = _task_module
        plant_repo = deps.get_plant_repo.return_value
        plant_repo.get_all.return_value = ([_plant()], 1)
        plant_repo.resolve_phase_name.return_value = "dormancy"

        with patch.object(module, "DormancyTrigger") as trigger_cls:
            result = module.check_dormancy_triggers(current_temp_c=5.0, day_length_hours=9.0)
            trigger_cls.return_value.should_trigger_dormancy.assert_not_called()

        assert result == {"triggered": 0}

    def test_triggers_dormancy_when_conditions_met(self, _task_module):
        module, deps = _task_module
        plant_repo = deps.get_plant_repo.return_value
        plant_repo.get_all.return_value = ([_plant()], 1)
        plant_repo.resolve_phase_name.return_value = "vegetative"

        phase_service = MagicMock()
        deps.get_phase_service.return_value = phase_service

        with patch.object(module, "DormancyTrigger") as trigger_cls:
            trigger = trigger_cls.return_value
            trigger.should_trigger_dormancy.return_value = True
            trigger.get_dormancy_phase_key.return_value = "phase_dormant"

            result = module.check_dormancy_triggers(current_temp_c=2.0, day_length_hours=8.0)

        assert result == {"triggered": 1}
        phase_service.transition_phase.assert_called_once_with("plant_1", "phase_dormant", reason="dormancy_trigger")

    def test_no_trigger_when_conditions_not_met(self, _task_module):
        module, deps = _task_module
        plant_repo = deps.get_plant_repo.return_value
        plant_repo.get_all.return_value = ([_plant()], 1)
        plant_repo.resolve_phase_name.return_value = "vegetative"

        with patch.object(module, "DormancyTrigger") as trigger_cls:
            trigger_cls.return_value.should_trigger_dormancy.return_value = False

            result = module.check_dormancy_triggers(current_temp_c=20.0, day_length_hours=14.0)

        assert result == {"triggered": 0}

    def test_swallows_per_plant_error(self, _task_module):
        module, deps = _task_module
        plant_repo = deps.get_plant_repo.return_value
        plant_repo.get_all.return_value = ([_plant()], 1)
        plant_repo.resolve_phase_name.return_value = "vegetative"

        with patch.object(module, "DormancyTrigger") as trigger_cls:
            trigger_cls.return_value.should_trigger_dormancy.side_effect = RuntimeError("boom")

            result = module.check_dormancy_triggers(current_temp_c=2.0, day_length_hours=8.0)

        assert result == {"triggered": 0}
