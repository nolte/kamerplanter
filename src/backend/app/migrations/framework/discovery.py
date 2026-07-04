"""Version-module discovery and sequence validation (NFR-016 M-1).

Loads every ``app/migrations/versions/vNNNN_*.py`` module, extracts its exported
``migration`` object and validates that the resulting set of versions is unique,
strictly monotone and gapless starting at ``0001``.
"""

from __future__ import annotations

import importlib
import pkgutil
import re

from app.migrations import versions as versions_pkg
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationDiscoveryError

_MODULE_RE = re.compile(r"^v(?P<number>\d{4})_[a-z0-9_]+$")


def normalize_version(value: str) -> str:
    """Return a zero-padded 4-digit version string (``"2"`` -> ``"0002"``)."""
    return str(int(value)).zfill(4)


def validate_sequence(migrations: list[Migration]) -> None:
    """Validate uniqueness, strict monotonicity and gaplessness (M-1)."""
    versions = [m.version for m in migrations]
    if len(set(versions)) != len(versions):
        raise MigrationDiscoveryError(f"Duplicate migration versions: {sorted(versions)}")
    numbers = sorted(int(v) for v in versions)
    for expected, actual in enumerate(numbers, start=1):
        if expected != actual:
            raise MigrationDiscoveryError(
                f"Non-contiguous version numbering: expected {expected:04d}, got {actual:04d}"
            )


def load_migrations() -> list[Migration]:
    """Discover, import and validate all version modules, ascending by version."""
    module_names: list[str] = []
    for info in pkgutil.iter_modules(versions_pkg.__path__):
        if info.ispkg:
            continue
        if _MODULE_RE.match(info.name):
            module_names.append(info.name)

    migrations: list[Migration] = []
    for name in sorted(module_names):
        module = importlib.import_module(f"{versions_pkg.__name__}.{name}")
        migration = getattr(module, "migration", None)
        if migration is None:
            raise MigrationDiscoveryError(f"Version module {name!r} does not export a 'migration' object")
        if not isinstance(migration, Migration):
            raise MigrationDiscoveryError(f"Version module {name!r} 'migration' is not a Migration instance")
        migrations.append(migration)

    migrations.sort(key=lambda m: m.version)
    validate_sequence(migrations)
    return migrations
