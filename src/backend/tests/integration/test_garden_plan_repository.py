"""REQ-053 WP 1.8 (#2327) — the garden-plan batch and read model against a real ArangoDB.

What no double can decide, measured here: that the revision check and the writes are **one** stream
transaction (a failure after the first write leaves nothing behind, and a stale revision writes nothing),
that the two-tenant site join of ``load_structure`` really hides a foreign site's rows (the open item of
WP 1.7), that a location delete cascades through slots and every edge written on them, and that moving a
bed leaves its slot documents byte-identical (GP-ACC-005).

Every "nothing is there" assertion is paired with the positive control in the same test — the tenant's
own row read through the same path — so an empty answer cannot be a reader that sees nothing at all.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, PlanError, PlanRevisionConflictError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.garden_plan_repository import _BATCH_WRITE, ArangoGardenPlanRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.garden_plan import PlanBatchWrite
from app.domain.models.site import Location
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("garden_plan_repository")
A, B = "ten_a", "ten_b"
USER = "u_sabine"

_DOCUMENTS = (
    col.SITES,
    col.LOCATIONS,
    col.SLOTS,
    col.GARDEN_OBJECTS,
    col.GARDEN_PLAN_AUDIT,
    col.CARE_EVENTS,
    col.LOCATION_TYPES,
    col.USERS,
    col.PLANT_INSTANCES,
    col.TASKS,
)
#: Every edge collection the batch transaction declares — derived, so a relation added to the graph later is
#: created here and the cascade tests below see it.
_EDGES = tuple(
    definition["edge_collection"]
    for definition in col.GRAPH_EDGE_DEFINITIONS
    if definition["edge_collection"] in _BATCH_WRITE
)
#: Measured 2026-10-17 at ≈ 0.85 MB for the "large" class (see the test); the spec
#: target (GP-NFR-031, REQ-053 v1.5/E-13) is ≈ 1 MB uncompressed.
LARGE_PLAN_RESPONSE_CEILING_BYTES = 1_000_000
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}


def rect(x, y, w=2, h=1, rotation=0):
    return {"kind": "rect", "origin": [x, y], "width_m": w, "length_m": h, "rotation_deg": rotation}


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
    for name in dict.fromkeys(_EDGES):
        db.create_collection(name, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    database.collection(col.LOCATION_TYPES).insert({"_key": "greenhouse", "name": "GH", "is_bed": False})
    database.collection(col.SITES).insert(
        {
            "_key": "site_a",
            "tenant_key": A,
            "name": "Garten A",
            "type": "outdoor",
            "total_area_m2": 0.0,
            "timezone": "UTC",
        }
    )
    database.collection(col.SITES).insert(
        {
            "_key": "site_b",
            "tenant_key": B,
            "name": "Garten B",
            "type": "outdoor",
            "total_area_m2": 0.0,
            "timezone": "UTC",
        }
    )
    return database


@pytest.fixture
def service(db) -> GardenPlanService:
    return GardenPlanService(ArangoSiteRepository(db), ArangoGardenPlanRepository(db))


def batch(service, ops, *, site="site_a", tenant=A, revision=0, role=TenantRole.LEAD):
    return service.apply_batch(
        site, tenant_key=tenant, user_key=USER, role=role, expected_revision=revision, operations=ops, body_bytes=100
    )


def first_save(service, *, site="site_a", tenant=A):
    from app.domain.models.garden_plan import SetBoundaryOp

    return service.set_boundary(
        site,
        tenant_key=tenant,
        user_key=USER,
        role=TenantRole.LEAD,
        operation=SetBoundaryOp(op="set_boundary", boundary=_BOUNDARY),
        expected_revision=None,
    )


def create(temp, geometry, **data):
    return {
        "op": "create_location",
        "temp_key": temp,
        "data": {"name": f"Beet {temp}", "location_type_key": "bed", "geometry": geometry, **data},
    }


class TestTheFirstSaveGpAcc001:
    def test_it_creates_the_plan_with_revision_one_and_a_derived_area(self, db, service) -> None:
        result = first_save(service)

        assert result.plan_revision == 1
        stored = db.collection(col.SITES).get("site_a")
        assert stored["plan"]["plan_revision"] == 1 and stored["plan"]["plan_updated_by"] == USER
        assert stored["total_area_m2"] == 100.0
        assert stored["plan"]["boundary"] == {**_BOUNDARY, "origin": [0.0, 0.0], "width_m": 10.0, "length_m": 10.0}
        # The audit row of the boundary change was written in the same transaction.
        (audit,) = list(db.collection(col.GARDEN_PLAN_AUDIT).all())
        assert (audit["op"], audit["revision"], audit["tenant_key"], audit["user_key"]) == ("set_boundary", 1, A, USER)

    def test_a_second_save_with_a_polygon_leaves_no_rect_keys_behind(self, db, service) -> None:
        first_save(service)
        from app.domain.models.garden_plan import SetBoundaryOp

        triangle = {"kind": "polygon", "points": [[0, 0], [10, 0], [0, 10]]}
        service.set_boundary(
            "site_a",
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            operation=SetBoundaryOp(op="set_boundary", boundary=triangle),
            expected_revision=1,
        )
        stored = db.collection(col.SITES).get("site_a")["plan"]["boundary"]
        assert set(stored) == {"kind", "points", "rotation_deg"}  # ``merge=False``: nothing of the rect survives
        service.get_plan("site_a", tenant_key=A)  # and the document still parses


class TestTheBatchIsOneTransaction:
    def test_a_created_bed_has_its_contains_edge_and_the_site_moves_to_revision_two(self, db, service) -> None:
        first_save(service)
        result = batch(service, [create("t1", rect(4, 4))], revision=1)

        assert result.plan_revision == 2
        (key,) = result.key_map.values()
        location = db.collection(col.LOCATIONS).get(key)
        assert location["site_key"] == "site_a" and location["area_m2"] == 2.0 and location["depth"] == 0
        edges = list(db.collection(col.CONTAINS).find({"_to": f"{col.LOCATIONS}/{key}"}))
        assert [e["_from"] for e in edges] == [f"{col.SITES}/site_a"]

    def test_a_child_gets_its_parents_real_key_and_an_edge_from_it(self, db, service) -> None:
        first_save(service)
        result = batch(
            service,
            [
                create("house", rect(1, 1, 5, 5))
                | {"data": {**create("house", rect(1, 1, 5, 5))["data"], "location_type_key": "greenhouse"}},
                create("child", rect(2, 2, 1, 1), parent_location_key="house"),
            ],
            revision=1,
        )
        child = db.collection(col.LOCATIONS).get(result.key_map["child"])
        assert child["parent_location_key"] == result.key_map["house"] and child["depth"] == 1
        (edge,) = list(db.collection(col.CONTAINS).find({"_to": f"{col.LOCATIONS}/{result.key_map['child']}"}))
        assert edge["_from"] == f"{col.LOCATIONS}/{result.key_map['house']}"

    def test_a_failure_after_the_first_write_leaves_nothing_behind(self, db) -> None:
        """The atomicity claim itself: a created bed, an update of a document that is gone, one abort."""
        repo = ArangoGardenPlanRepository(db)
        first_save(GardenPlanService(ArangoSiteRepository(db), repo))
        write = PlanBatchWrite(
            site_key="site_a",
            tenant_key=A,
            editor_key=USER,
            expected_revision=1,
            basis_revision=1,
            location_inserts=[("t", Location(name="Neu", site_key="site_a", area_m2=0, geometry=rect(4, 4)))],
            location_updates=[("ghost", {"name": "Weg"})],
        )
        with pytest.raises(WriteConflictError):
            repo.apply_plan_batch(write)

        assert list(db.collection(col.LOCATIONS).all()) == []
        assert list(db.collection(col.CONTAINS).all()) == []
        assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 1
        # Positive control: the same repository does write when nothing fails.
        repo.apply_plan_batch(
            PlanBatchWrite(
                site_key="site_a",
                tenant_key=A,
                editor_key=USER,
                expected_revision=1,
                basis_revision=1,
                location_inserts=[("t", Location(name="Neu", site_key="site_a", area_m2=0, geometry=rect(4, 4)))],
            )
        )
        assert len(list(db.collection(col.LOCATIONS).all())) == 1

    def test_a_stale_revision_writes_nothing_gp_acc_010(self, db, service) -> None:
        first_save(service)
        winner = batch(service, [create("a", rect(1, 1))], revision=1)
        assert winner.plan_revision == 2
        with pytest.raises(PlanRevisionConflictError) as conflict:
            batch(service, [create("b", rect(6, 6))], revision=1)

        assert conflict.value.current_revision == 2
        assert conflict.value.details[0]["changed_by"] == "Sabine"
        assert [loc["name"] for loc in db.collection(col.LOCATIONS).all()] == ["Beet a"]
        assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 2

    def test_the_revision_changed_between_the_read_and_the_transaction_is_a_conflict(self, db) -> None:
        repo = ArangoGardenPlanRepository(db)
        first_save(GardenPlanService(ArangoSiteRepository(db), repo))
        write = PlanBatchWrite(
            site_key="site_a", tenant_key=A, editor_key=USER, expected_revision=1, basis_revision=0
        )  # the service validated against revision 0, the client expects 1, the store says 1
        with pytest.raises(PlanRevisionConflictError):
            repo.apply_plan_batch(write)

    def test_another_tenants_site_is_not_found_inside_the_transaction_too(self, db) -> None:
        repo = ArangoGardenPlanRepository(db)
        with pytest.raises(NotFoundError):
            repo.apply_plan_batch(
                PlanBatchWrite(site_key="site_b", tenant_key=A, editor_key=USER, expected_revision=0, basis_revision=0)
            )
        with pytest.raises(NotFoundError):
            repo.apply_plan_batch(
                PlanBatchWrite(site_key="site_b", tenant_key="", editor_key=USER, expected_revision=0, basis_revision=0)
            )


class TestTheTwoTenantSiteJoin:
    def test_a_foreign_sites_structure_is_invisible_and_the_own_is_not(self, db, service) -> None:
        first_save(service, site="site_a", tenant=A)
        first_save(service, site="site_b", tenant=B)
        batch(service, [create("a", rect(1, 1))], site="site_a", tenant=A, revision=1)
        batch(service, [create("b", rect(1, 1))], site="site_b", tenant=B, revision=1)
        repo = ArangoGardenPlanRepository(db)

        own_locations, _ = repo.load_structure("site_a", tenant_key=A)
        foreign_locations, _ = repo.load_structure("site_a", tenant_key=B)

        assert [loc.name for loc in own_locations] == ["Beet a"]  # positive control
        assert foreign_locations == []
        assert repo.load_structure("site_b", tenant_key=A) == ([], [])
        with pytest.raises(ValueError, match="tenant_key"):
            repo.load_structure("site_a", tenant_key="")  # an empty tenant is no tenant

    def test_the_service_answers_404_for_the_foreign_site_on_every_method(self, db, service) -> None:
        first_save(service, site="site_b", tenant=B)
        for call in (
            lambda: service.get_plan("site_b", tenant_key=A),
            lambda: service.list_audit("site_b", tenant_key=A),
            lambda: batch(service, [create("a", rect(1, 1))], site="site_b", tenant=A, revision=1),
        ):
            with pytest.raises(NotFoundError):
                call()
        assert service.get_plan("site_b", tenant_key=B).plan_revision == 1  # positive control
        assert list(db.collection(col.LOCATIONS).all()) == []

    def test_a_key_of_the_other_tenants_site_cannot_be_referenced(self, db, service) -> None:
        first_save(service, site="site_a", tenant=A)
        first_save(service, site="site_b", tenant=B)
        theirs = batch(service, [create("b", rect(1, 1))], site="site_b", tenant=B, revision=1).key_map["b"]
        from app.common.exceptions import PlanValidationError

        with pytest.raises(PlanValidationError) as refused:
            batch(
                service,
                [{"op": "delete", "entity": "location", "key": theirs}],
                site="site_a",
                tenant=A,
                revision=1,
            )
        assert refused.value.codes == ["reference.not_found"]
        assert db.collection(col.LOCATIONS).get(theirs) is not None  # theirs is untouched


class TestMovingABedLeavesItsSlotsAloneGpAcc005:
    def test_the_slot_documents_are_byte_identical_and_the_read_model_transforms_them(self, db, service) -> None:
        first_save(service)
        bed = batch(service, [create("bed", rect(1, 1, 2, 1))], revision=1).key_map["bed"]
        slots = db.collection(col.SLOTS)
        for n in range(12):
            created = slots.insert(
                {
                    "slot_id": f"BED_P{n}",
                    "location_key": bed,
                    "slot_role": "position",
                    "geometry": {"kind": "point", "origin": [0.1 * n, 0.2]},
                    "capacity_plants": 1,
                    "currently_occupied": False,
                    "sequence": n + 1,
                }
            )
            db.collection(col.HAS_SLOT).insert(
                {"_from": f"{col.LOCATIONS}/{bed}", "_to": f"{col.SLOTS}/{created['_key']}"}
            )
        before = sorted(slots.all(), key=lambda d: d["_key"])

        batch(
            service,
            [{"op": "update_geometry", "entity": "location", "key": bed, "geometry": rect(1, 1.5, 2, 1, 90)}],
            revision=2,
        )

        after = sorted(slots.all(), key=lambda d: d["_key"])
        assert after == before  # including ``_rev``: not a single slot document was rewritten
        view = service.get_plan("site_a", tenant_key=A)
        by_id = {slot.slot_id: slot for slot in view.slots}
        assert len(view.slots) == 12
        # p_plan = origin + R(90°)·p_bed with origin (1, 1.5): slot P0 (0, 0.2) → (1 - 0.2, 1.5 + 0)
        assert by_id["BED_P0"].plan_geometry["origin"] == pytest.approx([0.8, 1.5])
        assert by_id["BED_P10"].plan_geometry["origin"] == pytest.approx([0.8, 2.5])


class TestDeleteCascade:
    def _seed(self, db, service):
        first_save(service)
        result = batch(
            service,
            [
                create("house", rect(1, 1, 6, 6), location_type_key="greenhouse"),
                create("row", rect(2, 2, 1, 1), parent_location_key="house"),
                {
                    "op": "create_garden_object",
                    "temp_key": "inside",
                    "data": {
                        "object_type": "path",
                        "parent_location_key": "house",
                        "geometry": {"kind": "polyline", "points": [[2, 5], [6, 5]], "width_m": 0.5},
                    },
                },
                {
                    "op": "create_garden_object",
                    "temp_key": "outside",
                    "data": {
                        "object_type": "path",
                        "geometry": {"kind": "polyline", "points": [[0.5, 9], [9, 9]], "width_m": 0.5},
                    },
                },
            ],
            revision=1,
        )
        keys = result.key_map
        slot = db.collection(col.SLOTS).insert({"slot_id": "ROW_P1", "location_key": keys["row"]})
        other = db.collection(col.SLOTS).insert({"slot_id": "ROW_P2", "location_key": keys["row"]})
        db.collection(col.HAS_SLOT).insert({"_from": f"{col.LOCATIONS}/{keys['row']}", "_to": slot["_id"]})
        db.collection(col.ADJACENT_TO).insert({"_from": slot["_id"], "_to": other["_id"]})
        db.collection(col.ADJACENT_TO).insert({"_from": other["_id"], "_to": slot["_id"]})
        db.collection(col.HAS_TASK).insert(
            {"_from": f"{col.GARDEN_OBJECTS}/{keys['inside']}", "_to": f"{col.TASKS}/t1"}
        )
        return keys

    def test_the_subtree_its_slots_and_every_edge_go_in_one_transaction_and_are_audited(self, db, service) -> None:
        keys = self._seed(db, service)
        result = batch(service, [{"op": "delete", "entity": "location", "key": keys["house"]}], revision=2)

        assert sorted(result.deleted) == sorted([keys["house"], keys["row"], keys["inside"]])
        assert list(db.collection(col.LOCATIONS).all()) == []
        assert list(db.collection(col.SLOTS).all()) == []
        for edge in (col.CONTAINS, col.HAS_SLOT, col.ADJACENT_TO, col.HAS_TASK):
            assert [
                e
                for e in db.collection(edge).all()
                if "garden_objects/" in e["_from"] + e["_to"]
                or "slots/" in e["_from"] + e["_to"]
                or "locations/" in e["_from"] + e["_to"]
            ] == [], edge
        # Positive control: the object outside the house survived, with its site edge.
        assert [o["_key"] for o in db.collection(col.GARDEN_OBJECTS).all()] == [keys["outside"]]
        assert len(list(db.collection(col.HAS_GARDEN_OBJECT).all())) == 1
        audit = {(a["op"], a["key"]): a for a in db.collection(col.GARDEN_PLAN_AUDIT).find({"revision": 3})}
        assert set(audit) == {
            ("delete", keys["house"]),
            ("delete_cascade", keys["row"]),
            ("delete_cascade", keys["inside"]),
        }
        assert all(a["tenant_key"] == A and a["user_key"] == USER for a in audit.values())

    def test_a_plant_standing_in_the_subtree_blocks_the_delete_and_nothing_goes(self, db, service) -> None:
        keys = self._seed(db, service)
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": "p1",
                "tenant_key": A,
                "instance_id": "T-1",
                "species_key": "sp",
                "location_key": keys["row"],
                "removed_on": None,
            }
        )
        with pytest.raises(PlanError) as refused:
            batch(service, [{"op": "delete", "entity": "location", "key": keys["house"]}], revision=2)
        assert refused.value.status_code == 409 and refused.value.details[0]["active_plant_count"] == 1
        assert len(list(db.collection(col.LOCATIONS).all())) == 2
        # A removed plant does not block (positive control for the predicate).
        db.collection(col.PLANT_INSTANCES).update({"_key": "p1", "removed_on": "2026-10-01"})
        assert batch(service, [{"op": "delete", "entity": "location", "key": keys["house"]}], revision=2).deleted

    def test_the_transaction_rechecks_plants_a_stale_service_read_would_miss(self, db, service) -> None:
        keys = self._seed(db, service)
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": "p1",
                "tenant_key": A,
                "instance_id": "T-1",
                "species_key": "sp",
                "location_key": keys["row"],
                "removed_on": None,
            }
        )
        repo = ArangoGardenPlanRepository(db)
        with pytest.raises(PlanError):  # the service would have refused; here the repository is driven directly
            repo.apply_plan_batch(
                PlanBatchWrite(
                    site_key="site_a",
                    tenant_key=A,
                    editor_key=USER,
                    expected_revision=2,
                    basis_revision=2,
                    location_deletes=[keys["row"]],
                )
            )
        assert len(list(db.collection(col.LOCATIONS).all())) == 2

    def test_deleting_an_object_cuts_its_edges_and_audits_it(self, db, service) -> None:
        keys = self._seed(db, service)
        batch(service, [{"op": "delete", "entity": "garden_object", "key": keys["inside"]}], revision=2)
        assert db.collection(col.GARDEN_OBJECTS).get(keys["inside"]) is None
        assert list(db.collection(col.HAS_TASK).all()) == []
        assert [e["_to"] for e in db.collection(col.HAS_GARDEN_OBJECT).all()] == [
            f"{col.GARDEN_OBJECTS}/{keys['outside']}"
        ]


class TestTheReadModel:
    def test_plants_and_open_task_counts_ride_in_the_same_read(self, db, service) -> None:
        first_save(service)
        bed = batch(service, [create("bed", rect(1, 1, 2, 1))], revision=1).key_map["bed"]
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": "p1",
                "tenant_key": A,
                "instance_id": "T-1",
                "species_key": "sp",
                "location_key": bed,
                "removed_on": None,
                "slot_key": "s",
            }
        )
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": "p2",
                "tenant_key": A,
                "instance_id": "T-2",
                "species_key": "sp",
                "location_key": bed,
                "removed_on": "2026-01-01",
            }
        )
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": "p3",
                "tenant_key": B,
                "instance_id": "X-1",
                "species_key": "sp",
                "location_key": bed,
                "removed_on": None,
            }
        )
        tasks = db.collection(col.TASKS)
        tasks.insert(
            {
                "tenant_key": A,
                "entity_type": "location",
                "entity_key": bed,
                "status": "pending",
                "due_date": "2020-01-01T00:00:00+00:00",
            }
        )
        tasks.insert(
            {
                "tenant_key": A,
                "entity_type": "plant_instance",
                "entity_key": "p1",
                "status": "in_progress",
                "due_date": "2999-01-01T00:00:00+00:00",
            }
        )
        tasks.insert({"tenant_key": A, "entity_type": "location", "entity_key": bed, "status": "completed"})
        tasks.insert(
            {"tenant_key": A, "entity_type": "location", "entity_key": bed, "status": "pending", "suggested": True}
        )
        tasks.insert({"tenant_key": B, "entity_type": "location", "entity_key": bed, "status": "pending"})

        view = service.get_plan("site_a", tenant_key=A)

        assert [p.key for p in view.plants] == ["p1"]  # removed and foreign plants stay out
        assert view.task_counters[bed].open_task_count == 2
        assert view.task_counters[bed].overdue_task_count == 1
        assert view.season_states == {bed: "planted"}
        assert view.plan_updated_by_name == "Sabine"

    def test_a_garden_objects_open_tasks_ride_in_the_same_read_and_a_foreign_tenant_does_not_leak(
        self, db, service
    ) -> None:
        first_save(service)
        keys = batch(
            service,
            [
                {
                    "op": "create_garden_object",
                    "temp_key": "compost",
                    "data": {"object_type": "compost", "geometry": rect(8, 8, 1, 1)},
                }
            ],
            revision=1,
        ).key_map
        compost = keys["compost"]
        tasks = db.collection(col.TASKS)
        tasks.insert(
            {
                "tenant_key": A,
                "entity_type": "garden_object",
                "entity_key": compost,
                "status": "pending",
                "due_date": "2020-01-01T00:00:00+00:00",
            }
        )
        tasks.insert({"tenant_key": A, "entity_type": "garden_object", "entity_key": compost, "status": "completed"})
        tasks.insert(
            {
                "tenant_key": A,
                "entity_type": "garden_object",
                "entity_key": compost,
                "status": "pending",
                "suggested": True,
            }
        )
        tasks.insert({"tenant_key": B, "entity_type": "garden_object", "entity_key": compost, "status": "pending"})

        view = service.get_plan("site_a", tenant_key=A)

        assert view.object_task_counters[compost].open_task_count == 1  # open, own tenant, not a suggestion
        assert view.object_task_counters[compost].overdue_task_count == 1
        assert service.get_plan("site_a", tenant_key=A, include=frozenset({"plants"})).object_task_counters == {}

    def test_archived_slots_stay_out_of_the_plan(self, db, service) -> None:
        first_save(service)
        bed = batch(service, [create("bed", rect(1, 1, 2, 1))], revision=1).key_map["bed"]
        db.collection(col.SLOTS).insert(
            {"slot_id": "BED_P1", "location_key": bed, "geometry": {"kind": "point", "origin": [0, 0]}}
        )
        db.collection(col.SLOTS).insert(
            {"slot_id": "BED_P2", "location_key": bed, "archived_at": "2026-01-01T00:00:00+00:00"}
        )
        assert [s.slot_id for s in service.get_plan("site_a", tenant_key=A).slots] == ["BED_P1"]

    def test_the_audit_list_is_newest_first_and_names_the_editor(self, db, service) -> None:
        first_save(service)
        bed = batch(service, [create("bed", rect(1, 1, 2, 1))], revision=1).key_map["bed"]
        batch(service, [{"op": "delete", "entity": "location", "key": bed}], revision=2)
        entries = service.list_audit("site_a", tenant_key=A)
        assert [(e.revision, e.op) for e in entries] == [(3, "delete"), (1, "set_boundary")]
        assert entries[0].changed_by_name == "Sabine" and entries[0].summary == "Beet bed"
        assert service.list_audit("site_a", tenant_key=A, offset=1, limit=1)[0].revision == 1

    def test_a_large_garden_fits_the_response_budget_and_the_time_budget(self, db, service) -> None:
        """GP-NFR-002/031: 150 beds, 300 objects, 3 000 slots, 2 000 plants.

        **Measured against a ceiling, not against the spec's 500 KB.** The "large" class of §25.1 comes to
        about 0.85 MB of compact JSON in this shape (3 000 slots ≈ 0.43 MB, 2 000 plants ≈ 0.28 MB), because
        every slot and plant is an object with named fields. The ceiling below is the *measured* size with
        a margin: it stops the response from growing, it does not certify GP-NFR-031. The gap is a spec
        decision (compact encoding, paginated plants as §25.1 foresees from the load limit, or a larger
        budget) and is tracked in the issue named in the work package's report.
        """
        import time

        from app.api.v1.garden_plan.tenant_router import _plan_response

        first_save(service)
        locations = db.collection(col.LOCATIONS)
        beds = locations.insert_many(
            [
                {
                    "name": f"Beet {n}",
                    "site_key": "site_a",
                    "location_type_key": "bed",
                    "depth": 0,
                    "path": f"beet_{n}",
                    "area_m2": 2.0,
                    "bed_status": "active",
                    "geometry": rect(0.1 + (n % 15) * 0.65, 0.1 + (n // 15) * 0.9, 0.6, 0.8),
                    "bbox": [0.0, 0.0, 1.0, 1.0],
                }
                for n in range(150)
            ]
        )
        bed_keys = [b["_key"] for b in beds]
        db.collection(col.GARDEN_OBJECTS).insert_many(
            [
                {
                    "site_key": "site_a",
                    "object_type": "path",
                    "label": f"Weg {n}",
                    "geometry": {
                        "kind": "polyline",
                        "points": [[0.5, 9 + n * 0.001], [9, 9 + n * 0.001]],
                        "width_m": 0.3,
                    },
                    "bbox": [0.0, 0.0, 1.0, 1.0],
                    "props": {"object_type": "path", "surface": "gravel"},
                }
                for n in range(300)
            ]
        )
        slot_docs = []
        for n in range(3000):
            slot_docs.append(
                {
                    "slot_id": f"BEET{n // 20}_R{n % 20}",
                    "location_key": bed_keys[n // 20],
                    "slot_role": "position",
                    "geometry": {"kind": "point", "origin": [0.1 + (n % 5) * 0.1, 0.1 + (n % 7) * 0.1]},
                    "capacity_plants": 1,
                    "currently_occupied": n < 2000,
                    "row_index": n % 7,
                    "sequence": n % 20 + 1,
                }
            )
        db.collection(col.SLOTS).insert_many(slot_docs)
        db.collection(col.PLANT_INSTANCES).insert_many(
            [
                {
                    "tenant_key": A,
                    "instance_id": f"TOM-{n:04d}",
                    "species_key": "species_solanum_lycopersicum",
                    "location_key": bed_keys[n // 20],
                    "slot_key": f"{n + 1000000}",
                    "current_phase_key": "growth_phase_vegetative",
                    "removed_on": None,
                }
                for n in range(2000)
            ]
        )
        started = time.perf_counter()
        view = service.get_plan("site_a", tenant_key=A)
        response = _plan_response(view)
        elapsed = time.perf_counter() - started
        size = len(response.model_dump_json(exclude_none=True).encode())

        assert (len(view.locations), len(view.garden_objects), len(view.slots), len(view.plants)) == (
            150,
            300,
            3000,
            2000,
        )
        assert size <= LARGE_PLAN_RESPONSE_CEILING_BYTES, f"{size} bytes"
        # A single sample on a shared CI runner (0.5-0.7 s measured there) cannot certify the 300 ms p95 of
        # GP-NFR-002; that assertion belongs to the benchmark suite (WP 5.4). This bound only catches an
        # order-of-magnitude regression such as a per-slot query.
        assert elapsed <= 3.0, f"{elapsed:.3f} s (single sample, not a p95)"


class TestAStaleReadCannotOverwriteWhatAnotherPathChanged:
    """Review F-01 — the batch writes the fields it changed, not the whole model it read earlier."""

    def test_a_z_order_change_leaves_a_status_set_after_the_read_alone(self, db) -> None:
        repo = ArangoGardenPlanRepository(db)
        service = GardenPlanService(ArangoSiteRepository(db), repo)
        first_save(service)
        bed = batch(service, [create("bed", rect(1, 1, 2, 1))], revision=1).key_map["bed"]
        stale = repo.load_structure

        def read_then_change_elsewhere(site_key, *, tenant_key):
            result = stale(site_key, tenant_key=tenant_key)
            # PUT /locations, a status route, a soil edit … run outside the plan revision (GP-NFR-007).
            db.collection(col.LOCATIONS).update(
                {"_key": bed, "bed_status": "retired", "irrigation_zone_key": "zone_1", "soil_profile": {"ph": 6.5}}
            )
            return result

        repo.load_structure = read_then_change_elsewhere  # type: ignore[method-assign]
        batch(service, [{"op": "set_z_order", "entity": "location", "key": bed, "z_order": 9}], revision=2)

        stored = db.collection(col.LOCATIONS).get(bed)
        assert stored["z_order"] == 9
        assert (stored["bed_status"], stored["irrigation_zone_key"], stored["soil_profile"]) == (
            "retired",
            "zone_1",
            {"ph": 6.5},
        )

    def test_a_geometry_that_changes_kind_leaves_none_of_the_old_kinds_keys(self, db, service) -> None:
        first_save(service)
        bed = batch(service, [create("bed", rect(1, 1, 2, 1))], revision=1).key_map["bed"]
        triangle = {"kind": "polygon", "points": [[1, 1], [4, 1], [1, 4]]}
        batch(service, [{"op": "update_geometry", "entity": "location", "key": bed, "geometry": triangle}], revision=2)
        assert set(db.collection(col.LOCATIONS).get(bed)["geometry"]) == {"kind", "points", "rotation_deg"}
        service.get_plan("site_a", tenant_key=A)  # parses


class TestEveryRelationOfADeletedVertexGoes:
    """Review F-02 — the cascade is derived from the graph, not from the list ``delete_location`` carries."""

    def test_reservations_care_events_and_zone_links_do_not_dangle(self, db, service) -> None:
        first_save(service)
        keys = batch(
            service,
            [
                create("bed", rect(1, 1, 3, 2)),
                {
                    "op": "create_garden_object",
                    "temp_key": "barrel",
                    "data": {
                        "object_type": "water_source",
                        "geometry": {"kind": "point", "origin": [8, 8]},
                        "props": {"water_source_kind": "rain_barrel"},
                    },
                },
            ],
            revision=1,
        ).key_map
        slot = db.collection(col.SLOTS).insert({"slot_id": "BED_P1", "location_key": keys["bed"]})
        bed_id, barrel_id = f"{col.LOCATIONS}/{keys['bed']}", f"{col.GARDEN_OBJECTS}/{keys['barrel']}"
        relations = {
            col.RUN_PLANNED_AT: {"_from": "planting_runs/run_1", "_to": slot["_id"]},  # a run's reservation
            col.CARE_EVENT_AT: {"_from": "care_events/ev_1", "_to": bed_id},
            col.ZONE_COVERS: {"_from": "irrigation_zones/z_1", "_to": bed_id},
            col.ZONE_SUPPLIED_BY: {"_from": "irrigation_zones/z_1", "_to": barrel_id},
            col.PLACED_IN: {"_from": "plant_instances/historic", "_to": slot["_id"]},
        }
        for edge, doc in relations.items():
            db.collection(edge).insert(doc)
        survivor = db.collection(col.ZONE_COVERS).insert(
            {"_from": "irrigation_zones/z_1", "_to": "locations/elsewhere"}
        )

        batch(
            service,
            [
                {"op": "delete", "entity": "location", "key": keys["bed"]},
                {"op": "delete", "entity": "garden_object", "key": keys["barrel"]},
            ],
            revision=2,
        )

        for edge in relations:
            ends = {e["_from"] for e in db.collection(edge).all()} | {e["_to"] for e in db.collection(edge).all()}
            assert not ends & {bed_id, barrel_id, slot["_id"]}, f"{edge} still points at a deleted vertex"
        assert db.collection(col.ZONE_COVERS).get(survivor["_key"]) is not None  # positive control: other edges stay


class _LosesTheRace(ArangoGardenPlanRepository):
    """A repository whose transaction is overtaken: a rival commits between its read and its first write."""

    def __init__(self, db, rival) -> None:
        super().__init__(db)
        self._rival = rival

    def _take_revision(self, txn, write, revision) -> None:
        self._rival()
        super()._take_revision(txn, write, revision)


class TestTwoWritersAtOneRevisionGpAcc010:
    def test_the_loser_is_told_the_revision_conflict_not_a_write_conflict(self, db) -> None:
        winner_repo = ArangoGardenPlanRepository(db)
        winner = GardenPlanService(ArangoSiteRepository(db), winner_repo)
        first_save(winner)

        def rival() -> None:
            batch(winner, [create("winner", rect(1, 1))], revision=1)

        loser = GardenPlanService(ArangoSiteRepository(db), _LosesTheRace(db, rival))
        with pytest.raises(PlanRevisionConflictError) as conflict:
            batch(loser, [create("loser", rect(6, 6))], revision=1)

        assert conflict.value.current_revision == 2 and conflict.value.details[0]["changed_by"] == "Sabine"
        assert [loc["name"] for loc in db.collection(col.LOCATIONS).all()] == ["Beet winner"]
        assert db.collection(col.SITES).get("site_a")["plan"]["plan_revision"] == 2
