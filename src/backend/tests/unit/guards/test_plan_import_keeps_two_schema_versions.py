"""GP-NFR-072 (REQ-053 §23.1, WP 8.28 #2671): the import reads the two ``schema_version``s before the current one.

The predicate: for the ``SCHEMA_VERSION`` the export writes, every one of the (up to) two previous versions has a
migrator in :data:`app.domain.engines.plan_schema_migration.MIGRATORS`, and the chain from each reaches the current
version. Raising ``SCHEMA_VERSION`` without adding the migrators turns this red; the planted cases below show the
detector telling the two apart.
"""

from __future__ import annotations

from typing import Any

from app.api.v1.garden_plan import schemas as plan_schemas
from app.domain.engines.plan_schema_migration import MIGRATORS, missing_migrators, readable_versions
from app.domain.models import garden_plan_export


def _lift(document: dict[str, Any]) -> dict[str, Any]:
    return document


def test_the_current_version_keeps_its_two_predecessors_readable() -> None:
    current = garden_plan_export.SCHEMA_VERSION

    assert missing_migrators(current, MIGRATORS) == [], (
        f"schema_version {current!r} needs a migrator for each of the two versions before it (GP-NFR-072); "
        "add them to plan_schema_migration.MIGRATORS"
    )
    assert set(readable_versions()) >= {current, *MIGRATORS}


def test_the_plan_read_and_the_backup_name_the_same_version() -> None:
    """``GET /plan`` and the export carry one ``schema_version`` (GP-NFR-004); two constants must not drift."""
    assert plan_schemas.SCHEMA_VERSION == garden_plan_export.SCHEMA_VERSION


def test_the_detector_tells_a_missing_migrator_from_a_present_one() -> None:
    assert missing_migrators("2", {}) == ["1"]  # version raised, no migrator: red
    assert missing_migrators("2", {"1": _lift}) == []  # with one: green
    assert missing_migrators("3", {"2": _lift}) == ["1"]  # only the last step: still red
    assert missing_migrators("3", {"1": _lift, "2": _lift}) == []
