"""v0112 (#2952): the missing ``placed_in`` edges planned, inserted and reverted on a fake volume.

The fake answers the scan from plain dicts with the scan's own rules (a plant with a ``slot_key`` and no edge to that
slot, sorted by key, the slot -> location -> site chain resolved) and applies the insert with the insert's rules
(skip a plant whose slot or tenant changed, or that has the edge by now). The real AQL runs in
``tests/integration/test_v0112_placed_in_backfill.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0112_placed_in_backfill import PlacedInBackfillMigration, migration

NOW = datetime(2026, 11, 15, 9, 30, tzinfo=UTC)


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.inserts: list[int] = []
        self.before_apply: Callable[[], None] | None = None

    def _has_edge(self, from_id: str, to_id: str) -> bool:
        return any(e["_from"] == from_id and e["_to"] == to_id for e in self.db.edges)

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        if query == migration.SCAN:
            return iter(self._scan())
        if query == migration.APPLY:
            assert bind_vars["marker"] == "v0112"
            self.inserts.append(len(bind_vars["rows"]))
            if self.before_apply is not None:
                self.before_apply()
            inserted = 0
            for u in bind_vars["rows"]:
                plant = self.db.plants.get(u["plant_key"])
                if plant is None or plant.get("slot_key") != u["slot_key"]:
                    continue
                if plant.get("tenant_key") != u["tenant_key"] or self._has_edge(u["from_id"], u["to_id"]):
                    continue
                self.db.edges.append(
                    {"_from": u["from_id"], "_to": u["to_id"], "created_at": u["created_at"], "backfilled_by": "v0112"}
                )
                inserted += 1
            return iter([inserted])
        if query == migration.COUNT_MARKED:
            return iter([sum(1 for e in self.db.edges if e.get("backfilled_by") == bind_vars["marker"])])
        if query == migration.REMOVE_MARKED:
            before = len(self.db.edges)
            self.db.edges = [e for e in self.db.edges if e.get("backfilled_by") != bind_vars["marker"]]
            return iter([before - len(self.db.edges)])
        raise AssertionError(f"unexpected query: {query[:60]}")

    def _scan(self) -> list[dict[str, Any]]:
        rows = []
        for key in sorted(self.db.plants):
            plant = self.db.plants[key]
            slot_key = plant.get("slot_key")
            if not slot_key or self._has_edge(f"plant_instances/{key}", f"slots/{slot_key}"):
                continue
            slot = self.db.slots.get(slot_key)
            location_key = slot.get("location_key") if slot else None
            location = self.db.locations.get(location_key) if location_key else None
            site_key = location.get("site_key") if location else None
            site = self.db.sites.get(site_key) if site_key else None
            rows.append(
                {
                    "key": key,
                    "tenant_key": plant.get("tenant_key"),
                    "slot_key": slot_key,
                    "created_at": plant.get("created_at"),
                    "planted_on": plant.get("planted_on"),
                    "slot_found": slot is not None,
                    "location_key": location_key,
                    "location_found": location is not None,
                    "site_key": site_key,
                    "site_found": site is not None,
                    "site_tenant_key": site.get("tenant_key") if site else None,
                }
            )
        return rows


class _FakeDb:
    def __init__(self) -> None:
        self.plants: dict[str, dict[str, Any]] = {}
        self.slots: dict[str, dict[str, Any]] = {}
        self.locations: dict[str, dict[str, Any]] = {}
        self.sites: dict[str, dict[str, Any]] = {}
        self.edges: list[dict[str, Any]] = []
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return True


@pytest.fixture
def db() -> _FakeDb:
    fake = _FakeDb()
    fake.sites = {"site_a": {"tenant_key": "t_a"}, "site_b": {"tenant_key": "t_b"}, "site_legacy": {}}
    fake.locations = {
        "bed_a": {"site_key": "site_a"},
        "bed_a2": {"site_key": "site_a"},
        "bed_b": {"site_key": "site_b"},
        "bed_legacy": {"site_key": "site_legacy"},
        "bed_nosite": {"site_key": ""},
        "bed_gone_site": {"site_key": "site_gone"},
    }
    fake.slots = {
        "a1": {"location_key": "bed_a"},
        "a2": {"location_key": "bed_a2"},
        "b1": {"location_key": "bed_b"},
        "legacy": {"location_key": "bed_legacy"},
        "nosite": {"location_key": "bed_nosite"},
        "gone_site": {"location_key": "bed_gone_site"},
        "noloc": {"location_key": None},
        "gone_loc": {"location_key": "bed_gone"},
    }
    return fake


def _plant(db: _FakeDb, key: str, slot: str | None, tenant: str = "t_a", **fields: Any) -> None:
    db.plants[key] = {"tenant_key": tenant, "slot_key": slot, "planted_on": "2026-04-01", **fields}


def _edge(db: _FakeDb, plant: str, slot: str) -> None:
    db.edges.append({"_from": f"plant_instances/{plant}", "_to": f"slots/{slot}", "created_at": "2026-04-01"})


class TestFrozenLiterals:
    def test_the_frozen_collection_names_are_todays_constants(self) -> None:
        assert (
            PlacedInBackfillMigration.PLANTS,
            PlacedInBackfillMigration.SLOTS,
            PlacedInBackfillMigration.LOCATIONS,
            PlacedInBackfillMigration.SITES,
            PlacedInBackfillMigration.EDGES,
        ) == (col.PLANT_INSTANCES, col.SLOTS, col.LOCATIONS, col.SITES, col.PLACED_IN)

    def test_metadata(self) -> None:
        assert (migration.version, migration.name, migration.reversible, migration.kind) == (
            "0112",
            "placed_in_backfill",
            True,
            None,
        )


class TestUp:
    def test_a_legacy_moved_plant_gets_the_edge_to_its_slot_and_keeps_the_old_one(self, db: _FakeDb) -> None:
        _plant(db, "p1", "a2", created_at="2026-04-01T08:00:00+00:00")
        _edge(db, "p1", "a1")  # created on a1, moved to a2 before #2948

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 1
        targets = sorted(e["_to"] for e in db.edges if e["_from"] == "plant_instances/p1")
        assert targets == ["slots/a1", "slots/a2"]
        new = next(e for e in db.edges if e["_to"] == "slots/a2")
        assert new["backfilled_by"] == "v0112"
        assert new["created_at"] == "2026-04-01T08:00:00+00:00"
        old = next(e for e in db.edges if e["_to"] == "slots/a1")
        assert "backfilled_by" not in old  # the slot it left keeps its history edge untouched

    def test_a_plant_with_its_edge_and_one_without_a_slot_are_not_touched(self, db: _FakeDb) -> None:
        _plant(db, "placed", "a1")
        _edge(db, "placed", "a1")
        _plant(db, "loose", None)

        report = migration.up(db)  # type: ignore[arg-type]

        assert (report.scanned, report.changed) == (0, 0)
        assert len(db.edges) == 1

    def test_a_removed_plant_is_backfilled_too(self, db: _FakeDb) -> None:
        _plant(db, "gone", "a1", removed_on="2026-09-01")

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 1

    @pytest.mark.parametrize(
        ("slot", "tenant", "reason"),
        [
            ("missing_slot", "t_a", "slot_missing"),
            ("noloc", "t_a", "slot_without_location"),
            ("gone_loc", "t_a", "location_missing"),
            ("nosite", "t_a", "location_without_site"),
            ("gone_site", "t_a", "site_missing"),
            ("legacy", "t_a", "site_without_tenant"),
            ("b1", "t_a", "cross_tenant"),
            ("a1", "", "cross_tenant"),
        ],
    )
    def test_an_unresolvable_or_foreign_slot_is_listed_and_left_alone(
        self, db: _FakeDb, slot: str, tenant: str, reason: str
    ) -> None:
        _plant(db, "p", slot, tenant=tenant)

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert db.edges == []
        assert report.details["unresolved"] == {reason: {"count": 1, "listed": ["p"]}}
        assert report.details["unresolved_count"] == 1

    def test_the_second_run_is_a_noop(self, db: _FakeDb) -> None:
        _plant(db, "p1", "a2")
        _plant(db, "p2", "b1")  # foreign: stays unresolved on every run

        first = migration.up(db)  # type: ignore[arg-type]
        second = migration.up(db)  # type: ignore[arg-type]

        assert first.changed == 1
        assert second.changed == 0
        assert second.details["unresolved_count"] == 1

    def test_the_dry_run_counts_and_writes_nothing(self, db: _FakeDb) -> None:
        _plant(db, "p1", "a2")
        _plant(db, "p2", "a1")
        _plant(db, "p3", "b1")

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.dry_run is True
        assert report.changed == 0
        assert report.details["will_insert"] == 2
        assert report.details["listed_keys"] == ["p1", "p2"]
        assert db.edges == []
        assert db.aql.inserts == []

    def test_a_plant_moved_or_given_its_edge_after_the_scan_is_skipped(self, db: _FakeDb) -> None:
        _plant(db, "moved", "a2")
        _plant(db, "edged", "a1")

        def writer() -> None:
            db.plants["moved"]["slot_key"] = "a1"
            _edge(db, "edged", "a1")

        db.aql.before_apply = writer

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 0
        assert report.details["skipped_changed_since_scan"] == 2
        assert not any(e.get("backfilled_by") for e in db.edges)

    def test_inserts_are_batched(self, db: _FakeDb, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(PlacedInBackfillMigration, "BATCH_SIZE", 2)
        for n in range(5):
            _plant(db, f"p{n}", "a1")

        report = migration.up(db)  # type: ignore[arg-type]

        assert report.changed == 5
        assert db.aql.inserts == [2, 2, 1]


class TestPlacedAt:
    @pytest.mark.parametrize(
        ("row", "expected"),
        [
            ({"created_at": "2026-03-02T10:00:00+00:00", "planted_on": "2026-04-01"}, "2026-03-02T10:00:00+00:00"),
            ({"created_at": None, "planted_on": "2026-04-01"}, "2026-04-01T00:00:00+00:00"),
            ({"created_at": "", "planted_on": "not-a-date"}, NOW.isoformat()),
            ({}, NOW.isoformat()),
        ],
        ids=["created_at", "planted_on", "unparsable", "nothing"],
    )
    def test_the_best_known_time(self, row: dict[str, Any], expected: str) -> None:
        assert PlacedInBackfillMigration.placed_at(row, NOW) == expected


class TestDown:
    def test_down_removes_exactly_the_marked_edges(self, db: _FakeDb) -> None:
        _plant(db, "p1", "a2")
        _edge(db, "p1", "a1")
        _plant(db, "p2", "a1")
        _edge(db, "p2", "a1")
        migration.up(db)  # type: ignore[arg-type]
        assert len(db.edges) == 3

        dry = migration.down(db, dry_run=True)  # type: ignore[arg-type]
        assert (dry.changed, dry.details["will_remove"], len(db.edges)) == (0, 1, 3)

        report = migration.down(db)  # type: ignore[arg-type]

        assert report.changed == 1
        assert sorted(e["_to"] for e in db.edges) == ["slots/a1", "slots/a1"]
        assert not any(e.get("backfilled_by") for e in db.edges)
