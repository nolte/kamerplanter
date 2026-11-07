"""GP-NFR-004 / GP-NFR-072: the migration chain of the garden-plan backup (WP 8.28, #2671)."""

from __future__ import annotations

from typing import Any

import pytest

from app.domain.engines.plan_schema_migration import migrate, readable_versions, required_predecessors


def _step(to: str):
    def lift(document: dict[str, Any]) -> dict[str, Any]:
        return {**document, "schema_version": to, "trail": [*document.get("trail", []), to]}

    return lift


class TestTheChain:
    def test_a_file_two_versions_old_runs_both_migrators_in_order(self) -> None:
        migrated = migrate({"schema_version": "1"}, "3", {"1": _step("2"), "2": _step("3")})

        assert migrated == {"schema_version": "3", "trail": ["2", "3"]}

    def test_the_current_version_is_returned_unchanged(self) -> None:
        document = {"schema_version": "3"}

        assert migrate(document, "3", {"1": _step("2"), "2": _step("3")}) is document

    def test_a_gap_in_the_chain_makes_the_older_versions_unreadable(self) -> None:
        migrators = {"1": _step("2"), "3": _step("4")}  # no "2"

        assert readable_versions("4", migrators) == ["3", "4"]
        with pytest.raises(ValueError):
            migrate({"schema_version": "1"}, "4", migrators)

    def test_a_migrator_that_skips_a_version_is_refused(self) -> None:
        with pytest.raises(ValueError, match="must produce '2'"):
            migrate({"schema_version": "1"}, "3", {"1": _step("3"), "2": _step("3")})

    def test_today_only_version_1_exists_and_it_is_readable(self) -> None:
        assert readable_versions() == ["1"]
        assert migrate({"schema_version": "1", "x": 1}) == {"schema_version": "1", "x": 1}


@pytest.mark.parametrize(
    ("current", "required"),
    [("1", []), ("2", ["1"]), ("3", ["1", "2"]), ("7", ["5", "6"])],
)
def test_the_two_versions_before_the_current_one_are_required(current: str, required: list[str]) -> None:
    assert required_predecessors(current) == required
