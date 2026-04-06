import structlog
from psycopg_pool import ConnectionPool

from app.config.settings import Settings

logger = structlog.get_logger(__name__)


class TimescaleConnection:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: ConnectionPool | None = None

    def connect(self) -> ConnectionPool:
        if self._pool is not None:
            return self._pool

        conninfo = (
            f"host={self._settings.timescaledb_host} "
            f"port={self._settings.timescaledb_port} "
            f"dbname={self._settings.timescaledb_database} "
            f"user={self._settings.timescaledb_username} "
            f"password={self._settings.timescaledb_password}"
        )

        self._pool = ConnectionPool(
            conninfo=conninfo,
            min_size=self._settings.timescaledb_pool_min_size,
            max_size=self._settings.timescaledb_pool_max_size,
            open=True,
        )

        logger.info(
            "timescaledb_connected",
            host=self._settings.timescaledb_host,
            port=self._settings.timescaledb_port,
            database=self._settings.timescaledb_database,
        )
        return self._pool

    @property
    def pool(self) -> ConnectionPool:
        if self._pool is None:
            return self.connect()
        return self._pool

    def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            self._pool = None
            logger.info("timescaledb_disconnected")

    def is_connected(self) -> bool:
        if self._pool is None:
            return False
        try:
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
