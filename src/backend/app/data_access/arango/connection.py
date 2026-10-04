from arango import ArangoClient
from arango.database import StandardDatabase
from arango.exceptions import DatabaseCreateError, DatabasePropertiesError

from app.config.settings import Settings

#: ``ERROR_ARANGO_DATABASE_NOT_FOUND`` — only an account that may see every
#: database (root) is told a database is missing; others get ERR 11.
_DATABASE_NOT_FOUND = 1228
#: ``ERROR_ARANGO_DUPLICATE_NAME`` — another replica created it first.
_DUPLICATE_NAME = 1207
#: ``ERROR_FORBIDDEN`` — HTTP 401/403 for an account without the needed right.
_FORBIDDEN = 11


class ArangoDatabaseAccessError(RuntimeError):
    """The configured account cannot open — or cannot create — the application database (#2126)."""


class ArangoConnection:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: ArangoClient | None = None
        self._db: StandardDatabase | None = None

    def connect(self) -> StandardDatabase:
        """Open the application database with the configured account.

        Asks the database itself first (``GET /_api/database/current``), which an
        application-scoped account with access to that one database may do; only
        a *database not found* answer leads to ``_system`` to create it. Until
        #2126 every connect opened ``_system`` and listed the databases, which
        only root may do — so the application could run as nothing but root.
        """
        if self._db is not None:
            return self._db

        self._client = ArangoClient(hosts=f"http://{self._settings.arangodb_host}:{self._settings.arangodb_port}")
        name = self._settings.arangodb_database
        database = self._client.db(
            name,
            username=self._settings.arangodb_username,
            password=self._settings.arangodb_password,
        )
        try:
            database.properties()
        except DatabasePropertiesError as exc:
            if exc.error_code == _DATABASE_NOT_FOUND:
                self._create_database(self._client, name)
            elif exc.error_code == _FORBIDDEN:
                raise ArangoDatabaseAccessError(
                    f"ArangoDB account {self._settings.arangodb_username!r} (ARANGODB_USERNAME) cannot open the "
                    f"database {name!r}: it does not exist, or the account has no access to it "
                    f"[HTTP {exc.http_code}][ERR {exc.error_code}]. An application-scoped account needs the "
                    "database to exist and 'rw' on it — the Helm chart's arangodb `app-user` container "
                    "provisions both."
                ) from None
            else:
                raise

        self._db = database
        return self._db

    def _create_database(self, client: ArangoClient, name: str) -> None:
        system = client.db(
            "_system",
            username=self._settings.arangodb_username,
            password=self._settings.arangodb_password,
        )
        try:
            system.create_database(name)
        except DatabaseCreateError as exc:
            if exc.error_code == _DUPLICATE_NAME:
                return
            if exc.error_code == _FORBIDDEN:
                raise ArangoDatabaseAccessError(
                    f"ArangoDB database {name!r} does not exist and account "
                    f"{self._settings.arangodb_username!r} (ARANGODB_USERNAME) cannot create it "
                    f"[HTTP {exc.http_code}][ERR {exc.error_code}]. Create the database with an administrative "
                    "account, or let the Helm chart's arangodb `app-user` container provision it."
                ) from None
            raise

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
