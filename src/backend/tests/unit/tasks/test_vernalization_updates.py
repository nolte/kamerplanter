"""Unit tests for the vernalization-tracking Celery task (REQ-022).

Mocks ``app.common.dependencies`` (imported lazily inside the task body) and
patches ``VernalizationTracker`` at its import location. Tests assert the
result dict and the cold-day / required-flag branches.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_dependencies(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_plant_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_lifecycle_repo = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    yield mock_deps

    if "app.tasks.vernalization_updates" in sys.modules:
        del sys.modules["app.tasks.vernalization_updates"]


def _plant(**overrides):
    data = {"key": "plant_1", "removed_on": None, "species_key": "species_1"}
    data.update(overrides)
    return SimpleNamespace(**data)


class TestUpdateVernalizationProgress:
    def test_counts_cold_day_for_required_species(self, _mock_dependencies):
        _mock_dependencies.get_plant_repo.return_value.get_all.return_value = ([_plant()], 1)
        phase_repo = MagicMock()
        phase_repo.get_lifecycle_by_species.return_value = SimpleNamespace(vernalization_required=True)
        _mock_dependencies.get_lifecycle_repo.return_value = phase_repo

        with patch("app.domain.engines.vernalization_tracker.VernalizationTracker") as tracker_cls:
            tracker_cls.return_value.is_cold_day.return_value = True

            from app.tasks.vernalization_updates import update_vernalization_progress

            result = update_vernalization_progress(avg_temp_c=2.0)

        assert result == {"cold_day": True, "plants_tracked": 1}

    def test_skips_species_without_vernalization(self, _mock_dependencies):
        _mock_dependencies.get_plant_repo.return_value.get_all.return_value = ([_plant()], 1)
        phase_repo = MagicMock()
        phase_repo.get_lifecycle_by_species.return_value = SimpleNamespace(vernalization_required=False)
        _mock_dependencies.get_lifecycle_repo.return_value = phase_repo

        with patch("app.domain.engines.vernalization_tracker.VernalizationTracker") as tracker_cls:
            tracker_cls.return_value.is_cold_day.return_value = True

            from app.tasks.vernalization_updates import update_vernalization_progress

            result = update_vernalization_progress(avg_temp_c=2.0)

        assert result == {"cold_day": True, "plants_tracked": 0}

    def test_warm_day_tracks_nothing(self, _mock_dependencies):
        _mock_dependencies.get_plant_repo.return_value.get_all.return_value = ([_plant()], 1)
        phase_repo = MagicMock()
        phase_repo.get_lifecycle_by_species.return_value = SimpleNamespace(vernalization_required=True)
        _mock_dependencies.get_lifecycle_repo.return_value = phase_repo

        with patch("app.domain.engines.vernalization_tracker.VernalizationTracker") as tracker_cls:
            tracker_cls.return_value.is_cold_day.return_value = False

            from app.tasks.vernalization_updates import update_vernalization_progress

            result = update_vernalization_progress(avg_temp_c=18.0)

        assert result == {"cold_day": False, "plants_tracked": 0}

    def test_skips_removed_plants(self, _mock_dependencies):
        _mock_dependencies.get_plant_repo.return_value.get_all.return_value = (
            [_plant(removed_on="2026-01-01")],
            1,
        )
        phase_repo = MagicMock()
        _mock_dependencies.get_lifecycle_repo.return_value = phase_repo

        with patch("app.domain.engines.vernalization_tracker.VernalizationTracker") as tracker_cls:
            tracker_cls.return_value.is_cold_day.return_value = True

            from app.tasks.vernalization_updates import update_vernalization_progress

            result = update_vernalization_progress(avg_temp_c=2.0)

        assert result == {"cold_day": True, "plants_tracked": 0}
        phase_repo.get_lifecycle_by_species.assert_not_called()
