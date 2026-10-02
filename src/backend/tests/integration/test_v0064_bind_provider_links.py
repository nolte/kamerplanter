"""#1869 — the provider-link lookup and v0064 against a real ArangoDB.

* v0064 binds a legacy link (no ``oidc_config_slug`` attribute at all, the shape
  of a document written before #1815) to the only configuration of its type,
  leaves one with two configurations of its type alone, and a second run changes
  nothing; it drops the (type, ``sub``) unique index, so the same ``sub`` can be
  linked at a second configuration, while (type, configuration, ``sub``) stays unique;
* ``list_by_provider`` answers every link of a (type, ``sub``) pair — the
  candidates the login picks from by configuration — not the first one.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient
from arango.exceptions import DocumentInsertError

from app.common.enums import AuthProviderType
from app.data_access.arango import collections as col
from app.data_access.arango.auth_provider_repository import ArangoAuthProviderRepository
from app.migrations.versions.v0064_bind_provider_links_to_configuration import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("v0064_bind_provider_links")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    # An existing volume: the (type, sub) unique index from before #1869, then the
    # startup ``ensure_collections`` of this release.
    db.create_collection(col.AUTH_PROVIDERS).add_persistent_index(fields=["provider", "provider_user_id"], unique=True)
    col.ensure_collections(db)
    configs = db.collection(col.OIDC_PROVIDER_CONFIGS)
    for slug, provider_type in (("google", "google"), ("corp-a", "oidc"), ("corp-b", "oidc")):
        configs.insert({"_key": slug, "slug": slug, "provider_type": provider_type, "enabled": slug != "corp-b"})
    links = db.collection(col.AUTH_PROVIDERS)
    # Documents of before #1815: no ``oidc_config_slug`` attribute at all.
    links.insert({"_key": "g_legacy", "user_key": "u1", "provider": "google", "provider_user_id": "g-1"})
    links.insert({"_key": "o_legacy", "user_key": "u1", "provider": "oidc", "provider_user_id": "shared"})
    yield db
    system.delete_database(TEST_DATABASE)


def _unique_index_fields(database) -> list[list[str]]:
    return [
        list(i["fields"])
        for i in database.collection(col.AUTH_PROVIDERS).indexes()
        if i.get("unique") and i["type"] == "persistent"
    ]


def test_v0064_binds_only_unambiguous_legacy_links_and_is_idempotent(database) -> None:
    dry = migration.up(database, dry_run=True)
    assert (dry.scanned, dry.details["bound"], dry.changed) == (2, 1, 0)
    assert "oidc_config_slug" not in database.collection(col.AUTH_PROVIDERS).get("g_legacy")
    assert ["provider", "provider_user_id"] in _unique_index_fields(database)

    first = migration.up(database)
    second = migration.up(database)

    links = database.collection(col.AUTH_PROVIDERS)
    assert links.get("g_legacy")["oidc_config_slug"] == "google"
    # Two ``oidc`` configurations (one disabled): not guessed.
    assert links.get("o_legacy").get("oidc_config_slug") is None
    assert (first.details["bound"], first.details["legacy_unique_indexes_dropped"]) == (1, 1)
    assert (second.scanned, second.changed) == (1, 0)
    assert _unique_index_fields(database) == [["provider", "oidc_config_slug", "provider_user_id"]]


def test_the_same_sub_at_another_configuration_can_be_linked_and_both_are_candidates(database) -> None:
    """Runs after the migration: the (type, sub) index is gone, (type, configuration, sub) holds."""
    links = database.collection(col.AUTH_PROVIDERS)
    links.insert(
        {
            "_key": "o_bound",
            "user_key": "u2",
            "provider": "oidc",
            "provider_user_id": "shared",
            "oidc_config_slug": "corp-a",
            "issuer": "https://idp-a.example",
        }
    )
    with pytest.raises(DocumentInsertError):
        links.insert({"user_key": "u3", "provider": "oidc", "provider_user_id": "shared", "oidc_config_slug": "corp-a"})

    rows = ArangoAuthProviderRepository(database).list_by_provider(AuthProviderType.OIDC, "shared")

    assert sorted((r.key, r.oidc_config_slug) for r in rows) == [("o_bound", "corp-a"), ("o_legacy", None)]
