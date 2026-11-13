"""#2715 item 1 — the garden-plan underlay sweep against a real ArangoDB.

An underlay is uploaded (``POST /attachments``, category ``garden_plan_underlay``) and named by the site in a second
request (``PUT /sites/{key}/plan/underlay``). A PUT that never happens leaves an unreferenced underlay, and before
``cleanup_orphaned_underlays`` nothing removed it before the tenant erasure.

This module runs the **task body** the beat sends (``_cleanup_orphaned_underlays``) with the real
``ArangoAttachmentRepository`` and ``AttachmentService`` (only the object store is a double) and reads the outcome
off the attachment collection:

* a never-named underlay older than the floor is deleted, record and object, in every tenant;
* an underlay a site names (``plan.underlay.attachment_key``, a dotted carrier) stays, and so does a fresh one;
* an old orphan of another category stays — each sweep owns its own category;
* an undated orphan is counted as ``held_undated``, not deleted.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from arango import ArangoClient

from app.config.settings import settings
from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.collections import ensure_collections
from app.domain.services.attachment_service import AttachmentService
from app.tasks import storage_tasks
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("orphan_underlay")
TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"
FLOOR_HOURS = 48
OLD = datetime.now(UTC) - timedelta(hours=FLOOR_HOURS + 24)
RECENT = datetime.now(UTC) - timedelta(hours=1)
CATEGORY = "garden_plan_underlay"

pytestmark = pytest.mark.usefixtures("arango_db")


def _attachment(
    key: str, *, created_at: datetime | None, category: str = CATEGORY, tenant: str = TENANT
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
        "storage_key": f"t/{tenant}/{category}/2026/11/obj-{key}.jpg",
    }
    if created_at is not None:
        row["created_at"] = created_at.isoformat()
    return row


def _site(key: str, underlay_key: str) -> dict[str, object]:
    return {
        "_key": key,
        "tenant_key": TENANT,
        "name": key,
        "plan": {
            "underlay": {
                "attachment_key": underlay_key,
                "calibration": {"p1_px": [0, 0], "p2_px": [100, 0], "distance_m": 10.0},
            }
        },
    }


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
    # Uploaded, never named by a site (the PUT was refused or never sent) - the case the sweep exists for.
    attachments.insert(_attachment("never-named", created_at=OLD))
    attachments.insert(_attachment("never-named-other-tenant", created_at=OLD, tenant=OTHER_TENANT))
    # Named by a site's plan: the dotted carrier ``plan.underlay.attachment_key``.
    attachments.insert(_attachment("named", created_at=OLD))
    database.collection(col.SITES).insert(_site("site-1", "named"))
    # Inside the floor: the PUT follows within the same client flow.
    attachments.insert(_attachment("fresh", created_at=RECENT))
    # Another category: the bed-photo sweep's business.
    attachments.insert(_attachment("old-bed-photo", created_at=OLD, category="location"))
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
        result = await storage_tasks._cleanup_orphaned_underlays(FLOOR_HOURS, 500)
    return result, storage


async def test_a_never_named_underlay_past_the_floor_is_deleted_and_nothing_else(db) -> None:  # type: ignore[no-untyped-def]
    result, storage = await _sweep(db)

    remaining = _keys(db)
    assert "never-named" not in remaining and "never-named-other-tenant" not in remaining
    assert {"named", "fresh", "old-bed-photo", "undated"} <= remaining
    assert result["found"] == 2 and result["deleted"] == 2 and result["failed"] == 0
    assert result["held_undated"] == 1
    deleted_objects = {call.args[0] for call in storage.delete_object.await_args_list}
    assert f"t/{TENANT}/{CATEGORY}/2026/11/obj-never-named.jpg" in deleted_objects
    assert f"t/{OTHER_TENANT}/{CATEGORY}/2026/11/obj-never-named-other-tenant.jpg" in deleted_objects
    assert not any("obj-named.jpg" in key or "obj-fresh" in key for key in deleted_objects)


async def test_an_underlay_whose_site_let_go_of_it_is_collected(db) -> None:  # type: ignore[no-untyped-def]
    """A replace or remove committed and its discard failed: the site no longer names the picture."""
    db.collection(col.SITES).update({"_key": "site-1", "plan": {"underlay": None}}, keep_none=True)

    await _sweep(db)

    assert "named" not in _keys(db)


async def test_a_second_run_deletes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    await _sweep(db)

    result, storage = await _sweep(db)

    assert result["found"] == 0 and result["deleted"] == 0
    storage.delete_object.assert_not_awaited()
