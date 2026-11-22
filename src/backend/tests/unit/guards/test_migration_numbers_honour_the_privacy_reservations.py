"""A migration number the privacy plan reserves is taken only by the migration it reserves it for.

``spec/privacy/09-migrations-and-backfills.md`` plans its migrations by number - ``Migration `v0108_name```
headings - before their code exists. NFR-016 M-1 keeps ``versions/`` gapless, so a feature branch that
lands first takes the next free number, which is exactly the one the plan holds. Nothing failed when #2832
took v0108 for ``v0108_location_tent_fields`` while the plan reserved it for ``v0108_privacy_tombstone_copies``:
both would have been "migration 0108" on an installation, and the runner would have recorded the first and
skipped the second for good (#2832 review, SEC-001). The plan moved its migrations to v0109-v0111 (W-27).

The guard reads the reservations from the plan itself, so a renumbering there is followed without an edit here,
and fails when a module in ``app/migrations/versions/`` carries a reserved number under another name. A number
the plan has not reserved is free for anyone; a placeholder such as ``vNNNN_rekey_tombstones`` reserves nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the privacy migration plan is unreachable from here")

PLAN = _REPO_ROOT / "spec" / "privacy" / "09-migrations-and-backfills.md"
VERSIONS = _REPO_ROOT / "src" / "backend" / "app" / "migrations" / "versions"

#: ``Migration `v0108_privacy_tombstone_copies``` - the plan's way of reserving a number for a named migration.
_RESERVATION = re.compile(r"Migration `v(?P<number>\d{4})_(?P<name>[a-z0-9_]+)`")
_MODULE = re.compile(r"^v(?P<number>\d{4})_(?P<name>[a-z0-9_]+)\.py$")


def reservations(text: str) -> dict[str, set[str]]:
    """Reserved number -> the migration names the plan gives it (one, unless the plan contradicts itself)."""
    reserved: dict[str, set[str]] = {}
    for match in _RESERVATION.finditer(text):
        reserved.setdefault(match["number"], set()).add(match["name"])
    return reserved


def collisions(reserved: dict[str, set[str]], module_names: list[str]) -> list[str]:
    """The modules that carry a reserved number under a name the plan does not reserve it for."""
    found: list[str] = []
    for module in sorted(module_names):
        match = _MODULE.match(module)
        if match is None or match["number"] not in reserved:
            continue
        if match["name"] not in reserved[match["number"]]:
            found.append(f"{module} takes v{match['number']}, reserved for {sorted(reserved[match['number']])}")
    return found


def _modules() -> list[str]:
    return [path.name for path in VERSIONS.glob("v*.py")]


def test_the_plan_reserves_numbers_the_parser_can_read() -> None:
    """The measuring tool first: a heading format the regex misses would make every run below vacuously green."""
    reserved = reservations(PLAN.read_text(encoding="utf-8"))

    assert {"0109", "0110", "0111"} <= reserved.keys()
    assert all(len(names) == 1 for names in reserved.values()), reserved


def test_no_migration_takes_a_number_reserved_for_another() -> None:
    reserved = reservations(PLAN.read_text(encoding="utf-8"))

    assert collisions(reserved, _modules()) == []


class TestTheRule:
    """The rule on a fixed plan, so the two outcomes are pinned apart from today's tree."""

    PLAN_TEXT = (
        "**Migration `v0108_privacy_tombstone_copies`** (`kind = privacy_correction`)\n"
        "**Migration `v0109_tenant_record_keeping_default`**\n"
        "(2) Migration `vNNNN_rekey_tombstones`: placeholder\n"
    )

    def test_a_placeholder_reserves_nothing(self) -> None:
        assert reservations(self.PLAN_TEXT).keys() == {"0108", "0109"}

    @pytest.mark.parametrize(
        ("modules", "expected"),
        [
            (["v0108_privacy_tombstone_copies.py"], []),
            (["v0111_location_tent_fields.py"], []),
            (["v0107_care_event_tombstone_performer.py", "__init__.py"], []),
            (
                ["v0108_location_tent_fields.py"],
                ["v0108_location_tent_fields.py takes v0108, reserved for ['privacy_tombstone_copies']"],
            ),
        ],
        ids=["the-reserved-one", "a-free-number", "unreserved-and-not-a-module", "another-name"],
    )
    def test_collisions(self, modules: list[str], expected: list[str]) -> None:
        assert collisions(reservations(self.PLAN_TEXT), modules) == expected
