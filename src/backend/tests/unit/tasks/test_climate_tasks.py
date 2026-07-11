"""Unit tests for the REQ-041 ``fetch_climate_normals`` Celery task.

Mocks ``app.common.dependencies`` (imported lazily inside the task body) and
stubs the NASA POWER adapter via the registry so no real adapter / HTTP / DB is
touched. Covers the disabled kill-switch, the TTL cache-hit skip and the write
path (with the ``has_climate_normal`` edge left to the repository).
"""

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from app.domain.models.weather import ClimateNormal


@pytest.fixture
def task_module(monkeypatch):
    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_climate_normal_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_site_repo = MagicMock()  # type: ignore[attr-defined]
    mock_deps.get_db = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.climate_tasks as module

    yield module, mock_deps


def _stub_adapter(monkeypatch, normal):
    """Register a stub ``nasa-power`` adapter that returns ``normal`` (or raises)."""
    from app.domain.services import weather_adapter_registry as reg

    class _StubAdapter:
        source_name = "nasa-power"

        def __init__(self, *args, **kwargs):
            pass

        async def fetch_climate_normals(self, *, latitude, longitude):
            if isinstance(normal, Exception):
                raise normal
            return normal

    monkeypatch.setattr(reg.WeatherAdapterRegistry, "get", classmethod(lambda cls, name: _StubAdapter))


def _site_doc(**overrides):
    doc = {"_key": "site1", "name": "Beet", "type": "outdoor", "tenant_key": "t1", "gps_coordinates": [52.5, 13.4]}
    doc.update(overrides)
    return doc


def _normal():
    return ClimateNormal(
        site_key="",
        source="nasa-power",
        fetched_at=datetime.now(tz=UTC),
        monthly_temp_min_c=[-3.0] * 12,
        coldest_month_min_c=-3.0,
    )


class TestFetchClimateNormals:
    def test_noop_when_disabled(self, task_module, monkeypatch):
        module, _deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", False, raising=False)

        assert module.fetch_climate_normals() == {"status": "skipped", "reason": "climate_normals_disabled"}

    def test_noop_when_climate_switch_off(self, task_module, monkeypatch):
        module, _deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "nasa_power_climate_enabled", False, raising=False)

        assert module.fetch_climate_normals() == {"status": "skipped", "reason": "climate_normals_disabled"}

    def test_writes_normal_for_outdoor_site(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "nasa_power_climate_enabled", True, raising=False)
        _stub_adapter(monkeypatch, _normal())

        db = MagicMock()
        db.aql.execute.return_value = iter([_site_doc()])
        deps.get_db.return_value = db
        site_repo = MagicMock()
        site_repo._from_doc.side_effect = lambda doc: doc
        deps.get_site_repo.return_value = site_repo
        normal_repo = MagicMock()
        normal_repo.find_one.return_value = None  # nothing cached yet
        deps.get_climate_normal_repo.return_value = normal_repo

        result = module.fetch_climate_normals()

        assert result == {"status": "ok", "written": 1, "skipped": 0, "errors": 0}
        normal_repo.upsert.assert_called_once()
        written = normal_repo.upsert.call_args.args[0]
        assert written.site_key == "site1"
        assert written.tenant_key == "t1"
        assert written.climate_normal_id == "site1:nasa-power"

    def test_skips_fresh_record_within_ttl(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "nasa_power_climate_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "nasa_power_climate_ttl_days", 180, raising=False)
        _stub_adapter(monkeypatch, _normal())

        db = MagicMock()
        db.aql.execute.return_value = iter([_site_doc()])
        deps.get_db.return_value = db
        site_repo = MagicMock()
        site_repo._from_doc.side_effect = lambda doc: doc
        deps.get_site_repo.return_value = site_repo

        fresh = _normal()
        fresh.fetched_at = datetime.now(tz=UTC) - timedelta(days=10)  # well within 180d TTL
        normal_repo = MagicMock()
        normal_repo.find_one.return_value = fresh
        deps.get_climate_normal_repo.return_value = normal_repo

        result = module.fetch_climate_normals()

        assert result == {"status": "ok", "written": 0, "skipped": 1, "errors": 0}
        normal_repo.upsert.assert_not_called()

    def test_refetches_after_ttl_expired(self, task_module, monkeypatch):
        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "nasa_power_climate_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "nasa_power_climate_ttl_days", 180, raising=False)
        _stub_adapter(monkeypatch, _normal())

        db = MagicMock()
        db.aql.execute.return_value = iter([_site_doc()])
        deps.get_db.return_value = db
        site_repo = MagicMock()
        site_repo._from_doc.side_effect = lambda doc: doc
        deps.get_site_repo.return_value = site_repo

        stale = _normal()
        stale.fetched_at = datetime.now(tz=UTC) - timedelta(days=200)  # past the 180d TTL
        normal_repo = MagicMock()
        normal_repo.find_one.return_value = stale
        deps.get_climate_normal_repo.return_value = normal_repo

        result = module.fetch_climate_normals()

        assert result["written"] == 1
        normal_repo.upsert.assert_called_once()

    def test_http_error_skips_site_without_aborting(self, task_module, monkeypatch):
        import httpx

        module, deps = task_module
        monkeypatch.setattr(module.settings, "weather_enabled", True, raising=False)
        monkeypatch.setattr(module.settings, "nasa_power_climate_enabled", True, raising=False)
        _stub_adapter(monkeypatch, httpx.HTTPError("429 Too Many Requests"))

        db = MagicMock()
        db.aql.execute.return_value = iter([_site_doc()])
        deps.get_db.return_value = db
        site_repo = MagicMock()
        site_repo._from_doc.side_effect = lambda doc: doc
        deps.get_site_repo.return_value = site_repo
        normal_repo = MagicMock()
        normal_repo.find_one.return_value = None
        deps.get_climate_normal_repo.return_value = normal_repo

        result = module.fetch_climate_normals()

        assert result["status"] == "ok"
        assert result["written"] == 0
        assert result["errors"] == 1
        normal_repo.upsert.assert_not_called()
