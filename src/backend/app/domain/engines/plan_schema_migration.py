"""The migration chain of the garden-plan backup: a file of an older ``schema_version`` is read as the current one.

GP-NFR-004 / GP-NFR-072 (REQ-053 §23.1): a breaking change of the backup raises ``schema_version``, and the import
keeps reading at least the two versions before it ("a January export must be readable in December").

A migrator lifts a document by exactly one version: ``MIGRATORS["1"]`` takes a ``"1"`` document and returns the
same plan as a ``"2"`` document. The import runs the chain from the file's version up to
:data:`~app.domain.models.garden_plan_export.SCHEMA_VERSION` *before* it validates anything, so every later step -
the key check, the model, the references - only ever sees the current shape.

While ``"1"`` is the only version there is nothing to migrate and :data:`MIGRATORS` is empty. The guard
``tests/unit/guards/test_plan_import_keeps_two_schema_versions.py`` turns red the moment ``SCHEMA_VERSION`` is
raised without migrators for the two versions before it.

Versions are decimal strings (``"1"``, ``"2"`` ...), compared as numbers.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from app.domain.models import garden_plan_export

type Migrator = Callable[[dict[str, Any]], dict[str, Any]]

#: GP-NFR-072: how many versions before the current one the import must still read.
KEPT_PREDECESSORS = 2

#: From-version -> the migrator to the next version. Empty while ``"1"`` is the only ``schema_version``.
MIGRATORS: Mapping[str, Migrator] = {}


def current_version() -> str:
    """The ``schema_version`` the export writes and the import validates against."""
    return garden_plan_export.SCHEMA_VERSION


def required_predecessors(current: str, kept: int = KEPT_PREDECESSORS) -> list[str]:
    """The versions before ``current`` that must stay readable, oldest first (none below ``"1"``)."""
    number = int(current)
    return [str(version) for version in range(max(1, number - kept), number)]


def missing_migrators(current: str, migrators: Mapping[str, Migrator]) -> list[str]:
    """The required predecessors of ``current`` that have no migrator: what the guard reports."""
    return [version for version in required_predecessors(current) if version not in migrators]


def readable_versions(current: str | None = None, migrators: Mapping[str, Migrator] | None = None) -> list[str]:
    """``current`` and every older version from which an unbroken chain of migrators reaches it, oldest first."""
    current = current_version() if current is None else current
    migrators = MIGRATORS if migrators is None else migrators
    readable = [current]
    version = int(current) - 1
    while version >= 1 and str(version) in migrators:
        readable.insert(0, str(version))
        version -= 1
    return readable


def migrate(
    document: dict[str, Any], current: str | None = None, migrators: Mapping[str, Migrator] | None = None
) -> dict[str, Any]:
    """``document`` lifted to ``current``; its ``schema_version`` must be one of :func:`readable_versions`.

    Each step must advance ``schema_version`` by exactly one - a migrator that skips or repeats a version is a bug,
    raised here rather than validated against the wrong model.
    """
    current = current_version() if current is None else current
    migrators = MIGRATORS if migrators is None else migrators
    if document.get("schema_version") not in readable_versions(current, migrators):
        raise ValueError(f"schema_version {document.get('schema_version')!r} cannot be migrated to {current!r}")
    while (version := str(document["schema_version"])) != current:
        document = migrators[version](document)
        expected = str(int(version) + 1)
        if str(document.get("schema_version")) != expected:
            raise ValueError(f"the migrator from {version!r} must produce {expected!r}")
    return document
