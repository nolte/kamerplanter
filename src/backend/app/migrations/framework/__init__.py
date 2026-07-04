"""Versioned ArangoDB migration framework (ADR-005 / NFR-016).

Public surface: the :class:`Migration` base class, the uniform
:class:`MigrationReport`, the :class:`MigrationRunner` and the
:func:`run_pending_migrations` startup entrypoint.
"""

from app.migrations.framework.base import Migration
from app.migrations.framework.report import (
    IrreversibleMigrationError,
    MigrationDiscoveryError,
    MigrationError,
    MigrationLockError,
    MigrationReport,
    NonLinearHistoryError,
)
from app.migrations.framework.runner import MigrationRunner, run_pending_migrations

__all__ = [
    "IrreversibleMigrationError",
    "Migration",
    "MigrationDiscoveryError",
    "MigrationError",
    "MigrationLockError",
    "MigrationReport",
    "MigrationRunner",
    "NonLinearHistoryError",
    "run_pending_migrations",
]
