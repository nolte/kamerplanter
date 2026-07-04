"""AP-8 / SEC-B4 — tenant-isolation is enforced, not opt-in.

Prior to this fix ``BaseArangoRepository.get_all`` only applied the tenant
filter ``if tenant_key`` — a caller that forgot the argument (default ``None``
or the empty-string sentinel ``""``) silently received documents of *every*
tenant.  These tests pin the enforced behaviour:

* tenant-scoped repositories raise ``ValueError`` when neither ``tenant_key``
  nor an explicit ``all_tenants=True`` system opt-in is supplied,
* a supplied ``tenant_key`` scopes the query so tenant A never sees tenant B
  documents (cross-tenant negative test over the real ``get_all`` code path),
* ``all_tenants=True`` restores the deliberate system-wide read,
* global (tenant-less) collections keep working without any ``tenant_key``.

The injected ``StandardDatabase`` is a genuine I/O boundary and is doubled: the
guard tests use a plain ``MagicMock`` (the guard fires before any query runs);
the data-level tests use a tiny fake that replays ArangoDB's ``tenant_key``
FILTER so that ``get_all(tenant_key=...)`` returns only the matching rows.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.data_access.arango.tank_repository import ArangoTankRepository


# ── Fake ArangoDB that replays the tenant_key FILTER ────────────────────────
class _FakeAql:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        rows = self._docs
        # Replay any "doc.tenant_key == @vN" filter the query builder emitted.
        for var, value in bind_vars.items():
            if f"doc.tenant_key == @{var}" in query:
                rows = [d for d in rows if d.get("tenant_key") == value]
        if "COLLECT WITH COUNT" in query:
            return iter([len(rows)])
        return iter([dict(d) for d in rows])


class _FakeDb:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.aql = _FakeAql(docs)

    def collection(self, _name: str):  # pragma: no cover - unused by get_all
        return MagicMock()


class _ScopedRepo(BaseArangoRepository):
    """Minimal tenant-scoped repo exercising the real base get_all path.

    Unbound raw view (this test asserts on raw dicts), so it opts into raw
    mode to satisfy the FR-002 A3 fail-fast guard.
    """

    is_tenant_scoped = True

    def __init__(self, db) -> None:
        super().__init__(db, "scoped_collection", raw=True)


class _GlobalRepo(BaseArangoRepository):
    """Minimal global (tenant-less) repo — no guard must fire.

    Unbound raw view; opts into raw mode (FR-002 A3).
    """

    def __init__(self, db) -> None:
        super().__init__(db, "global_collection", raw=True)


# Real tenant-scoped repositories (all reach the guard through get_all).
_SCOPED_REPO_FACTORIES = [
    ArangoPlantInstanceRepository,
    ArangoTankRepository,
    ArangoNutrientPlanRepository,
    ArangoPlantingRunRepository,
    ArangoFertilizerRepository,
]


class TestTenantScopeGuard:
    @pytest.mark.parametrize("factory", _SCOPED_REPO_FACTORIES)
    def test_missing_tenant_key_raises(self, factory):
        repo = factory(MagicMock())
        with pytest.raises(ValueError, match="tenant-scoped"):
            repo.get_all(offset=0, limit=50)

    @pytest.mark.parametrize("factory", _SCOPED_REPO_FACTORIES)
    def test_empty_string_tenant_key_raises(self, factory):
        # "" is the codebase's no-tenant sentinel and must NOT be a leak vector.
        repo = factory(MagicMock())
        with pytest.raises(ValueError, match="tenant-scoped"):
            repo.get_all(offset=0, limit=50, tenant_key="")

    def test_guard_fires_on_own_aql_filter_branch(self):
        # Repos with a custom filter branch must guard before building AQL.
        repo = ArangoNutrientPlanRepository(MagicMock())
        with pytest.raises(ValueError, match="tenant-scoped"):
            repo.get_all(offset=0, limit=50, filters={"is_template": True})

    def test_fertilizer_filter_without_tenant_raises(self):
        repo = ArangoFertilizerRepository(MagicMock())
        with pytest.raises(ValueError, match="tenant-scoped"):
            repo.get_all(offset=0, limit=50, filters={"fertilizer_type": "supplement"})

    def test_global_repo_without_tenant_key_is_allowed(self):
        db = _FakeDb([{"_key": "g1", "_id": "global_collection/g1"}])
        items, total = _GlobalRepo(db).get_all(offset=0, limit=50)
        assert total == 1
        assert items[0]["_key"] == "g1"

    def test_real_global_species_repo_needs_no_tenant_key(self):
        # Species is a global catalog: get_all() without tenant_key must not raise.
        db = _FakeDb([])
        items, total = ArangoSpeciesRepository(db).get_all(offset=0, limit=50)
        assert items == []
        assert total == 0


class TestCrossTenantIsolation:
    """Cross-tenant negative test over the real base get_all code path."""

    @pytest.fixture
    def db(self):
        return _FakeDb(
            [
                {"_key": "a1", "_id": "scoped_collection/a1", "tenant_key": "tenant_a"},
                {"_key": "a2", "_id": "scoped_collection/a2", "tenant_key": "tenant_a"},
                {"_key": "b1", "_id": "scoped_collection/b1", "tenant_key": "tenant_b"},
            ]
        )

    def test_tenant_a_never_sees_tenant_b(self, db):
        items, total = _ScopedRepo(db).get_all(tenant_key="tenant_a")
        keys = {d["_key"] for d in items}
        assert keys == {"a1", "a2"}
        assert "b1" not in keys
        assert total == 2

    def test_tenant_b_only_sees_own(self, db):
        items, total = _ScopedRepo(db).get_all(tenant_key="tenant_b")
        assert {d["_key"] for d in items} == {"b1"}
        assert total == 1

    def test_all_tenants_opt_in_returns_every_tenant(self, db):
        items, total = _ScopedRepo(db).get_all(all_tenants=True)
        assert {d["_key"] for d in items} == {"a1", "a2", "b1"}
        assert total == 3
