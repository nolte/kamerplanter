"""#2715 item 7 — ``ArangoAttachmentRepository.get_many`` against a real ArangoDB.

The bed gallery read (``LocationPhotoService._view``) asked one ``get`` per photo, up to 50 round trips per gallery
read or write. ``get_many`` answers the whole list in one query; what is pinned here is that the query keeps the
tenant boundary ``get`` keeps (another tenant's key reads as absent), drops unknown keys, and tolerates repeats.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.collections import ensure_collections
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("attachment_get_many")
TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"

pytestmark = pytest.mark.usefixtures("arango_db")


def _row(key: str, tenant: str) -> dict[str, object]:
    return {
        "_key": key,
        "tenant_key": tenant,
        "mime_type": "image/jpeg",
        "byte_size": 10,
        "sha256": f"sha-{key}",
        "original_filename": f"{key}.jpg",
        "created_by": "user-1",
        "category": "location",
        "storage_key": f"t/{tenant}/location/2026/11/{key}.jpg",
        "created_at": "2026-11-13T10:00:00+00:00",
    }


@pytest.fixture
def repo():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    attachments = database.collection(col.ATTACHMENTS)
    for key in ("p1", "p2", "p3"):
        attachments.insert(_row(key, TENANT))
    attachments.insert(_row("foreign", OTHER_TENANT))

    yield ArangoAttachmentRepository(database)

    system.delete_database(TEST_DATABASE)
    client.close()


def test_one_query_answers_the_tenants_records_and_nothing_else(repo) -> None:  # type: ignore[no-untyped-def]
    found = repo.get_many(["p3", "foreign", "missing", "p1", "p3"], TENANT)

    assert set(found) == {"p3", "p1"}
    assert all(attachment.tenant_key == TENANT for attachment in found.values())
    assert found["p1"] == repo.get("p1", TENANT)


def test_the_other_tenant_reads_only_its_own(repo) -> None:  # type: ignore[no-untyped-def]
    assert set(repo.get_many(["p1", "foreign"], OTHER_TENANT)) == {"foreign"}


def test_no_keys_is_no_query_and_an_empty_tenant_is_refused(repo) -> None:  # type: ignore[no-untyped-def]
    assert repo.get_many([], TENANT) == {}
    with pytest.raises(ValueError, match="tenant"):
        repo.get_many(["p1"], "")
