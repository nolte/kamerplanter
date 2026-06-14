"""Unit tests for ArangoConsentRepository (REQ-025).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection. Assertions target
returned ``ConsentRecord`` models and the AQL bind_vars / edges emitted.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.consent_repository import ArangoConsentRepository
from app.domain.models.privacy import ConsentRecord


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoConsentRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "c1", "user_key": "u1", "purpose": "sentry", "granted": True}
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> ConsentRecord:
    defaults = {"user_key": "u1", "purpose": "sentry", "granted": True}
    defaults.update(kwargs)
    return ConsentRecord(**defaults)


class TestCreate:
    def test_creates_record_and_user_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, ConsentRecord)
        assert result.key == "c1"
        # Document insert + has_consent edge insert.
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "users/u1"
        assert edge["_to"] == "consent_records/c1"

    def test_skips_edge_without_user_key(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(user_key="")}

        repo.create(_model(user_key=""))

        assert coll.insert.call_count == 1


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("c1"), ConsentRecord)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("c1") is None


class TestGetByUserAndPurpose:
    def test_returns_first_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(purpose="hibp")])

        result = repo.get_by_user_and_purpose("u1", "hibp")

        assert result.purpose == "hibp"
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["user_key"] == "u1"
        assert bind_vars["purpose"] == "hibp"

    def test_returns_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.get_by_user_and_purpose("u1", "hibp") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(granted=False)}

        result = repo.update("c1", _model(granted=False))

        assert result.granted is False
        assert coll.update.call_args.args[0]["_key"] == "c1"


class TestListByUser:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(), _doc(_key="c2", purpose="enrichment")])

        result = repo.list_by_user("u1")

        assert len(result) == 2
        assert all(isinstance(r, ConsentRecord) for r in result)


class TestDelete:
    def test_removes_edges_then_deletes(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("c1") is True
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"consent_id": "consent_records/c1"}
        mock_db.collection.return_value.delete.assert_called_once_with("c1")


class TestDeleteAllForUser:
    def test_counts_removed_rows(self, repo, mock_db):
        # side_effect (not return_value) yields a fresh cursor per call, so the
        # assertion holds even if the method is invoked more than once.
        mock_db.aql.execute.side_effect = lambda *a, **k: iter([1, 1, 1])

        assert repo.delete_all_for_user("u1") == 3

    def test_zero_when_nothing_removed(self, repo, mock_db):
        mock_db.aql.execute.side_effect = lambda *a, **k: iter([])

        assert repo.delete_all_for_user("u1") == 0
