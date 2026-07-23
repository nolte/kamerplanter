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
    mock_deps.get_plant_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_quarter_climate_service = MagicMock()  # type: ignore[attr-defined]
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
        # #706: balcony sites are frost-exposed and must be evaluated too
        # (OVERWINTERING_SITE_TYPES). Compare as a set — frozenset order varies.
        site_repo.find_site_docs_by_types.assert_called_once()
        (called_types,) = site_repo.find_site_docs_by_types.call_args[0]
        assert set(called_types) == {"outdoor", "greenhouse", "balcony"}

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


def _plant(key: str, *, removed: bool = False):
    from datetime import date

    from app.domain.models.plant_instance import PlantInstance

    return PlantInstance(
        _key=key,
        tenant_key="t1",
        instance_id=key,
        species_key="sp1",
        planted_on=date(2024, 1, 1),
        removed_on=date(2024, 2, 1) if removed else None,
    )


class TestEvaluateQuarterClimate:
    def test_noop_when_kill_switch_disabled(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", False, raising=False)

        result = module.evaluate_quarter_climate()

        assert result == {"status": "skipped", "reason": "season_state_eval_disabled"}
        deps.get_plant_repo.assert_not_called()

    def test_counts_warnings_and_skips_removed(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        plant_repo = MagicMock()
        plant_repo.get_all.return_value = ([_plant("p1"), _plant("p2"), _plant("p3", removed=True)], 3)
        deps.get_plant_repo.return_value = plant_repo

        service = MagicMock()
        # p1 raises a warning task, p2 does not.
        service.evaluate_plant.side_effect = [object(), None]
        deps.get_quarter_climate_service.return_value = service

        result = module.evaluate_quarter_climate()

        assert result == {"status": "ok", "evaluated": 2, "warnings": 1, "errors": 0}

    def test_one_bad_plant_is_isolated(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        plant_repo = MagicMock()
        plant_repo.get_all.return_value = ([_plant("p1"), _plant("p2")], 2)
        deps.get_plant_repo.return_value = plant_repo

        service = MagicMock()
        service.evaluate_plant.side_effect = [RuntimeError("boom"), None]
        deps.get_quarter_climate_service.return_value = service

        result = module.evaluate_quarter_climate()

        assert result == {"status": "ok", "evaluated": 2, "warnings": 0, "errors": 1}

    def test_ac6_union_frost_exposed_locations_with_type_selected_sites(self, task_module, monkeypatch):
        """AC-6: Site selection includes both type-based and frost-exposed-location sites.

        The task unions type-selected sites (outdoor/greenhouse/balcony) with any site
        that owns ≥1 frost_exposed=true location, so a mixed indoor site with a
        frost-exposed corner is evaluated. A site in both sets is de-duplicated by _key.
        """
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        # Type-based: 2 outdoor sites
        type_docs = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor"},
            {"_key": "s2", "name": "Beet B", "type": "outdoor"},
        ]
        # Frost-exposed locations: s2 (already in type_docs) + s3 (indoor with frost-exposed location)
        frost_location_keys = ["s2", "s3"]
        frost_docs = [
            {"_key": "s2", "name": "Beet B", "type": "outdoor"},  # Duplicate
            {"_key": "s3", "name": "Indoor Garden", "type": "indoor"},  # New
        ]

        site_repo = MagicMock()
        site_repo.find_site_docs_by_types.return_value = type_docs
        site_repo.find_site_keys_with_frost_exposed_location.return_value = frost_location_keys
        site_repo.find_site_docs_by_keys.return_value = frost_docs
        deps.get_site_repo.return_value = site_repo

        service = MagicMock()
        # s1 evaluated, s2 evaluated (despite duplication), s3 evaluated
        service.evaluate_site_detailed.side_effect = [
            (_state("s1"), False),
            (_state("s2"), False),
            (_state("s3"), True),  # This one transitioned
        ]
        deps.get_season_state_service.return_value = service

        result = module.evaluate_season_states()

        # All 3 unique sites should be evaluated
        assert result == {"status": "ok", "evaluated": 3, "transitions": 1, "errors": 0}
        # find_site_docs_by_keys should be called with frost_location_keys
        site_repo.find_site_docs_by_keys.assert_called_once()
        called_keys = site_repo.find_site_docs_by_keys.call_args[0][0]
        assert set(called_keys) == {"s2", "s3"}

    def test_ac6_empty_frost_location_sites_still_evals_type_sites(self, task_module, monkeypatch):
        """AC-6: When no sites have frost-exposed locations, type-based sites are still evaluated."""
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        type_docs = [
            {"_key": "s1", "name": "Beet A", "type": "outdoor"},
        ]

        site_repo = MagicMock()
        site_repo.find_site_docs_by_types.return_value = type_docs
        site_repo.find_site_keys_with_frost_exposed_location.return_value = []
        site_repo.find_site_docs_by_keys.return_value = []
        deps.get_site_repo.return_value = site_repo

        service = MagicMock()
        service.evaluate_site_detailed.return_value = (_state("s1"), False)
        deps.get_season_state_service.return_value = service

        result = module.evaluate_season_states()

        assert result == {"status": "ok", "evaluated": 1, "transitions": 0, "errors": 0}
        # find_site_docs_by_keys is called with empty list, which short-circuits
        site_repo.find_site_docs_by_keys.assert_called_once_with([])

    def test_ac6_no_short_circuit_when_frost_keys_empty(self, task_module, monkeypatch):
        """Verify find_site_docs_by_keys is still called even when frost_location_keys is empty."""
        module, deps = task_module
        monkeypatch.setattr(module.settings, "season_state_eval_enabled", True, raising=False)

        site_repo = MagicMock()
        site_repo.find_site_docs_by_types.return_value = []
        site_repo.find_site_keys_with_frost_exposed_location.return_value = []
        site_repo.find_site_docs_by_keys.return_value = []
        deps.get_site_repo.return_value = site_repo

        service = MagicMock()
        deps.get_season_state_service.return_value = service

        result = module.evaluate_season_states()

        assert result == {"status": "ok", "evaluated": 0, "transitions": 0, "errors": 0}
        site_repo.find_site_docs_by_keys.assert_called_once_with([])
