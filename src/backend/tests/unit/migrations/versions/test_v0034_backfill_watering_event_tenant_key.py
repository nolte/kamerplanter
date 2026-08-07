"""Tests for v0034_backfill_watering_event_tenant_key (#951).

The migration repairs the rows three write paths persisted without a tenant:
batch-created ``plant_instances`` (from their run), confirm-produced
``watering_events`` (from their plant) and the ``feeding_events`` derived from
them (from their plant, else from the watering event). The stages run in
dependency order, so an event whose only reference is a plant that stage 1 has
just repaired still resolves. Unresolvable rows are left untouched and reported.
Idempotent, dry-run-safe, irreversible.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0034_backfill_watering_event_tenant_key import migration


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
        if "@edges" in bind_vars:
            return iter(self._resolve_edge(query, bind_vars))
        collection = bind_vars["@collection"]
        docs = self._db.data.get(collection, {})
        return iter(
            {"key": key, "id": f"{collection}/{key}", **{f: doc.get(f) for f in _projection(query)}}
            for key, doc in docs.items()
            if not doc.get("tenant_key")
        )

    def _resolve_edge(self, query: str, bind_vars: dict[str, Any]) -> list[str]:
        near, far = ("_from", "_to") if "edge._from == @doc_id" in query else ("_to", "_from")
        out: list[str] = []
        for edge in self._db.edges.get(bind_vars["@edges"], []):
            if edge[near] != bind_vars["doc_id"]:
                continue
            collection, key = edge[far].split("/", 1)
            other = self._db.data.get(collection, {}).get(key)
            if other and other.get("tenant_key"):
                out.append(other["tenant_key"])
        return out


def _projection(query: str) -> list[str]:
    """The extra fields the scan projects, read out of the RETURN clause."""
    fields = []
    for candidate in ("plant_keys", "plant_key", "watering_event_key"):
        if f"{candidate}: doc.{candidate}" in query:
            fields.append(candidate)
    return fields


class _FakeDb:
    def __init__(self, data: dict[str, dict[str, dict]], edges: dict[str, list[dict]]) -> None:
        self.data = data
        self.edges = edges
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.data or name in self.edges

    def collection(self, name: str) -> _FakeCollection:
        return _FakeCollection(self.data[name])


def _sample() -> _FakeDb:
    data: dict[str, dict[str, dict]] = {
        col.PLANTING_RUNS: {
            "run-a": {"tenant_key": "tenant-A"},
        },
        col.PLANT_INSTANCES: {
            # Batch-created by ``create_plants`` — no tenant, reachable from its run.
            "plant-batch": {"tenant_key": ""},
            # An ordinary, already-stamped plant.
            "plant-ok": {"tenant_key": "tenant-A"},
            # Belongs to no run at all — must stay unresolved rather than guessed.
            "plant-orphan": {"tenant_key": ""},
        },
        col.WATERING_EVENTS: {
            # Confirm-produced, edge present.
            "we-edge": {"tenant_key": "", "plant_keys": ["plant-ok"]},
            # Edge missing; resolves through the plant stage 1 has just repaired.
            "we-embedded": {"tenant_key": "", "plant_keys": ["plant-batch"]},
            # Nothing resolvable.
            "we-orphan": {"tenant_key": "", "plant_keys": ["ghost"]},
            # Already stamped — must be left alone.
            "we-ok": {"tenant_key": "tenant-Z", "plant_keys": ["plant-ok"]},
        },
        col.FEEDING_EVENTS: {
            # Derived feeding event with a usable plant reference.
            "fe-plant": {"tenant_key": "", "plant_key": "plant-ok", "watering_event_key": "we-edge"},
            # No plant, but the watering event stage 2 repaired carries the tenant.
            "fe-via-event": {"tenant_key": "", "plant_key": "", "watering_event_key": "we-embedded"},
            # Nothing resolvable.
            "fe-orphan": {"tenant_key": "", "plant_key": "ghost", "watering_event_key": ""},
        },
    }
    edges = {
        col.RUN_CONTAINS: [
            {"_from": f"{col.PLANTING_RUNS}/run-a", "_to": f"{col.PLANT_INSTANCES}/plant-batch"},
        ],
        col.WATERED_PLANT: [
            {"_from": f"{col.WATERING_EVENTS}/we-edge", "_to": f"{col.PLANT_INSTANCES}/plant-ok"},
        ],
    }
    return _FakeDb(data, edges)


def test_all_three_stages_bind_their_rows_in_dependency_order():
    db = _sample()

    report = migration.up(db)

    assert db.data[col.PLANT_INSTANCES]["plant-batch"]["tenant_key"] == "tenant-A"
    assert db.data[col.WATERING_EVENTS]["we-edge"]["tenant_key"] == "tenant-A"
    # The point of the ordering: this one is only resolvable because stage 1 ran.
    assert db.data[col.WATERING_EVENTS]["we-embedded"]["tenant_key"] == "tenant-A"
    assert db.data[col.FEEDING_EVENTS]["fe-plant"]["tenant_key"] == "tenant-A"
    assert db.data[col.FEEDING_EVENTS]["fe-via-event"]["tenant_key"] == "tenant-A"

    assert report.changed == 5
    assert report.details["plant_instances"] == 1
    assert report.details["watering_events"] == 2
    assert report.details["feeding_events"] == 2


def test_unresolvable_rows_are_left_untouched_rather_than_guessed():
    db = _sample()

    report = migration.up(db)

    assert db.data[col.PLANT_INSTANCES]["plant-orphan"]["tenant_key"] == ""
    assert db.data[col.WATERING_EVENTS]["we-orphan"]["tenant_key"] == ""
    assert db.data[col.FEEDING_EVENTS]["fe-orphan"]["tenant_key"] == ""
    assert report.details["unresolved"] == 3


def test_an_already_stamped_row_is_not_rewritten():
    db = _sample()

    migration.up(db)

    assert db.data[col.WATERING_EVENTS]["we-ok"]["tenant_key"] == "tenant-Z"
    assert db.data[col.PLANT_INSTANCES]["plant-ok"]["tenant_key"] == "tenant-A"


def test_rerun_is_a_noop():
    db = _sample()
    migration.up(db)

    report = migration.up(db)

    assert report.changed == 0
    assert report.details["unresolved"] == 3


def test_dry_run_writes_nothing_but_plans_the_full_cascade():
    db = _sample()

    report = migration.up(db, dry_run=True)

    assert report.dry_run is True
    assert report.changed == 0
    # The cascade is planned in full, including the rows only stage 1 unlocks.
    assert report.details["to_update"] == 5
    assert db.data[col.PLANT_INSTANCES]["plant-batch"]["tenant_key"] == ""
    assert db.data[col.WATERING_EVENTS]["we-embedded"]["tenant_key"] == ""


def test_empty_database_is_a_noop():
    db = _FakeDb({}, {})

    report = migration.up(db)

    assert report.changed == 0
    assert report.scanned == 0


def test_migration_metadata():
    assert migration.version == "0034"
    assert migration.name == "backfill_watering_event_tenant_key"
    assert migration.reversible is False
