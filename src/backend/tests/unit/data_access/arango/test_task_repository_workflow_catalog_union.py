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
    #: The copy-on-write dedup predicate the repository emits (#1030). Its
    #: companion ``LET forked_source_keys = (...)`` collects this tenant's fork
    #: sources; here we replay both together against the in-memory rows.
    _SUPPRESS_CLAUSE = "doc._key NOT IN forked_source_keys"

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

        # Replay the copy-on-write dedup: the ``LET forked_source_keys`` subquery
        # collects the source_workflow_key of every fork THIS tenant owns, and
        # the FILTER drops any row whose _key is in that set. Applied BEFORE the
        # COUNT/LIMIT below so the fake mirrors real ArangoDB's paging maths.
        if self._SUPPRESS_CLAUSE in query and "tenant_key" in bind_vars:
            own = bind_vars["tenant_key"]
            forked_source_keys = {
                d.get("source_workflow_key")
                for d in self._docs
                if d.get("tenant_key") == own and d.get("source_workflow_key")
            }
            rows = [d for d in rows if d.get("_key") not in forked_source_keys]

        # Replay the "@target_entity_type IN doc.target_entity_types" filter.
        if "target_entity_type" in bind_vars:
            wanted = bind_vars["target_entity_type"]
            rows = [d for d in rows if wanted in d.get("target_entity_types", [])]

        if "COLLECT WITH COUNT" in query:
            return iter([len(rows)])
        # Emulate SORT doc.name for a stable, real-DB-like order.
        rows = sorted(rows, key=lambda d: d.get("name", ""))
        # Emulate ``LIMIT @offset, @limit`` so paging behaviour (and the #1030
        # pagination trap) is exercised the way real ArangoDB slices it.
        if "offset" in bind_vars and "limit" in bind_vars:
            start = bind_vars["offset"]
            rows = rows[start : start + bind_vars["limit"]]
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
    source_workflow_key: str | None = None,
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
    if source_workflow_key is not None:
        doc["source_workflow_key"] = source_workflow_key
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


class TestForkedSharedPlanIsDeduped:
    """Copy-on-write dedup (#1030): a fork suppresses its shared source row.

    After a tenant forks a shared *generated* activity plan (#1003/#1029), the
    fork is a ``WorkflowTemplate`` carrying that tenant's ``tenant_key`` and a
    ``source_workflow_key`` pointing at the shared original (``tenant_key == ""``).
    Without dedup the hybrid-catalog union surfaces BOTH rows under the same name
    — the N+1 the issue reports. The repository must suppress the shared source
    for the forking tenant, and only for them, and the count must reflect it.
    """

    @pytest.fixture
    def db(self) -> _FakeDb:
        # Two shared generated plans; tenant_a has forked the "Tomate" one.
        return _FakeDb(
            [
                _wf("shared_tomato", "", name="Tomate", is_system=True),  # shared original
                _wf("shared_basil", "", name="Basilikum", is_system=True),  # shared, unforked
                _wf(
                    "fork_tomato_a",
                    "tenant_a",
                    name="Tomate",
                    source_workflow_key="shared_tomato",
                ),  # tenant_a's private copy
            ]
        )

    def test_forking_tenant_sees_only_their_fork_not_the_source(self, db: _FakeDb) -> None:
        # RED against pre-#1030 code: the union returned BOTH "shared_tomato"
        # (the shared original) and "fork_tomato_a" — two identically-named
        # "Tomate" rows. The fix suppresses the shared source for this tenant.
        items, total = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_a")
        keys = {wt.key for wt in items}
        assert "shared_tomato" not in keys  # the shared original is hidden
        assert "fork_tomato_a" in keys  # the editable fork stays
        # N shared plans (Tomate + Basilikum) -> N rows, not N+1.
        assert keys == {"fork_tomato_a", "shared_basil"}
        assert total == 2
        # Exactly one "Tomate", and it is the fork.
        tomaten = [wt for wt in items if wt.name == "Tomate"]
        assert len(tomaten) == 1
        assert tomaten[0].key == "fork_tomato_a"

    def test_unforked_shared_plan_stays_visible_to_forking_tenant(self, db: _FakeDb) -> None:
        # A tenant who forked ONE plan still sees the shared plans they did not
        # fork — suppression is per-source, never blanket.
        items, _ = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_a")
        assert "shared_basil" in {wt.key for wt in items}

    def test_other_tenant_still_sees_the_shared_source(self, db: _FakeDb) -> None:
        # Direction B (#324): tenant_b has NOT forked, so nothing is suppressed —
        # they see the shared "Tomate" original and never tenant_a's fork.
        items, total = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_b")
        keys = {wt.key for wt in items}
        assert "shared_tomato" in keys
        assert "fork_tomato_a" not in keys  # foreign tenant's fork never leaks
        assert keys == {"shared_tomato", "shared_basil"}
        assert total == 2

    def test_system_context_without_tenant_suppresses_nothing(self, db: _FakeDb) -> None:
        # The seeder / internal callers read with an empty tenant_key: no
        # dedup LET is emitted, so every row (fork and source alike) is returned.
        items, total = ArangoTaskRepository(db).get_all_workflow_templates()
        assert {wt.key for wt in items} == {"shared_tomato", "shared_basil", "fork_tomato_a"}
        assert total == 3

    def test_count_matches_returned_rows_for_forking_tenant(self, db: _FakeDb) -> None:
        # The pagination trap the issue names: the suppression lives in the query
        # (before COUNT/LIMIT), so the reported total equals the row count. A
        # post-fetch Python filter would report 3 here while returning 2.
        items, total = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_a")
        assert total == len(items) == 2


class TestForkDedupSurvivesPagination:
    """The dedup total stays correct across page boundaries (#1030 trap).

    A post-fetch Python filter would corrupt paging: a page of shared rows that
    happens to contain a fork's source would come back one short, and the count
    would not match. Because the suppression is in AQL, the fake — which applies
    it before LIMIT — reproduces a stable, correct total regardless of the page.
    """

    @pytest.fixture
    def db(self) -> _FakeDb:
        # Three shared plans (a/b/c), tenant_a forked the middle one ("b_shared").
        return _FakeDb(
            [
                _wf("a_shared", "", name="Aubergine", is_system=True),
                _wf("b_shared", "", name="Basilikum", is_system=True),
                _wf("c_shared", "", name="Chili", is_system=True),
                _wf(
                    "b_fork_a",
                    "tenant_a",
                    name="Basilikum",
                    source_workflow_key="b_shared",
                ),
            ]
        )

    def test_total_is_deduped_count_not_raw_union(self, db: _FakeDb) -> None:
        _, total = ArangoTaskRepository(db).get_all_workflow_templates(tenant_key="tenant_a", offset=0, limit=50)
        # 3 shared + 1 fork - 1 suppressed source = 3, not the raw 4.
        assert total == 3

    def test_source_row_never_occupies_a_page_slot(self, db: _FakeDb) -> None:
        # Walk every single-row page; the suppressed source must appear on none of
        # them, and the fork must appear on exactly one.
        seen: list[str] = []
        for offset in range(3):
            items, _ = ArangoTaskRepository(db).get_all_workflow_templates(
                tenant_key="tenant_a", offset=offset, limit=1
            )
            seen.extend(wt.key for wt in items if wt.key)
        assert "b_shared" not in seen  # source suppressed on every page
        assert seen.count("b_fork_a") == 1  # fork present exactly once
        assert set(seen) == {"a_shared", "b_fork_a", "c_shared"}
