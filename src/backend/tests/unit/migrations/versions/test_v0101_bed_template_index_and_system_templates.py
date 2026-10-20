"""Tests for v0101_bed_template_index_and_system_templates (REQ-053 WP 7.8, #2474).

Pinned here: the migration and the bootstrap agree on the index, the system templates are exactly the standard sizes
of GP-FR-044/045 under fixed keys with no invented agronomic value (E-10), a run inserts what is missing and nothing
else (an operator's edit survives, a second run is a no-op), the dry run writes nothing, and the version is
irreversible. The behaviour against a real server is ``tests/integration/test_bed_template_repository.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.domain.models.bed_template import BedTemplate
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0101_bed_template_index_and_system_templates import (
    SYSTEM_TEMPLATES,
    TEMPLATE_INDEX_FIELDS,
    migration,
)
from tests.unit.guards.test_tenant_unique_indexes_are_scoped import _RecordingCollection, _RecordingDb


class _Collection(_RecordingCollection):
    """The index recorder plus the few document calls the migration makes."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.documents: dict[str, dict[str, Any]] = {}
        self.insert_options: list[dict[str, Any]] = []

    def has(self, key: str) -> bool:
        return key in self.documents

    def insert(self, document: dict[str, Any], **options: Any) -> None:
        self.insert_options.append(options)
        self.documents.setdefault(document["_key"], document)


class _Db(_RecordingDb):
    def __init__(self) -> None:
        super().__init__()
        self.collections[col.BED_TEMPLATES] = _Collection(col.BED_TEMPLATES)


def _templates(db: _Db) -> dict[str, dict[str, Any]]:
    return db.collections[col.BED_TEMPLATES].documents  # type: ignore[attr-defined]


class TestTheShippedTemplates:
    def test_the_frozen_fields_equal_the_bootstrap_constant(self) -> None:
        assert list(TEMPLATE_INDEX_FIELDS) == col.BED_TEMPLATE_TENANT_INDEX_FIELDS == ["tenant_key", "name"]

    def test_the_bootstrap_builds_the_index(self) -> None:
        db = _RecordingDb()
        col.ensure_collections(db)  # type: ignore[arg-type]

        assert (["tenant_key", "name"], False) in [
            (r["fields"], r["unique"]) for r in db.collections[col.BED_TEMPLATES].rows
        ]

    def test_the_keys_are_fixed_and_unique(self) -> None:
        keys = [key for key, *_ in SYSTEM_TEMPLATES]

        assert len(keys) == len(set(keys)) == 9
        assert all(key.startswith("sys_") for key in keys)

    def test_the_sizes_are_the_standard_sizes_of_gp_fr_044_and_045(self) -> None:
        shapes = {
            key: (
                geometry["kind"],
                geometry.get("width_m"),
                geometry.get("length_m"),
                geometry.get("radius_m"),
                height,
            )
            for key, _name, _type, geometry, height in SYSTEM_TEMPLATES
        }

        assert shapes == {
            "sys_bed_1x1": ("rect", 1.0, 1.0, None, None),
            "sys_bed_2x1": ("rect", 2.0, 1.0, None, None),
            "sys_bed_3x1_2": ("rect", 3.0, 1.2, None, None),
            "sys_bed_4x1_2": ("rect", 4.0, 1.2, None, None),
            # The raised-bed standard differs between the two requirements: both ship (operator, 2026-10-19).
            "sys_raised_bed_1_2x2_4": ("rect", 1.2, 2.4, None, None),
            "sys_raised_bed_2x1x0_8": ("rect", 2.0, 1.0, None, 0.8),
            "sys_planter_d0_3": ("circle", None, None, 0.15, None),
            "sys_planter_d0_4": ("circle", None, None, 0.2, None),
            "sys_planter_d0_5": ("circle", None, None, 0.25, None),
        }

    def test_each_one_is_a_valid_global_bed_template(self) -> None:
        db = _Db()
        migration.up(db)  # type: ignore[arg-type]

        for document in _templates(db).values():
            template = BedTemplate(**document)
            assert template.is_system and "tenant_key" not in document and "created_by" not in document
            assert template.default_layout.row_spacing_cm is None and template.soil_profile_defaults is None


class TestUp:
    def test_it_creates_the_index_and_every_template_once(self) -> None:
        db = _Db()

        first = migration.up(db)  # type: ignore[arg-type]
        second = migration.up(db)  # type: ignore[arg-type]

        assert (first.changed, second.changed) == (1 + len(SYSTEM_TEMPLATES), 0)
        assert set(_templates(db)) == {key for key, *_ in SYSTEM_TEMPLATES}
        assert db.collections[col.BED_TEMPLATES].rows[0]["fields"] == ["tenant_key", "name"]

    def test_an_existing_template_is_left_as_it_is(self) -> None:
        db = _Db()
        db.collections[col.BED_TEMPLATES].documents["sys_bed_2x1"] = {"_key": "sys_bed_2x1", "name": "Edited"}  # type: ignore[attr-defined]

        report = migration.up(db)  # type: ignore[arg-type]

        assert _templates(db)["sys_bed_2x1"]["name"] == "Edited"
        assert "sys_bed_2x1" not in report.details["created"]

    def test_a_template_another_instance_inserted_meanwhile_is_not_an_error(self) -> None:
        db = _Db()
        migration.up(db)  # type: ignore[arg-type]

        options = db.collections[col.BED_TEMPLATES].insert_options  # type: ignore[attr-defined]

        assert options and all(o.get("overwrite_mode") == "ignore" for o in options)

    def test_the_dry_run_reports_and_writes_nothing(self) -> None:
        db = _Db()

        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert (report.dry_run, report.changed) == (True, 0)
        assert report.details["will_create"] == [key for key, *_ in SYSTEM_TEMPLATES]
        assert _templates(db) == {} and db.collections[col.BED_TEMPLATES].rows == []

    def test_an_absent_collection_is_reported_not_created(self) -> None:
        db = _RecordingDb()

        report = migration.up(db)  # type: ignore[arg-type]

        assert (report.changed, report.details["collection_absent"]) == (0, True)
        assert col.BED_TEMPLATES not in db.collections


def test_down_is_irreversible() -> None:
    with pytest.raises(IrreversibleMigrationError):
        migration.down(_Db())  # type: ignore[arg-type]
