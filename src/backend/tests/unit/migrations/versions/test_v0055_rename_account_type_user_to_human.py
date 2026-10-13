"""v0055 rewrites the stored ``account_type`` to the value REQ-023 declares (#1620).

What this tier decides: the classification (which row is rewritten, which is left
alone), that ``dry_run`` writes nothing, that a re-run is a no-op, and that the
scan is parametrised on the old value rather than interpolating it.

What it does not decide: whether ``HAS(u, "account_type")`` is false for a document
that was inserted without the attribute. That is a property of ArangoDB, and
``tests/integration/test_v0055_rename_account_type_user_to_human.py`` measures it
against a real server.

The AQL double answers this migration's two queries and refuses anything else —
including a scan that has grown a filter on ``"service"`` written as "everything
but", which would silently absorb an unknown third value. A double that returned
``[]`` for an unknown query would make the idempotence assertion pass vacuously.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from app.migrations.versions.v0055_rename_account_type_user_to_human import (
    NEW_VALUE,
    OLD_VALUE,
    RenameAccountTypeUserToHumanMigration,
)

_USERS = "users"

_OLD_DEFAULT = "u_stored_as_user"
_PRE_FIELD = "u_without_attribute"
_SERVICE = "u_service"
_ALREADY_HUMAN = "u_already_human"

_MUST_REWRITE = [_OLD_DEFAULT, _PRE_FIELD]
_MUST_KEEP = [_SERVICE, _ALREADY_HUMAN]


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.updates: list[dict[str, Any]] = []

    def update(self, patch: dict[str, Any], **kwargs: Any) -> None:  # noqa: ARG002
        self.updates.append(dict(patch))
        doc = self.docs[patch["_key"]]
        for name, value in patch.items():
            if name != "_key":
                doc[name] = value


class _Aql:
    def __init__(self, users: _Collection) -> None:
        self._users = users

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[Any]:  # noqa: ARG002
        normalised = re.sub(r"\s+", " ", query).strip()
        if normalised == f"RETURN LENGTH({_USERS})":
            return [len(self._users.docs)]
        if f"FOR u IN {_USERS}" not in normalised or 'HAS(u, "account_type")' not in normalised:
            raise AssertionError(f"unexpected query, this double cannot answer it: {normalised!r}")
        if '"service"' in normalised or "'service'" in normalised:
            raise AssertionError(
                "the scan names 'service'. The population is the two shapes that mean "
                "'not a service account', not 'everything that is not service'."
            )
        assert bind_vars == {"old": OLD_VALUE}, f"unexpected bind vars: {bind_vars!r}"
        return [
            key
            for key, doc in self._users.docs.items()
            if doc.get("account_type") == OLD_VALUE or "account_type" not in doc
        ]


class _Db:
    def __init__(self, docs: dict[str, dict[str, Any]], *, has_users: bool = True) -> None:
        self._col = _Collection(docs)
        self.aql = _Aql(self._col)
        self._has_users = has_users

    def has_collection(self, name: str) -> bool:
        return name == _USERS and self._has_users

    def collection(self, name: str) -> _Collection:
        assert name == _USERS
        return self._col

    def stored(self, key: str) -> dict[str, Any]:
        return self._col.docs[key]

    @property
    def updates(self) -> list[dict[str, Any]]:
        return self._col.updates


def _seeded() -> _Db:
    return _Db(
        {
            _OLD_DEFAULT: {"email": "erika@example.org", "account_type": OLD_VALUE, "is_active": True},
            _PRE_FIELD: {"email": "april@example.org", "is_active": True},
            _SERVICE: {"email": "bot@example.org", "account_type": "service", "is_active": True},
            _ALREADY_HUMAN: {"email": "done@example.org", "account_type": NEW_VALUE, "is_active": True},
        }
    )


class TestTheRewrite:
    @pytest.mark.parametrize("key", _MUST_REWRITE)
    def test_both_not_a_service_account_shapes_become_human(self, key: str) -> None:
        db = _seeded()

        RenameAccountTypeUserToHumanMigration().up(db)

        assert db.stored(key)["account_type"] == NEW_VALUE

    @pytest.mark.parametrize("key", _MUST_KEEP)
    def test_a_service_account_and_an_already_rewritten_row_are_not_touched(self, key: str) -> None:
        db = _seeded()
        before = dict(db.stored(key))

        RenameAccountTypeUserToHumanMigration().up(db)

        assert db.stored(key) == before
        assert all(patch["_key"] != key for patch in db.updates)

    def test_it_reports_exactly_the_rows_it_rewrote(self) -> None:
        report = RenameAccountTypeUserToHumanMigration().up(_seeded())

        assert sorted(report.details["keys"]) == sorted(_MUST_REWRITE)
        assert report.changed == len(_MUST_REWRITE)
        assert report.scanned == 4

    def test_the_other_fields_survive(self) -> None:
        db = _seeded()

        RenameAccountTypeUserToHumanMigration().up(db)

        assert db.stored(_OLD_DEFAULT)["email"] == "erika@example.org"
        assert db.stored(_OLD_DEFAULT)["is_active"] is True


class TestTheRunItself:
    def test_a_dry_run_writes_nothing_and_reports_the_same_plan(self) -> None:
        db = _seeded()

        dry = RenameAccountTypeUserToHumanMigration().up(db, dry_run=True)

        assert sorted(dry.details["keys"]) == sorted(_MUST_REWRITE)
        assert dry.changed == 0
        assert db.updates == []
        assert db.stored(_OLD_DEFAULT)["account_type"] == OLD_VALUE

    def test_it_is_idempotent(self) -> None:
        db = _seeded()
        migration = RenameAccountTypeUserToHumanMigration()
        migration.up(db)

        second = migration.up(db)

        assert second.changed == 0, "the migration rediscovered its own output"
        assert second.details["keys"] == []

    def test_a_database_without_the_collection_is_a_noop(self) -> None:
        report = RenameAccountTypeUserToHumanMigration().up(_Db({}, has_users=False))

        assert (report.scanned, report.changed) == (0, 0)

    def test_it_is_not_reversible(self) -> None:
        from app.migrations.framework.report import IrreversibleMigrationError

        migration = RenameAccountTypeUserToHumanMigration()
        assert migration.reversible is False
        with pytest.raises(IrreversibleMigrationError):
            migration.down(_seeded())
