"""Unit tests for ArangoEmailChangeRepository (REQ-025, Art. 16).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.email_change_repository import ArangoEmailChangeRepository
from app.domain.models.privacy import EmailChangeRequest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoEmailChangeRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {
        "_key": "ec1",
        "user_key": "u1",
        "new_email": "new@example.com",
        "verification_token_hash": "hash1",
        "status": "pending",
        "expires_at": "2026-06-20T00:00:00Z",
    }
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> EmailChangeRequest:
    defaults = {
        "user_key": "u1",
        "new_email": "new@example.com",
        "verification_token_hash": "hash1",
        "expires_at": datetime(2026, 6, 20, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return EmailChangeRequest(**defaults)


class TestCreate:
    def test_creates_request_and_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, EmailChangeRequest)
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "users/u1"
        assert edge["_to"] == "email_change_requests/ec1"


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("ec1"), EmailChangeRequest)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("ec1") is None


class TestGetByTokenHash:
    def test_returns_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.get_by_token_hash("hash1")

        assert result.verification_token_hash == "hash1"
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["token_hash"] == "hash1"

    def test_returns_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.get_by_token_hash("hash1") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(status="confirmed")}

        result = repo.update("ec1", _model())

        assert result.status == "confirmed"


class TestListPendingForUser:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.list_pending_for_user("u1")

        assert len(result) == 1
        assert isinstance(result[0], EmailChangeRequest)


class TestExpireOld:
    def test_counts_expired(self, repo, mock_db):
        # side_effect yields a fresh cursor per call (return_value would hand
        # back the same exhausted iterator on a second invocation).
        mock_db.aql.execute.side_effect = lambda *a, **k: iter([1, 1])

        assert repo.expire_old("2026-06-14T00:00:00Z") == 2
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["now"] == "2026-06-14T00:00:00Z"


class TestDelete:
    def test_removes_edges_then_deletes(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("ec1") is True
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"change_id": "email_change_requests/ec1"}


class TestDeleteExpiredUnconfirmed:
    """NFR-011 R-07 (#1800) — an unconfirmed request past its ``expires_at`` is hard-deleted, edges first."""

    def test_removes_edges_then_documents(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([1, 1, 1])]

        deleted = repo.delete_expired_unconfirmed("2026-06-21T00:00:00Z")

        assert deleted == 3
        assert mock_db.aql.execute.call_count == 2
        edges_call, docs_call = mock_db.aql.execute.call_args_list
        assert edges_call.kwargs["bind_vars"]["@edges"] == "requested_email_change"
        assert "REMOVE edge" in edges_call.args[0]
        assert "REMOVE doc" in docs_call.args[0]
        for call in (edges_call, docs_call):
            assert call.kwargs["bind_vars"]["unconfirmed"] == ["pending", "expired", "cancelled"]
            assert call.kwargs["bind_vars"]["now"] == "2026-06-21T00:00:00Z"

    def test_zero_when_nothing_due(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]
        assert repo.delete_expired_unconfirmed("2026-06-21T00:00:00Z") == 0


class TestDeleteConfirmedPastRevertWindow:
    """NFR-011 R-07b (#1800) — a confirmed change past its R-07a revert window is hard-deleted whole, edges first."""

    def test_removes_edges_then_documents(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([1])]

        deleted = repo.delete_confirmed_past_revert_window("2026-06-14T00:00:00Z")

        assert deleted == 1
        assert mock_db.aql.execute.call_count == 2
        edges_call, docs_call = mock_db.aql.execute.call_args_list
        assert edges_call.kwargs["bind_vars"]["@edges"] == "requested_email_change"
        for call in (edges_call, docs_call):
            assert call.kwargs["bind_vars"]["confirmed"] == ["confirmed", "reverted", "superseded"]
            assert call.kwargs["bind_vars"]["cutoff"] == "2026-06-14T00:00:00Z"

    def test_zero_when_nothing_due(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]
        assert repo.delete_confirmed_past_revert_window("2026-06-14T00:00:00Z") == 0
