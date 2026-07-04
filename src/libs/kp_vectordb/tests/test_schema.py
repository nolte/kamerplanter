"""Tests for the shared migration runner (no real database)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from kp_vectordb import run_migrations
from kp_vectordb import schema as schema_module


class _FakeCursor:
    def __init__(self, rows: list[tuple[str, ...]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[tuple[str, ...]]:
        return self._rows


class _FakeConn:
    """Records every executed statement; returns configured rows for SELECT."""

    def __init__(self, applied_rows: list[tuple[str, ...]] | None = None) -> None:
        self.executed: list[tuple[str, Any]] = []
        self._applied_rows = applied_rows or []

    def execute(self, sql: str, params: Any = None) -> _FakeCursor:
        self.executed.append((sql, params))
        if sql.strip().upper().startswith("SELECT"):
            return _FakeCursor(list(self._applied_rows))
        return _FakeCursor([])

    def commit(self) -> None:
        pass

    def __enter__(self) -> _FakeConn:
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


class _FakePool:
    def __init__(self, conn: _FakeConn, conninfo: str = "host=x") -> None:
        self._conn = conn
        self.conninfo = conninfo

    def connection(self) -> _FakeConn:
        return self._conn


def test_invalid_table_identifier_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid migrations_table"):
        run_migrations(object(), Path("/does-not-matter"), migrations_table="bad; DROP TABLE x")


def test_empty_migrations_dir_is_noop(tmp_path: Path) -> None:
    # Valid identifier + no *.sql files → returns before touching the pool.
    run_migrations(object(), tmp_path)  # object() has no .connection() and must stay untouched


def test_applies_pending_migrations_and_records_them(tmp_path: Path, monkeypatch: Any) -> None:
    (tmp_path / "001_init.sql").write_text(
        "-- leading comment\nCREATE TABLE foo (id int);\nINSERT INTO foo VALUES (1);\n",
        encoding="utf-8",
    )
    (tmp_path / "002_more.sql").write_text("CREATE TABLE bar (id int);\n", encoding="utf-8")

    # 002 is already recorded → must be skipped; 001 is pending.
    tracking_conn = _FakeConn(applied_rows=[("002_more.sql",)])
    pool = _FakePool(tracking_conn)

    migrate_conn = _FakeConn()
    monkeypatch.setattr(schema_module.psycopg, "connect", lambda *a, **k: migrate_conn)

    run_migrations(pool, tmp_path, migrations_table="inference_schema_migrations")

    # Tracking table + SELECT use the custom table name.
    assert any("inference_schema_migrations" in sql for sql, _ in tracking_conn.executed)

    migrate_stmts = [sql for sql, _ in migrate_conn.executed]
    # Pending 001 applied ...
    assert any("CREATE TABLE foo" in s for s in migrate_stmts)
    assert any("INSERT INTO foo" in s for s in migrate_stmts)
    # ... already-applied 002 skipped ...
    assert all("CREATE TABLE bar" not in s for s in migrate_stmts)
    # ... comment lines never executed as statements ...
    assert all(not s.strip().startswith("--") for s in migrate_stmts)
    # ... and 001 recorded into the tracking table with its filename bound as a parameter.
    inserts = [
        (sql, params) for sql, params in migrate_conn.executed if "INSERT INTO inference_schema_migrations" in sql
    ]
    assert inserts
    assert inserts[0][1] == ("001_init.sql",)


def test_default_tracking_table_name(tmp_path: Path, monkeypatch: Any) -> None:
    (tmp_path / "001_init.sql").write_text("CREATE TABLE foo (id int);\n", encoding="utf-8")
    tracking_conn = _FakeConn()
    pool = _FakePool(tracking_conn)
    migrate_conn = _FakeConn()
    monkeypatch.setattr(schema_module.psycopg, "connect", lambda *a, **k: migrate_conn)

    run_migrations(pool, tmp_path)

    assert any("schema_migrations" in sql for sql, _ in tracking_conn.executed)
