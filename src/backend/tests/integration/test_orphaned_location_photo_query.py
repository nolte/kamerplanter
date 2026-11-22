"""REQ-053 GP-FR-051 (#2661 SEC-001 / GDPR-001 / GDPR-002) — the bed-photo sweep against a real ArangoDB.

A bed photo is uploaded (``POST /attachments``, category ``location``) and linked in a second request. A link
that never happens (422 ``location.photo_limit_reached``, the bed deleted meanwhile, a dropped connection) and a
discard that failed after a bed write committed both leave an unreferenced ``location`` attachment, and before
``cleanup_orphaned_location_photos`` nothing ever removed it.

This module runs the **task body** the beat sends (``_cleanup_orphaned_location_photos``) with the real
``ArangoAttachmentRepository`` and the real ``AttachmentService`` (only the object store is a double — this tier
has none), and reads the outcome off the attachment collection:

* a never-linked ``location`` upload older than the floor is deleted, record and object;
* a photo a bed shows (``photo_refs``), a bed's cover (``cover_photo_ref``), a young upload and an old orphan of
  another category stay;
* a ``location`` attachment another carrier names (a plant gallery) stays — the reference check is over every
  carrier, not only beds;
* an undated orphan is counted as ``held_undated``, not deleted.

The task-photo sweep over the same query is measured in ``test_orphaned_task_photo_query.py``; this module adds
the ``location`` category, not a second copy of its spelling cases.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from arango import ArangoClient

from app.common.enums import AttachmentCategory
from app.config.settings import settings
from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.collections import ensure_collections
from app.domain.services.attachment_service import AttachmentService
from app.tasks import storage_tasks
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("orphan_location_photo")
TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"
FLOOR_HOURS = 48
OLD = datetime.now(UTC) - timedelta(hours=FLOOR_HOURS + 24)
RECENT = datetime.now(UTC) - timedelta(hours=1)

pytestmark = pytest.mark.usefixtures("arango_db")


def _attachment(
    key: str, *, created_at: datetime | None, category: str = "location", tenant: str = TENANT
) -> dict[str, object]:
    row: dict[str, object] = {
        "_key": key,
        "tenant_key": tenant,
        "mime_type": "image/jpeg",
        "byte_size": 1000,
        "sha256": f"sha-{key}",
        "original_filename": f"{key}.jpg",
        "created_by": "user-1",
        "category": category,
        # The writer's own shape (``StorageKeyBuilder``), so the delete takes the in-namespace path.
        "storage_key": f"t/{tenant}/{category}/2026/11/obj-{key}.jpg",
    }
    if created_at is not None:
        row["created_at"] = created_at.isoformat()
    return row


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)

    attachments = database.collection(col.ATTACHMENTS)
    # Uploaded, never linked (the link was refused, or the bed went first) — the case the sweep exists for.
    attachments.insert(_attachment("never-linked", created_at=OLD))
    attachments.insert(_attachment("never-linked-other-tenant", created_at=OLD, tenant=OTHER_TENANT))
    # Shown by a bed, and a bed's cover on its own (no photo_refs on that row).
    attachments.insert(_attachment("linked", created_at=OLD))
    attachments.insert(_attachment("cover-only", created_at=OLD))
    # The beds sit on a site of TENANT, as every linked bed does: the interactive scan reads a tenant's beds through
    # its sites (#2715 item 2), the sweep reads all of them.
    database.collection(col.SITES).insert({"_key": "site-1", "tenant_key": TENANT, "name": "Garten"})
    locations = database.collection(col.LOCATIONS)
    locations.insert({"_key": "bed-1", "name": "Beet 1", "site_key": "site-1", "photo_refs": ["linked"]})
    locations.insert({"_key": "bed-2", "name": "Beet 2", "site_key": "site-1", "cover_photo_ref": "cover-only"})
    # A location photo another carrier names: the check is over every carrier, not only beds.
    attachments.insert(_attachment("named-by-a-plant", created_at=OLD))
    database.collection(col.PLANT_INSTANCES).insert(
        {"_key": "plant-1", "tenant_key": TENANT, "photo_refs": ["named-by-a-plant"]}
    )
    # Inside the floor: the link follows within the same client flow.
    attachments.insert(_attachment("fresh", created_at=RECENT))
    # Another category: the task sweep's business, and off by default there.
    attachments.insert(_attachment("old-task-orphan", created_at=OLD, category="task"))
    # No readable created_at: never judged, counted.
    attachments.insert(_attachment("undated", created_at=None))

    yield database

    system.delete_database(TEST_DATABASE)
    client.close()


def _keys(db) -> set[str]:  # type: ignore[no-untyped-def]
    return {doc["_key"] for doc in db.collection(col.ATTACHMENTS).all()}


async def _sweep(db) -> tuple[dict, AsyncMock]:  # type: ignore[no-untyped-def]
    repo = ArangoAttachmentRepository(db)
    storage = AsyncMock()
    service = AttachmentService(storage=storage, attachment_repo=repo, settings=settings)
    with (
        patch("app.common.dependencies.get_attachment_repo", return_value=repo),
        patch("app.common.dependencies.get_attachment_service", return_value=service),
    ):
        result = await storage_tasks._cleanup_orphaned_location_photos(FLOOR_HOURS, 500)
    return result, storage


async def test_a_never_linked_bed_photo_past_the_floor_is_deleted_and_nothing_else(db) -> None:  # type: ignore[no-untyped-def]
    result, storage = await _sweep(db)

    remaining = _keys(db)
    assert "never-linked" not in remaining and "never-linked-other-tenant" not in remaining
    assert {"linked", "cover-only", "named-by-a-plant", "fresh", "old-task-orphan", "undated"} <= remaining
    assert result["found"] == 2 and result["deleted"] == 2 and result["failed"] == 0
    assert result["held_undated"] == 1
    # The object went with its record, under the row's own tenant namespace.
    deleted_objects = {call.args[0] for call in storage.delete_object.await_args_list}
    assert f"t/{TENANT}/location/2026/11/obj-never-linked.jpg" in deleted_objects
    assert f"t/{OTHER_TENANT}/location/2026/11/obj-never-linked-other-tenant.jpg" in deleted_objects
    assert not any("obj-linked" in key or "obj-fresh" in key for key in deleted_objects)


async def test_a_photo_linked_after_the_selection_survives_the_sweep(db) -> None:  # type: ignore[no-untyped-def]
    """#2715 review: the dedup hands an old record back and the link lands between selection and delete."""
    repo = ArangoAttachmentRepository(db)
    select = repo.find_orphaned_photos

    def select_then_link(*args, **kwargs):  # type: ignore[no-untyped-def]
        selected = select(*args, **kwargs)
        db.collection(col.LOCATIONS).insert(
            {"_key": "bed-3", "name": "Beet 3", "site_key": "site-1", "photo_refs": ["never-linked"]}
        )
        return selected

    storage = AsyncMock()
    service = AttachmentService(storage=storage, attachment_repo=repo, settings=settings)
    with (
        patch.object(repo, "find_orphaned_photos", side_effect=select_then_link),
        patch("app.common.dependencies.get_attachment_repo", return_value=repo),
        patch("app.common.dependencies.get_attachment_service", return_value=service),
    ):
        result = await storage_tasks._cleanup_orphaned_location_photos(FLOOR_HOURS, 500)

    assert "never-linked" in _keys(db) and "never-linked-other-tenant" not in _keys(db)
    assert result["deleted"] == 1 and result["skipped"] == 1


