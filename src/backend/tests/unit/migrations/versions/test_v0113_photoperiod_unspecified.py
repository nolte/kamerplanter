"""v0113 (#2857): a stored ``day_neutral`` that no seed source states becomes ``unspecified``, on a fake volume.

The fake answers the scan from plain dicts with the scan's rules (lifecycles holding ``day_neutral``, sorted by key,
with their species resolved) and applies the update with the update's rules (only a lifecycle that still holds
``day_neutral``). The real AQL runs in ``tests/integration/test_v0113_photoperiod_unspecified.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from app.common.enums import PhotoperiodType
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0113_photoperiod_unspecified import PhotoperiodUnspecifiedMigration, migration


class _FakeDb:
    def __init__(self, lifecycles: dict[str, dict[str, Any]], species: dict[str, dict[str, Any]]) -> None:
        self.lifecycles = lifecycles
        self.species = species
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in {"lifecycle_configs", "species"}


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self.db = db
        self.updates: list[tuple[str, int]] = []
        self.before_apply: Callable[[], None] | None = None

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = bind_vars or {}
        if query == migration.SCAN:
            assert (bind_vars["@lifecycles"], bind_vars["species"]) == ("lifecycle_configs", "species")
            return iter(self._scan(bind_vars["day_neutral"]))
        if query == migration.APPLY:
            if self.before_apply is not None:
                self.before_apply()
            self.updates.append((bind_vars["target"], len(bind_vars["keys"])))
            written = 0
            for key in bind_vars["keys"]:
                lifecycle = self.db.lifecycles.get(key)
                if lifecycle is None or lifecycle.get("photoperiod_type") != bind_vars["day_neutral"]:
                    continue
                lifecycle["photoperiod_type"] = bind_vars["target"]
                written += 1
            return iter([written])
        raise AssertionError(f"unexpected query: {query[:60]}")

    def _scan(self, day_neutral: str) -> list[dict[str, Any]]:
        rows = []
        for key in sorted(self.db.lifecycles):
            lifecycle = self.db.lifecycles[key]
            if lifecycle.get("photoperiod_type") != day_neutral:
                continue
            species = self.db.species.get(lifecycle.get("species_key") or "")
            rows.append(
                {
                    "key": key,
                    "species_found": species is not None,
                    "is_global": species is not None and not species.get("tenant_key"),
                    "scientific_name": None if species is None else species.get("scientific_name"),
                }
            )
        return rows


def _volume() -> _FakeDb:
    species = {
        "sp_hemp": {"scientific_name": "Cannabis sativa", "tenant_key": ""},
        "sp_basil": {"scientific_name": "Ocimum basilicum", "tenant_key": ""},
        "sp_untenanted": {"scientific_name": "Imaginaria secunda", "tenant_key": None},
        "sp_unsourced": {"scientific_name": "Imaginaria nullius", "tenant_key": ""},
        "sp_tenant_dahlia": {"scientific_name": "Dahlia pinnata", "tenant_key": "t_a"},
        "sp_poinsettia": {"scientific_name": "Euphorbia pulcherrima", "tenant_key": ""},
    }
    lifecycles = {
        "lc_hemp": {"species_key": "sp_hemp", "photoperiod_type": "day_neutral"},
        "lc_basil": {"species_key": "sp_basil", "photoperiod_type": "day_neutral"},
        "lc_untenanted": {"species_key": "sp_untenanted", "photoperiod_type": "day_neutral"},
        "lc_unsourced": {"species_key": "sp_unsourced", "photoperiod_type": "day_neutral"},
        "lc_tenant_dahlia": {"species_key": "sp_tenant_dahlia", "photoperiod_type": "day_neutral"},
        "lc_orphan": {"species_key": "sp_gone", "photoperiod_type": "day_neutral"},
        "lc_poinsettia": {"species_key": "sp_poinsettia", "photoperiod_type": "short_day"},
    }
    return _FakeDb(lifecycles, species)


def _types(db: _FakeDb) -> dict[str, str]:
    return {key: lc["photoperiod_type"] for key, lc in db.lifecycles.items()}


class TestSourcedTable:
    def test_hemp_is_short_day_as_its_lifecycle_config_states(self) -> None:
        assert migration.SOURCED["Cannabis sativa"] == "short_day"

    def test_it_holds_only_stated_types(self) -> None:
        stated = {PhotoperiodType.SHORT_DAY, PhotoperiodType.LONG_DAY, PhotoperiodType.DAY_NEUTRAL}

        assert len(migration.SOURCED) == 180
        assert set(migration.SOURCED.values()) <= {value.value for value in stated}

    def test_the_frozen_values_are_the_enum_values(self) -> None:
        assert PhotoperiodType.DAY_NEUTRAL.value == migration.DAY_NEUTRAL
        assert PhotoperiodType.UNSPECIFIED.value == migration.UNSPECIFIED


class TestDecide:
    @pytest.mark.parametrize(
        ("row", "expected"),
        [
            ({"species_found": False}, ("unspecified_species_missing", "unspecified")),
            (
                {"species_found": True, "is_global": False, "scientific_name": "Cannabis sativa"},
                ("unspecified_tenant_species", "unspecified"),
            ),
            (
                {"species_found": True, "is_global": True, "scientific_name": "Imaginaria nullius"},
                ("unspecified_without_source", "unspecified"),
            ),
            (
                {"species_found": True, "is_global": True, "scientific_name": "Ocimum basilicum"},
                ("kept_sourced", None),
            ),
            (
                {"species_found": True, "is_global": True, "scientific_name": "Cannabis sativa"},
                ("corrected", "short_day"),
            ),
        ],
    )
    def test_buckets(self, row: dict[str, Any], expected: tuple[str, str | None]) -> None:
        assert PhotoperiodUnspecifiedMigration.decide(row) == expected


class TestUp:
    def test_defaults_become_unspecified_and_hemp_gets_its_source(self) -> None:
        db = _volume()

        report = migration.up(db)  # type: ignore[arg-type]

        assert _types(db) == {
            "lc_hemp": "short_day",
            "lc_basil": "day_neutral",
            "lc_untenanted": "unspecified",
            "lc_unsourced": "unspecified",
            "lc_tenant_dahlia": "unspecified",
            "lc_orphan": "unspecified",
            "lc_poinsettia": "short_day",
        }
        assert (report.scanned, report.changed) == (6, 5)
        assert report.details["corrected_to"] == {"short_day": 1}
        assert {name: bucket["count"] for name, bucket in report.details["buckets"].items()} == {
            "corrected": 1,
            "kept_sourced": 1,
            "unspecified_without_source": 2,
            "unspecified_tenant_species": 1,
            "unspecified_species_missing": 1,
        }
        assert report.details["skipped_changed_since_scan"] == 0

    def test_a_second_run_writes_nothing(self) -> None:
        db = _volume()
        migration.up(db)  # type: ignore[arg-type]
        writes = list(db.aql.updates)

        again = migration.up(db)  # type: ignore[arg-type]

        assert (again.scanned, again.changed) == (1, 0)
        assert db.aql.updates == writes

    def test_the_dry_run_counts_and_writes_nothing(self) -> None:
        db = _volume()
        before = _types(db)

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert _types(db) == before
        assert (report.scanned, report.changed, report.details["will_write"]) == (6, 0, 5)
        assert db.aql.updates == []

    def test_a_lifecycle_a_person_changed_since_the_scan_is_skipped(self) -> None:
        db = _volume()

        def person_edits() -> None:
            db.lifecycles["lc_unsourced"]["photoperiod_type"] = "long_day"

        db.aql.before_apply = person_edits

        report = migration.up(db)  # type: ignore[arg-type]

        assert db.lifecycles["lc_unsourced"]["photoperiod_type"] == "long_day"
        assert (report.changed, report.details["skipped_changed_since_scan"]) == (4, 1)

    def test_a_volume_without_the_collections_is_a_no_op(self) -> None:
        class _Empty:
            def has_collection(self, name: str) -> bool:
                return False

        report = migration.up(_Empty())  # type: ignore[arg-type]

        assert (report.scanned, report.changed) == (0, 0)


def test_down_is_refused() -> None:
    assert migration.reversible is False
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_volume())  # type: ignore[arg-type]
