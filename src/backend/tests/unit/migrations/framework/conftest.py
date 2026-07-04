"""Shared in-memory ArangoDB fakes and migration factories for framework tests.

The fakes mimic just enough of the python-arango collection API for the tracking
layer, the lock and the runner: keyed insert (raising ``DocumentInsertError`` on a
duplicate exactly like the real driver), get/has/delete/replace and ``all()``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from arango.exceptions import DocumentInsertError

from app.migrations.framework.base import Migration
from app.migrations.framework.report import IrreversibleMigrationError, MigrationReport


class FakeCollection:
    """Minimal in-memory document collection."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._store: dict[str, dict[str, Any]] = {}

    def insert(self, doc: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        key = doc["_key"]
        if key in self._store and not overwrite:
            # Match the real driver: a duplicate _key raises DocumentInsertError.
            raise DocumentInsertError.__new__(DocumentInsertError)
        self._store[key] = dict(doc)
        return {"_key": key}

    def get(self, key: str) -> dict[str, Any] | None:
        doc = self._store.get(key)
        return dict(doc) if doc is not None else None

    def has(self, key: str) -> bool:
        return key in self._store

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def replace(self, doc: dict[str, Any]) -> None:
        self._store[doc["_key"]] = dict(doc)

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
    ) -> None:
        self.version = version
        self.name = name or f"migration_{version}"
        self.reversible = reversible
        self._up_changed = up_changed
        self._checksum_override = checksum_override
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
