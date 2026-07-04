"""VectorDB connection pool management (shared kp_vectordb infrastructure)."""

import structlog
from psycopg_pool import ConnectionPool

from .config import VectorDbConfig

logger = structlog.get_logger(__name__)


class VectorDbConnection:
    """Manages a psycopg connection pool to the pgvector database."""

    def __init__(self, config: VectorDbConfig) -> None:
        self._config = config
        self._pool: ConnectionPool | None = None

    def connect(self) -> ConnectionPool:
        """Create and open the connection pool. Returns the pool."""
        if self._pool is not None:
            return self._pool

        conninfo = (
            f"host={self._config.host} "
            f"port={self._config.port} "
            f"dbname={self._config.database} "
            f"user={self._config.username} "
            f"password={self._config.password}"
        )

        self._pool = ConnectionPool(
            conninfo=conninfo,
            min_size=self._config.pool_min_size,
            max_size=self._config.pool_max_size,
            open=True,
        )

        logger.info(
            "vectordb_connected",
            host=self._config.host,
            port=self._config.port,
            database=self._config.database,
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
