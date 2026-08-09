"""Tests for v0035_backfill_task_template_tenant_key (#965 item 1).

The migration stamps ``tenant_key`` on task templates that predate the field:

* a template of a tenant-owned workflow inherits that workflow's tenant,
* a template of a **system** workflow (``tenant_key == ""``) becomes global,
* a template of a **shared** auto-generated plan (``tenant_key == ""``) stays global,
* a **standalone** template (no parent) becomes global — the documented limitation:
  there is no stored owner to recover,
* a **dangling** parent reference becomes global for the same reason.

Idempotency keys on the attribute being *absent* (not empty), because ``""`` is a
legitimate final value here — a re-run must not re-touch a row it backfilled to
global. Dry-run computes the full plan and writes nothing. Irreversible.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0035_backfill_task_template_tenant_key import migration


class _FakeCollection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self._docs = docs

    def get(self, key: str) -> dict[str, Any] | None:
        return self._docs.get(key)


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        if "UPDATE" in query:
            docs = self._db.data[bind_vars["@collection"]]
            for pair in bind_vars["pairs"]:
                docs[pair["key"]]["tenant_key"] = pair["tenant_key"]
            return iter([])
        # The attribute-absence scan: FILTER doc.tenant_key == null
        collection = bind_vars["@collection"]
        docs = self._db.data.get(collection, {})
        return iter(
            {"key": key, "workflow_template_key": doc.get("workflow_template_key")}
            for key, doc in docs.items()
            if "tenant_key" not in doc
        )


class _FakeDb:
    def __init__(self, data: dict[str, dict[str, dict]]) -> None:
        self.data = data
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.data

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self.data[name])


def _sample() -> _FakeDb:
    data: dict[str, dict[str, dict]] = {
        col.WORKFLOW_TEMPLATES: {
            "wf-owned": {"tenant_key": "tenant-A"},
            "wf-system": {"tenant_key": "", "is_system": True},
            "wf-shared": {"tenant_key": "", "is_system": False, "auto_generated": True},
        },
        col.TASK_TEMPLATES: {
            # Child of a tenant-owned workflow → inherits its tenant.
            "tt-owned": {"workflow_template_key": "wf-owned"},
            # Child of a system workflow → global.
            "tt-system": {"workflow_template_key": "wf-system"},
            # Child of a shared auto-generated plan → global.
            "tt-shared": {"workflow_template_key": "wf-shared"},
            # Standalone: no parent at all → global (the documented limitation).
            "tt-standalone": {"workflow_template_key": None},
            # Dangling parent reference → global (owner unsourceable).
            "tt-dangling": {"workflow_template_key": "wf-gone"},
            # Already backfilled to global — attribute present, must be skipped.
            "tt-done-global": {"workflow_template_key": None, "tenant_key": ""},
            # Already owned — attribute present, must be skipped.
            "tt-done-owned": {"workflow_template_key": "wf-owned", "tenant_key": "tenant-A"},
        },
    }
    return _FakeDb(data)


def test_a_template_of_a_tenant_owned_workflow_inherits_its_tenant():
    db = _sample()

    migration.up(db)

    assert db.data[col.TASK_TEMPLATES]["tt-owned"]["tenant_key"] == "tenant-A"


def test_system_shared_standalone_and_dangling_all_become_global():
    db = _sample()

    migration.up(db)

    tts = db.data[col.TASK_TEMPLATES]
    assert tts["tt-system"]["tenant_key"] == ""
    assert tts["tt-shared"]["tenant_key"] == ""
    assert tts["tt-standalone"]["tenant_key"] == ""
    assert tts["tt-dangling"]["tenant_key"] == ""


def test_report_counts_each_reason():
    db = _sample()

    report = migration.up(db)

    # 5 attribute-less rows are stamped; the 2 already-present rows are skipped.
    assert report.changed == 5
    assert report.scanned == 5
    assert report.details["from_tenant_parent"] == 1
    assert report.details["system_or_shared_parent"] == 2
    assert report.details["standalone"] == 1
    assert report.details["dangling_parent"] == 1


def test_already_stamped_rows_are_left_untouched():
    db = _sample()

    migration.up(db)

    # Both a global and an owned row that already carry the attribute are skipped,
    # so an empty owner is never mistaken for "not yet done".
    assert db.data[col.TASK_TEMPLATES]["tt-done-global"]["tenant_key"] == ""
    assert db.data[col.TASK_TEMPLATES]["tt-done-owned"]["tenant_key"] == "tenant-A"


def test_rerun_is_a_noop():
    db = _sample()
    migration.up(db)

    report = migration.up(db)

    assert report.changed == 0
    assert report.noop is True


def test_dry_run_writes_nothing_but_plans_the_full_cascade():
    db = _sample()

    report = migration.up(db, dry_run=True)

    assert report.dry_run is True
    assert report.changed == 0
    assert report.details["to_update"] == 5
    # Nothing written: the attribute is still absent on every candidate row.
    assert "tenant_key" not in db.data[col.TASK_TEMPLATES]["tt-owned"]
    assert "tenant_key" not in db.data[col.TASK_TEMPLATES]["tt-standalone"]


def test_empty_database_is_a_noop():
    db = _FakeDb({})

    report = migration.up(db)

    assert report.changed == 0
    assert report.scanned == 0


def test_migration_metadata():
    assert migration.version == "0035"
    assert migration.name == "backfill_task_template_tenant_key"
    assert migration.reversible is False
