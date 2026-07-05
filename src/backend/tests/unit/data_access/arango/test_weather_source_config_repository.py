"""Unit tests for ``ArangoWeatherSourceConfigRepository`` (REQ-046).

Solitary unit tests with a MagicMock ``StandardDatabase``. Focus: tenant-scoped
reads/writes and the 1:1 upsert semantics.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.weather_source_config_repository import ArangoWeatherSourceConfigRepository
from app.domain.models.weather import WeatherSourceConfig, WeatherSourceEntry


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoWeatherSourceConfigRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "cfg1", "site_key": "site1", "tenant_key": "tenantA", "enabled": True, "sources": []}
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> WeatherSourceConfig:
    defaults = {"site_key": "site1", "tenant_key": "tenantA"}
    defaults.update(kwargs)
    return WeatherSourceConfig(**defaults)


class TestGetBySite:
    def test_binds_site_and_tenant(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.get_by_site("site1", "tenantA")

        assert isinstance(result, WeatherSourceConfig)
        bind = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind["site_key"] == "site1"
        assert bind["tenant_key"] == "tenantA"

    def test_none_when_absent(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.get_by_site("site1", "tenantA") is None


class TestUpsert:
    def test_requires_tenant_key(self, repo):
        with pytest.raises(ValueError, match="tenant_key"):
            repo.upsert(_model(tenant_key=""))

    def test_insert_when_absent_creates_doc_and_edge(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])  # get_by_site → none
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.upsert(_model(sources=[WeatherSourceEntry(source_name="open-meteo", kind="public")]))

        assert isinstance(result, WeatherSourceConfig)
        # config doc + has_weather_source_config edge
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "sites/site1"
        assert edge["_to"] == "weather_source_configs/cfg1"

    def test_update_when_present_skips_edge(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])  # get_by_site → existing
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(enabled=False)}

        result = repo.upsert(_model(enabled=False))

        assert result.enabled is False
        coll.update.assert_called_once()
        coll.insert.assert_not_called()


class TestDeleteBySite:
    def test_deletes_edge_then_doc(self, repo, mock_db):
        # get_by_site → existing; then delete_edges AQL; then doc delete.
        mock_db.aql.execute.return_value = iter([_doc()])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete_by_site("site1", "tenantA") is True
        mock_db.collection.return_value.delete.assert_called_once_with("cfg1")

    def test_returns_false_when_absent(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.delete_by_site("site1", "tenantA") is False
