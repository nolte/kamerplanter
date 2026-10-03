"""#2034 — v0074 drops the hash-typed provider-link index v0064 left on pre-June volumes.

The legacy index is created exactly as ``ensure_collections`` created it until
2026-06-07 (``{"type": "hash", ...}``); the database itself comes from today's
``ensure_collections``, so the per-configuration replacement is present as on a
migrated volume.
"""

from __future__ import annotations

import pytest
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.migrations.versions.v0064_bind_provider_links_to_configuration import (
    LEGACY_UNIQUE_FIELDS,
)
from app.migrations.versions.v0064_bind_provider_links_to_configuration import (
    migration as v0064,
)
from app.migrations.versions.v0074_retire_hash_typed_provider_link_index import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration drops an index on a real server"),
]

_DB_NAME = run_database_name("v0074_hash_provider_link_index")
_LINK = {"provider": "oidc", "provider_user_id": "subject-1", "user_key": "u1"}


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _legacy_on_fields(db) -> list[str]:
    return [idx["type"] for idx in db.collection(col.AUTH_PROVIDERS).indexes() if idx["fields"] == LEGACY_UNIQUE_FIELDS]


def _with_pre_june_index(db) -> None:
    db.collection(col.AUTH_PROVIDERS).add_index({"type": "hash", "fields": LEGACY_UNIQUE_FIELDS, "unique": True})


def test_the_hash_index_survives_v0064_and_is_dropped_here(db) -> None:
    links = db.collection(col.AUTH_PROVIDERS)
    _with_pre_june_index(db)
    links.insert({**_LINK, "oidc_config_slug": "corp-a"})
    v0064.up(db)
    assert _legacy_on_fields(db) == ["hash"], "the gap v0064 left"
    with pytest.raises(DocumentInsertError):
        links.insert({**_LINK, "oidc_config_slug": "corp-b", "user_key": "u2"})  # #1869, still in force

    report = migration.up(db)

    assert _legacy_on_fields(db) == []
    assert report.changed == 1
    assert report.details["legacy_index_types"] == ["hash"]
    links.insert({**_LINK, "oidc_config_slug": "corp-b", "user_key": "u2"})  # same sub, second configuration
    with pytest.raises(DocumentInsertError):
        links.insert({**_LINK, "oidc_config_slug": "corp-a", "user_key": "u3"})  # replacement still holds


def test_a_second_run_is_a_no_op(db) -> None:
    _with_pre_june_index(db)
    migration.up(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.details["legacy_indexes"] == 0
    assert _legacy_on_fields(db) == []


def test_a_dry_run_counts_and_drops_nothing(db) -> None:
    _with_pre_june_index(db)

    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert report.details["legacy_indexes"] == 1
    assert _legacy_on_fields(db) == ["hash"]


def test_without_the_per_configuration_replacement_nothing_is_dropped(db) -> None:
    links = db.collection(col.AUTH_PROVIDERS)
    for idx in links.indexes():
        if idx["fields"] == col.AUTH_PROVIDER_UNIQUE_FIELDS:
            links.delete_index(idx["id"])
    _with_pre_june_index(db)

    report = migration.up(db)

    assert report.precondition_unmet is True
    assert report.details["replacement_indexes"] == 0
    assert _legacy_on_fields(db) == ["hash"]
