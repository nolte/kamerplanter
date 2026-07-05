"""Shared in-memory ArangoDB fakes and migration factories for framework tests.

The fakes mimic just enough of the python-arango collection API for the tracking
layer, the lock and the runner: keyed insert (raising ``DocumentInsertError`` on a
duplicate exactly like the real driver), get/has/delete/replace and ``all()``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from arango.exceptions import (
    DocumentDeleteError,
    DocumentInsertError,
    DocumentReplaceError,
    DocumentRevisionError,
)

from app.migrations.framework.base import Migration
from app.migrations.framework.report import IrreversibleMigrationError, MigrationReport


class FakeCollection:
    """Minimal in-memory document collection.

    Models just enough of the python-arango contract for the lock's fencing:
    every stored document carries a monotonically-bumped ``_rev`` string, and
    ``replace``/``delete`` honour an optional ``_rev`` check (raising
    ``DocumentRevisionError`` on a mismatch) so compare-and-swap takeover and
    fenced release can be exercised deterministically.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._store: dict[str, dict[str, Any]] = {}
        self._rev_seq = 0

    def _next_rev(self) -> str:
        self._rev_seq += 1
        return str(self._rev_seq)

    def insert(self, doc: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        key = doc["_key"]
        if key in self._store and not overwrite:
            # Match the real driver: a duplicate _key raises DocumentInsertError.
            raise DocumentInsertError.__new__(DocumentInsertError)
        stored = dict(doc)
        stored["_rev"] = self._next_rev()
        self._store[key] = stored
        return {"_key": key, "_rev": stored["_rev"]}

    def get(self, key: str) -> dict[str, Any] | None:
        doc = self._store.get(key)
        return dict(doc) if doc is not None else None

    def has(self, key: str) -> bool:
        return key in self._store

    def delete(self, document: str | dict[str, Any], check_rev: bool = True) -> None:
        key = document if isinstance(document, str) else document["_key"]
        if key not in self._store:
            raise DocumentDeleteError.__new__(DocumentDeleteError)
        rev = document.get("_rev") if isinstance(document, dict) else None
        if check_rev and rev is not None and self._store[key]["_rev"] != rev:
            raise DocumentRevisionError.__new__(DocumentRevisionError)
        self._store.pop(key, None)

    def replace(self, doc: dict[str, Any], check_rev: bool = True) -> None:
        key = doc["_key"]
        if key not in self._store:
            raise DocumentReplaceError.__new__(DocumentReplaceError)
        if check_rev and doc.get("_rev") is not None and self._store[key]["_rev"] != doc["_rev"]:
            raise DocumentRevisionError.__new__(DocumentRevisionError)
        stored = {k: v for k, v in doc.items() if k != "_rev"}
        stored["_rev"] = self._next_rev()
        self._store[key] = stored

    def all(self) -> list[dict[str, Any]]:
        return [dict(doc) for doc in self._store.values()]


class FakeDatabase:
    """Minimal in-memory database exposing ``collection``/``has_collection``."""

    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def collection(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection(name)
        return self._collections[name]

    def has_collection(self, name: str) -> bool:
        return name in self._collections

    def create_collection(self, name: str, edge: bool = False) -> FakeCollection:
        self._collections[name] = FakeCollection(name)
        return self._collections[name]


class RecordingMigration(Migration):
    """A configurable fake migration that records its up/down invocations."""

    def __init__(
        self,
        version: str,
        *,
        name: str | None = None,
        reversible: bool = False,
        up_changed: int = 0,
        checksum_override: str | None = None,
        precondition_unmet: bool = False,
    ) -> None:
        self.version = version
        self.name = name or f"migration_{version}"
        self.reversible = reversible
        self._up_changed = up_changed
        self._checksum_override = checksum_override
        self._precondition_unmet = precondition_unmet
        self.up_calls: list[bool] = []
        self.down_calls: list[bool] = []

    def up(self, db: Any, *, dry_run: bool = False) -> MigrationReport:
        self.up_calls.append(dry_run)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=1,
            changed=self._up_changed,
            dry_run=dry_run,
            precondition_unmet=self._precondition_unmet and not dry_run,
        )

    def down(self, db: Any, *, dry_run: bool = False) -> MigrationReport:
        if not self.reversible:
            raise IrreversibleMigrationError(f"{self.version} is not reversible")
        self.down_calls.append(dry_run)
        return MigrationReport(version=self.version, name=self.name, dry_run=dry_run)

    def checksum(self) -> str:
        if self._checksum_override is not None:
            return self._checksum_override
        return super().checksum()


@pytest.fixture
def fake_db() -> FakeDatabase:
    return FakeDatabase()


@pytest.fixture
def make_migration() -> Callable[..., RecordingMigration]:
    def _factory(version: str, **kwargs: Any) -> RecordingMigration:
        return RecordingMigration(version, **kwargs)

    return _factory
