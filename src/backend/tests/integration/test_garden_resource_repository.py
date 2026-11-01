"""REQ-053 WP 1.9 (#2328) — the single-resource writes against a real ArangoDB.

What no double can decide, measured here: that a bed-status change, its care event, its audit row and the
revision are **one** transaction (a failure leaves none of them), that the counters read what the plant, task
and care-event collections really hold, that a slot batch is all or nothing — a duplicate ``slot_id`` from
the unique index undoes the deletes before it — and that the two-tenant reads (zone, counters, objects) hide
a foreign tenant's rows. Every "nothing is there" assertion is paired with the positive control.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from arango import ArangoClient

from app.common.enums import BedStatus, TenantRole
from app.common.exceptions import DuplicateError, NotFoundError, PlanError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.garden_plan_repository import (
    _BATCH_WRITE,
    _SLOT_BATCH_WRITE,
    ArangoGardenPlanRepository,
)
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.garden_plan import GardenObjectPatch, LocationPatch, SlotBatchRequest, SlotPatch
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("garden_resource_repository")
A, B = "ten_a", "ten_b"
USER = "u_sabine"

_DOCUMENTS = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.GARDEN_OBJECTS,
    col.GARDEN_PLAN_AUDIT,
    col.CARE_EVENTS,
    col.IRRIGATION_ZONES,
    col.SUBSTRATES,
    col.LOCATION_TYPES,
    col.USERS,
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.TASKS,
    # the plan read model asks when a bed was last watered (REQ-053 WP 7.3)
    col.WATERING_EVENTS,
)
_EDGES = tuple(
    dict.fromkeys(
        definition["edge_collection"]
        for definition in col.GRAPH_EDGE_DEFINITIONS
        if definition["edge_collection"] in {*_BATCH_WRITE, *_SLOT_BATCH_WRITE}
    )
)
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


def point(x: float, y: float) -> dict:
    return {"kind": "point", "origin": [x, y]}


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENTS:
        db.create_collection(name)
    for name in _EDGES:
        db.create_collection(name, edge=True)
    # The unique index the slot batch relies on for V-20 (production creates it in ``collections.py``).
    db.collection(col.SLOTS).add_persistent_index(fields=col.SLOT_ID_INDEX_FIELDS, unique=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    for key, tenant in (("site_a", A), ("site_b", B)):
        database.collection(col.SITES).insert(
            {
                "_key": key,
                "tenant_key": tenant,
                "name": key,
                "type": "outdoor",
                "total_area_m2": 0.0,
                "timezone": "UTC",
                "plan": {"boundary": _BOUNDARY, "plan_revision": 1, "north_angle_deg": 0.0},
            }
        )
    database.collection(col.LOCATIONS).insert(
        {
            "_key": "bed",
            "site_key": "site_a",
            "name": "Bed",
            "location_type_key": "bed",
            "area_m2": 2.0,
            "depth": 0,
            "path": "bed",
            "bed_status": "active",
            "geometry": {"kind": "rect", "origin": [1, 1], "width_m": 2, "length_m": 1, "rotation_deg": 0},
        }
    )
    database.collection(col.IRRIGATION_ZONES).insert({"_key": "zone_a", "tenant_key": A, "site_key": "site_a"})
    database.collection(col.IRRIGATION_ZONES).insert({"_key": "zone_b", "tenant_key": B, "site_key": "site_b"})
    database.collection(col.SUBSTRATES).insert({"_key": "sub_global", "tenant_key": ""})
    database.collection(col.SUBSTRATES).insert({"_key": "sub_a", "tenant_key": A})
    database.collection(col.SUBSTRATES).insert({"_key": "sub_b", "tenant_key": B})
    return database


@pytest.fixture
def repo(db) -> ArangoGardenPlanRepository:
    return ArangoGardenPlanRepository(db)


@pytest.fixture
def service(db, repo) -> GardenResourceService:
    sites = ArangoSiteRepository(db)
    return GardenResourceService(sites, repo, ArangoGardenObjectRepository(db), GardenPlanService(sites, repo))


def add_slot(db, key: str, slot_id: str, *, occupied: bool = False, archived: bool = False, geometry=None) -> None:
    db.collection(col.SLOTS).insert(
        {
            "_key": key,
            "slot_id": slot_id,
            "location_key": "bed",
            "capacity_plants": 1,
            "currently_occupied": occupied,
            "slot_role": "position",
            "geometry": geometry or point(0.5, 0.5),
            "archived_at": "2025-10-01T00:00:00+00:00" if archived else None,
        }
    )
    db.collection(col.HAS_SLOT).insert({"_from": f"{col.LOCATIONS}/bed", "_to": f"{col.SLOTS}/{key}"})


def slot_ids(db) -> list[str]:
    return sorted(doc["slot_id"] for doc in db.collection(col.SLOTS).all())


def batch(*ids: str, mode: str = "replace_unoccupied") -> SlotBatchRequest:
    return SlotBatchRequest.model_validate(
        {
            "mode": mode,
            "slots": [{"slot_id": slot_id, "geometry": point(0.2 + i * 0.1, 0.5)} for i, slot_id in enumerate(ids)],
        }
    )


class TestTheBedStatusIsOneTransaction:
    def test_status_event_audit_and_revision_land_together_gp_acc_015(self, db, service) -> None:
        stored, revision = service.change_bed_status(
            "bed", tenant_key=A, user_key=USER, role=TenantRole.LEAD, bed_status=BedStatus.RETIRED, reason="Dismantled"
        )

        assert stored.bed_status is BedStatus.RETIRED and revision == 2
        (event,) = list(db.collection(col.CARE_EVENTS).all())
        assert (event["category"], event["reason"], event["tenant_key"], event["location_key"]) == (
            "bed_status_change",
            "Dismantled",
            A,
            "bed",
        )
        (edge,) = list(db.collection(col.CARE_EVENT_AT).all())
        assert (edge["_from"], edge["_to"]) == (f"{col.CARE_EVENTS}/{event['_key']}", f"{col.LOCATIONS}/bed")
        (audit,) = list(db.collection(col.GARDEN_PLAN_AUDIT).all())
        assert (audit["op"], audit["revision"], audit["tenant_key"]) == ("retire", 2, A)

    def test_a_plant_standing_in_the_bed_is_a_409_and_nothing_is_written(self, db, service) -> None:
        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "p1", "tenant_key": A, "location_key": "bed", "removed_on": None}
        )
        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "p2", "tenant_key": A, "location_key": "bed", "removed_on": None}
        )

        with pytest.raises(PlanError) as exc:
            service.change_bed_status(
                "bed", tenant_key=A, user_key=USER, role=TenantRole.LEAD, bed_status=BedStatus.RETIRED, reason="x"
            )

        assert exc.value.details[0]["active_plant_count"] == 2
        assert db.collection(col.LOCATIONS).get("bed")["bed_status"] == "active"
        assert (
            db.collection(col.CARE_EVENTS).count() == 0
            and db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 1
        )

    def test_the_transaction_rechecks_plants_that_arrive_after_the_service_read(self, db, repo) -> None:
        from app.domain.models.care_event import CareEvent
        from app.domain.models.garden_plan import PlanBatchWrite

        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "late", "tenant_key": A, "location_key": "bed", "removed_on": None}
        )
        write = PlanBatchWrite(
            site_key="site_a",
            tenant_key=A,
            editor_key=USER,
            expected_revision=1,
            basis_revision=1,
            location_updates=[("bed", {"bed_status": "retired"})],
            care_events=[
                CareEvent(
                    tenant_key=A,
                    site_key="site_a",
                    location_key="bed",
                    category="bed_status_change",
                    performed_at=datetime.now(UTC),
                )
            ],
        )
        with pytest.raises(PlanError) as exc:
            repo.apply_plan_batch(write)

        assert exc.value.status_code == 409
        assert (
            db.collection(col.LOCATIONS).get("bed")["bed_status"] == "active"
            and db.collection(col.CARE_EVENTS).count() == 0
        )

    def test_a_status_changed_after_the_service_read_is_a_409_and_writes_nothing(self, db, repo) -> None:
        from app.domain.models.garden_plan import PlanBatchWrite

        db.collection(col.LOCATIONS).update({"_key": "bed", "bed_status": "retired"})  # the lead was faster
        write = PlanBatchWrite(
            site_key="site_a",
            tenant_key=A,
            editor_key=USER,
            expected_revision=1,
            basis_revision=1,
            location_updates=[("bed", {"bed_status": "active"})],
            status_from={"bed": "planned"},
        )
        with pytest.raises(PlanError) as exc:
            repo.apply_plan_batch(write)

        assert exc.value.status_code == 409 and exc.value.details[0]["code"] == "bed_status.changed"
        assert db.collection(col.LOCATIONS).get("bed")["bed_status"] == "retired"
        assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 1  # the aborted CAS left no trace

    def test_a_document_without_a_status_reads_as_active(self, db, repo) -> None:
        from app.domain.models.garden_plan import PlanBatchWrite

        db.collection(col.LOCATIONS).update({"_key": "bed", "bed_status": None}, keep_none=False)
        repo.apply_plan_batch(
            PlanBatchWrite(
                site_key="site_a",
                tenant_key=A,
                editor_key=USER,
                expected_revision=1,
                basis_revision=1,
                location_updates=[("bed", {"bed_status": "retired"})],
                status_from={"bed": "active"},
            )
        )
        assert db.collection(col.LOCATIONS).get("bed")["bed_status"] == "retired"

    def test_another_tenants_lead_gets_a_404_and_changes_nothing(self, db, service) -> None:
        with pytest.raises(NotFoundError):
            service.change_bed_status(
                "bed", tenant_key=B, user_key=USER, role=TenantRole.LEAD, bed_status=BedStatus.RETIRED, reason="x"
            )
        assert (
            db.collection(col.LOCATIONS).get("bed")["bed_status"] == "active"
            and db.collection(col.CARE_EVENTS).count() == 0
        )


class TestTheCounters:
    def test_plants_tasks_and_care_events_are_counted_per_bed_and_per_tenant(self, db, repo) -> None:
        plants = db.collection(col.PLANT_INSTANCES)
        plants.insert({"_key": "p1", "tenant_key": A, "location_key": "bed", "species_key": "sp_a", "removed_on": None})
        plants.insert({"_key": "p2", "tenant_key": A, "location_key": "bed", "species_key": "sp_b", "removed_on": None})
        plants.insert(
            {"_key": "p3", "tenant_key": A, "location_key": "bed", "species_key": "sp_a", "removed_on": "2026-01-01"}
        )
        plants.insert({"_key": "px", "tenant_key": B, "location_key": "bed", "species_key": "sp_x", "removed_on": None})
        tasks = db.collection(col.TASKS)
        tasks.insert(
            {
                "_key": "t1",
                "tenant_key": A,
                "status": "pending",
                "entity_type": "location",
                "entity_key": "bed",
                "due_date": "2020-01-01",
            }
        )
        tasks.insert(
            {
                "_key": "t2",
                "tenant_key": A,
                "status": "pending",
                "entity_type": "plant_instance",
                "entity_key": "p1",
                "due_date": "2999-01-01",
            }
        )
        tasks.insert(
            {"_key": "t3", "tenant_key": A, "status": "completed", "entity_type": "location", "entity_key": "bed"}
        )
        tasks.insert(
            {
                "_key": "t4",
                "tenant_key": B,
                "status": "pending",
                "entity_type": "location",
                "entity_key": "bed",
                "due_date": "2019-01-01",
            }
        )
        events = db.collection(col.CARE_EVENTS)
        events.insert({"tenant_key": A, "location_key": "bed", "performed_at": "2026-06-01T10:00:00+00:00"})
        events.insert({"tenant_key": A, "location_key": "bed", "performed_at": "2026-06-14T18:30:00+00:00"})
        events.insert(
            {
                "tenant_key": A,
                "location_key": "bed",
                "performed_at": "2026-09-01T00:00:00+00:00",
                "voided_at": "2026-09-02T00:00:00+00:00",
            }
        )
        events.insert({"tenant_key": B, "location_key": "bed", "performed_at": "2027-01-01T00:00:00+00:00"})

        own = repo.load_bed_counters(["bed", "nowhere"], tenant_key=A)

        assert set(own) == {"bed"}
        counters = own["bed"]
        assert (counters.active_plant_count, counters.species_keys) == (2, ["sp_a", "sp_b"])
        assert (counters.open_task_count, counters.overdue_task_count) == (2, 1)
        assert counters.next_due_at.year == 2020
        assert counters.last_care_at.isoformat().startswith("2026-06-14")  # the voided September event is not care
        foreign = repo.load_bed_counters(["bed"], tenant_key=B)["bed"]
        assert (foreign.active_plant_count, foreign.open_task_count) == (1, 1)

    def test_an_empty_tenant_is_no_tenant(self, repo) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            repo.load_bed_counters(["bed"], tenant_key="")


class TestReferencesAreTheTenants:
    def test_a_zone_resolves_to_its_site_only_for_its_tenant(self, repo) -> None:
        assert repo.irrigation_zone_site_key("zone_a", tenant_key=A) == "site_a"
        assert repo.irrigation_zone_site_key("zone_a", tenant_key=B) is None
        assert repo.irrigation_zone_site_key("nowhere", tenant_key=A) is None

    def test_a_substrate_is_visible_when_it_is_the_catalogue_or_the_tenants_own(self, repo) -> None:
        assert [repo.substrate_visible(key, tenant_key=A) for key in ("sub_global", "sub_a", "sub_b", "nowhere")] == [
            True,
            True,
            False,
            False,
        ]

    def test_the_patch_stores_an_own_zone_and_refuses_a_foreign_one(self, db, service) -> None:
        for key, ok in (("zone_a", True), ("zone_b", False)):
            patch = LocationPatch(irrigation_zone_key=key)
            if ok:
                stored, _ = service.patch_location(
                    "bed", tenant_key=A, user_key=USER, role=TenantRole.GROWER, patch=patch
                )
                assert stored.irrigation_zone_key == "zone_a"
            else:
                with pytest.raises(Exception) as exc:  # noqa: PT011 — PlanValidationError, asserted on the code
                    service.patch_location("bed", tenant_key=A, user_key=USER, role=TenantRole.GROWER, patch=patch)
                assert exc.value.details[0]["code"] == "reference.not_found"
        assert db.collection(col.LOCATIONS).get("bed")["irrigation_zone_key"] == "zone_a"


class TestPatchWritesOnlyWhatItChanged:
    def test_a_field_set_after_the_read_survives_a_patch_of_another_field(self, db, service) -> None:
        stored = service._owned_location("bed", tenant_key=A)
        db.collection(col.LOCATIONS).update({"_key": "bed", "sun_exposure": "shade"})  # another path, after the read

        service._plan.update_location_fields(stored.key, {"notes": "n"})

        document = db.collection(col.LOCATIONS).get("bed")
        assert document["notes"] == "n" and document["sun_exposure"] == "shade"

    def test_null_removes_the_field_and_a_nested_profile_is_replaced_whole(self, db, repo) -> None:
        repo.update_location_fields("bed", {"notes": "n", "soil_profile": {"soil_texture": "loam", "ph": 6.5}})
        repo.update_location_fields("bed", {"notes": None, "soil_profile": {"soil_texture": "clay"}})

        document = db.collection(col.LOCATIONS).get("bed")
        assert "notes" not in document and document["soil_profile"] == {"soil_texture": "clay"}

    def test_the_rotation_switch_is_stored_and_null_returns_it_to_the_type_default(self, db, service) -> None:
        """GP-FR-137 (#2544): ``rotation_enabled`` round trip through ArangoDB; ``null`` removes the attribute."""

        def patch(body: dict) -> None:
            service.patch_location(
                "bed", tenant_key=A, user_key=USER, role=TenantRole.GROWER, patch=LocationPatch.model_validate(body)
            )

        patch({"rotation_enabled": True})
        assert db.collection(col.LOCATIONS).get("bed")["rotation_enabled"] is True
        assert service._owned_location("bed", tenant_key=A).rotation_enabled is True

        patch({"rotation_enabled": None})
        assert "rotation_enabled" not in db.collection(col.LOCATIONS).get("bed")
        assert service._owned_location("bed", tenant_key=A).rotation_enabled is None

    def test_a_permanent_crop_is_not_switched_on_and_nothing_is_written(self, db, service) -> None:
        service.patch_location(
            "bed", tenant_key=A, user_key=USER, role=TenantRole.GROWER, patch=LocationPatch(rotation_exempt=True)
        )

        with pytest.raises(PlanError) as caught:
            service.patch_location(
                "bed", tenant_key=A, user_key=USER, role=TenantRole.GROWER, patch=LocationPatch(rotation_enabled=True)
            )

        assert caught.value.error_code == "patch.rotation_exempt_and_enabled"
        document = db.collection(col.LOCATIONS).get("bed")
        assert document["rotation_exempt"] is True and "rotation_enabled" not in document

    def test_a_deleted_location_is_a_404(self, repo) -> None:
        with pytest.raises(NotFoundError):
            repo.update_location_fields("gone", {"notes": "x"})

    def test_a_geometry_patch_raises_the_revision_and_moves_the_derived_values(self, db, service) -> None:
        stored, revision = service.patch_location(
            "bed",
            tenant_key=A,
            user_key=USER,
            role=TenantRole.GROWER,
            patch=LocationPatch.model_validate(
                {"geometry": {"kind": "rect", "origin": [4, 4], "width_m": 3, "length_m": 2, "rotation_deg": 0}}
            ),
        )
        document = db.collection(col.LOCATIONS).get("bed")
        assert revision == 2 and document["area_m2"] == 6.0 and document["bbox"] == [4.0, 4.0, 7.0, 6.0]
        assert stored.area_m2 == 6.0


#: The two write paths of ``update_location_fields``: the plain column write and the one that moves the zone edge.
_PATHS = pytest.mark.parametrize("extra", [{}, {"irrigation_zone_key": "zone_a"}], ids=["plain", "with_zone"])


def _patch(service: GardenResourceService, body: dict) -> None:
    service.patch_location(
        "bed", tenant_key=A, user_key=USER, role=TenantRole.GROWER, patch=LocationPatch.model_validate(body)
    )


class TestPatchWritesOnlyTheSentSiteConditionParts:
    """#2569: ``PATCH /locations`` merges the sent ``site_conditions`` parts into the stored value.

    It used to write the whole value it read: a sun profile the plan batch wrote between the PATCH's read and
    its write (#2538) was reverted without a 409.
    """

    @_PATHS
    def test_a_sun_profile_the_batch_writes_after_the_read_survives_a_microclimate_patch(
        self, db, repo, service, monkeypatch, extra
    ) -> None:
        db.collection(col.LOCATIONS).update(
            {"_key": "bed", "site_conditions": {"sun_profile": {"sun_window": "morning"}, "wind_exposure": "exposed"}}
        )
        column_write = repo.update_location_fields

        def batch_then_write(location_key, fields):
            # The plan batch lands after the PATCH read the bed (the service holds the stale "morning").
            service._plan_service.apply_batch(
                "site_a",
                tenant_key=A,
                user_key=USER,
                role=TenantRole.GROWER,
                expected_revision=None,
                operations=[
                    {
                        "op": "update_fields",
                        "entity": "location",
                        "key": "bed",
                        "fields": {"site_conditions": {"sun_profile": {"sun_window": "afternoon"}}},
                    }
                ],
                body_bytes=0,
            )
            assert db.collection(col.LOCATIONS).get("bed")["site_conditions"]["sun_profile"]["sun_window"] == (
                "afternoon"
            )  # the race really happened before the column write
            column_write(location_key, fields)

        monkeypatch.setattr(repo, "update_location_fields", batch_then_write)

        _patch(service, {"site_conditions": {"microclimate": {"frost_risk": "high"}}, **extra})

        document = db.collection(col.LOCATIONS).get("bed")
        conditions = document["site_conditions"]
        assert conditions["sun_profile"]["sun_window"] == "afternoon"  # the batch's value, not the stale read
        assert conditions["microclimate"]["frost_risk"] == "high" and conditions["wind_exposure"] == "exposed"
        assert document["frost_exposed"] is True  # the #2512 mirror still rides along
        if extra:
            assert document["irrigation_zone_key"] == "zone_a"

    @_PATHS
    def test_a_key_the_patch_clears_is_removed_nested_and_top_level(self, db, service, extra) -> None:
        _patch(
            service,
            {
                "site_conditions": {
                    "sun_profile": {"sun_window": "morning", "direct_sun_hours_summer": 5.5},
                    "microclimate": {"cold_air_pocket": True},
                    "slope_deg": 12.5,
                }
            },
        )

        _patch(
            service, {"site_conditions": {"sun_profile": {"direct_sun_hours_summer": None}, "slope_deg": None}, **extra}
        )

        conditions = db.collection(col.LOCATIONS).get("bed")["site_conditions"]
        assert "direct_sun_hours_summer" not in conditions["sun_profile"] and "slope_deg" not in conditions
        assert conditions["sun_profile"]["sun_window"] == "morning"  # a sibling key of the cleared one stays
        assert conditions["microclimate"]["cold_air_pocket"] is True
        stored = service._owned_location("bed", tenant_key=A).site_conditions
        assert stored is not None
        assert stored.sun_profile.direct_sun_hours_summer is None and stored.slope_deg is None

    @_PATHS
    def test_a_first_part_on_a_bed_without_conditions_reads_back_with_the_defaults(self, db, service, extra) -> None:
        assert "site_conditions" not in db.collection(col.LOCATIONS).get("bed")

        _patch(service, {"site_conditions": {"microclimate": {"frost_risk": "low"}}, **extra})

        assert db.collection(col.LOCATIONS).get("bed")["site_conditions"] == {"microclimate": {"frost_risk": "low"}}
        stored = service._owned_location("bed", tenant_key=A).site_conditions
        assert stored is not None and stored.microclimate.frost_risk == "low"
        assert stored.sun_profile.sun_window == "unknown" and stored.access_sides == []

    @_PATHS
    def test_null_still_clears_the_whole_value(self, db, service, extra) -> None:
        _patch(service, {"site_conditions": {"wind_exposure": "exposed"}})

        _patch(service, {"site_conditions": None, **extra})

        assert "site_conditions" not in db.collection(col.LOCATIONS).get("bed")

    def test_a_merged_write_on_a_deleted_location_is_a_404(self, repo) -> None:
        with pytest.raises(NotFoundError):
            repo.update_location_fields("gone", {"site_conditions": {"wind_exposure": "exposed"}})


class TestTheSlotBatchIsAllOrNothing:
    def test_replace_unoccupied_keeps_occupied_reserved_and_archived_slots(self, db, service) -> None:
        add_slot(db, "free", "BED_FREE")
        add_slot(db, "busy", "BED_BUSY", occupied=True)
        add_slot(db, "held", "BED_HELD")
        add_slot(db, "hist", "BED_HIST", archived=True)
        db.collection(col.PLANTING_RUNS).insert({"_key": "run1", "tenant_key": A})
        db.collection(col.RUN_PLANNED_AT).insert({"_from": "planting_runs/run1", "_to": f"{col.SLOTS}/held"})

        result = service.replace_slots("bed", tenant_key=A, role=TenantRole.GROWER, request=batch("BED_N1", "BED_N2"))

        assert (result.deleted_count, result.kept_count, len(result.created_keys)) == (1, 3, 2)
        assert slot_ids(db) == ["BED_BUSY", "BED_HELD", "BED_HIST", "BED_N1", "BED_N2"]
        edges = {e["_to"] for e in db.collection(col.HAS_SLOT).all()}
        assert f"{col.SLOTS}/free" not in edges and all(f"{col.SLOTS}/{k}" in edges for k in result.created_keys)

    def test_a_deleted_slot_takes_its_adjacency_with_it(self, db, service) -> None:
        add_slot(db, "free", "BED_FREE")
        add_slot(db, "other", "BED_OTHER", occupied=True)
        db.collection(col.ADJACENT_TO).insert({"_from": f"{col.SLOTS}/free", "_to": f"{col.SLOTS}/other"})
        db.collection(col.ADJACENT_TO).insert({"_from": f"{col.SLOTS}/other", "_to": f"{col.SLOTS}/free"})

        service.replace_slots("bed", tenant_key=A, role=TenantRole.GROWER, request=batch("BED_N1"))

        assert db.collection(col.ADJACENT_TO).count() == 0

    def test_a_duplicate_id_from_the_index_undoes_the_deletes_before_it(self, db, repo) -> None:
        from app.domain.models.garden_plan import SlotBatchWrite
        from app.domain.models.site import Slot

        add_slot(db, "free", "BED_FREE")
        add_slot(db, "taken", "BED_TAKEN", occupied=True)
        write = SlotBatchWrite(
            location_key="bed",
            delete_keys=["free"],
            inserts=[
                Slot(slot_id="BED_NEW", geometry=point(0.4, 0.4)),
                Slot(slot_id="BED_TAKEN", geometry=point(0.6, 0.4)),
            ],
        )
        with pytest.raises(DuplicateError):
            repo.replace_slots(write)

        assert slot_ids(db) == ["BED_FREE", "BED_TAKEN"]  # the delete and the first insert are gone with the abort
        assert db.collection(col.HAS_SLOT).count() == 2

    def test_a_slot_that_is_occupied_by_now_aborts_the_batch(self, db, repo) -> None:
        from app.domain.models.garden_plan import SlotBatchWrite
        from app.domain.models.site import Slot

        add_slot(db, "late", "BED_LATE", occupied=True)  # the service read it as free; a plant took it since
        with pytest.raises(WriteConflictError):
            repo.replace_slots(SlotBatchWrite("bed", ["late"], [Slot(slot_id="BED_NEW", geometry=point(0.4, 0.4))]))
        assert slot_ids(db) == ["BED_LATE"]

    def test_a_slot_reserved_by_now_aborts_the_batch(self, db, repo) -> None:
        from app.domain.models.garden_plan import SlotBatchWrite

        add_slot(db, "res", "BED_RES")
        db.collection(col.RUN_PLANNED_AT).insert({"_from": "planting_runs/run1", "_to": f"{col.SLOTS}/res"})
        with pytest.raises(WriteConflictError):
            repo.replace_slots(SlotBatchWrite("bed", ["res"], []))
        assert slot_ids(db) == ["BED_RES"]

    def test_a_slot_batch_writes_the_beds_own_document_so_that_a_parallel_one_loses(self, db, service) -> None:
        before = db.collection(col.LOCATIONS).get("bed").get("updated_at")
        service.replace_slots("bed", tenant_key=A, role=TenantRole.GROWER, request=batch("BED_N1"))
        assert db.collection(col.LOCATIONS).get("bed").get("updated_at") not in (None, before)

    def test_a_bed_that_vanished_before_the_transaction_is_a_404(self, db, repo) -> None:
        from app.domain.models.garden_plan import SlotBatchWrite
        from app.domain.models.site import Slot

        with pytest.raises(NotFoundError):
            repo.replace_slots(SlotBatchWrite("gone", [], [Slot(slot_id="GONE_N1", geometry=point(0.4, 0.4))]))
        assert db.collection(col.SLOTS).count() == 0 and db.collection(col.HAS_SLOT).count() == 0

    def test_the_site_quota_counts_active_slots_of_every_bed_of_the_site(self, db, repo) -> None:
        db.collection(col.LOCATIONS).insert(
            {"_key": "bed2", "site_key": "site_a", "name": "Bed 2", "location_type_key": "bed", "area_m2": 1.0}
        )
        db.collection(col.LOCATIONS).insert(
            {"_key": "bed_b", "site_key": "site_b", "name": "Foreign", "location_type_key": "bed", "area_m2": 1.0}
        )
        add_slot(db, "a1", "BED_A1")
        add_slot(db, "a2", "BED_A2", archived=True)
        db.collection(col.SLOTS).insert({"_key": "b2", "slot_id": "BED2_P1", "location_key": "bed2"})
        db.collection(col.SLOTS).insert({"_key": "x1", "slot_id": "FOREIGN_P1", "location_key": "bed_b"})

        assert repo.count_active_slots("site_a", tenant_key=A) == 2  # a1 and b2; the archived one is history
        assert repo.count_active_slots("site_a", tenant_key=B) == 0  # another tenant's view of the site: nothing

    def test_reserved_among_names_only_the_reserved(self, db, repo) -> None:
        add_slot(db, "res", "BED_RES")
        add_slot(db, "free", "BED_FREE")
        db.collection(col.PLANTING_RUNS).insert({"_key": "run1", "tenant_key": A})
        db.collection(col.RUN_PLANNED_AT).insert({"_from": "planting_runs/run1", "_to": f"{col.SLOTS}/res"})

        assert repo.reserved_among(["res", "free"], tenant_key=A) == {"res"}
        assert repo.reserved_among(["res", "free"], tenant_key=B) == set()  # another tenant's view of it: none
        assert repo.reserved_among([], tenant_key=A) == set()

    def test_another_tenants_lead_cannot_replace_the_slots(self, db, service) -> None:
        add_slot(db, "free", "BED_FREE")
        with pytest.raises(NotFoundError):
            service.replace_slots("bed", tenant_key=B, role=TenantRole.LEAD, request=batch("BED_N1"))
        assert slot_ids(db) == ["BED_FREE"]

    def test_a_slot_that_changes_its_geometry_kind_keeps_none_of_the_old_keys(self, db, service) -> None:
        add_slot(db, "free", "BED_FREE")
        zone = {"kind": "polygon", "points": [[0, 0], [1, 0], [1, 1], [0, 1]]}
        updated = service.patch_slot(
            "free",
            tenant_key=A,
            role=TenantRole.GROWER,
            patch=SlotPatch.model_validate({"slot_role": "zone", "geometry": zone}),
        )

        stored = db.collection(col.SLOTS).get("free")
        assert set(stored["geometry"]) == {"kind", "points", "rotation_deg"}  # no ``origin`` of the old point
        assert updated.slot_role == "zone" and updated.geometry.kind == "polygon"
        assert stored["geometry_source"] == "editor" and stored["slot_id"] == "BED_FREE"

    def test_the_slot_patch_stores_the_correction_and_a_foreign_tenant_cannot(self, db, service) -> None:
        add_slot(db, "free", "BED_FREE")
        updated = service.patch_slot(
            "free", tenant_key=A, role=TenantRole.GROWER, patch=SlotPatch.model_validate({"geometry": point(1.0, 0.25)})
        )
        assert updated.geometry.origin == (1.0, 0.25)
        assert db.collection(col.SLOTS).get("free")["geometry"]["origin"] == [1.0, 0.25]
        with pytest.raises(NotFoundError):
            service.patch_slot("free", tenant_key=B, role=TenantRole.LEAD, patch=SlotPatch(capacity_plants=5))
        assert db.collection(col.SLOTS).get("free")["capacity_plants"] == 1


class TestGardenObjectsThroughTheBatch:
    def test_create_patch_delete_and_the_two_tenant_reads(self, db, service) -> None:
        from app.domain.models.garden_plan import CreateGardenObjectData

        data = CreateGardenObjectData.model_validate(
            {
                "object_type": "tree",
                "label": "Apple",
                "geometry": {"kind": "circle", "origin": [8, 8], "radius_m": 1.0},
                "props": {"crown_radius_m": 1.0},
            }
        )
        created = service.create_garden_object("site_a", tenant_key=A, user_key=USER, role=TenantRole.GROWER, data=data)

        assert created.site_key == "site_a" and created.created_by == USER
        assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 2
        (edge,) = list(db.collection(col.HAS_GARDEN_OBJECT).all())
        assert edge["_to"] == f"{col.GARDEN_OBJECTS}/{created.key}"
        assert service.get_garden_object(created.key, tenant_key=A).label == "Apple"
        with pytest.raises(NotFoundError):
            service.get_garden_object(created.key, tenant_key=B)

        patched = service.patch_garden_object(
            created.key, tenant_key=A, user_key=USER, role=TenantRole.GROWER, patch=GardenObjectPatch(label="Pear")
        )
        assert patched.label == "Pear" and patched.created_by == USER

        service.delete_garden_object(created.key, tenant_key=A, user_key=USER, role=TenantRole.LEAD)
        assert db.collection(col.GARDEN_OBJECTS).count() == 0 and db.collection(col.HAS_GARDEN_OBJECT).count() == 0
        (audit,) = list(db.collection(col.GARDEN_PLAN_AUDIT).all())
        assert (audit["op"], audit["entity"]) == ("delete", "garden_object")


class TestDeleteALocation:
    def test_a_bed_with_plants_is_refused_and_an_empty_one_goes_with_its_slots(self, db, service) -> None:
        add_slot(db, "free", "BED_FREE")
        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "p1", "tenant_key": A, "location_key": "bed", "removed_on": None}
        )
        with pytest.raises(PlanError) as exc:
            service.delete_location("bed", tenant_key=A, user_key=USER, role=TenantRole.LEAD)
        assert exc.value.details[0]["active_plant_count"] == 1 and db.collection(col.LOCATIONS).has("bed")

        db.collection(col.PLANT_INSTANCES).update({"_key": "p1", "removed_on": "2026-10-01"})
        service.delete_location("bed", tenant_key=A, user_key=USER, role=TenantRole.LEAD)
        assert not db.collection(col.LOCATIONS).has("bed") and db.collection(col.SLOTS).count() == 0

    def test_another_tenants_lead_deletes_nothing(self, db, service) -> None:
        with pytest.raises(NotFoundError):
            service.delete_location("bed", tenant_key=B, user_key=USER, role=TenantRole.LEAD)
        assert db.collection(col.LOCATIONS).has("bed")
