"""spec/privacy PRIV-206 — the shared tombstone count binds everything and walks nested fields two deep."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.tombstone_census import ArangoTombstoneCensus, count_tombstones_by_field

PATTERN = "^anon_[0-9a-f]{16}$|^anon2_[0-9a-f]{16}$"


def _db(counts: list[int], *, missing: frozenset[str] = frozenset()) -> MagicMock:
    db = MagicMock()
    db.has_collection.side_effect = lambda name: name not in missing
    db.aql.execute.side_effect = [iter([n]) for n in counts]
    return db


def test_every_value_is_a_bind_parameter() -> None:
    db = _db([3])

    assert count_tombstones_by_field(db, [("tasks", "assigned_to_user_key")], PATTERN) == {
        "tasks.assigned_to_user_key": 3
    }
    query = db.aql.execute.call_args.args[0]
    binds = db.aql.execute.call_args.kwargs["bind_vars"]
    assert "tasks" not in query and "assigned_to_user_key" not in query and "anon" not in query
    assert binds == {"@collection": "tasks", "a": "assigned_to_user_key", "pattern": PATTERN}


def test_a_nested_field_is_two_bound_segments() -> None:
    db = _db([0])

    count_tombstones_by_field(db, [("sites", "plan.plan_updated_by")], PATTERN)

    binds = db.aql.execute.call_args.kwargs["bind_vars"]
    assert (binds["a"], binds["b"]) == ("plan", "plan_updated_by")


def test_a_missing_collection_counts_zero_without_a_query() -> None:
    db = _db([], missing=frozenset({"ai_audit_log"}))

    assert ArangoTombstoneCensus(db).count_tombstones([("ai_audit_log", "user_key")], PATTERN) == {
        "ai_audit_log.user_key": 0
    }
    db.aql.execute.assert_not_called()


@pytest.mark.parametrize("field", ["", "a.b.c", ".a", "a."])
def test_a_malformed_field_is_refused(field: str) -> None:
    with pytest.raises(ValueError):
        count_tombstones_by_field(_db([]), [("tasks", field)], PATTERN)
