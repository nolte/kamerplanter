"""v0102 (#2513): the frozen lists, the report shape and the dry run, on a fake volume.

The fake answers each scan from canned ids and records every ``REMOVE``; the AQL itself is measured on a real
ArangoDB by ``tests/integration/test_v0102_purge_site_orphans.py``.

**The frozen lists.** ``_SITE_KEYED_ROWS`` and ``_EDGE_ENDS`` are literals in the migration, so the migration keeps
doing what it did when it ran. The derivation tests below compare them with the graph as it is now: when the graph
grows they fail — then update the expectation *here* and write a new migration for the new relation; never edit
v0102.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.graph_edges import edges_touching
from app.data_access.arango.irrigation_zone_repository import ZONE_EDGES
from app.data_access.arango.site_repository import _SITE_DEPENDENTS
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions import v0102_purge_site_orphans as v0102
from app.migrations.versions.v0102_purge_site_orphans import migration

_VERTICES = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.GARDEN_OBJECTS,
    *_SITE_DEPENDENTS,
)


class TestTheFrozenListsAreTheDerivationOfTheirTime:
    def test_site_keyed_rows_are_garden_objects_and_the_site_dependents(self) -> None:
        frozen = v0102._SITE_KEYED_ROWS
        assert frozen == (col.GARDEN_OBJECTS, *_SITE_DEPENDENTS)

    def test_edge_ends_are_edges_touching_each_vertex_and_the_zone_edges(self) -> None:
        expected = (
            *((vertex, edges_touching(vertex)) for vertex in _VERTICES),
            (col.IRRIGATION_ZONES, ZONE_EDGES),
        )
        frozen = v0102._EDGE_ENDS
        assert frozen == expected

    def test_history_is_in_no_list(self) -> None:
        listed = {*v0102._SITE_KEYED_ROWS, *(vertex for vertex, _ in v0102._EDGE_ENDS)}
        assert col.CARE_EVENTS not in listed
        assert col.GARDEN_PLAN_AUDIT not in listed

    def test_the_steps_are_ordered_rows_then_locations_then_slots_then_edges(self) -> None:
        assert [name for name, _ in v0102._STEPS] == [
            *(f"{name}_of_missing_sites" for name in v0102._SITE_KEYED_ROWS),
            "unsited_garden_objects_of_missing_sites",
            "locations_of_missing_sites",
            "slots_of_removed_locations",
            "dangling_edges",
        ]

    def test_the_2528_nulling_step_exists_and_runs_last(self) -> None:
        """#2528: a nulling step is not a removal step (its ids would be deleted) and runs after every removal."""
        assert [name for name, _ in v0102._NULLING_STEPS] == ["locations_with_dangling_template_key"]
        assert "locations_with_dangling_template_key" not in [name for name, _ in v0102._STEPS]

        report = migration.up(_FakeDb())

        assert list(report.details)[-1] == "locations_with_dangling_template_key"
        assert "# --- #2528" not in Path(v0102.__file__).read_text(encoding="utf-8")


class _FakeAql:
    """Canned scans: two orphan forecasts, one orphan location with one slot, one dangling edge; two locations with a
    dangling ``template_key`` - ``bed`` (removed anyway) and ``bed2``."""

    def __init__(self, db: _FakeDb) -> None:
        self.db = db

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind = bind_vars or {}
        if query == v0102._UNSET_TEMPLATE_KEY:
            present = [key for key in bind["keys"] if f"{bind['@col']}/{key}" not in self.db.vanished]
            self.db.nulled.extend(f"{bind['@col']}/{key}" for key in present)
            return iter(present)
        if query == v0102._DANGLING_TEMPLATE_KEYS:
            assert bind == {"@locations": col.LOCATIONS, "templates": col.BED_TEMPLATES}
            return iter(["locations/bed", "locations/bed2"])
        if "REMOVE" in query:
            # ``RETURN OLD._key``: a key gone before the apply is skipped by ``ignoreErrors`` and returns nothing.
            present = [key for key in bind["keys"] if f"{bind['@col']}/{key}" not in self.db.vanished]
            self.db.removed.extend(f"{bind['@col']}/{key}" for key in present)
            return iter(present)
        if query == v0102._ROWS_OF_MISSING_SITES:
            if bind["@col"] == col.WEATHER_FORECASTS:
                return iter(["weather_forecasts/f1", "weather_forecasts/f2"])
            return iter(())
        if query == v0102._LOCATIONS_OF_MISSING_SITES:
            return iter([{"id": "locations/bed", "site_live": False, "parents": []}])
        if query == v0102._CHILD_LOCATIONS:
            return iter(())
        if query == v0102._SLOTS_OF_LOCATIONS:
            assert bind["ids"] == ["locations/bed"]
            return iter([["slots/s1"]])
        if bind.get("@edges") == col.CARE_EVENT_AT and bind.get("vertex") == col.LOCATIONS:
            assert "locations/bed" in bind["removed"]
            return iter(["care_event_at/e1"])
        return iter(())


