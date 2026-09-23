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

Needs a real ArangoDB — see the module docstring of ``test_orphaned_task_photo_query.py``
for how to start one; a missing database is a failure in CI and a loud skip locally
(``conftest.py``). This file carries the only executing coverage of this query, which is
the reason it is written as carefully as it is — and the reason #1432 put the tier into
a gate instead of leaving it to self-skip.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("task_photo_delete_state")
TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"
OWN_TASK = "task-own"
OTHER_TASK = "task-other"
UPLOADER = "user-uploader"


pytestmark = pytest.mark.usefixtures("arango_db")

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
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
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
    ],
)
def test_legacy_reference_spellings_still_protect(db, repo, spelling: str):
    """Every shape a `photo_refs` entry has ever had, on the shared path.

    Four review rounds each found one the resolver did not know, and each cost a
    photo. Resolving *every* path segment — rather than only the last — covers them
    all, including ``/attachments/{id}/thumbnails/{size}``, where the identifier is in
    the middle and the last segment is the size.

    A free-prose entry ("see attachment att-1 (uploaded …) for details") was listed
    here until round 7 and is gone, because it cannot occur and never could:
    ``TaskService._verify_photo_refs`` and ``PlantDiaryService`` both resolve each new
    reference through ``attachment_repo.get(ref, tenant_key)``, a document-key lookup
    that refuses anything else with a 422. That case was invented to justify a
    substring test, and the substring test is what round 7 removed — against numeric
    document keys it reported unrelated photos as shared, making them undeletable.
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


class TestTheKeyIsNumericAndStorageKeysCarryTheirOwnUlid:
    """Round 7 — the two premises the reference resolver was built on, both false.

    The resolver's safety argument read: "A ULID is 26 characters from Crockford's
    alphabet, so an incidental match is not a practical concern." Measured against a
    real ArangoDB, an attachment's ``_key`` is a **7-digit number** (``1024799``):
    ``BaseArangoRepository._to_doc`` pops ``_key`` before the insert and nothing
    configures a key generator, so ArangoDB's traditional generator assigns it.

    The second premise was that a storage key embeds the document key.
    ``StorageKeyBuilder.build`` mints its *own* ULID when the caller passes none, and
    ``AttachmentService.upload`` passes none — so ``t/{tenant}/task/2026/01/{ulid}.jpg``
    holds a ULID that has no relation to ``_key`` at all.

    Both premises were encoded in the fixtures, which is why seven review rounds
    could not see them: ``_attachment()`` built ``storage_key`` out of the very
    ``_key`` it was testing, a shape production never produces.
    """

    def test_a_thumbnail_size_segment_cannot_collide_with_a_key(self, db, repo):
        """Why the resolver may compare whole segments rather than parse known shapes.

        A ``/thumbnails/320`` size *is* a path segment, so segment matching would
        report an attachment keyed ``320`` as referenced. Measured against a real
        ArangoDB, no such key exists: two fresh databases assigned ``1024799`` and
        ``1034686``, seven digits, because the traditional generator starts from a
        large server tick. The first version of this case planted ``_key="320"`` — my
        own fixture inventing an impossible value for the fourth time in this PR, the
        same way ``_attachment()`` built ``storage_key`` out of the key it was testing.

        So this asserts the reachable half: a size segment does not protect an
        attachment whose key merely *looks* related.
        """
        db.collection(col.ATTACHMENTS).insert(_attachment("1024799"))
        db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
        db.collection(col.TASKS).insert(
            {
                "_key": OTHER_TASK,
                "tenant_key": TENANT,
                "photo_refs": ["/api/v1/t/tenant-a/attachments/2048888/thumbnails/1024"],
            }
        )

        assert _ask(repo, "1024799")[0] == "staged", (
            "a reference to a different attachment protected this one — under the old "
            "substring test every digit coincidence did (#1393 round 7, finding 1)"
        )

    def test_a_numeric_key_that_prefixes_a_newer_key_is_not_falsely_shared(self, db, repo):
        """The same class, in the shape a long-lived installation actually reaches.

        Keys are assigned monotonically, so an installation eventually holds both
        ``1234567`` and ``12345678``. A reference to the newer one then "mentions" the
        older one under substring matching, and the older one becomes undeletable.
        """
        db.collection(col.ATTACHMENTS).insert(_attachment("1234567"))
        db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
        db.collection(col.TASKS).insert({"_key": OTHER_TASK, "tenant_key": TENANT, "photo_refs": ["12345678"]})

        assert _ask(repo, "1234567")[0] == "staged"

    def test_a_real_storage_key_reference_still_protects_the_photo(self, db, repo):
        """Finding 2, and this is the direction that destroys data.

        The stored ``storage_key`` carries its own ULID. A ``photo_refs`` entry holding
        that storage key resolves to no document key at all, so the photo is reported
        unreferenced — and the sweep deletes a photo a carrier still shows.
        """
        storage_key = "t/tenant-a/task/2026/01/01JQ8ZK4Y7N3M5P6R8T9V0W1X2.jpg"
        db.collection(col.ATTACHMENTS).insert({**_attachment("1024799"), "storage_key": storage_key})
        db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
        db.collection(col.TASKS).insert({"_key": OTHER_TASK, "tenant_key": TENANT, "photo_refs": [storage_key]})

        assert _ask(repo, "1024799")[0] == "shared", (
            "a storage-key reference protected nothing, so the sweep would destroy a "
            "photo another carrier still references (#1393 round 7, finding 2)"
        )

    def test_the_same_storage_key_reference_seen_by_the_named_task(self, db, repo):
        """And it must resolve to ``task``, not ``staged``, for the delete route.

        Otherwise the route treats the task's own completion photo as a staged upload
        and lets its uploader — any grower — destroy the completion record.
        """
        storage_key = "t/tenant-a/task/2026/01/01JQ8ZK4Y7N3M5P6R8T9V0W1X2.jpg"
        db.collection(col.ATTACHMENTS).insert({**_attachment("1024799"), "storage_key": storage_key})
        db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": [storage_key]})

        assert _ask(repo, "1024799")[0] == "task"

    def test_a_carrier_row_without_a_tenant_stamp_still_protects(self, db, repo):
        """Finding 3. ``tenant_key`` defaults to ``""`` on Task, DiaryEntry and Inspection.

        The interactive query narrows its reference scan to the caller's tenant. A
        legacy or imported carrier row written before the tenant backfill carries no
        stamp, and a strict equality would drop it — reporting a photo it still
        references as staged, so its uploader (any grower) could destroy it and leave
        the dangling reference this whole design exists to prevent.

        Asserted on the unstamped row alone, not alongside a stamped one, so a fix
        that merely widened the filter to "any tenant" would not pass by accident.
        """
        db.collection(col.ATTACHMENTS).insert(_attachment("1024799"))
        db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
        db.collection(col.TASKS).insert({"_key": OTHER_TASK, "tenant_key": "", "photo_refs": ["1024799"]})

        assert _ask(repo, "1024799")[0] == "shared"

    def test_a_foreign_tenants_carrier_still_does_not_protect(self, db, repo):
        """The control for the case above: tolerating "" must not tolerate everything.

        Without this, widening the filter to drop the tenant condition entirely would
        satisfy the previous test and quietly undo the narrowing that finding 3 of
        round 5 added.
        """
        db.collection(col.ATTACHMENTS).insert(_attachment("1024799"))
        db.collection(col.TASKS).insert({"_key": OWN_TASK, "tenant_key": TENANT, "photo_refs": []})
        db.collection(col.TASKS).insert({"_key": OTHER_TASK, "tenant_key": OTHER_TENANT, "photo_refs": ["1024799"]})

        assert _ask(repo, "1024799")[0] == "staged"
