"""#1393 — the single query behind ``DELETE /tasks/{key}/photos/{id}``, run for real.

``task_photo_delete_state`` replaced three repository calls (two full reference scans
plus a key lookup) with one. That is a rewrite of a query whose answer decides whether
an attachment is **destroyed**, so it is exercised against a real ArangoDB here rather
than only against the service-level double in
``tests/unit/domain/services/test_deletable_from_task.py`` — the double cannot be
wrong about AQL, which is precisely the part that changed.

The three states and what each costs if the query gets it wrong:

``shared``   read as anything else → a plant gallery's cover, or another task's
             completion photo, is destroyed and its reference dangles.
``task``     read as ``shared``    → the remove button stops working on the task's
             own photos, permanently and with a 404 nobody can act on.
``staged``   read as ``task``      → any member may delete any other member's staged
             upload through any task key of the tenant (the round-5 finding).

Skipped when no ArangoDB answers on ``localhost:8529``. See the module docstring of
``test_orphaned_task_photo_query.py`` for how to start one. That the tier does not run
in CI is #1432; that this file therefore carries the only executing coverage of this
query is the reason it is written as carefully as it is.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository

ARANGO_URL = "http://localhost:8529"
ARANGO_PASSWORD = "rootpassword"
TEST_DATABASE = "kp_test_task_photo_delete_state"
TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"
OWN_TASK = "task-own"
OTHER_TASK = "task-other"
UPLOADER = "user-uploader"

ARANGO_AVAILABLE = False
try:
    from arango import ArangoClient

    _probe = ArangoClient(hosts=ARANGO_URL)
    _probe.db("_system", username="root", password=ARANGO_PASSWORD).version()
    ARANGO_AVAILABLE = True
except Exception:  # noqa: BLE001 — any failure means "no database here"
    pass

pytestmark = pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available on localhost:8529")

#: Collections the query reads. Spelled out rather than imported from
#: ``PHOTO_REF_COLLECTIONS``: a fixture built from the constant under test breaks its
#: own setup when the constant is wrong, instead of failing the case that would name
#: the defect.
_COLLECTIONS = [
    col.ATTACHMENTS,
    col.TASKS,
    col.PLANT_INSTANCES,
    col.PLANT_DIARY_ENTRIES,
    col.HARVEST_OBSERVATIONS,
    col.INSPECTIONS,
    col.STORAGE_OBSERVATIONS,
    col.PEST_IMAGE_CONTRIBUTIONS,
    col.PESTS,
]


def _attachment(key: str, *, tenant: str = TENANT, created_by: str = UPLOADER) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant,
        "mime_type": "image/jpeg",
        "byte_size": 1000,
        "sha256": f"sha-{key}",
        "original_filename": f"{key}.jpg",
        "created_by": created_by,
        "category": "task",
        "storage_key": f"{tenant}/task/2026/01/{key}.jpg",
        "created_at": datetime.now(UTC).isoformat(),
    }


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username="root", password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username="root", password=ARANGO_PASSWORD)
    for name in _COLLECTIONS:
        database.create_collection(name)
    yield database
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def repo(db):
    repository = ArangoAttachmentRepository.__new__(ArangoAttachmentRepository)
    repository._db = db
    repository._collection_name = col.ATTACHMENTS
    return repository


def _ask(repo, attachment_id: str, task_key: str = OWN_TASK, tenant: str = TENANT):
    return repo.task_photo_delete_state(attachment_id, tenant, task_key=task_key)


def test_a_staged_upload_reports_staged_with_its_uploader(db, repo):
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})

    assert _ask(repo, "att-1") == ("staged", UPLOADER)


def test_a_photo_the_named_task_references_reports_task(db, repo):
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": ["att-1"]})

    assert _ask(repo, "att-1") == ("task", UPLOADER)


def test_another_task_holding_it_reports_shared(db, repo):
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
    db.collection(col.TASKS).insert({"_key": OTHER_TASK, "tenant_key": TENANT, "photo_refs": ["att-1"]})

    assert _ask(repo, "att-1") == ("shared", UPLOADER)


def test_both_the_named_task_and_another_carrier_reports_shared(db, repo):
    """The precedence that matters: shared wins over task.

    sha256 deduplication makes this the *normal* shape for a photo used twice, and
    reading it as ``task`` would delete a row a plant gallery still shows.
    """
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": ["att-1"]})
    db.collection(col.PLANT_INSTANCES).insert({"_key": "p1", "tenant_key": TENANT, "photo_refs": ["att-1"]})

    assert _ask(repo, "att-1") == ("shared", UPLOADER)


@pytest.mark.parametrize(
    ("collection", "document"),
    [
        (col.PLANT_INSTANCES, {"tenant_key": TENANT, "photo_refs": ["att-1"]}),
        (col.PLANT_DIARY_ENTRIES, {"tenant_key": TENANT, "photo_refs": ["att-1"]}),
        (col.HARVEST_OBSERVATIONS, {"tenant_key": TENANT, "photo_refs": ["att-1"]}),
        (col.INSPECTIONS, {"tenant_key": TENANT, "photo_refs": ["att-1"]}),
        (col.STORAGE_OBSERVATIONS, {"tenant_key": TENANT, "photo_refs": ["att-1"]}),
        (col.PLANT_INSTANCES, {"tenant_key": TENANT, "cover_photo_ref": "att-1"}),
        (col.PEST_IMAGE_CONTRIBUTIONS, {"tenant_key": TENANT, "attachment_id": "att-1"}),
        (col.PESTS, {"reference_image_refs": ["att-1"]}),
    ],
    ids=lambda value: value if isinstance(value, str) else "doc",
)
def test_every_carrier_makes_it_shared(db, repo, collection: str, document: dict):
    """One case per carrier, so a collection dropped from the scan names itself.

    The non-task carriers are the point: a task-category attachment "should" only be
    referenced by a task, and this query refuses to rest on that — the plant-gallery
    cover that shares a task photo's bytes is exactly what sha256 deduplication
    produces.
    """
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
    db.collection(collection).insert({"_key": "carrier-1", **document})

    assert _ask(repo, "att-1")[0] == "shared"


@pytest.mark.parametrize(
    "spelling",
    [
        "att-1",
        "/api/v1/t/tenant-a/attachments/att-1",
        "t/tenant-a/task/2026/01/att-1.jpg",
        "t/tenant-a/task/2026/01/att-1.jpg/",
        "/api/v1/t/tenant-a/attachments/att-1?download=1",
        "/api/v1/t/tenant-a/attachments/att-1/thumbnails/320",
        "see attachment att-1 (uploaded 2026-01-02) for details",
    ],
)
def test_legacy_reference_spellings_still_protect(db, repo, spelling: str):
    """Every shape a `photo_refs` entry has ever had, on the shared path.

    Four review rounds each found one the resolver did not know, and each cost a
    photo. The substring net closed the class; this pins that the *new* query carries
    it too, rather than reintroducing the enumeration it replaced.
    """
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
    db.collection(col.TASKS).insert({"_key": OTHER_TASK, "tenant_key": TENANT, "photo_refs": [spelling]})

    assert _ask(repo, "att-1")[0] == "shared", (
        f"a reference spelled {spelling!r} stopped protecting the photo — this is the "
        f"failure mode that cost a photo in each of review rounds 1 to 4 (#1393)"
    )


def test_a_foreign_tenants_attachment_is_missing(db, repo):
    """Tenant isolation, asserted on the destructive path.

    ``missing`` rather than a state with a ``created_by``: the caller turns this into
    a 404, so the route never confirms that some other tenant's attachment is real.
    """
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1", tenant=OTHER_TENANT))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})

    assert _ask(repo, "att-1") == ("missing", None)


def test_an_unknown_id_is_missing(db, repo):
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})

    assert _ask(repo, "att-nowhere") == ("missing", None)


def test_an_unknown_task_key_leaves_a_staged_photo_staged(db, repo):
    """The named task not existing must not turn ``staged`` into ``task``.

    ``own_refs`` comes from a ``FIRST(...)`` that yields ``null`` for a missing task;
    without the ``|| []`` fallback the ``CONTAINS`` scan over ``null`` would not mean
    what it should. The route resolves the task before calling this, so the case is
    not reachable through it today — which is why it is pinned here rather than left
    to a future caller to discover.
    """
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))

    assert _ask(repo, "att-1", task_key="task-does-not-exist") == ("staged", UPLOADER)


def test_a_foreign_tenants_task_does_not_count_as_the_named_task(db, repo):
    """The task lookup is tenant-filtered, so a key collision across tenants is inert.

    Without the filter, tenant B owning a task with the same key and this photo in its
    ``photo_refs`` would report ``task`` — handing tenant A's caller a deletion the
    photo's own tenant never authorised.
    """
    db.collection(col.ATTACHMENTS).insert(_attachment("att-1"))
    db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": OTHER_TENANT, "photo_refs": ["att-1"]})

    assert _ask(repo, "att-1") == ("staged", UPLOADER)
