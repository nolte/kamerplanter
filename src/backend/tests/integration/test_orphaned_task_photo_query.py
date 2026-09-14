"""#1393 — the query that decides which task photos get deleted, against a real ArangoDB.

`cleanup_orphaned_task_photos` deletes every row this query returns. That makes it
the most dangerous line in the change: a reference the query fails to see is a
photo destroyed, and no amount of care in the Celery task around it can recover
one.

**Why a real database and not a captured query string.** The unit tier can pin
that the AQL mentions the right collections; it cannot say what
``att._key IN (d.photo_refs || [])`` answers when ``photo_refs`` is missing, null,
empty, or holds a URI from before the #1339 normalisation. Those are the shapes
real rows are in, and they decide whether a photo lives.

**Every carrier is exercised, not just tasks.** ``PHOTO_REF_COLLECTIONS`` lists six
collections because a destructive query may not rest on "a task-category
attachment should only ever be referenced by a task". Each of the six gets a row
here, and each must protect its photo — a collection dropped from the tuple turns
exactly one of these red, which is the point of having six cases rather than one
parametrised over a list the code also supplies.

Skipped when no ArangoDB answers on ``localhost:8529``. Run it with::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_orphaned_task_photo_query.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import (
    ArangoAttachmentRepository,
)

ARANGO_URL = "http://localhost:8529"
ARANGO_PASSWORD = "rootpassword"
TEST_DATABASE = "kamerplanter_orphan_photo_test"

TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"
#: The quota measurement deletes what it finds, so it gets a tenant nothing else
#: reads. Sharing one would make every other case depend on test order — and the
#: order that happens to work today is not a property anyone is maintaining.
QUOTA_TENANT = "tenant-quota"

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
OLD = NOW - timedelta(hours=72)
RECENT = NOW - timedelta(hours=1)
CUTOFF = NOW - timedelta(hours=48)

ARANGO_AVAILABLE = False
try:  # pragma: no cover - probe, not behaviour
    from arango import ArangoClient

    _probe = ArangoClient(hosts=ARANGO_URL)
    _probe.db("_system", username="root", password=ARANGO_PASSWORD).version()
    ARANGO_AVAILABLE = True
    _probe.close()
except Exception:  # noqa: BLE001 - any failure means "not available"
    pass

pytestmark = pytest.mark.skipif(not ARANGO_AVAILABLE, reason="ArangoDB not available on localhost:8529")


def _attachment(key: str, *, created_at: datetime, category: str = "task", tenant: str = TENANT) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant,
        "mime_type": "image/jpeg",
        "byte_size": 1000,
        "sha256": f"sha-{key}",
        "original_filename": f"{key}.jpg",
        "created_by": "user-1",
        "category": category,
        "storage_key": f"{tenant}/{category}/{key}.jpg",
        "created_at": created_at.isoformat(),
    }


#: One row per carrier, so a collection dropped from ``PHOTO_REF_COLLECTIONS``
#: fails exactly one case and names it.
REFERENCED: list[tuple[str, str, dict]] = [
    (col.TASKS, "ref-task", {"tenant_key": TENANT, "title": "Giessen"}),
    (col.PLANT_INSTANCES, "ref-plant", {"tenant_key": TENANT, "instance_id": "P-1"}),
    (col.PLANT_DIARY_ENTRIES, "ref-diary", {"tenant_key": TENANT, "plant_key": "p1"}),
    (col.HARVEST_OBSERVATIONS, "ref-harvest", {"tenant_key": TENANT}),
    (col.INSPECTIONS, "ref-inspection", {"tenant_key": TENANT}),
    (col.STORAGE_OBSERVATIONS, "ref-storage", {"tenant_key": TENANT}),
]


#: The other fields that hold an attachment id, one row each.
#:
#: None of these normally holds a ``task``-category attachment — which is exactly
#: why they are here. The sweep's whole design refuses to rest on "a task-category
#: row should only ever be referenced by a task", and these cases are that refusal
#: applied to the three fields review found unchecked: the id is task-category *and*
#: referenced from one of them, so only an actual check saves it.
REFERENCED_BY_OTHER_FIELD: list[tuple[str, str, dict]] = [
    (col.PLANT_INSTANCES, "ref-cover", {"tenant_key": TENANT, "cover_photo_ref": "ref-cover"}),
    (
        col.PEST_IMAGE_CONTRIBUTIONS,
        "ref-pest-image",
        {"tenant_key": TENANT, "attachment_id": "ref-pest-image"},
    ),
    (col.PESTS, "ref-pest-gallery", {"reference_image_refs": ["ref-pest-gallery"]}),
]


#: One per review round, each a shape that used to be deleted.
#:
#: ``{key}`` is the attachment id, ``{tenant}`` the tenant slug. The last entry is
#: the one `_photo_response` hands to every client as `thumbnail_uris`, so it is not
#: a hypothetical at all.
SPELLINGS_THAT_COST_A_PHOTO: list[str] = [
    "t/{tenant}/task/2026/01/{key}.jpg",
    "t/{tenant}/task/2026/01/{key}.jpg/",
    "/api/v1/t/{tenant}/attachments/{key}?download=1",
    "/api/v1/t/{tenant}/attachments/{key}/thumbnails/320",
]


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username="root", password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username="root", password=ARANGO_PASSWORD)

    # From this file's own list, deliberately **not** from `PHOTO_REF_COLLECTIONS`.
    # Building the fixture out of the constant under test means dropping an entry
    # breaks the setup instead of demonstrating the defect: measured, the whole
    # module errored rather than failing the one carrier case. A test whose data
    # comes from the code it checks cannot fail the way it is supposed to.
    # `dict.fromkeys` rather than a set: deduplicated (plant_instances appears in
    # both lists) while keeping a stable order, so a failure reads the same twice.
    for name in dict.fromkeys(
        [
            col.ATTACHMENTS,
            *[collection for collection, _key, _doc in REFERENCED],
            *[collection for collection, _key, _doc in REFERENCED_BY_OTHER_FIELD],
        ]
    ):
        database.create_collection(name)

    attachments = database.collection(col.ATTACHMENTS)

    # The three orphan paths #1393 names.
    attachments.insert(_attachment("orphan-abandoned", created_at=OLD))
    attachments.insert(_attachment("orphan-unstaged", created_at=OLD))
    attachments.insert(_attachment("orphan-task-deleted", created_at=OLD))
    # Another tenant's orphan: the sweep is installation-wide, so it belongs here.
    attachments.insert(_attachment("orphan-other-tenant", created_at=OLD, tenant=OTHER_TENANT))

    # Too young to judge: an upload is an orphan by design until its form is submitted.
    attachments.insert(_attachment("young-upload", created_at=RECENT))

    # Not a task photo at all.
    attachments.insert(_attachment("diary-photo", created_at=OLD, category="diary"))

    # One referenced photo per carrier.
    for collection, key, doc in REFERENCED:
        attachments.insert(_attachment(key, created_at=OLD))
        database.collection(collection).insert({**doc, "_key": f"doc-{key}", "photo_refs": [key]})

    # The quota measurement's own rows: two orphans and one referenced photo, so
    # both directions can be measured without touching another tenant's fixture.
    attachments.insert(_attachment("quota-orphan-1", created_at=OLD, tenant=QUOTA_TENANT))
    attachments.insert(_attachment("quota-orphan-2", created_at=OLD, tenant=QUOTA_TENANT))
    attachments.insert(_attachment("quota-referenced", created_at=OLD, tenant=QUOTA_TENANT))
    database.collection(col.TASKS).insert(
        {"_key": "quota-task", "tenant_key": QUOTA_TENANT, "photo_refs": ["quota-referenced"]}
    )

    for collection, key, doc in REFERENCED_BY_OTHER_FIELD:
        attachments.insert(_attachment(key, created_at=OLD))
        database.collection(collection).insert({**doc, "_key": f"doc-{key}"})

    # Historical `photo_refs` spellings. `migrate_photo_refs` exists because entries
    # were once `/api/v1/t/{slug}/attachments/{id}` URIs or storage keys, and that
    # migration is manual rather than beat-scheduled — so an installation that never
    # ran it still holds them.
    # **The shapes the writer actually produces**, not a simplified stand-in.
    #
    # The first version of this fixture planted `f"{TENANT}/task/ref-by-storage-key"`
    # — no extension — while `_attachment()` gave the same row a `storage_key`
    # ending in `.jpg`. The fixture contradicted its own data: it asserted protection
    # for a shape that cannot occur and stayed green while the real one was deleted.
    # That is the #947 / #1155 class this module's own docstring names as the reason
    # the original defect went unseen.
    #
    # `StorageKeyBuilder` emits `t/{tenant}/{cat}/{yyyy}/{mm}/{ulid}.{ext}`, and
    # `normalize_photo_ref` resolves a reference to the **ULID stem** of the last
    # segment — extension and `_t{size}` thumbnail suffix stripped. Every row below
    # carries an extension for that reason.
    attachments.insert(_attachment("ref-by-uri", created_at=OLD))
    attachments.insert(_attachment("ref-by-storage-key", created_at=OLD))
    attachments.insert(_attachment("ref-by-thumb-suffix", created_at=OLD))
    tasks_legacy = database.collection(col.TASKS)
    tasks_legacy.insert(
        {
            "_key": "t-legacy-uri",
            "tenant_key": TENANT,
            "photo_refs": [f"/api/v1/t/{TENANT}/attachments/ref-by-uri.jpg"],
        }
    )
    tasks_legacy.insert(
        {
            "_key": "t-legacy-key",
            "tenant_key": TENANT,
            "photo_refs": [f"t/{TENANT}/task/2026/01/ref-by-storage-key.jpg"],
        }
    )
    tasks_legacy.insert(
        {
            "_key": "t-legacy-thumb",
            "tenant_key": TENANT,
            "photo_refs": [f"t/{TENANT}/task/2026/01/ref-by-thumb-suffix_t320.webp"],
        }
    )

    # **Every spelling that has cost a photo, one row each.**
    #
    # Four review rounds each found one the candidate list did not know. They are
    # here not because the list now knows them — it does, for the first three — but
    # because the sweep no longer depends on knowing: a reference that *mentions* the
    # key protects the photo, whatever shape it is in. These rows are what proves
    # that, and the last of them is the one the product builds itself.
    for index, spelling in enumerate(SPELLINGS_THAT_COST_A_PHOTO):
        key = f"ref-spelling-{index}"
        attachments.insert(_attachment(key, created_at=OLD))
        database.collection(col.TASKS).insert(
            {
                "_key": f"t-spelling-{index}",
                "tenant_key": TENANT,
                "photo_refs": [spelling.format(key=key, tenant=TENANT)],
            }
        )

    # A shape nobody has enumerated, and deliberately unlike every branch of the
    # candidate list: wrapped in text, with the id neither first nor last.
    attachments.insert(_attachment("ref-exotic", created_at=OLD))
    database.collection(col.TASKS).insert(
        {
            "_key": "t-exotic",
            "tenant_key": TENANT,
            "photo_refs": ["see attachment ref-exotic (uploaded 2026-01-02) for details"],
        }
    )

    # Shapes a real row is in, none of which may be read as a reference.
    attachments.insert(_attachment("orphan-empty-refs", created_at=OLD))
    attachments.insert(_attachment("orphan-null-refs", created_at=OLD))
    attachments.insert(_attachment("orphan-no-field", created_at=OLD))
    tasks = database.collection(col.TASKS)
    tasks.insert({"_key": "t-empty", "tenant_key": TENANT, "photo_refs": []})
    tasks.insert({"_key": "t-null", "tenant_key": TENANT, "photo_refs": None})
    tasks.insert({"_key": "t-missing", "tenant_key": TENANT})

    yield database

    system.delete_database(TEST_DATABASE)
    client.close()


@pytest.fixture
def repo(db):
    return ArangoAttachmentRepository(db)


def _found(repo) -> set[str]:
    return {a.key for a in repo.find_orphaned_task_photos(older_than=CUTOFF)}


class TestWhatTheSweepCollects:
    def test_the_three_orphan_paths_are_found(self, repo):
        found = _found(repo)

        assert {"orphan-abandoned", "orphan-unstaged", "orphan-task-deleted"} <= found

    def test_another_tenant_orphan_is_found_too(self, repo):
        """The sweep is housekeeping, not a tenant operation."""
        assert "orphan-other-tenant" in _found(repo)

    def test_the_row_carries_its_own_tenant(self, repo):
        """The caller deletes tenant-scoped, so it needs the row's tenant back."""
        by_key = {a.key: a for a in repo.find_orphaned_task_photos(older_than=CUTOFF)}

        assert by_key["orphan-other-tenant"].tenant_key == OTHER_TENANT


