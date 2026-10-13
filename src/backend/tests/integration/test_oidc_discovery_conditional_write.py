"""/code-review of #1910 — the discovery test stores a document only while the issuer is unchanged.

``POST /admin/oidc-providers/{key}/test`` fetches the discovery document from the
issuer it read, for up to the fetch timeout, paced by that issuer. A step-up'd
repoint that lands in between must not receive the old issuer's endpoints (sign-in
prefers the discovery document's). ``ArangoOidcConfigRepository.update_discovery``
makes the issuer check and the write one AQL statement; the check is a driver and
server contract, so it is measured here and not against a double.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1910 the conditional update is an AQL contract; no double may answer it"),
]

_DB_NAME = run_database_name("oidc_discovery_conditional")
_DISCOVERY = {
    "issuer": "https://old.example.org",
    "authorization_endpoint": "https://old.example.org/authorize",
    "token_endpoint": "https://old.example.org/token",
    "nested": {"a": 1},
}


@pytest.fixture
def repo():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    db = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.OIDC_PROVIDER_CONFIGS)
    db.collection(col.OIDC_PROVIDER_CONFIGS).insert(
        {
            "_key": "cfg-1",
            "slug": "corp",
            "display_name": "Corp",
            "issuer_url": "https://old.example.org",
            "client_id": "c",
            "enabled": True,
            "discovery_document": {"stale": True, "nested": {"b": 2}},
        }
    )
    try:
        yield ArangoOidcConfigRepository(db)
    finally:
        system.delete_database(_DB_NAME)


def test_the_document_is_stored_while_the_issuer_is_unchanged(repo: ArangoOidcConfigRepository) -> None:
    stored = repo.update_discovery(
        "cfg-1", issuer_url="https://old.example.org", discovery_document=_DISCOVERY, refreshed_at=datetime.now(UTC)
    )

    assert stored is True
    config = repo.get_by_key("cfg-1")
    assert config is not None
    # Replaced as a whole, not merged into the previous document.
    assert config.discovery_document == _DISCOVERY
    assert config.discovery_refreshed_at is not None


def test_nothing_is_stored_after_the_issuer_changed(repo: ArangoOidcConfigRepository) -> None:
    repo.update_fields("cfg-1", {"issuer_url": "https://new.example.org"})

    stored = repo.update_discovery(
        "cfg-1", issuer_url="https://old.example.org", discovery_document=_DISCOVERY, refreshed_at=datetime.now(UTC)
    )

    assert stored is False
    config = repo.get_by_key("cfg-1")
    assert config is not None
    assert config.discovery_document == {"stale": True, "nested": {"b": 2}}
    assert config.issuer_url == "https://new.example.org"
