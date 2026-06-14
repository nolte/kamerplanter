"""Unit tests for ArangoCalendarFeedRepository (REQ-015).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.calendar_feed_repository import ArangoCalendarFeedRepository
from app.domain.models.calendar import CalendarFeed


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoCalendarFeedRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {
        "_key": "f1",
        "name": "My Feed",
        "token": "tok123",
        "user_key": "u1",
        "tenant_key": "t1",
        "is_active": True,
    }
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> CalendarFeed:
    defaults = {"name": "My Feed", "token": "tok123", "user_key": "u1", "tenant_key": "t1"}
    defaults.update(kwargs)
    return CalendarFeed(**defaults)


class TestSave:
    def test_inserts_and_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.save(_model())

        assert isinstance(result, CalendarFeed)
        assert result.key == "f1"


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("f1"), CalendarFeed)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("f1") is None


class TestGetByToken:
    def test_returns_first_match(self, repo, mock_db):
        # find_by_field issues a single AQL list query.
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.get_by_token("tok123")

        assert isinstance(result, CalendarFeed)
        assert result.token == "tok123"

    def test_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.get_by_token("tok123") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(name="Renamed")}

        result = repo.update("f1", _model(name="Renamed"))

        assert result.name == "Renamed"


class TestListByUser:
    def test_filters_user_and_tenant(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.list_by_user("u1", "t1")

        assert len(result) == 1
        assert isinstance(result[0], CalendarFeed)
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["user_key"] == "u1"
        assert bind_vars["tenant_key"] == "t1"

    def test_empty_result(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.list_by_user("u1", "t1") == []


class TestDelete:
    def test_returns_true_on_success(self, repo, mock_db):
        mock_db.collection.return_value.delete.return_value = True
        assert repo.delete("f1") is True

    def test_returns_false_on_error(self, repo, mock_db):
        mock_db.collection.return_value.delete.side_effect = Exception("nope")
        assert repo.delete("f1") is False
