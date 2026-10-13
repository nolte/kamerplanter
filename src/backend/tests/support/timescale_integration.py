"""The TimescaleDB connection contract of the integration tier (#1793).

Mirrors :mod:`tests.support.arango_integration`: one address, one probe, and
run-scoped database names so two sessions on one server cannot drop each other's
database. The variable names are ``Settings``' own (``env_prefix: ""``), so the
tier and a real ``Settings(...)`` point at the same server.

Defaults match ``docker-compose.yml``'s ``timescaledb`` profile, so a developer
who ran ``docker compose --profile timescaledb up -d`` needs no environment.
"""

from __future__ import annotations

import os
from functools import cache

import psycopg
from psycopg import sql
from psycopg_pool import ConnectionPool

from tests.support.arango_integration import (
    belongs_to_this_run,
    is_stale_run_database,
    run_database_name,
)

TIMESCALE_HOST = os.environ.get("TIMESCALEDB_HOST", "localhost")
TIMESCALE_PORT = os.environ.get("TIMESCALEDB_PORT", "5432")
TIMESCALE_USERNAME = os.environ.get("TIMESCALEDB_USERNAME", "postgres")
TIMESCALE_PASSWORD = os.environ.get("TIMESCALEDB_PASSWORD", "changeme")

#: The maintenance database every probe and every CREATE/DROP DATABASE runs on.
MAINTENANCE_DATABASE = "postgres"


def conninfo(database: str) -> str:
    """A libpq connection string for *database* on the tier's server."""
    return (
        f"host={TIMESCALE_HOST} port={TIMESCALE_PORT} dbname={database} "
        f"user={TIMESCALE_USERNAME} password={TIMESCALE_PASSWORD}"
    )


def connection_address() -> str:
    """The address and user the tier connects as, for a failure message."""
    return f"{TIMESCALE_HOST}:{TIMESCALE_PORT} (user {TIMESCALE_USERNAME!r})"


@cache
def probe_failure() -> str | None:
    """Why TimescaleDB is unreachable (or lacks the extension), ``None`` when it answers."""
    try:
        with psycopg.connect(conninfo(MAINTENANCE_DATABASE), connect_timeout=5) as conn:
            row = conn.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'").fetchone()
    except Exception as exc:  # noqa: BLE001 - any failure means "this module cannot run"
        return f"{type(exc).__name__}: {exc}"
    if row is None:
        return "the server answers but offers no timescaledb extension (plain PostgreSQL?)"
    return None


def provision_database(base: str) -> str:
    """Create a run-scoped database with the extension installed; return its name."""
    name = run_database_name(base)
    with psycopg.connect(conninfo(MAINTENANCE_DATABASE), autocommit=True) as conn:
        conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    with psycopg.connect(conninfo(name), autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    return name


def drop_databases(select) -> list[str]:  # type: ignore[no-untyped-def]
    """Drop every run-scoped database *select* accepts; return the names dropped."""
    dropped = []
    with psycopg.connect(conninfo(MAINTENANCE_DATABASE), autocommit=True) as conn:
        names = [row[0] for row in conn.execute("SELECT datname FROM pg_database").fetchall()]
        for name in sorted(names):
            if select(name):
                conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))
                dropped.append(name)
    return dropped


def drop_this_runs_databases() -> list[str]:
    return drop_databases(belongs_to_this_run)


def drop_stale_databases() -> list[str]:
    return drop_databases(is_stale_run_database)


def open_pool(database: str) -> ConnectionPool:
    return ConnectionPool(conninfo(database), min_size=1, max_size=4, open=True)
