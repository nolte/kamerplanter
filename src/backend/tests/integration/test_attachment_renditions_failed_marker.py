"""#2108 — ``mark_renditions_failed`` against a real ArangoDB.

The thumbnail task marks the *object*: every record of the tenant that holds the
same ``storage_key`` (records share an object since #1770) must read
``renditions_failed`` afterwards, a record of another tenant must not, and a
record written before the field existed must read ``False``. A double cannot
certify the AQL filter, so this runs the repository against the real
collections and indexes from ``ensure_collections``.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import AttachmentCategory
from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.domain.models.attachment import Attachment
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("attachment_renditions_failed")

pytestmark = pytest.mark.usefixtures("arango_db")

SHARED_KEY = "t/t-a/diary/2026/10/01JSHAREDOBJECT00000000000.jpg"


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def repo(database) -> ArangoAttachmentRepository:
    return ArangoAttachmentRepository(database)


def _record(tenant_key: str, created_by: str, storage_key: str) -> Attachment:
    return Attachment(
        tenant_key=tenant_key,
        mime_type="image/jpeg",
        byte_size=100,
        sha256="a" * 64,
        original_filename="p.jpg",
        created_by=created_by,
        category=AttachmentCategory.DIARY,
        storage_key=storage_key,
    )


def test_every_holder_in_the_tenant_is_marked_and_nothing_else(repo: ArangoAttachmentRepository, database) -> None:
    first = repo.create(_record("t-a", "u-1", SHARED_KEY))
    second = repo.create(_record("t-a", "u-2", SHARED_KEY))
    unrelated = repo.create(_record("t-a", "u-1", "t/t-a/diary/2026/10/01JOTHEROBJECT000000000000.jpg"))
    foreign = repo.create(_record("t-b", "u-9", SHARED_KEY))

    marked = repo.mark_renditions_failed("t-a", SHARED_KEY)

    assert marked == 2
    assert repo.get(first.key, "t-a").renditions_failed is True
    assert repo.get(second.key, "t-a").renditions_failed is True
    assert repo.get(unrelated.key, "t-a").renditions_failed is False
    assert repo.get(foreign.key, "t-b").renditions_failed is False


def test_a_record_written_before_the_field_existed_reads_false(repo: ArangoAttachmentRepository, database) -> None:
    created = repo.create(_record("t-a", "u-3", "t/t-a/diary/2026/10/01JLEGACYOBJECT00000000000.jpg"))
    database.aql.execute(
        "FOR a IN @@c FILTER a._key == @k UPDATE a WITH { renditions_failed: null } IN @@c OPTIONS { keepNull: false }",
        bind_vars={"@c": col.ATTACHMENTS, "k": created.key},
    )
    raw = database.collection(col.ATTACHMENTS).get(created.key)
    assert "renditions_failed" not in raw

    assert repo.get(created.key, "t-a").renditions_failed is False


def test_an_unknown_object_marks_nothing(repo: ArangoAttachmentRepository) -> None:
    assert repo.mark_renditions_failed("t-a", "t/t-a/diary/2026/10/01JNOSUCHOBJECT00000000000.jpg") == 0
