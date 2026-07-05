"""Nutrient plans are a hybrid catalog (SEC-B4 regression, PR #324 follow-up).

Globally seeded system plans carry ``tenant_key == ""``; per-tenant custom
plans carry the owning ``tenant_key``.  ``ArangoNutrientPlanRepository.get_all``
must therefore union the caller's own rows with the global rows — mirroring the
fertilizer repository — while still never leaking rows of a *foreign* tenant.

Prior to the fix the plan repository applied the strict filter
``doc.tenant_key == @tenant_key`` (both in its own ``filters`` branch and in the
inherited ``_list_docs`` fallback), so the globally seeded plans (empty
tenant_key) matched no real tenant and the list came back empty.

The injected ``StandardDatabase`` is a genuine I/O boundary and is doubled by a
tiny fake that replays the hybrid-catalog union FILTER the repository emits, so
``get_all(tenant_key=...)`` returns exactly the rows real ArangoDB would.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository


# ── Fake ArangoDB that replays the hybrid-catalog union FILTER ──────────────
class _FakeAql:
    #: The exact union predicate the repository emits for a tenant-scoped read.
    _UNION_CLAUSE = '(doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null)'

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        rows = self._docs

        # Replay the hybrid-catalog union: own tenant rows PLUS global rows
        # (empty-string or missing tenant_key).
        if self._UNION_CLAUSE in query and "tenant_key" in bind_vars:
            own = bind_vars["tenant_key"]
            rows = [d for d in rows if d.get("tenant_key") in (own, "", None)]

        # Replay any additional "doc.<field> == @valN" equality filters.
        for var, value in bind_vars.items():
            if not var.startswith("val"):
                continue
            field = self._field_for_val(query, var)
            if field is not None:
                rows = [d for d in rows if d.get(field) == value]

        if "COLLECT WITH COUNT" in query:
            return iter([len(rows)])
        return iter([dict(d) for d in rows])

    @staticmethod
    def _field_for_val(query: str, var: str) -> str | None:
        marker = f"== @{var}"
        idx = query.find(marker)
        if idx == -1:
            return None
        # "doc.<field> == @valN" — walk back to the field name after "doc.".
        prefix = query[:idx].rstrip()
        doc_prefix = "doc."
        start = prefix.rfind(doc_prefix)
        if start == -1:
            return None
        return prefix[start + len(doc_prefix) :]


class _FakeDb:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.aql = _FakeAql(docs)

    def collection(self, _name: str):  # pragma: no cover - unused by get_all
        return MagicMock()


def _plan(key: str, tenant_key: str | None, *, name: str = "Plan", is_template: bool = False) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "_key": key,
        "_id": f"nutrient_plans/{key}",
        "name": name,
        "is_template": is_template,
    }
    if tenant_key is not None:
        doc["tenant_key"] = tenant_key
    return doc


class TestHybridCatalogUnion:
    """A tenant sees global plans + own plans, never a foreign tenant's plans."""

    @pytest.fixture
    def db(self) -> _FakeDb:
        return _FakeDb(
            [
                _plan("sys1", "", name="System Base A"),  # globally seeded
                _plan("sys2", None, name="System Base B"),  # global, missing key
                _plan("a1", "tenant_a", name="Tenant A Custom"),
                _plan("b1", "tenant_b", name="Tenant B Custom"),
            ]
        )

    def test_seeded_global_plan_is_visible_to_tenant(self, db: _FakeDb) -> None:
        items, total = ArangoNutrientPlanRepository(db).get_all(tenant_key="tenant_a")
        keys = {p.key for p in items}
        assert "sys1" in keys
        assert "sys2" in keys
        assert total == 3

    def test_tenant_own_plan_is_visible(self, db: _FakeDb) -> None:
        items, _ = ArangoNutrientPlanRepository(db).get_all(tenant_key="tenant_a")
        assert "a1" in {p.key for p in items}

    def test_cross_tenant_plan_is_never_visible(self, db: _FakeDb) -> None:
        # SEC — the most important assertion: tenant A must never see tenant B.
        items, total = ArangoNutrientPlanRepository(db).get_all(tenant_key="tenant_a")
        keys = {p.key for p in items}
        assert "b1" not in keys
        assert keys == {"sys1", "sys2", "a1"}
        assert total == 3

    def test_other_tenant_sees_globals_plus_own_only(self, db: _FakeDb) -> None:
        items, total = ArangoNutrientPlanRepository(db).get_all(tenant_key="tenant_b")
        assert {p.key for p in items} == {"sys1", "sys2", "b1"}
        assert total == 3

    def test_all_tenants_opt_in_returns_every_plan(self, db: _FakeDb) -> None:
        items, total = ArangoNutrientPlanRepository(db).get_all(all_tenants=True)
        assert {p.key for p in items} == {"sys1", "sys2", "a1", "b1"}
        assert total == 4


class TestHybridCatalogUnionWithFilters:
    """The union must also hold on the ``filters`` branch (e.g. is_template)."""

    @pytest.fixture
    def db(self) -> _FakeDb:
        return _FakeDb(
            [
                _plan("sys_tpl", "", name="System Template", is_template=True),
                _plan("sys_plain", "", name="System Plain", is_template=False),
                _plan("a_tpl", "tenant_a", name="Tenant A Template", is_template=True),
                _plan("b_tpl", "tenant_b", name="Tenant B Template", is_template=True),
            ]
        )

    def test_filtered_query_includes_global_and_own_matches(self, db: _FakeDb) -> None:
        items, total = ArangoNutrientPlanRepository(db).get_all(
            tenant_key="tenant_a",
            filters={"is_template": True},
        )
        keys = {p.key for p in items}
        assert keys == {"sys_tpl", "a_tpl"}
        assert "sys_plain" not in keys  # filtered out by is_template
        assert "b_tpl" not in keys  # foreign tenant never leaks
        assert total == 2
