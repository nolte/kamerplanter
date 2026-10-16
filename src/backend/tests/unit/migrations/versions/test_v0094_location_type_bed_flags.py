"""v0094 (#2325, REQ-053 M2): bed flags stamped on a fake volume — idempotent, a dry run writes nothing.

The fake models exactly what the migration reads and writes: ``has_collection`` and
the two AQL statements (one scan, one ``UPDATE``) dispatched on their text. The real
AQL is measured in ``tests/integration/test_v0094_v0095_req053_m2_m3.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions import v0094_location_type_bed_flags as module
from app.migrations.versions.v0094_location_type_bed_flags import migration
from app.migrations.yaml_loader import load_yaml


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.updates: list[list[dict[str, Any]]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        assert bind_vars["@collection"] == col.LOCATION_TYPES
        docs = self.db.docs
        if "UPDATE u._key" in query:
            self.updates.append(list(bind_vars["updates"]))
            for update in bind_vars["updates"]:
                docs[update["_key"]].update(update["patch"])
            return iter(())
        if "t.is_bed == null" in query:
            return iter(
                {
                    "_key": d["_key"],
                    "is_bed": d.get("is_bed"),
                    "has_supports_layout": d.get("supports_layout") is not None,
                }
                for d in docs.values()
                if d.get("is_bed") is None or d.get("supports_layout") is None
            )
        raise AssertionError(f"unexpected query: {query}")


class _FakeDb:
    def __init__(self, docs: list[dict[str, Any]] | None = None, *, present: bool = True) -> None:
        self.docs: dict[str, dict[str, Any]] = {d["_key"]: dict(d) for d in docs or []}
        self.present = present
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return self.present and name == col.LOCATION_TYPES

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {k: dict(d) for k, d in self.docs.items()}


_PRE_M2_SEED_KEYS = (
    "zone",
    "home",
    "garden",
    "greenhouse",
    "building",
    "room",
    "balcony",
    "terrace",
    "tent",
    "bed",
    "shelf",
    "container",
)


def _pre_m2_volume() -> _FakeDb:
    """The 12 seeds as the loader wrote them before the flags, plus a user type and two partial rows."""
    seeds = [{"_key": key, "name": key, "is_indoor": False, "is_system": True} for key in _PRE_M2_SEED_KEYS]
    return _FakeDb(
        [
            *seeds,
            {"_key": "huegelbeet", "name": "Hügelbeet", "is_indoor": False, "is_system": False},
            # A row that carries ``is_bed`` but not the other flag — not a shape an app writer
            # produces (``model_dump`` writes both), but what a hand edit or a partial import
            # leaves behind. The stored ``true`` is kept and implies the layout.
            {"_key": "terrassenbeet", "name": "Terrassenbeet", "is_system": False, "is_bed": True},
            # The seed job of a newer image inserted this one with both flags: not matched at all.
            {"_key": "raised_bed", "name": "Hochbeet", "is_system": True, "is_bed": True, "supports_layout": True},
        ]
    )


class TestStamping:
    def test_bed_seeds_and_layout_seeds_get_their_flags(self) -> None:
        db = _pre_m2_volume()

        report = migration.up(db)

        assert report.changed == 14 and report.scanned == 14 and report.dry_run is False
        assert {k for k, d in db.docs.items() if d["is_bed"]} == {"bed", "raised_bed", "terrassenbeet"}
        assert {k for k, d in db.docs.items() if d["supports_layout"]} == {
            "bed",
            "raised_bed",
            "tent",
            "shelf",
            "terrassenbeet",
        }
        assert db.docs["huegelbeet"] == {
            "_key": "huegelbeet",
            "name": "Hügelbeet",
            "is_indoor": False,
            "is_system": False,
            "is_bed": False,
            "supports_layout": False,
        }

    def test_a_partial_row_keeps_its_stored_flag_and_the_bed_implies_the_layout(self) -> None:
        db = _pre_m2_volume()

        migration.up(db)

        # ``terrassenbeet`` is not a seed key: by key alone it would be ``false`` / ``false``.
        # The row carried ``is_bed = true`` — kept — and a bed supports a layout (§9.2a).
        assert db.docs["terrassenbeet"]["is_bed"] is True
        assert db.docs["terrassenbeet"]["supports_layout"] is True

    def test_the_rule_reads_the_key_and_not_is_system(self) -> None:
        """The PUT-rebuild defect left seeded rows with ``is_system = false`` on real volumes."""
        db = _FakeDb([{"_key": "bed", "name": "Beet", "is_system": False}, {"_key": "tent", "is_system": False}])

        migration.up(db)

        assert (db.docs["bed"]["is_bed"], db.docs["bed"]["supports_layout"]) == (True, True)
        assert (db.docs["tent"]["is_bed"], db.docs["tent"]["supports_layout"]) == (False, True)

    def test_the_report_names_the_true_stamps(self) -> None:
        report = migration.up(_pre_m2_volume())

        assert report.details["bed_type_keys"] == ["bed"]
        assert report.details["layout_type_keys"] == ["bed", "shelf", "tent", "terrassenbeet"]
        assert report.details["is_bed_missing"] == 13
        assert report.details["supports_layout_missing"] == 14
        assert report.details["updated"] == 14

    def test_second_run_changes_nothing(self) -> None:
        db = _pre_m2_volume()
        migration.up(db)
        before = db.snapshot()

        report = migration.up(db)

        assert report.changed == 0 and report.scanned == 0 and report.noop is True
        assert db.snapshot() == before
        assert len(db.aql.updates) == 1

    def test_dry_run_reports_and_writes_nothing(self) -> None:
        db = _pre_m2_volume()
        before = db.snapshot()

        report = migration.up(db, dry_run=True)

        assert report.dry_run is True and report.changed == 0 and report.scanned == 14
        assert report.details["will_update"] == 14
        assert report.details["bed_type_keys"] == ["bed"]
        assert db.snapshot() == before
        assert db.aql.updates == []

    def test_a_volume_without_the_collection_is_a_noop(self) -> None:
        report = migration.up(_FakeDb(present=False))

        assert report.changed == 0 and report.scanned == 0
        assert report.details["bed_type_keys"] == [] and report.details["layout_type_keys"] == []

    def test_updates_are_batched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(module, "_BATCH_SIZE", 5)
        db = _FakeDb([{"_key": f"t{i}", "is_system": False} for i in range(12)])

        migration.up(db)

        assert [len(chunk) for chunk in db.aql.updates] == [5, 5, 2]

    def test_down_is_refused(self) -> None:
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb())


class TestFrozenKeySetsMatchTheSeeds:
    """The seed file is binding for new installations; the migration's frozen sets must agree with it today.

    When a later seed change diverges, the seed file moves on and this test is retired —
    never the applied migration (M-7).
    """

    def test_every_seed_carries_the_flags_the_migration_would_stamp(self) -> None:
        seeds = load_yaml("location_types.yaml")["location_types"]
        assert len(seeds) == 16
        for seed in seeds:
            key = seed["key"]
            assert seed["is_bed"] is module.is_bed_for(key), key
            assert seed["supports_layout"] is module.supports_layout_for(key), key

    def test_the_bed_seeds_are_the_spec_list(self) -> None:
        assert set(module.BED_TYPE_KEYS) == {"bed", "raised_bed", "planter", "greenhouse_bed", "cold_frame"}
        assert set(module.LAYOUT_ONLY_TYPE_KEYS) == {"tent", "shelf"}
        assert module.BED_TYPE_KEYS.isdisjoint(module.LAYOUT_ONLY_TYPE_KEYS)
