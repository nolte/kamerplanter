"""Unit tests for ArangoErasureRepository (REQ-025, Art. 17).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.erasure_repository import ArangoErasureRepository
from app.domain.models.privacy import ErasureRequest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoErasureRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "er1", "user_key": "u1", "status": "scheduled"}
    doc.update(kwargs)
    return doc


class TestCreate:
    def test_creates_and_edges_to_user(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(ErasureRequest(user_key="u1"))

        assert isinstance(result, ErasureRequest)
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "users/u1"
        assert edge["_to"] == "erasure_requests/er1"


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("er1"), ErasureRequest)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("er1") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(status="in_progress")}

        result = repo.update("er1", ErasureRequest(user_key="u1"))

        assert result.status == "in_progress"


class TestListByUser:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.list_by_user("u1")

        assert len(result) == 1
        assert isinstance(result[0], ErasureRequest)


class TestFindActiveForUser:
    def test_returns_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.find_active_for_user("u1")

        assert isinstance(result, ErasureRequest)
        assert "doc.status IN ['scheduled', 'in_progress']" in mock_db.aql.execute.call_args.args[0]

    def test_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.find_active_for_user("u1") is None


class TestListDueForHardDelete:
    def test_filters_by_now(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.list_due_for_hard_delete("2026-06-14T00:00:00Z")

        assert len(result) == 1
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["now"] == "2026-06-14T00:00:00Z"

    def test_empty_result(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.list_due_for_hard_delete("2026-06-14T00:00:00Z") == []
