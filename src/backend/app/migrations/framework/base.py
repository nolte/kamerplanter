"""The :class:`Migration` base class (NFR-016 §3.1 / ADR-005 §4).

A migration is a single, versioned, one-time transformation of *existing* data or
structure.  Concrete migrations subclass :class:`Migration`, set the class-level
metadata (``version``, ``name``, ``description``, ``reversible``) and override
``up`` — and ``down`` only when they are honestly reversible.

The ``version`` string is zero-padded to four digits (``"0001"``) and forms the
``_key`` of the document tracked in ``schema_migrations``.
"""

from __future__ import annotations

import hashlib
import inspect

from arango.database import StandardDatabase

from app.migrations.framework.report import IrreversibleMigrationError, MigrationReport


class Migration:
    """Base class for a single versioned migration.

    Subclasses MUST set :attr:`version` and :attr:`name` and override :meth:`up`.
    Reversible migrations set ``reversible = True`` and override :meth:`down`;
    everything else keeps the default :meth:`down`, which raises
    :class:`IrreversibleMigrationError` (M-6 — honest reversibility).
    """

    version: str = ""
    name: str = ""
    description: str = ""
    reversible: bool = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        """Apply the migration.

        Implementations MUST be idempotent (M-3) and MUST honour ``dry_run`` by
        computing the report without writing anything (M-5).
        """
        raise NotImplementedError

    def down(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        """Revert the migration.

        The default implementation refuses: non-reversible migrations declare
        ``reversible = False`` and raise instead of faking an inverse (M-6).
        """
        raise IrreversibleMigrationError(f"Migration {self.version} ({self.name}) is not reversible")

    def checksum(self) -> str:
        """Return the SHA-256 of this migration's ``up`` source (M-7).

        Drift between the stored and the current checksum flags a migration that
        was edited after having been applied — applied migrations are immutable
        and corrections must ship as a new version.
        """
        source = inspect.getsource(type(self).up)
        return hashlib.sha256(source.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Migration {self.version} {self.name!r} reversible={self.reversible}>"
