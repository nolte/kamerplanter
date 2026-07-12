"""Smoke tests for the concrete version modules.

Each migration's ``up`` runs as a safe no-op against an empty database (idempotency
floor), honours ``dry_run``, and every irreversible migration's ``down`` raises
:class:`IrreversibleMigrationError` while the reversible baseline's ``down`` is a
no-op.
"""

from __future__ import annotations

import pytest

from app.migrations.framework.discovery import load_migrations
from app.migrations.framework.report import IrreversibleMigrationError, MigrationReport


class _NoopAql:
    """Returns an empty cursor for every query — an empty database."""

    def execute(self, *args, **kwargs):
        return iter([])


class _NoopCollection:
    def update(self, *args, **kwargs):  # pragma: no cover - never reached on empty data
        raise AssertionError("no document should be written on an empty database")

    def indexes(self):
        # Models a bootstrapped-but-empty database: ``ensure_collections`` already
        # created every persistent index, so a structural index migration
        # (v0009 notifications.group_key, v0011 climate_normals, v0012
        # irrigation_demands, v0013 hardiness_zones, v0014 cv_diagnosis) finds its
        # target present and is a no-op.
        return [
            {"type": "persistent", "fields": ["group_key", "tenant_key"], "unique": False},
            {"type": "persistent", "fields": ["tenant_key", "site_key", "source"], "unique": True},
            {
                "type": "persistent",
                "fields": ["tenant_key", "site_key", "run_key", "demand_date"],
                "unique": True,
            },
            {"type": "persistent", "fields": ["zone"], "unique": True},
            # v0014 plant_diagnosis_requests history index
            {"type": "persistent", "fields": ["tenant_key", "user_key", "created_at"], "unique": False},
            # v0015 InvenTree collection indexes
            {"type": "persistent", "fields": ["tenant_key"], "unique": False},
            {"type": "persistent", "fields": ["tenant_key", "entity_collection", "entity_key"], "unique": False},
            {"type": "persistent", "fields": ["tenant_key", "status", "created_at"], "unique": False},
            {"type": "persistent", "fields": ["reference_key"], "unique": False},
            {"type": "persistent", "fields": ["tenant_key", "equipment_type", "status"], "unique": False},
            # v0016 glossary collection indexes (glossary_terms + glossary_term_cache)
            {"type": "persistent", "fields": ["slug"], "unique": True},
            {"type": "persistent", "fields": ["category"], "unique": False},
            {"type": "persistent", "fields": ["is_active"], "unique": False},
            {
                "type": "persistent",
                "fields": ["term_slug", "language", "expertise_level", "kb_version"],
                "unique": True,
            },
            {"type": "persistent", "fields": ["valid_until"], "unique": False},
            # v0017 MCP collection indexes (mcp_audit_log + mcp_idempotency_record)
            {"type": "persistent", "fields": ["service_account_key"], "unique": False},
            {"type": "persistent", "fields": ["tenant_key", "created_at"], "unique": False},
            {"type": "persistent", "fields": ["created_at"], "unique": False},
            {
                "type": "persistent",
                "fields": ["service_account_key", "tool_name", "idempotency_key"],
                "unique": True,
            },
            {"type": "persistent", "fields": ["expires_at"], "unique": False},
        ]

    def add_persistent_index(self, *args, **kwargs):  # pragma: no cover - never reached on bootstrapped db
        raise AssertionError("no index should be created when the bootstrap index already exists")


class _NoopGraph:
    """A bootstrapped graph that already carries every edge definition."""

    def edge_definitions(self):
        # v0011 checks for the has_climate_normal edge; v0012 for the two
        # irrigation-demand edges; v0013 for located_in_zone; v0014 checks the four
        # CV-diagnosis edges — report all present so the structural migrations stay
        # no-ops on a bootstrapped database.
        return [
            {"edge_collection": "has_climate_normal"},
            {"edge_collection": "has_irrigation_demand"},
            {"edge_collection": "demand_for_run"},
            {"edge_collection": "located_in_zone"},
            {"edge_collection": "cv_diagnosed_for"},
            {"edge_collection": "cv_diagnosis_found"},
            {"edge_collection": "cv_attached_to_inspection"},
            {"edge_collection": "cv_phenotype_of"},
            # v0015 InvenTree integration edges
            {"edge_collection": "has_inventree_ref"},
            {"edge_collection": "has_stock_transaction"},
            {"edge_collection": "equipment_at"},
        ]

    def create_edge_definition(self, *args, **kwargs):  # pragma: no cover - never reached on bootstrapped db
        raise AssertionError("no edge definition should be created when the bootstrap already added it")


class _NoopDb:
    """An empty database: scans return nothing, so every migration is a no-op.

    Structural migrations (v0009 index, v0011 collection/edge) additionally probe
    ``has_collection`` / ``has_graph``; the bootstrapped model reports everything as
    already present so those migrations report ``changed == 0`` too.
    """

    def __init__(self) -> None:
        self.aql = _NoopAql()

    def collection(self, name: str) -> _NoopCollection:
        return _NoopCollection()

    def has_collection(self, name: str) -> bool:
        return True

    def has_graph(self, name: str) -> bool:
        return True

    def graph(self, name: str) -> _NoopGraph:
        return _NoopGraph()


def _migrations():
    return load_migrations()


class TestVersionSmoke:
    def test_up_is_noop_on_empty_db(self):
        for migration in _migrations():
            report = migration.up(_NoopDb())
            assert isinstance(report, MigrationReport)
            assert report.version == migration.version
            assert report.changed == 0
            assert report.noop is True

    def test_up_dry_run_writes_nothing(self):
        for migration in _migrations():
            report = migration.up(_NoopDb(), dry_run=True)
            assert report.dry_run is True
            assert report.changed == 0

    def test_down_matches_reversibility(self):
        for migration in _migrations():
            if migration.reversible:
                report = migration.down(_NoopDb())
                assert isinstance(report, MigrationReport)
            else:
                with pytest.raises(IrreversibleMigrationError):
                    migration.down(_NoopDb())

    def test_baseline_is_the_only_reversible(self):
        migrations = _migrations()
        assert migrations[0].name == "baseline"
        assert migrations[0].reversible is True
        assert all(not m.reversible for m in migrations[1:])

    def test_retire_harvest_runs_before_seeds(self):
        # AC-6 relies on the harvest reclassification running before any plan seed
        # reads phase entries on a legacy volume. The framework guarantees this by
        # running *every* discovered migration before the seeds (O-1), so it is
        # enough that the migration is present — it need not be the last one.
        # (Later migrations, e.g. v0006, read raw documents and never trigger the
        # strict Pydantic phase read that AC-6 guards against, so ordering after
        # v0005 is safe.)
        names = [m.name for m in _migrations()]
        assert "retire_harvest_phase" in names
