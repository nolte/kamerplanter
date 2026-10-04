"""#2126 — the application starts under an account scoped to its own database.

The Helm chart's arangodb ``app-user`` container provisions an account with
``rw`` on the application database (database level and ``*`` collections) and
``none`` on ``_system``; the backend, the worker and the backup connect with it
instead of root. This module boots the production start path — ``connect``,
``ensure_collections``, every migration, every seed — under exactly those grants
against a real server.

Measured before #2126 (ArangoDB 3.12.12, such an account, its database existing)::

    DatabaseListError 401 11 [HTTP 401][ERR 11] No read access to database.

— ``ArangoConnection.connect`` listed the databases through ``_system`` before
opening its own, so the application could run as root only.

The grants are applied here with python-arango because the integration tier has
no ``arangosh``; the chart's script (values.yaml, ``controllers.arangodb
.containers.app-user``) grants the same three levels, and that script was run
against ArangoDB 3.12.12 under the pod's security context on 2026-10-04.

Run with: pytest tests/integration/test_arango_app_scoped_account.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import secrets

import pytest
from arango import ArangoClient
from arango.exceptions import ArangoServerError

from app.config.settings import Settings
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.connection import ArangoConnection
from app.migrations.framework.runner import run_pending_migrations
from app.migrations.seeds.registry import run_seeds
from tests.support.arango_integration import (
    ARANGO_HOST,
    ARANGO_PASSWORD,
    ARANGO_PORT,
    ARANGO_URL,
    ARANGO_USERNAME,
    run_database_name,
)
from tests.support.seed_boot import bind_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("boots the application under an app-scoped account on a real server"),
]


@pytest.fixture
def app_account():
    """A run-scoped database and an account with the chart's grants on it; both removed afterwards."""
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    name = run_database_name("app_scoped_account")
    user = f"{name}_app"
    password = secrets.token_hex(24)
    if system.has_database(name):
        system.delete_database(name)
    system.create_database(name)
    if system.has_user(user):
        system.delete_user(user)
    system.create_user(username=user, password=password, active=True)
    system.update_permission(username=user, permission="rw", database=name)
    system.update_permission(username=user, permission="rw", database=name, collection="*")
    system.update_permission(username=user, permission="none", database="_system")
    try:
        yield name, user, password
    finally:
        system.delete_user(user, ignore_missing=True)
        system.delete_database(name, ignore_missing=True)


def test_the_app_boots_under_an_account_scoped_to_its_database(app_account, monkeypatch) -> None:
    name, user, password = app_account
    settings = Settings(
        arangodb_host=ARANGO_HOST,
        arangodb_port=int(ARANGO_PORT),
        arangodb_database=name,
        arangodb_username=user,
        arangodb_password=password,
    )
    connection = ArangoConnection(settings)

    db = connection.connect()
    ensure_collections(db)
    bind_database(monkeypatch, db)
    run_pending_migrations(db)
    run_seeds(db)

    assert db.collection("schema_migrations").count() > 0, "the migrations ran (non-vacuous)"
    assert db.collection("species").count() > 0, "the seeds ran (non-vacuous)"
    with pytest.raises(ArangoServerError):
        ArangoClient(hosts=ARANGO_URL).db("_system", username=user, password=password).collections()
    connection.close()