class _FakeDb:
    def __init__(self, *, sites: bool = True, missing: frozenset[str] = frozenset()) -> None:
        self.sites = sites
        self.missing = missing
        self.removed: list[str] = []
        self.nulled: list[str] = []
        self.vanished: set[str] = set()
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        if name in self.missing:
            return False
        return self.sites or name != col.SITES


class TestTheReport:
    def test_every_step_reports_matched_removed_and_capped_keys(self) -> None:
        report = migration.up(_FakeDb())

        assert list(report.details) == [name for name, _ in (*v0102._STEPS, *v0102._NULLING_STEPS)]
        assert report.details["weather_forecasts_of_missing_sites"] == {
            "matched": 2,
            "removed": 2,
            "keys": ["f1", "f2"],
        }
        assert report.details["locations_of_missing_sites"] == {"matched": 1, "removed": 1, "keys": ["bed"]}
        assert report.details["slots_of_removed_locations"] == {"matched": 1, "removed": 1, "keys": ["s1"]}
        assert report.details["dangling_edges"] == {"matched": 1, "removed": 1, "keys": ["care_event_at/e1"]}
        assert report.details["season_states_of_missing_sites"] == {"matched": 0, "removed": 0, "keys": []}
        assert report.details["locations_with_dangling_template_key"] == {"matched": 1, "nulled": 1, "keys": ["bed2"]}
        assert (report.version, report.scanned, report.changed, report.dry_run) == ("0102", 6, 6, False)

    def test_the_apply_removes_exactly_what_was_matched(self) -> None:
        db = _FakeDb()
        migration.up(db)

        assert sorted(db.removed) == sorted(
            ["weather_forecasts/f1", "weather_forecasts/f2", "locations/bed", "slots/s1", "care_event_at/e1"]
        )
        assert db.nulled == ["locations/bed2"]

    def test_a_location_the_removals_take_is_not_nulled(self) -> None:
        db = _FakeDb()
        migration.up(db)

        assert "locations/bed" in db.removed and "locations/bed" not in db.nulled

    def test_a_location_gone_before_the_nulling_is_matched_but_not_counted(self) -> None:
        db = _FakeDb()
        db.vanished.add("locations/bed2")

        detail = migration.up(db).details["locations_with_dangling_template_key"]

        assert (detail["matched"], detail["nulled"]) == (1, 0)

    def test_a_volume_without_bed_templates_nulls_nothing(self) -> None:
        db = _FakeDb(missing=frozenset({col.BED_TEMPLATES}))

        report = migration.up(db)

        assert report.details["locations_with_dangling_template_key"] == {"matched": 0, "nulled": 0, "keys": []}
        assert db.nulled == []
        assert report.details["locations_of_missing_sites"]["removed"] == 1

    def test_a_key_gone_before_the_apply_is_matched_but_not_counted_as_removed(self) -> None:
        db = _FakeDb()
        db.vanished.add("weather_forecasts/f2")

        report = migration.up(db)

        detail = report.details["weather_forecasts_of_missing_sites"]
        assert (detail["matched"], detail["removed"]) == (2, 1)
        assert detail["removed"] == detail["matched"] - 1
        assert (report.scanned, report.changed) == (6, 5)

    def test_keys_are_capped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(v0102, "_LISTED", 1)

        report = migration.up(_FakeDb(), dry_run=True)

        assert report.details["weather_forecasts_of_missing_sites"]["keys"] == ["f1"]
        assert report.details["weather_forecasts_of_missing_sites"]["matched"] == 2


class TestTheDryRun:
    def test_writes_nothing_and_reports_the_same_matches(self) -> None:
        dry_db, wet_db = _FakeDb(), _FakeDb()

        dry = migration.up(dry_db, dry_run=True)
        wet = migration.up(wet_db)

        assert dry_db.removed == [] and dry_db.nulled == []
        assert (dry.dry_run, dry.changed, dry.scanned) == (True, 0, wet.scanned)
        assert {step: d["matched"] for step, d in dry.details.items()} == {
            step: d["matched"] for step, d in wet.details.items()
        }
        assert all(d.get("removed", 0) == 0 and d.get("nulled", 0) == 0 for d in dry.details.values())
        assert dry.details["locations_with_dangling_template_key"]["matched"] == 1


class TestGuards:
    def test_a_volume_without_sites_is_left_alone(self) -> None:
        db = _FakeDb(sites=False)

        report = migration.up(db)

        assert (report.scanned, report.changed, report.details) == (0, 0, {})
        assert db.removed == [] and db.nulled == []

    def test_down_is_irreversible(self) -> None:
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_FakeDb())

    def test_an_edge_end_other_than_from_or_to_is_refused(self) -> None:
        with pytest.raises(ValueError, match="Not an edge endpoint"):
            v0102._dangling_end("_key")
