"""REQ-053 WP 8.18 (#2661) - the bed-photo transactions against ArangoDB.

What only the database can show: the bed is resolved through its site's tenant inside the transaction (a
``Location`` has no ``tenant_key``), the attachment is the tenant's own ``location`` record, the touch of that
record makes a concurrent removal conflict, a removal keeps a photo another bed still names (``photo_refs`` and
``cover_photo_ref`` are carriers of the reference scan), and the bed and site deletes report the photos they
released. The service decisions are pinned in ``tests/unit/domain/services/test_location_photo_service.py``.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import AttachmentCategory, TenantRole
from app.common.exceptions import PlanValidationError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.location_photo_repository import ArangoLocationPhotoRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.interfaces.location_photo_repository import LocationPhotoState
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_import_service import GardenPlanImportService
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.location_photo_service import LocationPhotoService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("location_photo_repository")
A, B = "ten_a", "ten_b"
USER = "u_sabine"


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


def _photo(key: str, *, tenant: str = A, category: str = AttachmentCategory.LOCATION.value) -> dict[str, Any]:
    return {
        "_key": key,
        "tenant_key": tenant,
        "mime_type": "image/jpeg",
        "byte_size": 10,
        "sha256": key.ljust(64, "0"),
        "original_filename": "beet.jpg",
        "created_by": USER,
        "category": category,
        "storage_key": f"t/{tenant}/{category}/2026/11/{key}.jpg",
    }


def _bed(key: str, site: str, **extra: Any) -> dict[str, Any]:
    return {"_key": key, "name": key, "site_key": site, "location_type_key": "bed", "area_m2": 2.0, **extra}


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    for site, tenant in (("site_a", A), ("site_b", B)):
        database.collection(col.SITES).insert(
            {"_key": site, "tenant_key": tenant, "name": site, "type": "outdoor", "plan": {"plan_revision": 1}}
        )
    database.collection(col.LOCATIONS).insert(_bed("bed_a", "site_a"))
    database.collection(col.LOCATIONS).insert(_bed("bed_a2", "site_a"))
    database.collection(col.LOCATIONS).insert(_bed("bed_b", "site_b"))
    return database


def _stored(db, key: str) -> tuple[list[str], str | None]:
    doc = db.collection(col.LOCATIONS).get(key)
    return doc.get("photo_refs") or [], doc.get("cover_photo_ref")


class TestTheWrites:
    def test_add_prepends_sets_the_first_cover_and_touches_the_record(self, db) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p1"))
        db.collection(col.ATTACHMENTS).insert(_photo("p2"))
        repo = ArangoLocationPhotoRepository(db)

        first = repo.add_photo("bed_a", tenant_key=A, attachment_key="p1", max_photos=50)
        second = repo.add_photo("bed_a", tenant_key=A, attachment_key="p2", max_photos=50)
        again = repo.add_photo("bed_a", tenant_key=A, attachment_key="p2", max_photos=50)

        assert (first.status, second.status, again.status) == ("written", "written", "unchanged")
        assert second.state == LocationPhotoState(("p2", "p1"), "p1")
        assert _stored(db, "bed_a") == (["p2", "p1"], "p1")
        assert db.collection(col.ATTACHMENTS).get("p2").get("updated_at")  # the touch

    @pytest.mark.parametrize(
        "record",
        [_photo("p_x", tenant=B), _photo("p_x", category=AttachmentCategory.PLANT.value), None],
        ids=["foreign_tenant", "wrong_category", "absent"],
    )
    def test_add_refuses_anything_but_the_tenants_location_record(self, db, record) -> None:
        if record is not None:
            db.collection(col.ATTACHMENTS).insert(record)

        write = ArangoLocationPhotoRepository(db).add_photo("bed_a", tenant_key=A, attachment_key="p_x", max_photos=50)

        assert write.status == "attachment_not_found"
        assert _stored(db, "bed_a") == ([], None)
        if record is not None:
            assert "updated_at" not in db.collection(col.ATTACHMENTS).get("p_x")  # nothing of another kind touched

    def test_another_tenants_bed_is_not_found_inside_the_transaction(self, db) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p1"))
        repo = ArangoLocationPhotoRepository(db)

        assert repo.add_photo("bed_b", tenant_key=A, attachment_key="p1", max_photos=50).status == "location_not_found"
        assert repo.set_cover("bed_b", tenant_key=A, attachment_key=None).status == "location_not_found"
        assert repo.remove_photo("bed_b", tenant_key=A, attachment_key="p1").status == "location_not_found"
        assert _stored(db, "bed_b") == ([], None)

    def test_an_empty_tenant_is_no_tenant(self, db) -> None:
        with pytest.raises(ValueError):
            ArangoLocationPhotoRepository(db).add_photo("bed_a", tenant_key="", attachment_key="p1", max_photos=50)

    def test_the_bound_holds_in_the_transaction(self, db) -> None:
        for key in ("p1", "p2"):
            db.collection(col.ATTACHMENTS).insert(_photo(key))
        repo = ArangoLocationPhotoRepository(db)
        repo.add_photo("bed_a", tenant_key=A, attachment_key="p1", max_photos=1)

        assert repo.add_photo("bed_a", tenant_key=A, attachment_key="p2", max_photos=1).status == "limit_reached"
        assert _stored(db, "bed_a") == (["p1"], "p1")

    def test_remove_clears_the_cover_and_drops_the_attribute(self, db) -> None:
        db.collection(col.LOCATIONS).update({"_key": "bed_a", "photo_refs": ["p2", "p1"], "cover_photo_ref": "p1"})
        repo = ArangoLocationPhotoRepository(db)

        write = repo.remove_photo("bed_a", tenant_key=A, attachment_key="p1")

        assert write.state == LocationPhotoState(("p2",), None)
        assert "cover_photo_ref" not in db.collection(col.LOCATIONS).get("bed_a")
        assert repo.remove_photo("bed_a", tenant_key=A, attachment_key="p1").status == "not_a_photo"

    def test_the_cover_must_be_a_photo_of_the_bed(self, db) -> None:
        db.collection(col.LOCATIONS).update({"_key": "bed_a", "photo_refs": ["p2", "p1"], "cover_photo_ref": "p1"})
        repo = ArangoLocationPhotoRepository(db)

        assert repo.set_cover("bed_a", tenant_key=A, attachment_key="elsewhere").status == "not_a_photo"
        assert repo.set_cover("bed_a", tenant_key=A, attachment_key="p2").state == LocationPhotoState(
            ("p2", "p1"), "p2"
        )
        assert _stored(db, "bed_a") == (["p2", "p1"], "p2")


class _AddOvertaken(ArangoLocationPhotoRepository):
    """An add that has read the bed when a rival commits, before it touches the attachment record."""

    def __init__(self, db, rival) -> None:
        super().__init__(db)
        self._rival = rival

    def _read(self, txn, location_key, tenant_key):  # type: ignore[no-untyped-def,override]
        state = super()._read(txn, location_key, tenant_key)
        self._rival()
        return state


class _RemovalOvertaken(ArangoAttachmentRepository):
    def __init__(self, db, rival) -> None:
        super().__init__(db)
        self._rival = rival

    def _unreferenced_in(self, txn, attachment_id, tenant_key) -> bool:  # type: ignore[no-untyped-def]
        answer = super()._unreferenced_in(txn, attachment_id, tenant_key)
        self._rival()
        return answer


class TestTheReferenceIsACarrier:
    """``locations.photo_refs`` / ``cover_photo_ref`` are in the reference scan: a named photo is never removed."""

    @pytest.mark.parametrize(
        "fields",
        [{"photo_refs": ["p1"]}, {"photo_refs": ["p1"], "cover_photo_ref": "p1"}],
        ids=["photo_refs", "photo_refs_and_cover"],
    )
    def test_a_photo_another_bed_names_is_kept(self, db, fields) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p1"))
        db.collection(col.LOCATIONS).update({"_key": "bed_a2", **fields})

        assert ArangoAttachmentRepository(db).remove_if_unreferenced("p1", A) is None
        assert db.collection(col.ATTACHMENTS).get("p1") is not None

    def test_a_photo_no_bed_names_is_removed(self, db) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p1"))

        assert ArangoAttachmentRepository(db).remove_if_unreferenced("p1", A) is not None

    def test_a_removal_committed_after_the_adds_read_makes_the_add_conflict(self, db) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p1"))

        def rival() -> None:  # nothing names p1 yet, so another request removes it
            assert ArangoAttachmentRepository(db).remove_if_unreferenced("p1", A) is not None

        with pytest.raises(WriteConflictError):
            _AddOvertaken(db, rival).add_photo("bed_a", tenant_key=A, attachment_key="p1", max_photos=50)

        assert db.collection(col.ATTACHMENTS).get("p1") is None  # the race really happened
        assert _stored(db, "bed_a") == ([], None)  # the bed names no deleted photo

    def test_an_add_committed_after_the_scan_makes_the_removal_conflict_and_the_photo_stays(self, db) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p1"))

        def rival() -> None:  # bed_a takes p1 after the removal's scan saw no reference
            ArangoLocationPhotoRepository(db).add_photo("bed_a", tenant_key=A, attachment_key="p1", max_photos=50)

        with pytest.raises(WriteConflictError):
            _RemovalOvertaken(db, rival).remove_if_unreferenced("p1", A)

        assert _stored(db, "bed_a") == (["p1"], "p1")
        assert db.collection(col.ATTACHMENTS).get("p1") is not None


class TestTheDeletesReportTheirPhotos:
    def test_the_plan_batch_delete_reports_the_photos_of_the_deleted_bed(self, db) -> None:
        db.collection(col.LOCATIONS).update({"_key": "bed_a", "photo_refs": ["p2", "p1"], "cover_photo_ref": "p1"})
        db.collection(col.LOCATIONS).update({"_key": "bed_a2", "photo_refs": ["other"]})
        plans = GardenPlanService(ArangoSiteRepository(db), ArangoGardenPlanRepository(db))

        result = plans.apply_batch(
            "site_a",
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            expected_revision=None,
            operations=[{"op": "delete", "entity": "location", "key": "bed_a"}],
            body_bytes=0,
        )

        assert result.released_photo_refs == ["p2", "p1"]
        assert db.collection(col.LOCATIONS).get("bed_a") is None
        assert "released_photo_refs" not in result.model_dump()  # never part of the response

    def test_the_site_delete_reports_the_photos_of_its_beds(self, db) -> None:
        db.collection(col.LOCATIONS).update({"_key": "bed_a", "photo_refs": ["p1", "shared"]})
        db.collection(col.LOCATIONS).update({"_key": "bed_a2", "photo_refs": ["shared"]})
        db.collection(col.LOCATIONS).update({"_key": "bed_b", "photo_refs": ["p_b"]})

        deletion = ArangoSiteRepository(db).delete_site("site_a", tenant_key=A, user_key=USER)

        assert sorted(deletion.location_photo_refs) == ["p1", "shared"]
        assert _stored(db, "bed_b") == (["p_b"], None)


class _Deleter:
    """The slice of ``AttachmentService`` the photo service needs, over the real repository (no object storage)."""

    def __init__(self, repo: ArangoAttachmentRepository) -> None:
        self._repo = repo

    async def delete_if_unreferenced(self, attachment_id: str, tenant_key: str) -> bool:
        return self._repo.remove_if_unreferenced(attachment_id, tenant_key) is not None


class TestTheServiceOnTheDatabase:
    def _service(self, db) -> LocationPhotoService:
        attachments = ArangoAttachmentRepository(db)
        return LocationPhotoService(
            ArangoSiteRepository(db), ArangoLocationPhotoRepository(db), attachments, lambda: _Deleter(attachments)
        )

    def test_a_foreign_attachment_is_reference_not_found(self, db) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p_b", tenant=B))

        with pytest.raises(PlanValidationError) as refused:
            self._service(db).add_photo("bed_a", "p_b", tenant_key=A, user_key=USER, role=TenantRole.GROWER)

        assert refused.value.codes == ["reference.not_found"] and _stored(db, "bed_a") == ([], None)

    async def test_link_list_remove_round_trip(self, db) -> None:
        db.collection(col.ATTACHMENTS).insert(_photo("p1"))
        db.collection(col.ATTACHMENTS).insert(_photo("shared"))
        service = self._service(db)
        for bed, photo in (("bed_a", "p1"), ("bed_a", "shared"), ("bed_a2", "shared")):
            service.add_photo(bed, photo, tenant_key=A, user_key=USER, role=TenantRole.GROWER)

        listed = service.list_photos("bed_a", tenant_key=A, user_key=USER, role=TenantRole.VIEWER)
        assert [photo.attachment.key for photo in listed.photos] == ["shared", "p1"] and listed.cover_photo_ref == "p1"

        await service.remove_photo("bed_a", "p1", tenant_key=A, user_key=USER, role=TenantRole.GROWER)
        await service.remove_photo("bed_a", "shared", tenant_key=A, user_key=USER, role=TenantRole.GROWER)

        assert _stored(db, "bed_a") == ([], None)
        assert db.collection(col.ATTACHMENTS).get("p1") is None  # nothing else named it
        assert db.collection(col.ATTACHMENTS).get("shared") is not None  # bed_a2 still shows it


class TestAReplaceImportAndARestoreDiscardThePhotos:
    """#2661 follow-up: a ``replace`` import (and a restore, which is one) deletes beds through the plan batch, so the
    photos those beds held are reported from the transaction and discarded after the commit."""

    def _importer(self, db) -> GardenPlanImportService:
        sites, plans_repo = ArangoSiteRepository(db), ArangoGardenPlanRepository(db)
        plans = GardenPlanService(sites, plans_repo)
        attachments = ArangoAttachmentRepository(db)
        photos = LocationPhotoService(
            sites, ArangoLocationPhotoRepository(db), attachments, lambda: _Deleter(attachments)
        )
        return GardenPlanImportService(
            sites, plans_repo, plans, GardenPlanExportService(sites, plans_repo, plans), photos=lambda: photos
        )

    async def test_the_replaced_beds_photos_go_and_a_photo_another_site_shows_stays(self, db) -> None:
        for key in ("p_own", "p_shared"):
            db.collection(col.ATTACHMENTS).insert(_photo(key))
        db.collection(col.LOCATIONS).update(
            {"_key": "bed_a", "photo_refs": ["p_shared", "p_own"], "cover_photo_ref": "p_own"}
        )
        db.collection(col.SITES).insert({"_key": "site_a2", "tenant_key": A, "name": "site_a2", "type": "outdoor"})
        db.collection(col.LOCATIONS).insert(_bed("bed_other_site", "site_a2", photo_refs=["p_shared"]))
        importer = self._importer(db)
        document = importer._export.export_json("site_a", tenant_key=A).model_dump(mode="json")

        report = importer.import_plan(
            "site_a",
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            mode="replace",
            dry_run=False,
            force=False,
            confirm_site_name="site_a",
            document=document,
        )
        await importer.release_photos(report, tenant_key=A)

        assert report.applied and sorted(report.released_photo_refs) == ["p_own", "p_shared"]
        assert db.collection(col.LOCATIONS).get("bed_a") is None  # replaced by beds with new keys
        assert db.collection(col.ATTACHMENTS).get("p_own") is None
        assert db.collection(col.ATTACHMENTS).get("p_shared") is not None  # bed_other_site still shows it
