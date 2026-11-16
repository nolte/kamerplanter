"""spec/privacy/09 §5a / §9 / §12 (TA-700, TA-716) — v0114 against a real ArangoDB (#2976).

The AQL is what this module measures: the tenant predicate, the ``DOCUMENT`` lookup that tells a live account from
an erased one, ``UNSET`` of the old field with an explicit ``null`` key kept, global templates left alone, and that
the propagation repository reads the result and resolves the display name. The phases (partial run, residual) are
pinned in ``tests/unit/migrations/versions/test_v0114_rooting_protocol_author_key.py``.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0114_rooting_protocol_author_key.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.repositories.propagation_repository import PropagationRepository
from app.migrations.versions.v0114_rooting_protocol_author_key import (
    BUCKET_DROPPED,
    BUCKET_KEYED,
    BUCKET_TO_MARKER,
    migration,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the correction is AQL over rooting_protocols and users on a real server"),
]

_DB_NAME = run_database_name("v0114_rooting_protocol_author_key")


def _insert(database, collection: str, documents: list[dict]) -> None:  # type: ignore[no-untyped-def]
    results = database.collection(collection).insert_many(documents)
    assert [r for r in results if isinstance(r, Exception)] == []


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    _insert(
        database,
        col.TENANTS,
        [
            {"_key": "t_a", "name": "a", "slug": "a", "owner_user_key": "lisa", "status": "active"},
            {"_key": "t_s", "name": "s", "slug": "s", "owner_user_key": "lisa", "status": "suspended"},
            {"_key": "t_d", "name": "d", "slug": "d", "owner_user_key": "lisa", "status": "deleted"},
        ],
    )
    _insert(database, col.USERS, [{"_key": "lisa", "email": "l@example.com", "display_name": "Lisa"}])
    protocols = []
    for tenant in ("t_a", "t_s", "t_d"):
        protocols += [
            {"_key": f"{tenant}_live", "tenant_key": tenant, "name": "a", "method": "cutting", "author": "lisa"},
            {"_key": f"{tenant}_gone", "tenant_key": tenant, "name": "b", "method": "cutting", "author": "erased"},
            {"_key": f"{tenant}_none", "tenant_key": tenant, "name": "c", "method": "cutting", "author": None},
        ]
    protocols.append({"_key": "global", "tenant_key": "", "name": "g", "method": "cutting", "author": "lisa"})
    _insert(database, col.ROOTING_PROTOCOLS, protocols)
    yield database
    system.delete_database(_DB_NAME)


def _get(database, key: str) -> dict:  # type: ignore[no-untyped-def]
    doc = database.collection(col.ROOTING_PROTOCOLS).get(key)
    return {k: v for k, v in doc.items() if not k.startswith("_")}


def test_the_dry_run_counts_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    assert report.details["buckets"][BUCKET_KEYED] == {"t_a": 1, "t_s": 1}
    assert report.details["buckets"][BUCKET_TO_MARKER] == {"t_a": 1, "t_s": 1}
    assert report.details["buckets"][BUCKET_DROPPED] == {"t_a": 1, "t_s": 1}
    assert _get(db, "t_a_live")["author"] == "lisa"


def test_the_run_moves_the_key_and_leaves_deleted_tenants_and_global_rows_alone(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db)

    assert report.details["status"] == "applied"
    assert report.changed == 6
    for tenant in ("t_a", "t_s"):
        live, gone, none = (_get(db, f"{tenant}_{name}") for name in ("live", "gone", "none"))
        assert "author" not in live and live["author_user_key"] == "lisa"
        assert "author" not in gone and gone["author_user_key"] == "_anonymized"
        assert "author" not in none and none["author_user_key"] is None
    assert _get(db, "t_d_live")["author"] == "lisa"
    assert _get(db, "global")["author"] == "lisa"
    assert migration.up(db).changed == 0


def test_the_repository_reads_the_corrected_row_and_names_its_author(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)
    repo = PropagationRepository(db)

    protocol = repo.get_protocol("t_a_live", "t_a")

    assert protocol is not None
    assert protocol.author_user_key == "lisa"
    assert repo.account_display_names(["lisa", "erased", "_anonymized"]) == {"lisa": "Lisa"}
