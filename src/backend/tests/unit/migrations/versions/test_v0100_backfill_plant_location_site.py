"""v0100 (#2499): plant location/site backfill planned and applied on a fake volume.

The fake evaluates the scan from plain dicts (sorted by plant key, like ``SORT p._key``) and applies the batched
``UPDATE`` with the same rules as the AQL: skip a plant whose fields changed since the scan, never overwrite a set
field, never join a location to another site; it returns the number of changed plants. The real AQL is exercised
by the integration suite.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0100_backfill_plant_location_site import migration


class _FakeCursor:
    """The scan result as a non-streaming server cursor: fixed when the query runs, read row by row."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = iter(rows)
        self.consumed = 0

    def __iter__(self) -> _FakeCursor:
        return self

    def __next__(self) -> dict[str, Any]:
        row = next(self._rows)
        self.consumed += 1
        return row


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.scan_options: dict[str, Any] = {}
        self.cursor: _FakeCursor | None = None
        #: Per ``UPDATE`` statement: its batch size and how many scan rows had been read when it ran.
        self.applied: list[tuple[int, int]] = []
        #: A live writer that runs between the scan and each ``UPDATE`` statement.
        self.before_apply: Callable[[], None] | None = None

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **options: Any) -> Any:
        bind_vars = bind_vars or {}
        if "updates" in bind_vars:  # the UPDATE statement; the scan binds no updates
            self.applied.append((len(bind_vars["updates"]), self.cursor.consumed if self.cursor else 0))
            if self.before_apply is not None:
                self.before_apply()
            changed = 0
            for u in bind_vars["updates"]:
                doc = self.db.plants.get(u["_key"])
                if doc is None:
                    continue
                current_location, current_site = doc.get("location_key"), doc.get("site_key")
                if (current_location, current_site) != (u["seen_location_key"], u["seen_site_key"]):
                    continue
                location = current_location
                if u["location_key"] is not None and current_location is None and current_site in (None, u["site"]):
                    location = u["location_key"]
                site = u["site_key"] if u["site_key"] is not None and current_site is None else current_site
                if (location, site) != (current_location, current_site):
                    doc["location_key"], doc["site_key"] = location, site
                    changed += 1
            return _FakeCursor([changed])
        self.scan_options = options
        rows = []
        for p in sorted(self.db.plants.values(), key=lambda doc: doc["_key"]):
            if p.get("location_key") is not None and p.get("site_key") is not None:
                continue
            slot = self.db.slots.get(p["slot_key"]) if p.get("slot_key") else None
            loc = self.db.locations.get(slot["location_key"]) if slot and slot.get("location_key") else None
            own = self.db.locations.get(p["location_key"]) if p.get("location_key") else None
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
                    "location_site_tenant_key": self.db.site_tenant(loc),
                    "location_site_key": loc.get("site_key") if loc else None,
                    "location_site_found": self.db.site_of(loc) is not None,
                    "own_found": own is not None,
                    "own_site_tenant_key": self.db.site_tenant(own),
                    "own_site_key": own.get("site_key") if own else None,
                    "own_site_found": self.db.site_of(own) is not None,
                }
            )
        self.cursor = _FakeCursor(rows)
        return self.cursor


class _FakeDb:
    def __init__(self, plants, slots, locations, sites=(), *, present: bool = True) -> None:
        self.sites = {d["_key"]: dict(d) for d in sites}
        self.plants = {d["_key"]: dict(d) for d in plants}
        self.slots = {d["_key"]: dict(d) for d in slots}
        self.locations = {d["_key"]: dict(d) for d in locations}
        self.present = present
        self.aql = _FakeAql(self)

    def site_of(self, location):
        """The site document anchoring ``location`` (``None`` when the location names none or it is gone)."""
        return self.sites.get(location.get("site_key")) if location else None

    def site_tenant(self, location):
        """The tenant of the site anchoring ``location`` (locations carry no tenant of their own, #1397)."""
        site = self.site_of(location)
        return site.get("tenant_key") if site else None

    def has_collection(self, name: str) -> bool:
        return self.present and name == col.PLANT_INSTANCES


