from pathlib import Path

import psycopg
import structlog
from psycopg_pool import ConnectionPool

logger = structlog.get_logger(__name__)

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"

_TRACKING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""


def ensure_timescale_schema(pool: ConnectionPool) -> None:
    """Run SQL migration files in order. Idempotent via tracking table."""
    migration_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        logger.info("timescale_schema_no_migrations")
        return

    with pool.connection() as conn:
        conn.execute(_TRACKING_TABLE_SQL)
        conn.commit()

        applied = {row[0] for row in conn.execute("SELECT filename FROM schema_migrations").fetchall()}
        conn.commit()

    # Use autocommit connection for DDL that cannot run inside transactions
    # (e.g. TimescaleDB continuous aggregates)
    conninfo = pool.conninfo
    with psycopg.connect(conninfo, autocommit=True) as conn:
        for migration_file in migration_files:
            if migration_file.name in applied:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            logger.info("timescale_migration_apply", filename=migration_file.name)

            # Execute each statement separately (split on semicolons)
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (migration_file.name,),
            )
            logger.info("timescale_migration_applied", filename=migration_file.name)

    logger.info("timescale_schema_ready", total_migrations=len(migration_files))