async def test_a_second_run_deletes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    await _sweep(db)

    result, storage = await _sweep(db)

    assert result["found"] == 0 and result["deleted"] == 0
    storage.delete_object.assert_not_awaited()


async def test_a_photo_left_by_a_failed_discard_is_collected(db) -> None:  # type: ignore[no-untyped-def]
    """GDPR-002: the bed went (its reference with it), the discard after the commit failed — the sweep catches it."""
    db.collection(col.LOCATIONS).delete("bed-1")

    await _sweep(db)

    assert "linked" not in _keys(db)


def test_the_task_query_is_unchanged_by_the_category_parameter(db) -> None:  # type: ignore[no-untyped-def]
    """The task sweep keeps its own category: it never offers a bed photo, the bed sweep never a task photo."""
    repo = ArangoAttachmentRepository(db)
    cutoff = datetime.now(UTC) - timedelta(hours=FLOOR_HOURS)

    task = {a.key for a in repo.find_orphaned_task_photos(older_than=cutoff)}
    location = {a.key for a in repo.find_orphaned_photos(AttachmentCategory.LOCATION, older_than=cutoff)}

    assert task == {"old-task-orphan"}
    assert location == {"never-linked", "never-linked-other-tenant"}
    assert repo.count_undated_orphaned_task_photos() == 0
    assert repo.count_undated_orphaned_photos(AttachmentCategory.LOCATION) == 1


def test_the_dry_run_count_asks_the_discards_rule_with_the_deleted_beds_gone(db) -> None:  # type: ignore[no-untyped-def]
    """#2715 review F: ``releasable_after_location_delete`` - a photo the deleted beds named goes, one a bed that
    stays, another carrier or another tenant holds does not, a stale ref and another category are not counted."""
    repo = ArangoAttachmentRepository(db)
    asked = ["linked", "cover-only", "named-by-a-plant", "never-linked-other-tenant", "gone", "old-task-orphan"]

    both = repo.releasable_after_location_delete(asked, tenant_key=TENANT, location_keys=["bed-1", "bed-2"])
    one = repo.releasable_after_location_delete(asked, tenant_key=TENANT, location_keys=["bed-1"])

    assert set(both) == {"linked", "cover-only"}
    assert set(one) == {"linked"}  # bed-2 stays and still names its cover
    assert repo.releasable_after_location_delete(asked, tenant_key="", location_keys=["bed-1"]) == []