def _volume() -> _FakeDb:
    plants = [
        {"_key": "ok", "tenant_key": "t1", "slot_key": "s1", "location_key": None, "site_key": None},
        {"_key": "half", "tenant_key": "t1", "slot_key": "s1", "location_key": "L1", "site_key": None},
        {"_key": "done", "tenant_key": "t1", "slot_key": "s1", "location_key": "L1", "site_key": "S1"},
        {"_key": "keep", "tenant_key": "t1", "slot_key": "s1", "location_key": "L4", "site_key": None},
        {"_key": "ghostloc", "tenant_key": "t1", "slot_key": "s1", "location_key": "OTHER", "site_key": None},
        {"_key": "foreignown", "tenant_key": "t1", "slot_key": "s1", "location_key": "L2", "site_key": None},
        {"_key": "nosite", "tenant_key": "t1", "slot_key": "s1", "location_key": "L5", "site_key": None},
        {"_key": "notenant", "slot_key": "s1", "location_key": None, "site_key": None},
        {"_key": "noslot", "tenant_key": "t1", "slot_key": None, "location_key": None, "site_key": None},
        {"_key": "ghost", "tenant_key": "t1", "slot_key": "gone", "location_key": None, "site_key": None},
        {"_key": "foreign", "tenant_key": "t1", "slot_key": "s2", "location_key": None, "site_key": None},
        {"_key": "nolocslot", "tenant_key": "t1", "slot_key": "s3", "location_key": None, "site_key": None},
        # #2524 item 1: site already set, location missing
        {"_key": "halfsame", "tenant_key": "t1", "slot_key": "s1", "location_key": None, "site_key": "S1"},
        {"_key": "halfother", "tenant_key": "t1", "slot_key": "s1", "location_key": None, "site_key": "S_other"},
        # #2524 item 2: each broken link of the site chain has its own reason
        {"_key": "sitemissing", "tenant_key": "t1", "slot_key": "s4", "location_key": None, "site_key": None},
        {"_key": "legacy", "tenant_key": "t1", "slot_key": "s5", "location_key": None, "site_key": None},
        {"_key": "legacyown", "tenant_key": "t1", "slot_key": "s1", "location_key": "L7", "site_key": None},
    ]
    slots = [
        {"_key": "s1", "location_key": "L1"},
        {"_key": "s2", "location_key": "L2"},
        {"_key": "s3"},
        {"_key": "s4", "location_key": "L6"},
        {"_key": "s5", "location_key": "L7"},
    ]
    locations = [
        {"_key": "L1", "site_key": "S1"},
        {"_key": "L2", "site_key": "S2"},
        {"_key": "L4", "site_key": "S4"},
        {"_key": "L5"},
        {"_key": "L6", "site_key": "S_gone"},
        {"_key": "L7", "site_key": "S7"},
    ]
    sites = [
        {"_key": "S1", "tenant_key": "t1"},
        {"_key": "S2", "tenant_key": "t2"},
        {"_key": "S4", "tenant_key": "t1"},
        {"_key": "S7"},
    ]
    return _FakeDb(plants, slots, locations, sites)


def test_dry_run_reports_and_writes_nothing() -> None:
    db = _volume()
    before = {k: dict(v) for k, v in db.plants.items()}
    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]
    assert db.plants == before
    assert report.dry_run is True and report.changed == 0
    d = report.details
    assert d["will_update"] == 4  # ok, half, keep, halfsame
    assert d["sets_location_key"] == 2  # ok, halfsame
    assert d["sets_site_key"] == 3  # ok, half, keep
    assert "location_without_site_key" not in d  # a reason under "unresolved" now, not a dead counter
    assert d["unresolved"]["no_slot"] == {"count": 1, "listed": ["noslot"]}
    assert d["unresolved"]["slot_missing"]["listed"] == ["ghost"]
    assert sorted(d["unresolved"]["cross_tenant"]["listed"]) == ["foreign", "foreignown", "notenant"]
    assert d["unresolved"]["location_missing"]["listed"] == ["ghostloc"]
    assert d["unresolved"]["slot_without_location"]["listed"] == ["nolocslot"]
    assert d["unresolved"]["location_without_site_key"]["listed"] == ["nosite"]
    assert d["unresolved"]["site_missing"]["listed"] == ["sitemissing"]
    assert sorted(d["unresolved"]["site_without_tenant"]["listed"]) == ["legacy", "legacyown"]
    assert d["unresolved"]["site_mismatch"]["listed"] == ["halfother"]
    assert d["unresolved_count"] == 12
    assert report.scanned == d["will_update"] + d["unresolved_count"]  # every scanned plant is planned or listed


