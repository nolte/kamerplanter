"""Repository-level tenant isolation for survival analytics (REQ-003 G1 / SEC-B4).

``get_survival_stats`` MUST be strictly tenant-scoped. These tests pin that the
AQL binds the collection via ``@@col`` (never interpolated), filters every
row on ``p.tenant_key == @tenant_key``, passes the caller's tenant_key through
as a bind var, and rejects the empty-tenant sentinel before any query runs.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository


class _CapturingAql:
    def __init__(self) -> None:
        self.query: str | None = None
        self.bind_vars: dict[str, Any] | None = None
        self.result: dict[str, Any] = {
            "total": 0,
            "terminated": 0,
            "died": 0,
            "by_type": [],
            "by_cause": [],
            "by_phase": [],
        }

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.query = query
        self.bind_vars = bind_vars or {}
        return iter([self.result])


class _CapturingDb:
    def __init__(self) -> None:
        self.aql = _CapturingAql()

    def collection(self, _name: str):  # pragma: no cover - unused here
        raise AssertionError("get_survival_stats must not touch a raw collection")


def test_survival_stats_query_is_tenant_scoped() -> None:
    db = _CapturingDb()
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    result = repo.get_survival_stats("tenant-A")

    assert result == db.aql.result
    # Collection bound, not interpolated (injection guard).
    assert "@@col" in (db.aql.query or "")
    assert db.aql.bind_vars is not None
    assert db.aql.bind_vars["@col"] == "plant_instances"
    # Tenant filter present on the row scan and the caller's key passed through.
    assert "p.tenant_key == @tenant_key" in (db.aql.query or "")
    assert db.aql.bind_vars["tenant_key"] == "tenant-A"
    # No literal tenant value interpolated into the query string.
    assert "tenant-A" not in (db.aql.query or "")
    # Regression guard: "concluded" (terminated) is derived from removed_on, not
    # termination_type — otherwise plain-removed / pre-feature plants would be
    # miscounted as still-in-cultivation and inflate the survival rate.
    assert "r.removed_on != null" in (db.aql.query or "")


def test_survival_stats_rejects_empty_tenant_key() -> None:
    db = _CapturingDb()
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="tenant-scoped"):
        repo.get_survival_stats("")

    # Guard fires before any query is executed.
    assert db.aql.query is None
