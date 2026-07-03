"""Unit tests for ArangoDataExportRepository (REQ-025, NFR-011).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.data_export_repository import ArangoDataExportRepository
from app.domain.models.privacy import DataExportRequest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoDataExportRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "de1", "user_key": "u1", "status": "pending"}
    doc.update(kwargs)
    return doc


class TestCreate:
    def test_creates_and_edges_to_user(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(DataExportRequest(user_key="u1"))

        assert isinstance(result, DataExportRequest)
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "users/u1"
        assert edge["_to"] == "data_export_requests/de1"


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("de1"), DataExportRequest)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("de1") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(status="completed")}

        result = repo.update("de1", DataExportRequest(user_key="u1"))

        assert result.status == "completed"


class TestListByUser:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.list_by_user("u1")

        assert len(result) == 1
        assert isinstance(result[0], DataExportRequest)


class TestListActiveByUser:
    def test_filters_pending_and_processing(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.list_active_by_user("u1")

        assert len(result) == 1
        assert "doc.status IN ['pending', 'processing']" in mock_db.aql.execute.call_args.args[0]


class TestDelete:
    def test_removes_edges_then_deletes(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("de1") is True
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"export_id": "data_export_requests/de1"}


class TestExpireOld:
    def test_counts_expired(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([1])

        assert repo.expire_old("2026-06-14T00:00:00Z") == 1
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["now"] == "2026-06-14T00:00:00Z"


class TestListStalePending:
    def test_returns_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(), _doc(_key="de2")])

        result = repo.list_stale_pending("2026-06-14T00:00:00Z")

        assert len(result) == 2
        assert all(isinstance(r, DataExportRequest) for r in result)

    def test_filters_pending_before_cutoff(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.list_stale_pending("2026-06-14T00:00:00Z")

        query = mock_db.aql.execute.call_args.args[0]
        assert 'doc.status == "pending"' in query
        assert "doc.requested_at < @cutoff" in query
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["cutoff"] == "2026-06-14T00:00:00Z"