def test_apply_fills_nulls_and_never_overwrites() -> None:
    db = _volume()
    report = migration.up(db)  # type: ignore[arg-type]
    assert report.changed == report.details["updated"] == 4
    assert report.details["skipped_changed_since_scan"] == 0
    assert report.scanned == report.details["updated"] + report.details["unresolved_count"]
    assert (db.plants["ok"]["location_key"], db.plants["ok"]["site_key"]) == ("L1", "S1")
    assert (db.plants["half"]["location_key"], db.plants["half"]["site_key"]) == ("L1", "S1")
    # N2: site comes from the plant's own location, not from the slot's (L1 / S1)
    assert (db.plants["keep"]["location_key"], db.plants["keep"]["site_key"]) == ("L4", "S4")
    # N2: own location missing / cross-tenant -> untouched
    assert (db.plants["ghostloc"]["location_key"], db.plants["ghostloc"]["site_key"]) == ("OTHER", None)
    assert (db.plants["foreignown"]["location_key"], db.plants["foreignown"]["site_key"]) == ("L2", None)
    # location without a site has no anchor: unresolved, no update (N4)
    assert db.plants["nosite"]["site_key"] is None
    # N3: plant without a tenant never matches a location
    assert db.plants["notenant"]["location_key"] is None
    for key in ("noslot", "ghost", "foreign", "nolocslot", "sitemissing", "legacy"):
        assert db.plants[key]["location_key"] is None and db.plants[key]["site_key"] is None
    assert (db.plants["legacyown"]["location_key"], db.plants["legacyown"]["site_key"]) == ("L7", None)
    # #2524 item 1: the slot's location only joins a site_key that names the same site
    assert (db.plants["halfsame"]["location_key"], db.plants["halfsame"]["site_key"]) == ("L1", "S1")
    assert (db.plants["halfother"]["location_key"], db.plants["halfother"]["site_key"]) == (None, "S_other")


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


def _single(plant: dict[str, Any], location: dict[str, Any], site: dict[str, Any] | None) -> _FakeDb:
    """One plant on slot ``s1`` in ``location``, anchored by ``site`` (``None`` = the site does not exist)."""
    return _FakeDb(
        [{"_key": "p", "slot_key": "s1", "location_key": None, "site_key": None, **plant}],
        [{"_key": "s1", "location_key": location["_key"]}],
        [location],
        [site] if site is not None else [],
    )


def test_half_set_plant_with_another_site_is_left_untouched() -> None:
    """#2524 item 1: a plant with ``site_key`` S_other must not receive location L1 of site S1."""
    db = _single(
        {"tenant_key": "t1", "site_key": "S_other"},
        {"_key": "L1", "site_key": "S1"},
        {"_key": "S1", "tenant_key": "t1"},
    )

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.changed == 0
    assert (db.plants["p"]["location_key"], db.plants["p"]["site_key"]) == (None, "S_other")
    assert report.details["unresolved"] == {"site_mismatch": {"count": 1, "listed": ["p"]}}


def test_half_set_plant_with_the_derived_site_only_receives_the_location() -> None:
    db = _single(
        {"tenant_key": "t1", "site_key": "S1"}, {"_key": "L1", "site_key": "S1"}, {"_key": "S1", "tenant_key": "t1"}
    )

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.changed == 1
    assert (report.details["sets_location_key"], report.details["sets_site_key"]) == (1, 0)
    assert (db.plants["p"]["location_key"], db.plants["p"]["site_key"]) == ("L1", "S1")


@pytest.mark.parametrize(
    ("plant", "location", "site", "reason"),
    [
        ({"tenant_key": "t1"}, {"_key": "L1"}, None, "location_without_site_key"),
        ({"tenant_key": "t1"}, {"_key": "L1", "site_key": "S1"}, None, "site_missing"),
        ({"tenant_key": "t1"}, {"_key": "L1", "site_key": "S1"}, {"_key": "S1"}, "site_without_tenant"),
        ({"tenant_key": "t1"}, {"_key": "L1", "site_key": "S1"}, {"_key": "S1", "tenant_key": "t2"}, "cross_tenant"),
        ({}, {"_key": "L1", "site_key": "S1"}, {"_key": "S1", "tenant_key": "t1"}, "cross_tenant"),
        ({}, {"_key": "L1", "site_key": "S1"}, {"_key": "S1"}, "cross_tenant"),
        # the writer's empty-string defaults (app/domain/models/site.py), next to the missing-field forms above
        ({"tenant_key": "t1"}, {"_key": "L1", "site_key": ""}, None, "location_without_site_key"),
        (
            {"tenant_key": "t1"},
            {"_key": "L1", "site_key": "S1"},
            {"_key": "S1", "tenant_key": ""},
            "site_without_tenant",
        ),
    ],
    ids=[
        "location-without-site",
        "site-gone",
        "legacy-site",
        "foreign-site",
        "plant-without-tenant",
        "plant-and-site-without-tenant",
        "location-with-empty-site-key",
        "site-with-empty-tenant-key",
    ],
)
def test_each_broken_site_link_has_its_own_reason(
    plant: dict[str, Any], location: dict[str, Any], site: dict[str, Any] | None, reason: str
) -> None:
    """#2524 item 2: legacy data (site without tenant) is told apart from really foreign data."""
    db = _single(plant, location, site)

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.changed == 0
    assert report.details["unresolved"] == {reason: {"count": 1, "listed": ["p"]}}
    assert (db.plants["p"]["location_key"], db.plants["p"]["site_key"]) == (None, None)


