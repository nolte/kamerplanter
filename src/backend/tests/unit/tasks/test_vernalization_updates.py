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


def _plant(**overrides):
    data = {
        "key": "plant_1",
        "removed_on": None,
        "species_key": "species_1",
        "chill_days_accumulated": 0,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class TestUpdateVernalizationProgress:
    def test_counts_cold_day_for_required_species(self, _mock_dependencies):
        plant = _plant()
        plant_repo = _mock_dependencies.get_plant_repo.return_value
        plant_repo.get_all.return_value = ([plant], 1)
        plant_repo.increment_chill_days.return_value = 1
        phase_repo = MagicMock()
        phase_repo.get_lifecycle_by_species.return_value = SimpleNamespace(vernalization_required=True)
        _mock_dependencies.get_lifecycle_repo.return_value = phase_repo

        with patch("app.domain.engines.vernalization_tracker.VernalizationTracker") as tracker_cls:
            tracker_cls.return_value.is_cold_day.return_value = True

            from app.tasks.vernalization_updates import update_vernalization_progress

            result = update_vernalization_progress(avg_temp_c=2.0)

        assert result == {"cold_day": True, "plants_tracked": 1}
        # E2: the chill day is accumulated and persisted (#1970: as a field-level increment)
        plant_repo.increment_chill_days.assert_called_once_with("plant_1")
        plant_repo.update.assert_not_called()

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


class _ReplacingPlantRepo:
    """Keeps documents like the real repository: ``update`` REPLACES the stored document.

    ``get_all`` hands out snapshots (copies), so a write of a snapshot reverts
    whatever changed in the store since the read -- the #1970 defect.
    """

    def __init__(self, docs: dict[str, dict]):
        self.docs = docs
        self.update_calls = 0

    def get_all(self, offset=0, limit=50, *, all_tenants=False):
        keys = sorted(self.docs)
        return [SimpleNamespace(**self.docs[k]) for k in keys[offset : offset + limit]], len(keys)

    def update(self, key, plant):
        self.update_calls += 1
        self.docs[key] = dict(vars(plant))
        return plant

    def increment_chill_days(self, key):
        doc = self.docs.get(key)
        if doc is None or doc["removed_on"] is not None:
            return None
        doc["chill_days_accumulated"] += 1
        return doc["chill_days_accumulated"]


def _run_cold_day(deps, repo, lifecycle_lookup=None):
    lifecycle = MagicMock()
    lifecycle.get_lifecycle_by_species.side_effect = lifecycle_lookup or (
        lambda _species: SimpleNamespace(vernalization_required=True)
    )
    deps.get_plant_repo.return_value = repo
    deps.get_lifecycle_repo.return_value = lifecycle
    with patch("app.domain.engines.vernalization_tracker.VernalizationTracker") as tracker_cls:
        tracker_cls.return_value.is_cold_day.return_value = True
        from app.tasks.vernalization_updates import update_vernalization_progress

        return update_vernalization_progress(avg_temp_c=2.0)


class TestConcurrentPlantChanges:
    """#1970: the chill-day write must not revert a change made between read and write."""

    def test_a_phase_change_between_read_and_write_survives(self, _mock_dependencies):
        repo = _ReplacingPlantRepo({"p1": {**vars(_plant(key="p1")), "current_phase_key": "veg"}})

        def interleave(_species):
            repo.docs["p1"]["current_phase_key"] = "flower"  # a phase transition lands mid-task
            return SimpleNamespace(vernalization_required=True)

        result = _run_cold_day(_mock_dependencies, repo, interleave)

        assert result["plants_tracked"] == 1
        assert repo.docs["p1"]["chill_days_accumulated"] == 1
        assert repo.docs["p1"]["current_phase_key"] == "flower"

    def test_a_removal_between_read_and_write_is_not_resurrected(self, _mock_dependencies):
        repo = _ReplacingPlantRepo({"p1": vars(_plant(key="p1"))})

        def interleave(_species):
            repo.docs["p1"]["removed_on"] = "2026-10-01"
            return SimpleNamespace(vernalization_required=True)

        result = _run_cold_day(_mock_dependencies, repo, interleave)

        assert repo.docs["p1"]["removed_on"] == "2026-10-01"
        assert repo.docs["p1"]["chill_days_accumulated"] == 0
        assert result["plants_tracked"] == 0


class TestAllPlantsAreVisited:
    def test_plants_beyond_the_first_page_are_counted(self, _mock_dependencies):
        docs = {f"p{i:05d}": vars(_plant(key=f"p{i:05d}")) for i in range(2500)}
        repo = _ReplacingPlantRepo(docs)

        result = _run_cold_day(_mock_dependencies, repo)

        assert result["plants_tracked"] == 2500
        assert all(d["chill_days_accumulated"] == 1 for d in docs.values())
