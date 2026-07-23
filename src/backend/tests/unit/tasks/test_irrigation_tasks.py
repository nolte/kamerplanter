"""REQ-037 — unit tests for the ``compute_irrigation_demand`` Celery task.

Mocks ``app.common.dependencies`` (imported lazily inside the task body) so no real
repository / DB is touched. Covers the disabled kill-switch, the outdoor/greenhouse
scoping (indoor sites are never even queried) and the write path.
"""

import sys
from datetime import UTC, date, datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.domain.models.weather import WeatherForecast


@pytest.fixture
def task_module(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    for name in (
        "get_irrigation_demand_repo",
        "get_lifecycle_repo",
        "get_planting_run_repo",
        "get_site_repo",
        "get_species_repo",
        "get_weather_forecast_repo",
    ):
        setattr(mock_deps, name, MagicMock())
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.irrigation_tasks as module

    monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
    monkeypatch.setattr(module.settings, "irrigation_demand_enabled", True, raising=False)
    yield module, mock_deps


def _site_doc(site_type="outdoor"):
    return {
        "_key": "site1",
        "name": "Beet",
        "type": site_type,
        "tenant_key": "t1",
        "gps_coordinates": [50.8, 13.4],
    }


def _forecast():
    return WeatherForecast(
        site_key="site1",
        tenant_key="t1",
        forecast_date=date(2026, 7, 6),
        temp_min_c=12.3,
        temp_max_c=21.5,
        humidity_percent=73.5,
        wind_speed_kmh=7.5,
        precipitation_mm=0.0,
        solar_radiation_mj_m2=22.07,
        source="nasa-power",
        fetched_at=datetime.now(UTC),
    )


def _wire_repos(deps, *, runs, forecasts=None):
    site_repo = MagicMock()
    site_repo.find_site_docs_by_types.return_value = [_site_doc()]
    site_repo._from_doc.side_effect = lambda doc: doc
    site_repo.get_location_by_key.return_value = SimpleNamespace(area_m2=5.0)
    deps.get_site_repo.return_value = site_repo

    forecast_repo = MagicMock()
    forecast_repo.find_by_site.return_value = _forecast() if forecasts is None else forecasts
    # find_by_site returns a list
    forecast_repo.find_by_site.return_value = [_forecast()] if forecasts is None else forecasts
    deps.get_weather_forecast_repo.return_value = forecast_repo

    run_repo = MagicMock()
    run_repo.get_runs_at_site.return_value = runs
    run_repo.get_entries.return_value = [SimpleNamespace(species_key="sp1")]
    deps.get_planting_run_repo.return_value = run_repo

    species_repo = MagicMock()
    species_repo.get_by_key.return_value = SimpleNamespace(default_crop_coefficient_kc=None, plant_category=None)
    deps.get_species_repo.return_value = species_repo

    lifecycle_repo = MagicMock()
    lifecycle_repo.get_phase_by_key.return_value = SimpleNamespace(crop_coefficient_kc=1.05)
    deps.get_lifecycle_repo.return_value = lifecycle_repo

    demand_repo = MagicMock()
    deps.get_irrigation_demand_repo.return_value = demand_repo

    return site_repo, demand_repo


class TestComputeIrrigationDemand:
    def test_noop_when_disabled(self, task_module, monkeypatch):
        module, _deps = task_module
        monkeypatch.setattr(module.settings, "irrigation_demand_enabled", False, raising=False)
        assert module.compute_irrigation_demand() == {"status": "skipped", "reason": "irrigation_demand_disabled"}

    def test_weather_relevant_sites_including_balcony_are_queried(self, task_module):
        # #706: balcony is a frost-/weather-exposed site type and must be
        # queried alongside outdoor/greenhouse (shared WEATHER_RELEVANT_SITE_TYPES).
        # Compare as a set — frozenset iteration order is not guaranteed.
        module, deps = task_module
        site_repo, _demand = _wire_repos(deps, runs=[])
        module.compute_irrigation_demand()
        site_repo.find_site_docs_by_types.assert_called_once()
        (called_types,) = site_repo.find_site_docs_by_types.call_args[0]
        assert set(called_types) == {"outdoor", "greenhouse", "balcony"}

    def test_writes_demand_for_active_run(self, task_module):
        module, deps = task_module
        run = SimpleNamespace(key="run1", current_phase_key="phase1", location_key="loc1")
        _site_repo, demand_repo = _wire_repos(deps, runs=[run])

        result = module.compute_irrigation_demand()

        assert result["status"] == "ok"
        assert result["written"] == 1
        demand_repo.upsert.assert_called_once()
        demand = demand_repo.upsert.call_args[0][0]
        assert demand.site_key == "site1"
        assert demand.run_key == "run1"
        assert demand.tenant_key == "t1"
        assert demand.et_method == "fao56_penman_monteith"
        assert demand.quality == "high"
        assert demand.kc_used == 1.05  # phase Kc wins the cascade
        assert demand.kc_source == "phase"
        assert demand.area_m2 == 5.0
        # positive demand on a dry day → some recommended volume
        assert demand.recommended_volume_liters > 0

    def test_no_runs_skips_site(self, task_module):
        module, deps = task_module
        _site_repo, demand_repo = _wire_repos(deps, runs=[])
        result = module.compute_irrigation_demand()
        assert result["written"] == 0
        demand_repo.upsert.assert_not_called()

    def test_site_without_gps_is_skipped(self, task_module):
        module, deps = task_module
        run = SimpleNamespace(key="run1", current_phase_key=None, location_key=None)
        site_repo, demand_repo = _wire_repos(deps, runs=[run])
        site_repo.find_site_docs_by_types.return_value = [_site_doc() | {"gps_coordinates": None}]
        result = module.compute_irrigation_demand()
        assert result["written"] == 0
        demand_repo.upsert.assert_not_called()
