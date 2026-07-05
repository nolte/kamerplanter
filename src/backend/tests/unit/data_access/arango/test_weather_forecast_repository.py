"""Unit tests for ``ArangoWeatherForecastRepository`` (REQ-046).

Solitary unit tests: the injected ``StandardDatabase`` is doubled with
MagicMock. No real ArangoDB connection.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.weather_forecast_repository import ArangoWeatherForecastRepository
from app.domain.models.weather import WeatherForecast


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoWeatherForecastRepository(mock_db)


def _model(**kwargs) -> WeatherForecast:
    defaults = {
        "site_key": "site1",
        "tenant_key": "tenantA",
        "forecast_date": date(2026, 7, 5),
        "source": "open-meteo",
        "fetched_at": datetime(2026, 7, 5, 6, 0, 0),
    }
    defaults.update(kwargs)
    return WeatherForecast(**defaults)


def _doc(**kwargs) -> dict:
    doc = {
        "_key": "wf1",
        "site_key": "site1",
        "tenant_key": "tenantA",
        "forecast_date": "2026-07-05",
        "source": "open-meteo",
        "fetched_at": "2026-07-05T06:00:00",
    }
    doc.update(kwargs)
    return doc


class TestUpsertDaily:
    def test_insert_when_absent_creates_doc_and_edge(self, repo, mock_db):
        # _find_existing → no match
        mock_db.aql.execute.return_value = iter([])
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.upsert_daily(_model())

        assert isinstance(result, WeatherForecast)
        # forecast doc + has_forecast edge
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "sites/site1"
        assert edge["_to"] == "weather_forecasts/wf1"

    def test_update_when_present_skips_edge(self, repo, mock_db):
        # _find_existing → one match
        mock_db.aql.execute.return_value = iter([_doc()])
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(temp_max_c=22.0)}

        result = repo.upsert_daily(_model(temp_max_c=22.0))

        assert result.temp_max_c == 22.0
        coll.update.assert_called_once()
        # No new insert (no duplicate edge) on the idempotent update path.
        coll.insert.assert_not_called()

    def test_find_existing_binds_composite_key(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        repo.upsert_daily(_model())

        bind = mock_db.aql.execute.call_args_list[0].kwargs["bind_vars"]
        assert bind["site_key"] == "site1"
        assert bind["forecast_date"] == "2026-07-05"
        assert bind["source"] == "open-meteo"
        assert bind["tenant_key"] == "tenantA"


class TestFindBySite:
    def test_binds_site_and_tenant(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.find_by_site("site1", "tenantA")

        assert len(result) == 1
        assert isinstance(result[0], WeatherForecast)
        bind = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind["site_key"] == "site1"
        assert bind["tenant_key"] == "tenantA"


class TestGet:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get("wf1"), WeatherForecast)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get("wf1") is None
