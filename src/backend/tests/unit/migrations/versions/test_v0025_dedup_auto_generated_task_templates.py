"""Tests for v0025_dedup_auto_generated_task_templates (Issue #619).

Verifies against a fake ArangoDB that per-phase duplicate task templates are collapsed
to one survivor per (workflow, activity) group, that the survivor's wf_contains and
instance_of edges are kept while the duplicates' edges are removed, that singletons and
distinct activities are left untouched, and that the migration is idempotent and
dry-run-safe.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0025_dedup_auto_generated_task_templates import migration, plan_removals


class _FakeAql:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        stripped = query.lstrip()
        tokens = query.split()
        if stripped.startswith("REMOVE"):
            collection = tokens[tokens.index("IN") + 1]
            docs = self._collections.setdefault(collection, [])
            self._collections[collection] = [d for d in docs if d.get("_key") != bind_vars["key"]]
            return iter([])
        if stripped.startswith("FOR") and "REMOVE" in tokens:
            # FOR e IN <col> FILTER e._to == @tt_id REMOVE e IN <col>
            collection = tokens[tokens.index("REMOVE") + 3]
            docs = self._collections.setdefault(collection, [])
            self._collections[collection] = [d for d in docs if d.get("_to") != bind_vars["tt_id"]]
            return iter([])
        # Plain scan: FOR d IN <col> RETURN d
        collection = tokens[tokens.index("IN") + 1]
        return iter(list(self._collections.setdefault(collection, [])))


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.aql = _FakeAql(collections)


def _tt(
    key: str,
    workflow: str = "wf1",
    activity_key: str = "transplant",
    name: str = "Umpflanzen",
    sequence_order: int = 0,
) -> dict[str, Any]:
    return {
        "_key": key,
        "workflow_template_key": workflow,
        "activity_key": activity_key,
        "name": name,
        "sequence_order": sequence_order,
    }


def _tt_id(key: str) -> str:
    return f"{col.TASK_TEMPLATES}/{key}"


def _collections() -> dict[str, list[dict[str, Any]]]:
    return {
        col.TASK_TEMPLATES: [
            # Four duplicate "Umpflanzen" templates in one workflow (the #619 bug).
            _tt("t1", activity_key="transplant", sequence_order=0),
            _tt("t2", activity_key="transplant", sequence_order=3),
            _tt("t3", activity_key="transplant", sequence_order=7),
            _tt("t4", activity_key="transplant", sequence_order=11),
            # A distinct activity in the same workflow — untouched.
            _tt("t5", activity_key="pruning", name="Rueckschnitt", sequence_order=1),
            # Same activity_key but a different workflow — a separate group, untouched.
            _tt("t6", workflow="wf2", activity_key="transplant", sequence_order=0),
        ],
        col.WF_CONTAINS: [
            {"_key": "w1", "_from": f"{col.WORKFLOW_TEMPLATES}/wf1", "_to": _tt_id("t1")},
            {"_key": "w2", "_from": f"{col.WORKFLOW_TEMPLATES}/wf1", "_to": _tt_id("t2")},
            {"_key": "w3", "_from": f"{col.WORKFLOW_TEMPLATES}/wf1", "_to": _tt_id("t3")},
            {"_key": "w4", "_from": f"{col.WORKFLOW_TEMPLATES}/wf1", "_to": _tt_id("t4")},
        ],
        col.INSTANCE_OF: [
            {"_key": "i2", "_from": f"{col.TASKS}/task-x", "_to": _tt_id("t2")},
        ],
    }


class TestPlanRemovals:
    def test_keeps_lowest_sequence_order_survivor(self) -> None:
        templates = _collections()[col.TASK_TEMPLATES]
        removals = plan_removals(templates)
        removed_keys = sorted(r["_key"] for r in removals)
        # t1 (sequence_order 0) survives; t2/t3/t4 removed. t5/t6 are singletons.
        assert removed_keys == ["t2", "t3", "t4"]

    def test_singletons_are_never_removed(self) -> None:
        removals = plan_removals([_tt("only", activity_key="a1")])
        assert removals == []

    def test_falls_back_to_name_without_activity_key(self) -> None:
        templates = [
            _tt("n1", activity_key="", name="Stroh unterlegen", sequence_order=0),
            _tt("n2", activity_key="", name="Stroh unterlegen", sequence_order=2),
        ]
        removals = plan_removals(templates)
        assert [r["_key"] for r in removals] == ["n2"]


class TestMigration:
    def test_collapses_duplicates_and_prunes_edges(self) -> None:
        collections = _collections()
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 3
        assert report.scanned == 6

        remaining = {t["_key"] for t in collections[col.TASK_TEMPLATES]}
        assert remaining == {"t1", "t5", "t6"}

        # Survivor edge kept; duplicate edges pruned.
        wf_to = {e["_to"] for e in collections[col.WF_CONTAINS]}
        assert wf_to == {_tt_id("t1")}
        # instance_of edge for removed t2 is gone.
        assert collections[col.INSTANCE_OF] == []

    def test_idempotent_on_second_run(self) -> None:
        db = _FakeDb(_collections())
        migration.up(db)  # type: ignore[arg-type]
        report = migration.up(db)  # type: ignore[arg-type]
        assert report.changed == 0
        assert report.noop is True

    def test_dry_run_writes_nothing(self) -> None:
        collections = _collections()
        db = _FakeDb(collections)
        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.dry_run is True
        assert report.changed == 0
        # Nothing removed.
        assert len(collections[col.TASK_TEMPLATES]) == 6
        assert len(collections[col.WF_CONTAINS]) == 4
        assert len(collections[col.INSTANCE_OF]) == 1
        # But the duplicate count is reported.
        assert len(report.details["removed_keys"]) == 3
