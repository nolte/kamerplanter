"""Unit tests for ArangoApiKeyRepository (REQ-023 Service Accounts).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.api_key_repository import ArangoApiKeyRepository
from app.domain.models.auth import ApiKey


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoApiKeyRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {
        "_key": "k1",
        "user_key": "u1",
        "label": "ci",
        "key_hash": "hash1",
        "key_prefix": "kp_abc",
        "revoked": False,
    }
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> ApiKey:
    defaults = {"user_key": "u1", "label": "ci", "key_hash": "hash1", "key_prefix": "kp_abc"}
    defaults.update(kwargs)
    return ApiKey(**defaults)


class TestCreate:
    def test_creates_and_edges_to_user(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, ApiKey)
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "users/u1"
        assert edge["_to"] == "api_keys/k1"


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("k1"), ApiKey)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("k1") is None


class TestGetByHash:
    def test_returns_non_revoked_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.get_by_hash("hash1")

        assert result.key_hash == "hash1"
        assert "doc.revoked == false" in mock_db.aql.execute.call_args.args[0]
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["hash"] == "hash1"

    def test_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.get_by_hash("hash1") is None


class TestListByUser:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(), _doc(_key="k2")])

        result = repo.list_by_user("u1")

        assert len(result) == 2
        assert all(isinstance(r, ApiKey) for r in result)


class TestUpdateLastUsed:
    def test_updates_timestamp(self, repo, mock_db):
        coll = mock_db.collection.return_value

        repo.update_last_used("k1")

        updated = coll.update.call_args.args[0]
        assert updated["_key"] == "k1"
        assert "last_used_at" in updated


class TestRevoke:
    def test_sets_revoked_true_and_returns_true(self, repo, mock_db):
        coll = mock_db.collection.return_value

        assert repo.revoke("k1") is True
        updated = coll.update.call_args.args[0]
        assert updated["_key"] == "k1"
        assert updated["revoked"] is True

    def test_returns_false_on_error(self, repo, mock_db):
        mock_db.collection.return_value.update.side_effect = Exception("nope")

        assert repo.revoke("k1") is False


class TestDelete:
    def test_returns_true_on_success(self, repo, mock_db):
        mock_db.collection.return_value.delete.return_value = True
        assert repo.delete("k1") is True

    def test_returns_false_on_error(self, repo, mock_db):
        mock_db.collection.return_value.delete.side_effect = Exception("nope")
        assert repo.delete("k1") is False