def test_dry_run_reports_exactly_what_the_real_run_writes() -> None:
    """#2524 item 4: one path for both modes, so ``will_update`` and the whole report match the real run."""
    db = _volume()

    dry = migration.up(db, dry_run=True)  # type: ignore[arg-type]
    real = migration.up(db)  # type: ignore[arg-type]

    assert dry.details.pop("will_update") == real.details.pop("updated") == real.changed
    assert real.details.pop("skipped_changed_since_scan") == 0
    assert dry.details == real.details
    assert dry.scanned == real.scanned


@pytest.mark.parametrize(
    ("plant", "writer", "after"),
    [
        ({}, {"site_key": "S_other"}, (None, "S_other")),
        ({}, {"location_key": "L_other"}, ("L_other", None)),
        ({"location_key": "L1"}, {"location_key": "L_other"}, ("L_other", None)),
    ],
    ids=["site-set-meanwhile", "location-set-meanwhile", "own-location-moved-meanwhile"],
)
def test_a_plant_changed_between_scan_and_apply_is_skipped(
    plant: dict[str, Any], writer: dict[str, Any], after: tuple[str | None, str | None]
) -> None:
    """#2524 review SCR-002: a live writer between scan and ``UPDATE`` wins; the plant is skipped, not mixed."""
    db = _single({"tenant_key": "t1", **plant}, {"_key": "L1", "site_key": "S1"}, {"_key": "S1", "tenant_key": "t1"})
    db.aql.before_apply = lambda: db.plants["p"].update(writer)

    report = migration.up(db)  # type: ignore[arg-type]

    assert (db.plants["p"]["location_key"], db.plants["p"]["site_key"]) == after
    assert report.changed == report.details["updated"] == 0
    assert report.details["skipped_changed_since_scan"] == 1
    assert report.scanned == (
        report.details["updated"] + report.details["skipped_changed_since_scan"] + report.details["unresolved_count"]
    )


def _volume_of(repairable: int, unplaced: int) -> _FakeDb:
    plants = [
        {"_key": f"r{i:04d}", "tenant_key": "t1", "slot_key": "s1", "location_key": None, "site_key": None}
        for i in range(repairable)
    ] + [
        {"_key": f"u{i:02d}", "tenant_key": "t1", "slot_key": None, "location_key": None, "site_key": None}
        for i in range(unplaced)
    ]
    return _FakeDb(
        plants,
        [{"_key": "s1", "location_key": "L1"}],
        [{"_key": "L1", "site_key": "S1"}],
        [{"_key": "S1", "tenant_key": "t1"}],
    )


def test_the_scan_is_streamed_and_applied_batch_by_batch() -> None:
    """#2524 item 4: no full list of rows or updates; each full batch is written while the cursor is still read."""
    db = _volume_of(1203, 30)

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.changed == 1203 and report.scanned == 1233
    # batch 1 and 2 ran as soon as they filled, the remainder after the last row
    assert db.aql.applied == [(500, 500), (500, 1000), (203, 1233)]
    assert db.aql.scan_options["batch_size"] == 500
    assert db.aql.scan_options["stream"] is False  # the result is fixed before the first update runs
    assert len(report.details["listed_keys"]) == 25 and report.details["listed_keys"][0] == "r0000"
    assert report.details["unresolved"]["no_slot"]["count"] == 30
    assert len(report.details["unresolved"]["no_slot"]["listed"]) == 25
    assert all((p["location_key"], p["site_key"]) == ("L1", "S1") for k, p in db.plants.items() if k.startswith("r"))


def test_a_dry_run_streams_without_writing() -> None:
    db = _volume_of(1203, 0)

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert report.details["will_update"] == 1203 and report.changed == 0
    assert db.aql.applied == []
