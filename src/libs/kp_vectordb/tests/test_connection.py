"""Tests for the shared VectorDbConnection pool wrapper (no real database)."""

from typing import Any

from kp_vectordb import VectorDbConfig, VectorDbConnection
from kp_vectordb import connection as connection_module


class _FakePool:
    def __init__(self, *, conninfo: str, min_size: int, max_size: int, open: bool) -> None:
        self.conninfo = conninfo
        self.min_size = min_size
        self.max_size = max_size
        self.opened = open
        self.closed = False

    def close(self) -> None:
        self.closed = True


def _config() -> VectorDbConfig:
    return VectorDbConfig(
        host="db",
        port=5433,
        database="vec",
        username="user",
        password="secret",
        pool_min_size=2,
        pool_max_size=7,
    )


def _patch_pool(monkeypatch: Any) -> None:
    monkeypatch.setattr(connection_module, "ConnectionPool", _FakePool)


def test_connect_builds_conninfo_from_config(monkeypatch: Any) -> None:
    _patch_pool(monkeypatch)
    conn = VectorDbConnection(_config())

    pool = conn.connect()

    assert "host=db" in pool.conninfo
    assert "port=5433" in pool.conninfo
    assert "dbname=vec" in pool.conninfo
    assert "user=user" in pool.conninfo
    assert "password=secret" in pool.conninfo
    assert pool.min_size == 2
    assert pool.max_size == 7
    assert pool.opened is True


def test_connect_is_idempotent(monkeypatch: Any) -> None:
    _patch_pool(monkeypatch)
    conn = VectorDbConnection(_config())

    first = conn.connect()
    second = conn.connect()

    assert first is second


def test_close_resets_pool(monkeypatch: Any) -> None:
    _patch_pool(monkeypatch)
    conn = VectorDbConnection(_config())
    pool = conn.connect()

    conn.close()

    assert pool.closed is True
    assert conn.is_connected() is False


def test_is_connected_false_before_connect() -> None:
    conn = VectorDbConnection(_config())
    assert conn.is_connected() is False