class TestWhatTheSweepMustNotTouch:
    @pytest.mark.parametrize(("collection", "key", "_doc"), REFERENCED, ids=[r[0] for r in REFERENCED])
    def test_a_photo_referenced_by_each_carrier_survives(self, repo, collection: str, key: str, _doc: dict):
        """One case per carrier. Dropping a collection from the tuple fails exactly this one."""
        assert key not in _found(repo), (
            f"a photo referenced from {collection} was offered for deletion; "
            "PHOTO_REF_COLLECTIONS is missing it (#1393)"
        )

    @pytest.mark.parametrize(
        ("collection", "key", "_doc"),
        REFERENCED_BY_OTHER_FIELD,
        ids=[row[0] for row in REFERENCED_BY_OTHER_FIELD],
    )
    def test_a_photo_referenced_by_another_field_survives(self, repo, collection: str, key: str, _doc: dict):
        """`cover_photo_ref`, `attachment_id`, `reference_image_refs` (#1424 finding 8).

        These are scalar and list fields outside ``photo_refs``. The row here is
        deliberately ``category == task`` while being referenced from one of them:
        if the category assumption ever slips, only the check saves the photo, and
        that is the assumption this whole design declines to trust.
        """
        assert key not in _found(repo), (
            f"a photo referenced from {collection} was offered for deletion; "
            "ATTACHMENT_REF_FIELDS is missing that field (#1393)"
        )

    @pytest.mark.parametrize(
        ("index", "spelling"),
        list(enumerate(SPELLINGS_THAT_COST_A_PHOTO)),
        ids=SPELLINGS_THAT_COST_A_PHOTO,
    )
    def test_no_spelling_that_ever_cost_a_photo_costs_one_again(self, repo, index: int, spelling: str):
        """One case per review round (#1424).

        The point is not that the candidate list has grown to cover these. It is that
        the sweep stopped depending on the list: a reference mentioning the key
        protects the photo whatever shape it takes, so the next unenumerated spelling
        is a missed collection rather than a destroyed photo.
        """
        assert f"ref-spelling-{index}" not in _found(repo), (
            f"a photo referenced as {spelling!r} was offered for deletion — the sweep is "
            "back to enumerating spellings (#1393)"
        )

    def test_a_spelling_nobody_has_thought_of_yet_is_also_safe(self, repo):
        """The class, not its four instances.

        A shape invented here on purpose, matching no branch of the candidate list.
        If this ever fails, someone removed the substring net and the sweep is one
        unusual reference away from destroying a photo again.
        """
        assert "ref-exotic" not in _found(repo)

    def test_a_young_upload_survives(self, repo):
        """The floor is the whole safety story: every upload is briefly an orphan."""
        assert "young-upload" not in _found(repo)

    def test_a_non_task_photo_is_out_of_scope(self, repo):
        assert "diary-photo" not in _found(repo)

    @pytest.mark.parametrize(
        ("key", "shape"),
        [
            ("ref-by-uri", "an /attachments/{id}.{ext} URI"),
            ("ref-by-storage-key", "a storage key t/{tenant}/{cat}/{yyyy}/{mm}/{ulid}.{ext}"),
            ("ref-by-thumb-suffix", "a thumbnail key carrying the _t{size} suffix"),
        ],
    )
    def test_a_legacy_reference_spelling_still_protects_its_photo(self, repo, key: str, shape: str):
        """The sweep must not depend on a migration nobody ran.

        ``migrate_photo_refs`` normalises these to bare ids, and it is manual — not
        beat-scheduled. An installation that never ran it would otherwise have every
        referenced task photo classified as an orphan and deleted, which is the worst
        possible outcome of a housekeeping job.
        """
        assert key not in _found(repo), f"a photo referenced as {shape} was offered for deletion (#1393)"

    @pytest.mark.parametrize("shape", ["orphan-empty-refs", "orphan-null-refs", "orphan-no-field"])
    def test_an_absent_photo_refs_list_does_not_crash_the_query(self, repo, shape: str):
        """``photo_refs`` missing, null or empty are all real shapes.

        They must read as "references nothing" rather than erroring — an exception
        here would leave the sweep never running, which is a silent failure of the
        whole feature rather than a loud one.
        """
        assert shape in _found(repo)


