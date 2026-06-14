"""Unit tests for ArangoProcessingRestrictionRepository (REQ-025, Art. 18/21).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.processing_restriction_repository import (
    ArangoProcessingRestrictionRepository,
)
from app.domain.models.privacy import ProcessingRestriction


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoProcessingRestrictionRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {
        "_key": "pr1",
        "user_key": "u1",
        "scope": "all",
        "reason": "objection_pending",
    }
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> ProcessingRestriction:
    defaults = {"user_key": "u1", "scope": "all", "reason": "objection_pending"}
    defaults.update(kwargs)
    return ProcessingRestriction(**defaults)


class TestCreate:
    def test_creates_and_edges_to_user(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, ProcessingRestriction)
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "users/u1"
        assert edge["_to"] == "processing_restrictions/pr1"


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("pr1"), ProcessingRestriction)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("pr1") is None


class TestGetByUserAndScope:
    def test_returns_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.get_by_user_and_scope("u1", "all")

        assert result.scope == "all"
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["user_key"] == "u1"
        assert bind_vars["scope"] == "all"

    def test_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.get_by_user_and_scope("u1", "all") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(scope="sensor_data")}

        result = repo.update("pr1", _model(scope="sensor_data"))

        assert result.scope == "sensor_data"


class TestListByUser:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(), _doc(_key="pr2")])

        result = repo.list_by_user("u1")

        assert len(result) == 2
        assert all(isinstance(r, ProcessingRestriction) for r in result)


class TestListActiveByUser:
    def test_filters_unlifted(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])

        result = repo.list_active_by_user("u1")

        assert len(result) == 1
        assert "doc.lifted_at == null" in mock_db.aql.execute.call_args.args[0]


class TestDelete:
    def test_removes_edges_then_deletes(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("pr1") is True
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"restriction_id": "processing_restrictions/pr1"}
