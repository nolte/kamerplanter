"""Unit tests for ``ArangoHarvestRepository.batch_id_exists`` (issue #744).

Solitary unit tests: the injected ``StandardDatabase`` is doubled with
MagicMock. ``batch_id_exists`` backs the deterministic batch-id generator, so
it must query the ``batch_id`` unique index globally (no tenant filter).
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.harvest_repository import ArangoHarvestRepository


@pytest.fixture
def mock_db():
    return MagicMock()


def test_batch_id_exists_true_when_a_match_is_found(mock_db):
    repo = ArangoHarvestRepository(mock_db)
    mock_db.aql.execute.return_value = iter([{"_key": "hb1", "batch_id": "H-1"}])

    assert repo.batch_id_exists("H-1") is True
    query = mock_db.aql.execute.call_args.args[0]
    bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
    # Filters on batch_id only — no tenant_key clause (index is global).
    assert "doc.batch_id == @v0" in query
    assert "tenant_key" not in query
    assert bind_vars["v0"] == "H-1"


def test_batch_id_exists_false_when_empty(mock_db):
    repo = ArangoHarvestRepository(mock_db)
    mock_db.aql.execute.return_value = iter([])

    assert repo.batch_id_exists("H-2") is False


def test_batch_id_exists_short_circuits_on_blank_input(mock_db):
    repo = ArangoHarvestRepository(mock_db)

    assert repo.batch_id_exists("") is False
    mock_db.aql.execute.assert_not_called()
