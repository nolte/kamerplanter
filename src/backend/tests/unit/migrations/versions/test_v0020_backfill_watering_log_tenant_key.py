"""Tests for v0020_backfill_watering_log_tenant_key (#580).

The migration binds every ``watering_logs`` document that still carries an
empty/absent ``tenant_key`` to its plant's tenant, resolved through the
``LOG_PLANT`` edge with the embedded ``plant_keys`` array as a fallback. Logs
whose plants yield no tenant are left untouched (reported as ``unresolved``).
Idempotent, dry-run-safe, irreversible.
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.migrations.versions.v0020_backfill_watering_log_tenant_key import migration


class _FakeCollection:
    def __init__(self, docs: dict[str, dict]) -> None:
        self._docs = docs

    def get(self, key: str) -> dict | None:
        return self._docs.get(key)


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        if "UPDATE" in query:
            logs = self._db.data[col.WATERING_LOGS]
            for pair in bind_vars["pairs"]:
                logs[pair["key"]]["tenant_key"] = pair["tenant_key"]
            return iter([])
        if bind_vars.get("@log_plant") == col.LOG_PLANT:
            # Resolve non-empty plant tenants for the given log via LOG_PLANT edges.
            log_id = bind_vars["log_id"]
            plants = self._db.data[col.PLANT_INSTANCES]
            result: list[str] = []
            for edge in self._db.edges:
                if edge["_from"] != log_id:
                    continue
                plant_key = edge["_to"].split("/", 1)[1]
                plant = plants.get(plant_key)
                if plant and plant.get("tenant_key"):
                    result.append(plant["tenant_key"])
            return iter(result)
        # Orphaned-logs scan.
        logs = self._db.data[col.WATERING_LOGS]
        return iter(
            {
                "key": key,
                "id": f"{col.WATERING_LOGS}/{key}",
                "plant_keys": doc.get("plant_keys"),
            }
            for key, doc in logs.items()
            if not doc.get("tenant_key")
        )


class _FakeDb:
    def __init__(self, data: dict[str, dict[str, dict]], edges: list[dict]) -> None:
        self.data = data
        self.edges = edges
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.data or name == col.LOG_PLANT

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self.data[name])


def _edge(log_key: str, plant_key: str) -> dict:
    return {"_from": f"{col.WATERING_LOGS}/{log_key}", "_to": f"{col.PLANT_INSTANCES}/{plant_key}"}


def _sample() -> tuple[dict[str, dict[str, dict]], list[dict]]:
    data = {
        col.WATERING_LOGS: {
            # Orphaned care/task log — resolvable via LOG_PLANT edge.
            "log_edge": {"tenant_key": "", "plant_keys": ["plant-A"]},
            # Orphaned log with no edge — resolvable via embedded plant_keys.
            "log_embedded": {"plant_keys": ["plant-B"]},
            # Orphaned log whose plant is gone — must stay unresolved.
            "log_orphan": {"tenant_key": "", "plant_keys": ["ghost"]},
            # Already bound — must be left untouched.
            "log_ok": {"tenant_key": "tenant-Z", "plant_keys": ["plant-A"]},
        },
        col.PLANT_INSTANCES: {
            "plant-A": {"tenant_key": "tenant-A"},
            "plant-B": {"tenant_key": "tenant-B"},
        },
    }
    edges = [_edge("log_edge", "plant-A")]
    return data, edges


def test_backfill_resolves_via_edge_and_embedded_fallback():
    data, edges = _sample()
    db = _FakeDb(data, edges)

    report = migration.up(db)

    assert data[col.WATERING_LOGS]["log_edge"]["tenant_key"] == "tenant-A"
    assert data[col.WATERING_LOGS]["log_embedded"]["tenant_key"] == "tenant-B"
    # Unresolvable log untouched; already-bound log untouched.
    assert data[col.WATERING_LOGS]["log_orphan"]["tenant_key"] == ""
    assert data[col.WATERING_LOGS]["log_ok"]["tenant_key"] == "tenant-Z"
    assert report.changed == 2
    assert report.scanned == 3  # 3 orphaned (log_ok excluded)
    assert report.details["unresolved"] == 1


def test_rerun_is_a_noop():
    data, edges = _sample()
    db = _FakeDb(data, edges)
    migration.up(db)
    report = migration.up(db)
    # Only the still-unresolved orphan remains; nothing new is written.
    assert report.changed == 0
    assert report.details["unresolved"] == 1


def test_dry_run_writes_nothing():
    data, edges = _sample()
    db = _FakeDb(data, edges)

    report = migration.up(db, dry_run=True)

    assert report.dry_run is True
    assert report.changed == 0
    assert report.details["to_update"] == 2
    assert data[col.WATERING_LOGS]["log_edge"]["tenant_key"] == ""


def test_empty_database_is_a_noop():
    db = _FakeDb({col.WATERING_LOGS: {}, col.PLANT_INSTANCES: {}}, [])
    report = migration.up(db)
    assert report.changed == 0
    assert report.scanned == 0


def test_migration_metadata():
    assert migration.version == "0020"
    assert migration.name == "backfill_watering_log_tenant_key"
    assert migration.reversible is False
