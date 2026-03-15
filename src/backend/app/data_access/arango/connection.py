from typing import TYPE_CHECKING

from arango import ArangoClient

if TYPE_CHECKING:
    from arango.database import StandardDatabase

    from app.config.settings import Settings


class ArangoConnection:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: ArangoClient | None = None
        self._db: StandardDatabase | None = None

    def connect(self) -> StandardDatabase:
        if self._db is not None:
            return self._db

        self._client = ArangoClient(hosts=f"http://{self._settings.arangodb_host}:{self._settings.arangodb_port}")

        sys_db = self._client.db(
            "_system",
            username=self._settings.arangodb_username,
            password=self._settings.arangodb_password,
        )

        if not sys_db.has_database(self._settings.arangodb_database):
            sys_db.create_database(self._settings.arangodb_database)

        self._db = self._client.db(
            self._settings.arangodb_database,
            username=self._settings.arangodb_username,
            password=self._settings.arangodb_password,
        )
        return self._db

    @property
    def db(self) -> StandardDatabase:
        if self._db is None:
            return self.connect()
        return self._db

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None

    def is_connected(self) -> bool:
        if self._db is None:
            return False
        try:
            self._db.version()
            return True
        except Exception:
            return False
