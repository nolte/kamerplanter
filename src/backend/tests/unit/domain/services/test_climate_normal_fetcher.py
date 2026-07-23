"""REQ-041 — unit tests for :class:`ClimateNormalFetcher` (on-demand fetch)."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.domain.models.site import Site
from app.domain.models.weather import ClimateNormal
from app.domain.services import climate_normal_fetcher as fetcher_module
from app.domain.services.climate_normal_fetcher import ClimateNormalFetcher


def _site(**overrides) -> Site:
    data = {
        "_key": "site1",
        "tenant_key": "t1",
        "name": "Beet",
        "type": "outdoor",
        "gps_coordinates": (52.5, 13.4),
    }
    data.update(overrides)
    return Site(**data)


def _normal(**overrides) -> ClimateNormal:
    data = {
        "site_key": "",
        "source": "nasa-power",
        "fetched_at": datetime.now(tz=UTC),
        "coldest_month_min_c": -17.0,
        "monthly_temp_min_c": [-17.0] * 12,
    }
    data.update(overrides)
    return ClimateNormal(**data)


def _make_adapter(returns: ClimateNormal | None):
    adapter = MagicMock()
    adapter.source_name = "nasa-power"

    async def _fetch(*, latitude: float, longitude: float) -> ClimateNormal | None:  # noqa: ARG001
        return returns

    adapter.fetch_climate_normals = _fetch
    return adapter


@pytest.fixture
def _enabled(monkeypatch):
    """Enable weather + climate-normals settings for the fetch to proceed."""
    monkeypatch.setattr(fetcher_module.settings, "weather_enabled", True)
    monkeypatch.setattr(fetcher_module.settings, "nasa_power_climate_enabled", True)
    monkeypatch.setattr(fetcher_module.settings, "weather_fetch_timeout_s", 5)
    monkeypatch.setattr(fetcher_module.settings, "nasa_power_climate_ttl_days", 180)


def _patch_registry(monkeypatch, adapter):
    from app.domain.services import weather_adapter_registry as registry

    monkeypatch.setattr(registry.WeatherAdapterRegistry, "get", staticmethod(lambda source: lambda **_: adapter))


class TestFetchForSite:
    def test_fetches_upserts_and_stamps_identity(self, monkeypatch, _enabled) -> None:
        repo = MagicMock()
        repo.find_one.return_value = None
        repo.upsert.side_effect = lambda rec: rec
        _patch_registry(monkeypatch, _make_adapter(_normal()))

        result = ClimateNormalFetcher(repo).fetch_for_site(_site())

        assert result is not None
        assert result.site_key == "site1"
        assert result.tenant_key == "t1"
        assert result.climate_normal_id == "site1:nasa-power"
        repo.upsert.assert_called_once()

    def test_reuses_fresh_existing_without_fetching(self, monkeypatch, _enabled) -> None:
        fresh = _normal(site_key="site1", tenant_key="t1", fetched_at=datetime.now(tz=UTC))
        repo = MagicMock()
        repo.find_one.return_value = fresh
        _patch_registry(monkeypatch, _make_adapter(_normal()))

        result = ClimateNormalFetcher(repo).fetch_for_site(_site())

        assert result is fresh
        repo.upsert.assert_not_called()

    def test_refetches_when_existing_is_stale(self, monkeypatch, _enabled) -> None:
        stale = _normal(site_key="site1", tenant_key="t1", fetched_at=datetime.now(tz=UTC) - timedelta(days=365))
        repo = MagicMock()
        repo.find_one.return_value = stale
        repo.upsert.side_effect = lambda rec: rec
        _patch_registry(monkeypatch, _make_adapter(_normal()))

        ClimateNormalFetcher(repo).fetch_for_site(_site())

        repo.upsert.assert_called_once()

    def test_returns_none_when_weather_disabled(self, monkeypatch) -> None:
        monkeypatch.setattr(fetcher_module.settings, "weather_enabled", False)
        repo = MagicMock()

        assert ClimateNormalFetcher(repo).fetch_for_site(_site()) is None
        repo.find_one.assert_not_called()

    def test_returns_none_without_gps(self, _enabled) -> None:
        repo = MagicMock()

        assert ClimateNormalFetcher(repo).fetch_for_site(_site(gps_coordinates=None)) is None

    def test_returns_none_when_adapter_yields_nothing(self, monkeypatch, _enabled) -> None:
        repo = MagicMock()
        repo.find_one.return_value = None
        _patch_registry(monkeypatch, _make_adapter(None))

        assert ClimateNormalFetcher(repo).fetch_for_site(_site()) is None
        repo.upsert.assert_not_called()

    def test_remote_error_is_swallowed(self, monkeypatch, _enabled) -> None:
        repo = MagicMock()
        repo.find_one.return_value = None
        adapter = MagicMock()
        adapter.source_name = "nasa-power"

        async def _boom(*, latitude: float, longitude: float):  # noqa: ARG001
            raise RuntimeError("429 Too Many Requests")

        adapter.fetch_climate_normals = _boom
        _patch_registry(monkeypatch, adapter)

        assert ClimateNormalFetcher(repo).fetch_for_site(_site()) is None
        repo.upsert.assert_not_called()
