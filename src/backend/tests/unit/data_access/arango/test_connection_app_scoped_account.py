"""#2126 — the backend connects with an account that has access to its own database only.

Before #2126 :meth:`ArangoConnection.connect` always opened ``_system`` and asked
``has_database`` first. Listing databases needs access to ``_system``, so an
application-scoped account — ``rw`` on ``kamerplanter`` and nothing else —
could not even start. Measured 2026-10-04 against ArangoDB 3.12.12 with such an
account::

    DatabaseListError 401 11 [HTTP 401][ERR 11] No read access to database.

Root was therefore the only account the code could run under. The connection now
asks the target database itself (``GET /_api/database/current``) and only goes to
``_system`` when the server answers *database not found* (``ERR 1228``, which
only an account allowed to see every database — root — receives). The responses
the doubles below give are the measured ones:

======================  ==============  ==================================
account                 database        ``/_api/database/current``
======================  ==============  ==================================
root                    exists          200
root                    missing         404, ERR 1228 *database not found*
app-scoped              its own         200
app-scoped              missing         401, ERR 11 *not authorized*
app-scoped              another         401, ERR 11 *No read access*
======================  ==============  ==================================

The real server is exercised by ``tests/integration/test_arango_app_scoped_account.py``.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from arango.exceptions import DatabaseCreateError, DatabasePropertiesError
from arango.request import Request
from arango.response import Response

from app.config.settings import Settings
from app.data_access.arango import connection as connection_module
from app.data_access.arango.connection import ArangoConnection, ArangoDatabaseAccessError

pytestmark = pytest.mark.allow_db_connection("connects a test double of ArangoClient, never a server")

# Built at run time so no credential-shaped literal sits in the source.
_PASSWORD = "-".join(("app", "scoped", "test", "value"))


def _server_error(error_type: type[Exception], status: int, error_num: int, message: str) -> Exception:
    response = Response("get", "http://arangodb:8529/_api/database/current", {}, status, message, "")
    response.error_code = error_num
    response.error_message = message
    return error_type(response, Request("get", "/_api/database/current"))


class _FakeClient:
    """ArangoClient double: records which databases were opened, with what account."""

    def __init__(self, target: MagicMock, system: MagicMock) -> None:
        self.opened: list[tuple[str, str]] = []
        self._handles = {"_system": system}
        self._target = target

    def db(self, name: str, username: str, password: str, **_: Any) -> MagicMock:
        assert password == _PASSWORD, "the configured password is passed through unchanged"
        self.opened.append((name, username))
        return self._handles.get(name, self._target)

    def close(self) -> None:  # pragma: no cover - not exercised here
        pass


def _connect(monkeypatch: pytest.MonkeyPatch, target: MagicMock, system: MagicMock, *, user: str) -> tuple[Any, Any]:
    client = _FakeClient(target, system)
    monkeypatch.setattr(connection_module, "ArangoClient", lambda **_: client)
    settings = Settings(
        arangodb_host="arangodb",
        arangodb_database="kamerplanter",
        arangodb_username=user,
        arangodb_password=_PASSWORD,
    )
    return ArangoConnection(settings), client


def test_an_app_scoped_account_never_opens_system_when_its_database_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    target, system = MagicMock(name="kamerplanter"), MagicMock(name="_system")
    target.properties.return_value = {"name": "kamerplanter"}
    conn, client = _connect(monkeypatch, target, system, user="kamerplanter")

    assert conn.connect() is target
    assert client.opened == [("kamerplanter", "kamerplanter")], "no `_system` handle for an existing database"
    system.has_database.assert_not_called()
    system.create_database.assert_not_called()


def test_a_missing_database_is_created_through_system_when_the_account_may(monkeypatch: pytest.MonkeyPatch) -> None:
    target, system = MagicMock(name="kamerplanter"), MagicMock(name="_system")
    target.properties.side_effect = _server_error(DatabasePropertiesError, 404, 1228, "database not found")
    conn, client = _connect(monkeypatch, target, system, user="root")

    assert conn.connect() is target
    system.create_database.assert_called_once_with("kamerplanter")
    assert ("_system", "root") in client.opened


def test_a_concurrent_create_of_the_same_database_is_not_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two replicas on a fresh volume both see 1228; the slower create meets ERR 1207 (duplicate name)."""
    target, system = MagicMock(name="kamerplanter"), MagicMock(name="_system")
    target.properties.side_effect = _server_error(DatabasePropertiesError, 404, 1228, "database not found")
    system.create_database.side_effect = _server_error(DatabaseCreateError, 409, 1207, "duplicate database name")
    conn, _ = _connect(monkeypatch, target, system, user="root")

    assert conn.connect() is target


@pytest.mark.parametrize(
    "message",
    ["not authorized to execute this request", "No read access to database."],
    ids=["database-missing", "no-grant"],
)
def test_an_account_without_access_fails_with_a_message_that_names_the_fix(
    monkeypatch: pytest.MonkeyPatch, message: str
) -> None:
    target, system = MagicMock(name="kamerplanter"), MagicMock(name="_system")
    target.properties.side_effect = _server_error(DatabasePropertiesError, 401, 11, message)
    conn, client = _connect(monkeypatch, target, system, user="kamerplanter")

    with pytest.raises(ArangoDatabaseAccessError) as excinfo:
        conn.connect()

    text = str(excinfo.value)
    assert "'kamerplanter'" in text and "ARANGODB_USERNAME" in text
    assert _PASSWORD not in text, "the error never carries the password"
    system.create_database.assert_not_called()
    assert ("_system", "kamerplanter") not in client.opened
    assert conn.is_connected() is False


def test_a_refused_create_names_the_missing_right(monkeypatch: pytest.MonkeyPatch) -> None:
    target, system = MagicMock(name="kamerplanter"), MagicMock(name="_system")
    target.properties.side_effect = _server_error(DatabasePropertiesError, 404, 1228, "database not found")
    system.create_database.side_effect = _server_error(DatabaseCreateError, 401, 11, "not authorized")
    conn, _ = _connect(monkeypatch, target, system, user="root")

    with pytest.raises(ArangoDatabaseAccessError, match="cannot create it"):
        conn.connect()


def test_any_other_server_error_propagates_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    target, system = MagicMock(name="kamerplanter"), MagicMock(name="_system")
    boom = _server_error(DatabasePropertiesError, 503, 503, "service unavailable")
    target.properties.side_effect = boom
    conn, _ = _connect(monkeypatch, target, system, user="kamerplanter")

    with pytest.raises(DatabasePropertiesError) as excinfo:
        conn.connect()
    assert excinfo.value is boom
