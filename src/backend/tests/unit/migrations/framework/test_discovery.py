"""NFR-016 M-1 — version discovery and strict sequence validation."""

from __future__ import annotations

import pytest

from app.migrations.framework.discovery import load_migrations, normalize_version, validate_sequence
from app.migrations.framework.report import MigrationDiscoveryError


class TestNormalizeVersion:
    @pytest.mark.parametrize(("value", "expected"), [("1", "0001"), ("0002", "0002"), ("42", "0042")])
    def test_zero_pads(self, value, expected):
        assert normalize_version(value) == expected


class TestLoadMigrations:
    def test_loads_contiguous_versions(self):
        migrations = load_migrations()
        versions = [m.version for m in migrations]

        assert versions == [
            "0001",
            "0002",
            "0003",
            "0004",
            "0005",
            "0006",
            "0007",
            "0008",
            "0009",
            "0010",
            "0011",
            "0012",
            "0013",
            "0014",
            "0015",
            "0016",
            "0017",
            "0018",
            "0019",
            "0020",
            "0021",
            "0022",
            "0023",
            "0024",
            "0025",
            "0026",
        ]
        # Baseline is the only reversible migration.
        assert migrations[0].reversible is True
        assert all(m.reversible is False for m in migrations[1:])


class TestValidateSequence:
    def test_accepts_contiguous(self, make_migration):
        validate_sequence([make_migration("0001"), make_migration("0002"), make_migration("0003")])

    def test_rejects_duplicate(self, make_migration):
        with pytest.raises(MigrationDiscoveryError):
            validate_sequence([make_migration("0001"), make_migration("0001")])

    def test_rejects_gap(self, make_migration):
        with pytest.raises(MigrationDiscoveryError):
            validate_sequence([make_migration("0001"), make_migration("0003")])

    def test_rejects_not_starting_at_one(self, make_migration):
        with pytest.raises(MigrationDiscoveryError):
            validate_sequence([make_migration("0002"), make_migration("0003")])
