"""Unit tests for ``ArangoHarvestRepository.batch_id_exists`` (issue #744).

Solitary unit tests: the injected ``StandardDatabase`` is doubled with
MagicMock. ``batch_id_exists`` backs the deterministic batch-id generator, so
it asks within the scope of the unique index it must satisfy: ``(tenant_key,
batch_id)`` since #2065.
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

    assert repo.batch_id_exists("H-1", tenant_key="t1") is True
    query = mock_db.aql.execute.call_args.args[0]
    bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
    # Filters on batch_id within the caller's tenant — the index's scope (#2065).
    assert "doc.batch_id == @v0" in query
    assert "doc.tenant_key ==" in query
    assert "t1" in bind_vars.values()
    assert bind_vars["v0"] == "H-1"


def test_batch_id_exists_false_when_empty(mock_db):
    repo = ArangoHarvestRepository(mock_db)
    mock_db.aql.execute.return_value = iter([])

    assert repo.batch_id_exists("H-2", tenant_key="t1") is False


def test_batch_id_exists_short_circuits_on_blank_input(mock_db):
    repo = ArangoHarvestRepository(mock_db)

    assert repo.batch_id_exists("", tenant_key="t1") is False
    mock_db.aql.execute.assert_not_called()


def test_batch_id_exists_refuses_an_empty_tenant(mock_db):
    """An empty tenant would read across every tenant — fail closed instead."""
    repo = ArangoHarvestRepository(mock_db)

    with pytest.raises(ValueError, match="tenant"):
        repo.batch_id_exists("H-1", tenant_key="")
    mock_db.aql.execute.assert_not_called()
