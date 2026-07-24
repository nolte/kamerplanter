"""VectorDB schema migration runner (shared kp_vectordb infrastructure)."""

import re
from pathlib import Path

import psycopg
import structlog
from psycopg_pool import ConnectionPool

logger = structlog.get_logger(__name__)

_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def run_migrations(
    pool: ConnectionPool,
    migrations_dir: Path,
    *,
    migrations_table: str = "schema_migrations",
) -> None:
    """Run SQL migration files in order. Idempotent via a tracking table.

    ``migrations_dir`` is the service-owned directory of ``NNN_*.sql`` files;
    ``migrations_table`` names the per-service tracking table. The table name is
    validated as a plain SQL identifier because it is interpolated into the
    DDL/DML below — it never originates from user input, but the guard keeps the
    surface injection-proof.
    """
    if not _IDENTIFIER_RE.match(migrations_table):
        raise ValueError(f"invalid migrations_table identifier: {migrations_table!r}")

    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        logger.info("vectordb_schema_no_migrations")
        return

    tracking_table_sql = (
        f"CREATE TABLE IF NOT EXISTS {migrations_table} ("
        "filename VARCHAR(255) PRIMARY KEY, "
        "applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
    )

    with pool.connection() as conn:
        conn.execute(tracking_table_sql)
        conn.commit()

        applied = {row[0] for row in conn.execute(f"SELECT filename FROM {migrations_table}").fetchall()}
        conn.commit()

    # ``ConnectionPool.conninfo`` is typed ``str | Callable[[], str]``; resolve a
    # factory to its connection string so ``psycopg.connect`` receives a plain str.
    conninfo = pool.conninfo
    if callable(conninfo):
        conninfo = conninfo()
    with psycopg.connect(conninfo, autocommit=True) as conn:
        for migration_file in migration_files:
            if migration_file.name in applied:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            logger.info("vectordb_migration_apply", filename=migration_file.name)

            # Strip SQL comments before splitting to avoid executing comment text.
            lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
            clean_sql = "\n".join(lines)
            for statement in clean_sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

            conn.execute(
                f"INSERT INTO {migrations_table} (filename) VALUES (%s)",
                (migration_file.name,),
            )
            logger.info("vectordb_migration_applied", filename=migration_file.name)

    logger.info("vectordb_schema_ready", total_migrations=len(migration_files))
