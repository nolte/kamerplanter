"""Unit tests for ArangoSensorRepository (REQ-005).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.sensor_repository import ArangoSensorRepository
from app.domain.models.sensor import Sensor


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoSensorRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "s1", "name": "Temp", "metric_type": "temperature", "is_active": True}
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> Sensor:
    defaults = {"name": "Temp", "metric_type": "temperature"}
    defaults.update(kwargs)
    return Sensor(**defaults)


class TestCreate:
    def test_create_without_links_inserts_only_doc(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, Sensor)
        assert coll.insert.call_count == 1

    def test_create_with_tank_adds_monitors_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(tank_key="tank1")}

        repo.create(_model(tank_key="tank1"))

        # sensor doc + monitors_tank edge
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "sensors/s1"
        assert edge["_to"] == "tanks/tank1"

    def test_create_with_site_adds_located_at_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(site_key="site1")}

        repo.create(_model(site_key="site1"))

        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_to"] == "sites/site1"

    def test_create_with_location_when_no_site(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(location_key="loc1")}

        repo.create(_model(location_key="loc1"))

        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_to"] == "locations/loc1"


class TestGet:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get("s1"), Sensor)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get("s1") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(name="Renamed")}

        result = repo.update("s1", _model(name="Renamed"))

        assert result.name == "Renamed"


class TestFinders:
    def test_find_by_tank_binds_tank_key(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(tank_key="tank1")])

        result = repo.find_by_tank("tank1")

        assert len(result) == 1
        assert isinstance(result[0], Sensor)
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["tank_key"] == "tank1"

    def test_find_by_site_binds_site_key(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(site_key="site1")])

        result = repo.find_by_site("site1")

        assert len(result) == 1
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["site_key"] == "site1"

    def test_find_by_location_binds_location_key(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.find_by_location("loc1")

        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["location_key"] == "loc1"


class TestDelete:
    def test_cleans_edges_then_deletes_doc(self, repo, mock_db):
        mock_db.collection.return_value.delete.return_value = True

        result = repo.delete("s1")

        assert result is True
        mock_db.collection.return_value.delete.assert_called_once_with("s1")
        # Two edge-cleanup AQL removals (monitors_tank, located_at).
        assert mock_db.aql.execute.call_count == 2

    def test_returns_false_when_doc_delete_fails(self, repo, mock_db):
        mock_db.collection.return_value.delete.side_effect = Exception("nope")

        assert repo.delete("s1") is False