class TestTheFloorIsHonoured:
    def test_nothing_is_returned_when_the_cutoff_predates_every_row(self, repo):
        ancient = NOW - timedelta(days=3650)

        assert repo.find_orphaned_task_photos(older_than=ancient) == []

    def test_the_limit_bounds_the_batch(self, repo):
        """A large backlog drains over several runs rather than in one transaction."""
        assert len(repo.find_orphaned_task_photos(older_than=CUTOFF, limit=2)) == 2


class TestTheQuotaIsActuallyReclaimed:
    """#1393's last acceptance criterion: a before/after measurement.

    The leak is not an exposure — every orphan stays tenant-scoped and
    permission-gated — it is a **quota** problem, because
    ``AttachmentService._enforce_quota`` counts every attachment row of the tenant
    against ``STORAGE_TENANT_QUOTA_MB``, linked or not. So the claim worth proving
    is not "rows disappear" but "the bytes the user could not reclaim come back".

    Measured through ``sum_bytes_by_tenant``, which is the function the quota gate
    itself calls, rather than by counting the rows this test deleted. Counting its
    own deletions would pass even if the quota read a different set of rows — and
    that divergence is precisely the kind of thing that makes a quota bug survive.

    The rows are removed with ``repo.delete``: this tier has ArangoDB and no object
    storage, so it measures the catalogue half of the sweep. The storage half is
    ``AttachmentService.delete``, which has its own tests.
    """

    def test_deleting_what_the_sweep_finds_frees_the_bytes_it_held(self, repo, db):
        before = repo.sum_bytes_by_tenant(QUOTA_TENANT)
        orphans = [a for a in repo.find_orphaned_task_photos(older_than=CUTOFF) if a.tenant_key == QUOTA_TENANT]
        assert orphans, "no orphans to measure — the fixture stopped exercising the leak"

        held_by_orphans = sum(a.byte_size for a in orphans)
        for attachment in orphans:
            assert attachment.key is not None
            repo.delete(attachment.key, QUOTA_TENANT)

        after = repo.sum_bytes_by_tenant(QUOTA_TENANT)

        assert after == before - held_by_orphans, (
            f"the tenant's counted bytes went {before} -> {after}, expected "
            f"{before - held_by_orphans}: the quota did not release what the sweep removed"
        )
        assert after < before, "the sweep freed nothing at all"

    def test_the_photos_that_survive_still_count(self, repo):
        """The control, and the direction that would be a disaster.

        A sweep that freed *everything* would also satisfy "after < before". What
        must remain counted is every referenced photo, because it is still stored.
        """
        remaining = repo.sum_bytes_by_tenant(QUOTA_TENANT)

        assert remaining > 0, "every photo of the tenant was swept, referenced ones included"
