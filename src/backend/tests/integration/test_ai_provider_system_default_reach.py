"""#2110: ``get_system_default`` reads the platform's provider rows only, against a **real** ArangoDB.

The glossary cache is shared by every tenant, so its generation is classified by
the platform's default provider. The AQL must never return a tenant's row —
not even a tenant that sorts first or marks its own row as default — and must
honour ``is_active`` and the default flag among the system rows.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.ai_repository import ArangoAiProviderRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("ai_provider_system_default")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    database.collection(col.AI_PROVIDER_CONFIGS).truncate()
    return database


def _row(key: str, tenant_key: str | None, provider_type: str, *, default: bool, active: bool = True) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant_key,
        "provider_type": provider_type,
        "display_name": key,
        "model_name": "m",
        "requires_consent": provider_type != "ollama",
        "is_active": active,
        "is_default": default,
    }


def test_a_tenants_default_row_is_never_the_platforms(db) -> None:
    providers = db.collection(col.AI_PROVIDER_CONFIGS)
    providers.insert(_row("aaa-tenant-cloud", "t1", "anthropic", default=True))
    providers.insert(_row("system-ollama", None, "ollama", default=True))

    found = ArangoAiProviderRepository(db).get_system_default()

    assert found is not None
    assert found.key == "system-ollama"
    # The tenant path still sees its own default first — unchanged.
    assert ArangoAiProviderRepository(db).get_default("t1", None).key == "aaa-tenant-cloud"


def test_the_default_flag_wins_among_active_system_rows(db) -> None:
    providers = db.collection(col.AI_PROVIDER_CONFIGS)
    providers.insert(_row("a-system-local", None, "ollama", default=False))
    providers.insert(_row("b-system-cloud", None, "anthropic", default=True))
    providers.insert(_row("c-system-retired", None, "anthropic", default=True, active=False))

    found = ArangoAiProviderRepository(db).get_system_default()

    assert found is not None
    assert found.key == "b-system-cloud"


def test_no_system_row_means_no_platform_provider(db) -> None:
    db.collection(col.AI_PROVIDER_CONFIGS).insert(_row("tenant-only", "t1", "anthropic", default=True))

    assert ArangoAiProviderRepository(db).get_system_default() is None
