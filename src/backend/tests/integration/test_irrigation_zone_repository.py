"""REQ-053 WP 7.1 (#2467) — the irrigation-zone writes against a real ArangoDB (production schema).

What no double can decide, measured here:

* the coverage is held twice — the ``zone_covers`` edge and ``Location.irrigation_zone_key`` — and every writer
  (``PUT …/locations``, ``DELETE``, ``PATCH /locations/{key}``, the plan import, the plan batch's delete of a
  water source) moves both in one transaction;
* the v0099 unique index on ``zone_covers._to`` refuses a second zone on a bed even when a writer forgets;
* the delete leaves no edge on the zone, no bed naming it, and one ``garden_plan_audit`` row (SR-011);
* the migration v0099 builds exactly the bootstrap's indexes, is idempotent, and refuses a volume with
  duplicate coverage instead of deleting an edge.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.common.exceptions import DuplicateError, NotFoundError, PlanValidationError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.irrigation_zone_repository import ArangoIrrigationZoneRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.garden_plan import LocationPatch
from app.domain.models.irrigation_zone import IrrigationZone, IrrigationZoneInput, IrrigationZonePatch
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.irrigation_zone_service import IrrigationZoneService
from app.migrations.versions.v0099_irrigation_zone_indexes import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("irrigation_zone_repository")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 20, "length_m": 20, "rotation_deg": 0}


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


def _bed(key: str, site: str, x: float) -> dict[str, Any]:
    return {
        "_key": key,
        "site_key": site,
        "name": key,
        "location_type_key": "bed",
        "area_m2": 2.0,
        "depth": 0,
        "path": key,
        "bed_status": "active",
        "geometry": {"kind": "rect", "origin": [x, 1], "width_m": 2, "length_m": 1, "rotation_deg": 0},
    }


def _barrel(key: str, site: str) -> dict[str, Any]:
    return {
        "_key": key,
        "site_key": site,
        "object_type": "water_source",
        "label": "",
        "geometry": {"kind": "point", "origin": [18, 18]},
        "props": {"object_type": "water_source", "water_source_kind": "rain_barrel"},
        "off_site": False,
        "locked": False,
        "z_order": 0,
    }


_TOUCHED = (
    col.SITES,
    col.LOCATIONS,
    col.GARDEN_OBJECTS,
    col.IRRIGATION_ZONES,
    col.GARDEN_PLAN_AUDIT,
    col.LOCATION_TYPES,
    col.USERS,
    col.CONTAINS,
    col.HAS_GARDEN_OBJECT,
    col.HAS_IRRIGATION_ZONE,
    col.ZONE_COVERS,
    col.ZONE_SUPPLIED_BY,
    col.ZONE_ACTUATED_BY,
)


@pytest.fixture
def db(database):
    for name in _TOUCHED:
        database.collection(name).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    for key, tenant in (("site_a", A), ("site_a2", A), ("site_b", B)):
        database.collection(col.SITES).insert(
            {
                "_key": key,
                "tenant_key": tenant,
                "name": key,
                "type": "outdoor",
                "total_area_m2": 0.0,
                "timezone": "UTC",
                "plan": {"boundary": _BOUNDARY, "plan_revision": 3, "north_angle_deg": 0.0},
            }
        )
    for index, key in enumerate(("bed_1", "bed_2", "bed_3")):
        database.collection(col.LOCATIONS).insert(_bed(key, "site_a", 1 + index * 3))
        database.collection(col.CONTAINS).insert({"_from": "sites/site_a", "_to": f"locations/{key}"})
    database.collection(col.LOCATIONS).insert(_bed("bed_b", "site_b", 1))
    database.collection(col.GARDEN_OBJECTS).insert(_barrel("barrel_a", "site_a"))
    database.collection(col.GARDEN_OBJECTS).insert(_barrel("barrel_b", "site_b"))
    return database


def _service(db) -> IrrigationZoneService:
    return IrrigationZoneService(
        ArangoIrrigationZoneRepository(db), ArangoSiteRepository(db), ArangoGardenObjectRepository(db)
    )


def _zone(db, name: str = "South", **data: Any) -> str:
    view = _service(db).create_zone(
        "site_a", tenant_key=A, role=TenantRole.GROWER, data=IrrigationZoneInput(name=name, **data)
    )
    return view.zone.key or ""


def _covers(db) -> set[tuple[str, str]]:
    return {(e["_from"].split("/")[1], e["_to"].split("/")[1]) for e in db.collection(col.ZONE_COVERS).all()}


def _fields(db) -> dict[str, str | None]:
    return {d["_key"]: d.get("irrigation_zone_key") for d in db.collection(col.LOCATIONS).all()}


class TestCreateAndEdit:
    def test_the_zone_is_stored_with_its_site_and_water_source_edges(self, db) -> None:
        key = _zone(db, water_source_key="barrel_a", irrigation_type="drip")

        stored = db.collection(col.IRRIGATION_ZONES).get(key)
        assert (stored["tenant_key"], stored["site_key"], stored["irrigation_type"]) == (A, "site_a", "drip")
        assert [e["_from"] for e in db.collection(col.HAS_IRRIGATION_ZONE).all()] == ["sites/site_a"]
        assert [e["_to"] for e in db.collection(col.ZONE_SUPPLIED_BY).all()] == ["garden_objects/barrel_a"]

    def test_a_changed_water_source_moves_its_edge_and_null_removes_it(self, db) -> None:
        key = _zone(db, water_source_key="barrel_a")
        db.collection(col.GARDEN_OBJECTS).insert(
            {**_barrel("barrel_a2", "site_a"), "geometry": {"kind": "point", "origin": [17, 17]}}
        )
        service = _service(db)

        service.patch_zone(
            key, tenant_key=A, role=TenantRole.GROWER, patch=IrrigationZonePatch(water_source_key="barrel_a2")
        )
        assert [e["_to"] for e in db.collection(col.ZONE_SUPPLIED_BY).all()] == ["garden_objects/barrel_a2"]

        service.patch_zone(key, tenant_key=A, role=TenantRole.GROWER, patch=IrrigationZonePatch(water_source_key=None))
        assert list(db.collection(col.ZONE_SUPPLIED_BY).all()) == []
        assert "water_source_key" not in db.collection(col.IRRIGATION_ZONES).get(key)

    def test_the_list_reads_only_the_tenants_zones_of_the_site(self, db) -> None:
        _zone(db, "B-zone")
        _zone(db, "A-zone")
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_b", "tenant_key": B, "site_key": "site_a", "name": "x"}
        )

        listed = ArangoIrrigationZoneRepository(db).list_zones_by_site("site_a", tenant_key=A, offset=0, limit=1)

        assert [z.name for z in listed] == ["A-zone"]
        assert ArangoIrrigationZoneRepository(db).get_zone_by_key("zone_b", tenant_key=A) is None


class TestCoverage:
    def test_replace_keeps_edge_and_field_in_step_and_moves_a_bed(self, db) -> None:
        service = _service(db)
        south, north = _zone(db, "South"), _zone(db, "North")

        service.replace_locations(south, tenant_key=A, role=TenantRole.GROWER, location_keys=["bed_1", "bed_2"])
        _, change = service.replace_locations(
            north, tenant_key=A, role=TenantRole.GROWER, location_keys=["bed_2", "bed_3"]
        )

        assert change.moved_from == {"bed_2": south}
        assert _covers(db) == {(south, "bed_1"), (north, "bed_2"), (north, "bed_3")}
        assert {k: v for k, v in _fields(db).items() if k.startswith("bed_") and k != "bed_b"} == {
            "bed_1": south,
            "bed_2": north,
            "bed_3": north,
        }

        service.replace_locations(south, tenant_key=A, role=TenantRole.GROWER, location_keys=[])
        assert _covers(db) == {(north, "bed_2"), (north, "bed_3")}
        assert "irrigation_zone_key" not in db.collection(col.LOCATIONS).get("bed_1")

    def test_a_bed_of_another_tenant_or_site_writes_nothing(self, db) -> None:
        key = _zone(db)
        db.collection(col.LOCATIONS).insert(_bed("bed_a2", "site_a2", 1))

        for foreign in ("bed_b", "bed_a2", "bed_gone"):
            with pytest.raises(PlanValidationError):
                _service(db).replace_locations(key, tenant_key=A, role=TenantRole.GROWER, location_keys=[foreign])

        assert _covers(db) == set()

    def test_the_unique_index_refuses_a_second_zone_on_a_bed(self, db) -> None:
        south, north = _zone(db, "South"), _zone(db, "North")
        db.collection(col.ZONE_COVERS).insert({"_from": f"irrigation_zones/{south}", "_to": "locations/bed_1"})

        with pytest.raises(Exception, match="unique"):
            db.collection(col.ZONE_COVERS).insert({"_from": f"irrigation_zones/{north}", "_to": "locations/bed_1"})

    def test_the_bed_patch_moves_the_edge_with_the_field(self, db) -> None:
        south, north = _zone(db, "South"), _zone(db, "North")
        sites, plan_repo = ArangoSiteRepository(db), ArangoGardenPlanRepository(db)
        resources = GardenResourceService(
            sites, plan_repo, ArangoGardenObjectRepository(db), GardenPlanService(sites, plan_repo)
        )

        def patch(zone: str | None) -> None:
            resources.patch_location(
                "bed_1",
                tenant_key=A,
                user_key=USER,
                role=TenantRole.GROWER,
                patch=LocationPatch(irrigation_zone_key=zone),
            )

        patch(south)
        assert _covers(db) == {(south, "bed_1")} and _fields(db)["bed_1"] == south
        patch(north)
        assert _covers(db) == {(north, "bed_1")} and _fields(db)["bed_1"] == north
        assert _service(db).get_zone(south, tenant_key=A).location_keys == ()
        patch(None)
        assert _covers(db) == set() and _fields(db)["bed_1"] is None

    def test_a_zone_deleted_after_the_check_is_reference_not_found_and_writes_nothing(self, db) -> None:
        with pytest.raises(PlanValidationError) as caught:
            ArangoGardenPlanRepository(db).update_location_fields("bed_1", {"irrigation_zone_key": "zone_gone"})

        assert caught.value.codes == ["reference.not_found"]
        assert _covers(db) == set() and _fields(db)["bed_1"] is None


class TestDelete:
    def test_one_transaction_clears_beds_edges_and_writes_the_audit_row(self, db) -> None:
        key = _zone(db, "South", water_source_key="barrel_a")
        _service(db).replace_locations(key, tenant_key=A, role=TenantRole.GROWER, location_keys=["bed_1", "bed_2"])
        # A row written before the edge was maintained: the field without its edge is cleared as well.
        db.collection(col.LOCATIONS).update({"_key": "bed_3", "irrigation_zone_key": key})

        _service(db).delete_zone(key, tenant_key=A, user_key=USER, role=TenantRole.LEAD)

        assert not db.collection(col.IRRIGATION_ZONES).has(key)
        assert {k: v for k, v in _fields(db).items() if v is not None} == {}
        for edge in (col.ZONE_COVERS, col.ZONE_SUPPLIED_BY, col.HAS_IRRIGATION_ZONE):
            assert list(db.collection(edge).all()) == [], edge
        (audit,) = list(db.collection(col.GARDEN_PLAN_AUDIT).all())
        assert (audit["op"], audit["entity"], audit["key"], audit["summary"], audit["revision"]) == (
            "delete",
            "irrigation_zone",
            key,
            "South",
            3,
        )
        assert (audit["tenant_key"], audit["site_key"], audit["user_key"]) == (A, "site_a", USER)

    def test_another_tenants_zone_is_not_deleted(self, db) -> None:
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_b", "tenant_key": B, "site_key": "site_b", "name": "x"}
        )

        with pytest.raises(NotFoundError):
            ArangoIrrigationZoneRepository(db).delete_zone("zone_b", tenant_key=A, user_key=USER)

        assert db.collection(col.IRRIGATION_ZONES).has("zone_b")
        assert list(db.collection(col.GARDEN_PLAN_AUDIT).all()) == []


class TestThePlanWritersKeepTheZoneConsistent:
    def test_deleting_a_water_source_in_the_batch_unlinks_the_zone(self, db) -> None:
        key = _zone(db, water_source_key="barrel_a")
        sites, plan_repo = ArangoSiteRepository(db), ArangoGardenPlanRepository(db)

        GardenPlanService(sites, plan_repo).apply_batch(
            "site_a",
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            expected_revision=3,
            operations=[{"op": "delete", "entity": "garden_object", "key": "barrel_a"}],
            body_bytes=0,
        )

        assert "water_source_key" not in db.collection(col.IRRIGATION_ZONES).get(key)
        assert list(db.collection(col.ZONE_SUPPLIED_BY).all()) == []

    def test_deleting_a_bed_in_the_batch_removes_its_coverage(self, db) -> None:
        key = _zone(db)
        _service(db).replace_locations(key, tenant_key=A, role=TenantRole.GROWER, location_keys=["bed_1", "bed_2"])
        sites, plan_repo = ArangoSiteRepository(db), ArangoGardenPlanRepository(db)

        GardenPlanService(sites, plan_repo).apply_batch(
            "site_a",
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            expected_revision=3,  # the coverage is outside the plan revision (GP-NFR-007)
            operations=[{"op": "delete", "entity": "location", "key": "bed_1"}],
            body_bytes=0,
        )

        assert _covers(db) == {(key, "bed_2")}


class TestMigrationV0099:
    def test_a_bootstrapped_volume_is_a_noop(self, db) -> None:
        report = migration.up(db)

        assert report.changed == 0
        assert (report.details["zone_site_index_present"], report.details["covers_target_index_present"]) == (
            True,
            True,
        )

    def test_a_volume_without_the_indexes_gets_them_once(self, db) -> None:
        for name, fields in ((col.IRRIGATION_ZONES, ["tenant_key", "site_key"]), (col.ZONE_COVERS, ["_to"])):
            for index in db.collection(name).indexes():
                if index.get("fields") == fields and index["type"] == "persistent":
                    db.collection(name).delete_index(index["id"])
        try:
            dry = migration.up(db, dry_run=True)
            assert (dry.changed, sorted(dry.details["will_create"])) == (0, ["covers_target", "zone_site"])

            applied = migration.up(db)
            again = migration.up(db)

            assert (applied.changed, again.changed) == (2, 0)
            unique = [i for i in db.collection(col.ZONE_COVERS).indexes() if i.get("fields") == ["_to"]]
            assert [i["unique"] for i in unique] == [True]
        finally:
            col.ensure_collections(db)

    def test_duplicate_coverage_is_reported_and_blocked_never_repaired(self, db) -> None:
        for index in db.collection(col.ZONE_COVERS).indexes():
            if index.get("fields") == ["_to"] and index["type"] == "persistent":
                db.collection(col.ZONE_COVERS).delete_index(index["id"])
        try:
            for zone in ("z1", "z2"):
                db.collection(col.ZONE_COVERS).insert({"_from": f"irrigation_zones/{zone}", "_to": "locations/bed_1"})

            # The boot's bootstrap runs first and must survive the duplicates (it absorbs the refusal).
            col.ensure_collections(db)
            dry = migration.up(db, dry_run=True)
            assert (dry.details["duplicate_targets"], dry.details["will_create"]) == (1, ["covers_target"])

            applied = migration.up(db)

            assert (applied.changed, applied.details["covers_target_blocked"]) == (0, True)
            assert db.collection(col.ZONE_COVERS).count() == 2  # nothing repaired
            assert not [i for i in db.collection(col.ZONE_COVERS).indexes() if i.get("fields") == ["_to"]]
        finally:
            db.collection(col.ZONE_COVERS).truncate()
            col.ensure_collections(db)


def test_the_stored_zone_validates_as_the_model(db) -> None:
    key = _zone(db, schedule_hint="  mornings ")

    stored = IrrigationZone.model_validate(db.collection(col.IRRIGATION_ZONES).get(key))

    assert stored.schedule_hint == "mornings"


def test_duplicate_error_is_the_typed_conflict_of_a_racing_writer(db) -> None:
    """Two writers of one bed that both pass their read: the index turns the loser into 409 ``conflict.duplicate``."""
    south, north = _zone(db, "South"), _zone(db, "North")
    db.collection(col.ZONE_COVERS).insert({"_from": f"irrigation_zones/{north}", "_to": "locations/bed_1"})

    from app.data_access.arango.transactions import stream_transaction

    with (
        pytest.raises(DuplicateError),
        stream_transaction(db, write=(col.ZONE_COVERS,), entity="irrigation_zone") as txn,
    ):
        txn.collection(col.ZONE_COVERS).insert({"_from": f"irrigation_zones/{south}", "_to": "locations/bed_1"})


class TestEveryWriterTakesTheZoneUnderItsAnchor:
    """Code review of WP 7.1: the plan import, the bed PATCH and the water source are checked inside the write."""

    def _import_bed(self, db, zone_key: str) -> None:
        from app.domain.models.garden_plan import PlanBatchWrite
        from app.domain.models.site import Location

        bed = Location.model_validate(
            {**_bed("ignored", "site_a", 12), "irrigation_zone_key": zone_key, "name": "Imported"}
        ).model_copy(update={"key": None})
        ArangoGardenPlanRepository(db).apply_plan_batch(
            PlanBatchWrite(
                site_key="site_a",
                tenant_key=A,
                editor_key=USER,
                expected_revision=3,
                basis_revision=3,
                location_inserts=[("t1", bed)],
            )
        )

    def test_the_import_takes_its_zone_and_writes_the_edge(self, db) -> None:
        key = _zone(db)

        self._import_bed(db, key)

        (imported,) = [d for d in db.collection(col.LOCATIONS).all() if d["name"] == "Imported"]
        assert _covers(db) == {(key, imported["_key"])}

    @pytest.mark.parametrize(
        "zone", ["zone_gone", "zone_b", "zone_a2"], ids=["deleted", "foreign tenant", "other site"]
    )
    def test_an_import_naming_a_zone_that_is_not_there_writes_nothing(self, db, zone: str) -> None:
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_b", "tenant_key": B, "site_key": "site_a", "name": "x"}
        )
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_a2", "tenant_key": A, "site_key": "site_a2", "name": "x"}
        )
        before = db.collection(col.LOCATIONS).count()

        with pytest.raises(WriteConflictError):
            self._import_bed(db, zone)

        assert db.collection(col.LOCATIONS).count() == before and _covers(db) == set()
        assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 3

    @pytest.mark.parametrize("zone", ["zone_b", "zone_a2"], ids=["foreign tenant", "other site"])
    def test_the_bed_patch_takes_only_a_zone_of_the_beds_own_site_and_tenant(self, db, zone: str) -> None:
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_b", "tenant_key": B, "site_key": "site_a", "name": "x"}
        )
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_a2", "tenant_key": A, "site_key": "site_a2", "name": "x"}
        )
        stamp = db.collection(col.IRRIGATION_ZONES).get(zone).get("updated_at")

        with pytest.raises(PlanValidationError) as caught:
            ArangoGardenPlanRepository(db).update_location_fields("bed_1", {"irrigation_zone_key": zone})

        assert caught.value.codes == ["reference.not_found"]
        assert _covers(db) == set() and _fields(db)["bed_1"] is None
        assert db.collection(col.IRRIGATION_ZONES).get(zone).get("updated_at") == stamp  # not even taken

    @pytest.mark.parametrize(
        "source", ["barrel_b", "barrel_gone", "barrel_a2"], ids=["foreign tenant", "absent", "other site"]
    )
    def test_a_water_source_gone_after_the_check_writes_no_zone(self, db, source: str) -> None:
        db.collection(col.GARDEN_OBJECTS).insert(_barrel("barrel_a2", "site_a2"))
        repo = ArangoIrrigationZoneRepository(db)
        zone = IrrigationZone(tenant_key=A, site_key="site_a", name="Z", water_source_key=source)

        with pytest.raises(PlanValidationError) as caught:
            repo.create_zone(zone, tenant_key=A)

        assert caught.value.codes == ["reference.not_found"]
        assert db.collection(col.IRRIGATION_ZONES).count() == 0
        assert list(db.collection(col.ZONE_SUPPLIED_BY).all()) == []

    def test_an_edit_to_a_water_source_gone_after_the_check_changes_nothing(self, db) -> None:
        key = _zone(db, water_source_key="barrel_a")

        with pytest.raises(PlanValidationError):
            ArangoIrrigationZoneRepository(db).update_zone(key, {"water_source_key": "barrel_gone"}, tenant_key=A)

        assert db.collection(col.IRRIGATION_ZONES).get(key)["water_source_key"] == "barrel_a"
        assert [e["_to"] for e in db.collection(col.ZONE_SUPPLIED_BY).all()] == ["garden_objects/barrel_a"]


class TestTheLegacyDeletesCascadeToTheZones:
    def test_deleting_a_site_removes_its_zones_and_their_edges(self, db) -> None:
        key = _zone(db, water_source_key="barrel_a")
        _service(db).replace_locations(key, tenant_key=A, role=TenantRole.GROWER, location_keys=["bed_1"])
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "zone_b", "tenant_key": B, "site_key": "site_b", "name": "x"}
        )
        db.collection(col.ZONE_COVERS).insert({"_from": "irrigation_zones/zone_b", "_to": "locations/bed_b"})

        ArangoSiteRepository(db).delete_site("site_a")

        assert [z["_key"] for z in db.collection(col.IRRIGATION_ZONES).all()] == ["zone_b"]  # positive control
        assert _covers(db) == {("zone_b", "bed_b")}
        assert list(db.collection(col.HAS_IRRIGATION_ZONE).all()) == []
        assert list(db.collection(col.ZONE_SUPPLIED_BY).all()) == []

    def test_deleting_a_location_removes_its_coverage(self, db) -> None:
        key = _zone(db)
        _service(db).replace_locations(key, tenant_key=A, role=TenantRole.GROWER, location_keys=["bed_1", "bed_2"])

        ArangoSiteRepository(db).delete_location("bed_1")

        assert _covers(db) == {(key, "bed_2")}
