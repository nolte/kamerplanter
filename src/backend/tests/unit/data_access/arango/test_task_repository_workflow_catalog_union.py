"""Workflow templates are a hybrid catalog (SEC-B4 regression, PR #324 follow-up).

Globally seeded system workflow templates carry ``tenant_key == ""`` (they are
authored in ``workflows.yaml`` with ``is_system: true`` and no tenant_key);
per-tenant custom templates carry the owning ``tenant_key``.
``ArangoTaskRepository.get_all_workflow_templates`` must therefore union the
caller's own rows with the global rows — mirroring the fertilizer and
nutrient-plan repositories — while still never leaking a *foreign* tenant's rows.

Prior to the fix the repository applied the strict filter
``doc.tenant_key == @tenant_key`` (PR #324), so the globally seeded templates
(empty tenant_key) matched no real tenant and the ``/aufgaben/workflows`` list
came back empty for every tenant.

The injected ``StandardDatabase`` is a genuine I/O boundary and is doubled by a
tiny fake that replays the hybrid-catalog union FILTER the repository emits, so
``get_all_workflow_templates(tenant_key=...)`` returns exactly the rows real
ArangoDB would.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.task_repository import ArangoTaskRepository


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

        # Replay the "@target_entity_type IN doc.target_entity_types" filter.
        if "target_entity_type" in bind_vars:
            wanted = bind_vars["target_entity_type"]
            rows = [d for d in rows if wanted in d.get("target_entity_types", [])]

        if "COLLECT WITH COUNT" in query:
            return iter([len(rows)])
        # Emulate SORT doc.name for a stable, real-DB-like order.
        rows = sorted(rows, key=lambda d: d.get("name", ""))
        return iter([dict(d) for d in rows])


class _FakeDb:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.aql = _FakeAql(docs)

    def collection(self, _name: str):  # pragma: no cover - unused by list query
        return MagicMock()


def _wf(
    key: str,
    tenant_key: str | None,
    *,
    name: str = "Workflow",
    is_system: bool = False,
    target_entity_types: list[str] | None = None,
) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "_key": key,
        "_id": f"workflow_templates/{key}",
        "name": name,
        "is_system": is_system,
        "target_entity_types": target_entity_types or ["plant_instance"],
    }
    if tenant_key is not None:
        doc["tenant_key"] = tenant_key
    return doc


class TestWorkflowHybridCatalogUnion:
    """A tenant sees global system templates + own templates, never a foreign tenant's."""

    @pytest.fixture
    def db(self) -> _FakeDb:
        return _FakeDb(
            [
                _wf("sys1", "", name="Cannabis SOG", is_system=True),  # globally seeded
                _wf("sys2", None, name="Tomato Standard", is_system=True),  # global, missing key
                _wf("a1", "tenant_a", name="Tenant A Custom"),
                _wf("b1", "tenant_b", name="Tenant B Custom"),
            ]
        )

    def test_seeded_system_template_is_visible_to_tenant(self, db: _FakeDb) -> None:
        items, total = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_a")
        keys = {wt.key for wt in items}
        assert "sys1" in keys
        assert "sys2" in keys
        assert total == 3

    def test_tenant_own_template_is_visible(self, db: _FakeDb) -> None:
        items, _ = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_a")
        assert "a1" in {wt.key for wt in items}

    def test_cross_tenant_template_is_never_visible(self, db: _FakeDb) -> None:
        # SEC — the most important assertion: tenant A must never see tenant B.
        items, total = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_a")
        keys = {wt.key for wt in items}
        assert "b1" not in keys
        assert keys == {"sys1", "sys2", "a1"}
        assert total == 3

    def test_other_tenant_sees_globals_plus_own_only(self, db: _FakeDb) -> None:
        items, total = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_b")
        assert {wt.key for wt in items} == {"sys1", "sys2", "b1"}
        assert total == 3

    def test_system_context_without_tenant_returns_every_template(self, db: _FakeDb) -> None:
        # The seeder reads with an empty tenant_key; that path stays unfiltered.
        items, total = ArangoTaskRepository(db).get_all_workflow_templates()
        assert {wt.key for wt in items} == {"sys1", "sys2", "a1", "b1"}
        assert total == 4


class TestWorkflowHybridCatalogUnionWithTargetFilter:
    """The union must also hold when ``target_entity_type`` narrows the list."""

    @pytest.fixture
    def db(self) -> _FakeDb:
        return _FakeDb(
            [
                _wf("sys_loc", "", name="System Location", is_system=True, target_entity_types=["location"]),
                _wf("sys_plant", "", name="System Plant", is_system=True, target_entity_types=["plant_instance"]),
                _wf("a_loc", "tenant_a", name="Tenant A Location", target_entity_types=["location"]),
                _wf("b_loc", "tenant_b", name="Tenant B Location", target_entity_types=["location"]),
            ]
        )

    def test_filtered_query_includes_global_and_own_matches(self, db: _FakeDb) -> None:
        items, total = ArangoTaskRepository(db).get_all_workflow_templates(
            tenant_key="tenant_a",
            target_entity_type="location",
        )
        keys = {wt.key for wt in items}
        assert keys == {"sys_loc", "a_loc"}
        assert "sys_plant" not in keys  # filtered out by target_entity_type
        assert "b_loc" not in keys  # foreign tenant never leaks
        assert total == 2
