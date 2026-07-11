"""Tests for the REQ-017 PropagationRepository pure logic.

Exercises the ancestor-path maximal-chain reduction (which also collapses the
duplicated sub-paths a cycle-truncated traversal emits) and the tenant-scoped
single-document reads, with a faked ArangoDB handle.
"""

from unittest.mock import MagicMock

from app.data_access.repositories.propagation_repository import PropagationRepository


def _repo_with_aql(rows) -> PropagationRepository:
    db = MagicMock()
    db.aql.execute.return_value = iter(rows)
    return PropagationRepository(db)


def test_trace_ancestor_paths_keeps_only_maximal_chains() -> None:
    # A linear chain reported at every depth collapses to the single longest chain.
    rows = [["m"], ["m", "gm"], ["m", "gm", "ggm"]]
    repo = _repo_with_aql(rows)

    result = repo.trace_ancestor_paths("pup", "tenant-a", max_depth=10)

    assert result == [["m", "gm", "ggm"]]


def test_trace_ancestor_paths_keeps_divergent_branches() -> None:
    rows = [["m", "a"], ["m", "b"]]
    repo = _repo_with_aql(rows)

    result = repo.trace_ancestor_paths("pup", "tenant-a", max_depth=10)

    assert sorted(result) == [["m", "a"], ["m", "b"]]


def test_trace_ancestor_paths_empty() -> None:
    repo = _repo_with_aql([])
    assert repo.trace_ancestor_paths("root", "tenant-a", max_depth=10) == []


def test_get_plant_raw_rejects_foreign_tenant() -> None:
    db = MagicMock()
    db.collection.return_value.get.return_value = {"_key": "p1", "tenant_key": "tenant-b"}
    repo = PropagationRepository(db)

    assert repo.get_plant_raw("p1", "tenant-a") is None


def test_get_plant_raw_returns_owned_plant() -> None:
    db = MagicMock()
    db.collection.return_value.get.return_value = {
        "_key": "p1",
        "tenant_key": "tenant-a",
        "instance_id": "T-1",
    }
    repo = PropagationRepository(db)

    doc = repo.get_plant_raw("p1", "tenant-a")

    assert doc is not None
    assert doc["_key"] == "p1"


def test_get_event_rejects_foreign_tenant() -> None:
    db = MagicMock()
    db.collection.return_value.get.return_value = {
        "_key": "evt-1",
        "tenant_key": "tenant-b",
        "method": "cutting",
    }
    repo = PropagationRepository(db)

    assert repo.get_event("evt-1", "tenant-a") is None
