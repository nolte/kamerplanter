"""VectorDB connection pool management."""

import structlog
from psycopg_pool import ConnectionPool

from app.config import Settings

logger = structlog.get_logger(__name__)


class VectorDbConnection:
    """Manages a psycopg connection pool to the pgvector database."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: ConnectionPool | None = None

    def connect(self) -> ConnectionPool:
        """Create and open the connection pool. Returns the pool."""
        if self._pool is not None:
            return self._pool

        conninfo = (
            f"host={self._settings.vectordb_host} "
            f"port={self._settings.vectordb_port} "
            f"dbname={self._settings.vectordb_database} "
            f"user={self._settings.vectordb_username} "
            f"password={self._settings.vectordb_password}"
        )

        self._pool = ConnectionPool(
            conninfo=conninfo,
            min_size=self._settings.vectordb_pool_min_size,
            max_size=self._settings.vectordb_pool_max_size,
            open=True,
        )

        logger.info(
            "vectordb_connected",
            host=self._settings.vectordb_host,
            port=self._settings.vectordb_port,
            database=self._settings.vectordb_database,
        )
        return self._pool

    @property
    def pool(self) -> ConnectionPool:
        """Return the pool, connecting lazily if needed."""
        if self._pool is None:
            return self.connect()
        return self._pool

    def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            logger.info("vectordb_disconnected")

    def is_connected(self) -> bool:
        """Check if the pool is alive with a simple SELECT 1."""
        if self._pool is None:
            return False
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
