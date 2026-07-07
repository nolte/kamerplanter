"""Unit tests for the REQ-047 §3.6 ``evaluate_season_states`` Celery task.

Mocks ``app.common.dependencies`` (imported lazily inside the task body) so no
real service / repository / DB is touched. ``Site`` is imported for real so the
defensive per-document construction (AC-18) is exercised end to end.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from app.common.enums import SeasonPhase, SeasonTriggerTier
from app.domain.models.season_state import SeasonState


@pytest.fixture
def task_module(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_season_state_service = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_site_repo = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.season_tasks as module

    yield module, mock_deps


def _state(site_key: str = "s1") -> SeasonState:
    return SeasonState(
        site_key=site_key,
        phase=SeasonPhase.WINTER_DORMANCY,
        trigger_tier=SeasonTriggerTier.LIVE,
    )


class TestEvaluateSeasonStates:
    def test_noop_when_kill_switch_disabled(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", False, raising=False)

        result = module.evaluate_season_states()

        assert result == {"status": "skipped", "reason": "season_state_eval_disabled"}
        deps.get_site_repo.assert_not_called()

    def test_counts_evaluations_and_transitions(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        site_repo = MagicMock()
        site_repo.find_site_docs_by_types.return_value = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor"},
            {"_key": "s2", "name": "Beet B", "type": "greenhouse"},
        ]
        deps.get_site_repo.return_value = site_repo

        service = MagicMock()
        # s1 transitions (changed=True), s2 evaluated but unchanged.
        service.evaluate_site_detailed.side_effect = [
            (_state("s1"), True),
            (_state("s2"), False),
        ]
        deps.get_season_state_service.return_value = service

        result = module.evaluate_season_states()

        assert result == {"status": "ok", "evaluated": 2, "transitions": 1, "errors": 0}
        site_repo.find_site_docs_by_types.assert_called_once_with(["outdoor", "greenhouse"])

    def test_none_state_is_not_evaluated(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        site_repo = MagicMock()
        site_repo.find_site_docs_by_types.return_value = [{"_key": "s1", "name": "Beet", "type": "outdoor"}]
        deps.get_site_repo.return_value = site_repo

        service = MagicMock()
        service.evaluate_site_detailed.return_value = (None, False)
        deps.get_season_state_service.return_value = service

        result = module.evaluate_season_states()

        assert result == {"status": "ok", "evaluated": 0, "transitions": 0, "errors": 0}

    def test_bad_site_document_is_skipped_not_aborting_run(self, task_module, monkeypatch):
        # AC-18: a schema-drift document (missing the required ``name``) must be
        # logged and counted as an error, while the following valid site still runs.
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        site_repo = MagicMock()
        site_repo.find_site_docs_by_types.return_value = [
            {"_key": "broken"},  # no ``name`` -> Pydantic ValidationError on Site(**doc)
            {"_key": "s2", "name": "Beet B", "type": "outdoor"},
        ]
        deps.get_site_repo.return_value = site_repo

        service = MagicMock()
        service.evaluate_site_detailed.return_value = (_state("s2"), True)
        deps.get_season_state_service.return_value = service

        result = module.evaluate_season_states()

        assert result == {"status": "ok", "evaluated": 1, "transitions": 1, "errors": 1}
        # The valid site is still evaluated exactly once despite the earlier bad doc.
        service.evaluate_site_detailed.assert_called_once()

    def test_service_error_on_one_site_is_isolated(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        site_repo = MagicMock()
        site_repo.find_site_docs_by_types.return_value = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor"},
            {"_key": "s2", "name": "Beet B", "type": "outdoor"},
        ]
        deps.get_site_repo.return_value = site_repo

        service = MagicMock()
        service.evaluate_site_detailed.side_effect = [
            RuntimeError("adapter exploded"),
            (_state("s2"), False),
        ]
        deps.get_season_state_service.return_value = service

        result = module.evaluate_season_states()

        assert result == {"status": "ok", "evaluated": 1, "transitions": 0, "errors": 1}
