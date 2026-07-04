"""Shared report dataclass and error hierarchy for the migration framework.

NFR-016 §3.1 defines *what* a migration must report (scanned/changed counts, the
dry-run flag, a duration). :class:`MigrationReport` is the single, uniform return
type every migration produces so the runner, the CLI and the tracking layer can
treat all migrations identically.

The framework-internal exceptions live here too, because ``report`` is the lowest
module in the framework import graph (base, tracking, discovery and runner all
import it).  These are *operational* startup/ops errors, not HTTP-facing
``KamerplanterError`` subclasses — they intentionally do NOT map to an API status
code.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


class MigrationError(Exception):
    """Base class for all migration-framework errors."""


class IrreversibleMigrationError(MigrationError):
    """Raised when ``down()`` is invoked on a non-reversible migration (M-6)."""


class NonLinearHistoryError(MigrationError):
    """Raised when pending versions do not form a gapless suffix of history (M-1)."""


class MigrationLockError(MigrationError):
    """Raised when the migration lock is held by another live runner (M-8)."""


class MigrationDiscoveryError(MigrationError):
    """Raised for missing, duplicate or non-contiguous version modules (M-1)."""


@dataclass
class MigrationReport:
    """Uniform result of a single migration ``up()``/``down()`` invocation.

    Attributes
    ----------
    version:
        The zero-padded version string of the owning migration (``"0004"``).
    name:
        The migration slug (``"backfill_tenant_key"``).
    scanned:
        Number of documents inspected.
    changed:
        Number of documents actually written (``0`` on a dry-run).
    dry_run:
        ``True`` when the report was computed without writing.
    duration_ms:
        Wall-clock duration filled in by the runner (``0.0`` when computed
        stand-alone).
    details:
        Free-form, migration-specific payload (e.g. changed keys, per-collection
        counts) preserved for logging and CLI output.
    """

    version: str
    name: str
    scanned: int = 0
    changed: int = 0
    dry_run: bool = False
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def noop(self) -> bool:
        """``True`` when nothing changed — the desired state of a re-run (M-3)."""
        return self.changed == 0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the report."""
        return asdict(self)
