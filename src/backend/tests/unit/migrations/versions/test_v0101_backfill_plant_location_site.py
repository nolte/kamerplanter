"""v0101 (#2499): plant location/site backfill planned and applied on a fake volume.

The fake evaluates the scan from plain dicts and applies the batched ``UPDATE`` with the same
"never overwrite a set field" rule as the AQL. The real AQL is exercised by the integration suite.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0101_backfill_plant_location_site import migration


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        if "UPDATE u._key" in query:
            for u in bind_vars["updates"]:
                doc = self.db.plants[u["_key"]]
                if doc.get("location_key") is None:
                    doc["location_key"] = u["location_key"]
                if doc.get("site_key") is None:
                    doc["site_key"] = u["site_key"]
            return iter(())
        rows = []
        for p in self.db.plants.values():
            if p.get("location_key") is not None and p.get("site_key") is not None:
                continue
            slot = self.db.slots.get(p["slot_key"]) if p.get("slot_key") else None
            loc = self.db.locations.get(slot["location_key"]) if slot and slot.get("location_key") else None
            rows.append(
                {
                    "_key": p["_key"],
                    "tenant_key": p.get("tenant_key"),
                    "location_key": p.get("location_key"),
                    "site_key": p.get("site_key"),
                    "slot_key": p.get("slot_key"),
                    "slot_found": slot is not None,
                    "slot_location_key": slot.get("location_key") if slot else None,
                    "location_found": loc is not None,
                    "location_tenant_key": loc.get("tenant_key") if loc else None,
                    "location_site_key": loc.get("site_key") if loc else None,
                }
            )
        return iter(rows)


class _FakeDb:
    def __init__(self, plants, slots, locations, *, present: bool = True) -> None:
        self.plants = {d["_key"]: dict(d) for d in plants}
        self.slots = {d["_key"]: dict(d) for d in slots}
        self.locations = {d["_key"]: dict(d) for d in locations}
        self.present = present
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return self.present and name == col.PLANT_INSTANCES


def _volume() -> _FakeDb:
    plants = [
        {"_key": "ok", "tenant_key": "t1", "slot_key": "s1", "location_key": None, "site_key": None},
        {"_key": "half", "tenant_key": "t1", "slot_key": "s1", "location_key": "L1", "site_key": None},
        {"_key": "done", "tenant_key": "t1", "slot_key": "s1", "location_key": "L1", "site_key": "S1"},
        {"_key": "keep", "tenant_key": "t1", "slot_key": "s1", "location_key": "OTHER", "site_key": None},
        {"_key": "noslot", "tenant_key": "t1", "slot_key": None, "location_key": None, "site_key": None},
        {"_key": "ghost", "tenant_key": "t1", "slot_key": "gone", "location_key": None, "site_key": None},
        {"_key": "foreign", "tenant_key": "t1", "slot_key": "s2", "location_key": None, "site_key": None},
        {"_key": "nolocslot", "tenant_key": "t1", "slot_key": "s3", "location_key": None, "site_key": None},
    ]
    slots = [
        {"_key": "s1", "location_key": "L1"},
        {"_key": "s2", "location_key": "L2"},
        {"_key": "s3"},
    ]
    locations = [
        {"_key": "L1", "tenant_key": "t1", "site_key": "S1"},
        {"_key": "L2", "tenant_key": "t2", "site_key": "S2"},
    ]
    return _FakeDb(plants, slots, locations)


def test_dry_run_reports_and_writes_nothing() -> None:
    db = _volume()
    before = {k: dict(v) for k, v in db.plants.items()}
    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]
    assert db.plants == before
    assert report.dry_run is True and report.changed == 0
    d = report.details
    assert d["will_update"] == 3  # ok, half, keep
    assert d["unresolved"]["no_slot"] == {"count": 1, "listed": ["noslot"]}
    assert d["unresolved"]["slot_missing"]["listed"] == ["ghost"]
    assert d["unresolved"]["cross_tenant"]["listed"] == ["foreign"]
    assert d["unresolved"]["slot_without_location"]["listed"] == ["nolocslot"]
    assert d["unresolved_count"] == 4


def test_apply_fills_nulls_and_never_overwrites() -> None:
    db = _volume()
    report = migration.up(db)  # type: ignore[arg-type]
    assert report.changed == 3
    assert (db.plants["ok"]["location_key"], db.plants["ok"]["site_key"]) == ("L1", "S1")
    assert (db.plants["half"]["location_key"], db.plants["half"]["site_key"]) == ("L1", "S1")
    assert db.plants["keep"]["location_key"] == "OTHER"
    assert db.plants["keep"]["site_key"] == "S1"
    for key in ("noslot", "ghost", "foreign", "nolocslot"):
        assert db.plants[key]["location_key"] is None and db.plants[key]["site_key"] is None


def test_second_run_changes_nothing_new() -> None:
    db = _volume()
    migration.up(db)  # type: ignore[arg-type]
    after_first = {k: dict(v) for k, v in db.plants.items()}
    report = migration.up(db)  # type: ignore[arg-type]
    assert report.changed == 0
    assert db.plants == after_first


def test_missing_collection_is_a_noop() -> None:
    report = migration.up(_FakeDb([], [], [], present=False))  # type: ignore[arg-type]
    assert report.scanned == 0 and report.changed == 0


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_volume())  # type: ignore[arg-type]
