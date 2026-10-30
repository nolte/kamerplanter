"""REQ-053 WP 5.3 (#2432) - the plan import against a real ArangoDB.

What no double can decide, measured here: that an export restored into an empty site gives back the geometry,
names, types and soil profiles under **new keys** (GP-ACC-031), that the snapshot of a ``replace`` lands in the
same transaction as the deletes, that a bed with a plant survives (V-09), and that a site of another tenant
answers 404 *before* the file is read.

Every "nothing happened" assertion is paired with the positive control in the same test.
"""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, PlanError, PlanValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.garden_plan_repository import _BATCH_WRITE, ArangoGardenPlanRepository
from app.data_access.arango.irrigation_zone_repository import ArangoIrrigationZoneRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.garden_plan import SetBoundaryOp
from app.domain.models.garden_plan_import import MAX_SNAPSHOTS_PER_SITE
from app.domain.models.irrigation_zone import IrrigationZone
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_import_service import GardenPlanImportService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("garden_plan_import")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
_BOUNDARY = {"kind": "rect", "origin": [0, 0], "width_m": 20, "length_m": 20, "rotation_deg": 0}

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
    # the plan read model asks when a bed was last watered (REQ-053 WP 7.3)
    col.WATERING_EVENTS,
    col.IRRIGATION_ZONES,
    col.SUBSTRATES,
    col.ACTUATORS,  # a zone transaction declares it for the coupling (WP 7.4)
)
_EDGES = tuple(
    definition["edge_collection"]
    for definition in col.GRAPH_EDGE_DEFINITIONS
    if definition["edge_collection"] in _BATCH_WRITE
)


def rect(x: float, y: float, w: float = 2, h: float = 1) -> dict[str, Any]:
    return {"kind": "rect", "origin": [x, y], "width_m": w, "length_m": h, "rotation_deg": 0}


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


def _site(key: str, tenant: str, name: str) -> dict[str, Any]:
    return {"_key": key, "tenant_key": tenant, "name": name, "type": "outdoor", "total_area_m2": 0.0, "timezone": "UTC"}


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.LOCATION_TYPES).insert({"_key": "bed", "name": "Bed", "is_bed": True})
    database.collection(col.LOCATION_TYPES).insert({"_key": "greenhouse", "name": "GH", "is_bed": False})
    database.collection(col.SITES).insert(_site("site_a", A, "Garten A"))
    database.collection(col.SITES).insert(_site("site_c", A, "Leerer Garten"))  # an empty site of the same tenant
    database.collection(col.SITES).insert(_site("site_b", B, "Garten B"))
    return database


class Rig:
    def __init__(self, db) -> None:
        sites, plans = ArangoSiteRepository(db), ArangoGardenPlanRepository(db)
        self.db = db
        self.plans = GardenPlanService(sites, plans, ArangoIrrigationZoneRepository(db))
        self.export = GardenPlanExportService(sites, plans, self.plans)
        self.dispatched: list[str] = []
        self.importer = GardenPlanImportService(
            sites, plans, self.plans, self.export, dispatch_adjacency=self.dispatched.append
        )

    def batch(self, ops, *, site="site_a", tenant=A, revision):
        return self.plans.apply_batch(
            site,
            tenant_key=tenant,
            user_key=USER,
            role=TenantRole.LEAD,
            expected_revision=revision,
            operations=ops,
            body_bytes=100,
        )

    def exported(self, site: str = "site_a", tenant: str = A) -> dict[str, Any]:
        return json.loads(self.export.export_json(site, tenant_key=tenant).model_dump_json())

    def exported_partial(self, scope: str, *names: str, site: str = "site_a", tenant: str = A) -> dict[str, Any]:
        document = self.export.export_json(site, tenant_key=tenant, scope=scope, keys=list(names))  # type: ignore[arg-type]
        return json.loads(document.model_dump_json())

    def location_key(self, name: str, site: str = "site_a") -> str:
        (row,) = list(self.db.collection(col.LOCATIONS).find({"site_key": site, "name": name}))
        return row["_key"]

    def object_key(self, label: str, site: str = "site_a") -> str:
        (row,) = list(self.db.collection(col.GARDEN_OBJECTS).find({"site_key": site, "label": label}))
        return row["_key"]

    def run(self, document, *, site="site_c", tenant=A, role=TenantRole.LEAD, **options: Any):
        arguments: dict[str, Any] = {
            "mode": "replace",
            "dry_run": False,
            "force": False,
            "confirm_site_name": "Leerer Garten",
        } | options
        return self.importer.import_plan(
            site, tenant_key=tenant, user_key=USER, role=role, document=document, **arguments
        )


@pytest.fixture
def rig(db) -> Rig:
    return Rig(db)


def build_source_plan(rig: Rig) -> dict[str, str]:
    """Five beds (one in a greenhouse), three objects, twenty slots, soil profiles - the GP-ACC-031 plan."""
    db = rig.db
    rig.plans.set_boundary(
        "site_a",
        tenant_key=A,
        user_key=USER,
        role=TenantRole.LEAD,
        operation=SetBoundaryOp(op="set_boundary", boundary=_BOUNDARY),
        expected_revision=None,
    )

    def bed(temp, geometry, **data):
        return {
            "op": "create_location",
            "temp_key": temp,
            "data": {"name": f"Beet {temp}", "location_type_key": "bed", "geometry": geometry, **data},
        }

    ops: list[dict[str, Any]] = [
        {
            "op": "create_location",
            "temp_key": "house",
            "data": {
                "name": "Gewaechshaus",
                "location_type_key": "greenhouse",
                "geometry": rect(10, 10, 8, 8),
            },
        },
        bed("b1", rect(1, 1, 3, 1)),
        bed("b2", rect(1, 3, 3, 1), notes="Mulch"),
        bed("b3", rect(1, 5, 3, 1), sun_exposure="full_sun"),
        bed("b4", rect(5, 1, 3, 1)),
        bed("b5", rect(11, 11, 3, 1), parent_location_key="house"),
    ]
    for number in range(3):
        ops.append(
            {
                "op": "create_garden_object",
                "temp_key": f"o{number}",
                "data": {
                    "object_type": "tree",
                    "label": f"Baum {number}",
                    "geometry": {"kind": "circle", "origin": [15 + number, 3], "radius_m": 0.8},
                    "props": {"object_type": "tree", "crown_radius_m": 0.8, "foliage": "deciduous"},
                },
            }
        )
    keys = rig.batch(ops, revision=1).key_map
    for temp, texture in (("b1", "loam"), ("b2", "sand")):
        db.collection(col.LOCATIONS).update(
            {
                "_key": keys[temp],
                "soil_profile": {"soil_texture": texture, "growing_medium_kind": "native_soil", "ph": 6.5},
                "bed_status": "active",
            }
        )
    for index, temp in enumerate(("b1", "b2", "b3", "b4")):
        for n in range(5):
            created = db.collection(col.SLOTS).insert(
                {
                    "slot_id": f"BED{index}_P{n}",
                    "location_key": keys[temp],
                    "slot_role": "position",
                    "geometry": {"kind": "point", "origin": [0.3 + 0.5 * n, 0.5]},
                    "capacity_plants": 1,
                    "currently_occupied": False,
                    "sequence": n + 1,
                }
            )
            db.collection(col.HAS_SLOT).insert(
                {"_from": f"{col.LOCATIONS}/{keys[temp]}", "_to": f"{col.SLOTS}/{created['_key']}"}
            )
    return keys


def normalised(document: dict[str, Any]) -> dict[str, Any]:
    """The export without keys, timestamps and the revision, references rewritten to names (the GP-ACC-031 diff)."""
    out = copy.deepcopy(document)
    name_of = {loc["key"]: loc["name"] for loc in out["locations"]}
    for loc in out["locations"]:
        loc["parent_location_key"] = name_of.get(loc["parent_location_key"])
        del loc["key"]
    for slot in out["slots"]:
        slot["location_key"] = name_of[slot["location_key"]]
        del slot["key"]
    for obj in out["garden_objects"]:
        obj["parent_location_key"] = name_of.get(obj["parent_location_key"])
        del obj["key"]
    out.pop("exported_at")
    out["plan"].pop("plan_revision")
    out.pop("site")  # the target is another site, with its own name
    out["locations"].sort(key=lambda item: item["name"])
    out["slots"].sort(key=lambda item: (item["location_key"], item["slot_id"]))
    out["garden_objects"].sort(key=lambda item: item["label"])
    return out


class TestRestoreGpAcc031:
    def test_an_export_replaced_into_an_empty_site_gives_back_the_plan_under_new_keys(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        assert len(source["locations"]) == 6 and len(source["slots"]) == 20 and len(source["garden_objects"]) == 3

        report = rig.run(source)

        assert report.applied and report.errors == [] and report.plan_revision == 1
        assert report.would_create.locations == 6 and report.would_create.slots == 20
        restored = rig.exported("site_c")
        assert normalised(restored) == normalised(source)
        # Positive control for the diff above: it does see a difference when there is one.
        changed = copy.deepcopy(restored)
        changed["locations"][0]["name"] = "anders"
        assert normalised(changed) != normalised(source)
        # Keys are new (GP-NFR-051): nothing the file named was kept.
        file_keys = {item["key"] for name in ("locations", "slots", "garden_objects") for item in source[name]}
        new_keys = {item["key"] for name in ("locations", "slots", "garden_objects") for item in restored[name]}
        assert new_keys and not (file_keys & new_keys)
        # The source site is untouched.
        assert rig.exported("site_a")["locations"] == source["locations"]

    def test_the_restored_documents_are_wired_like_created_ones(self, rig) -> None:
        build_source_plan(rig)
        rig.run(rig.exported())
        db = rig.db
        (house,) = [d for d in db.collection(col.LOCATIONS).find({"site_key": "site_c", "name": "Gewaechshaus"})]
        (child,) = [d for d in db.collection(col.LOCATIONS).find({"site_key": "site_c", "name": "Beet b5"})]
        assert child["parent_location_key"] == house["_key"] and child["depth"] == 1
        (edge,) = list(db.collection(col.CONTAINS).find({"_to": child["_id"]}))
        assert edge["_from"] == house["_id"]
        slot = next(iter(db.collection(col.SLOTS).find({"location_key": child["_key"]})), None)
        assert slot is None  # b5 has no slots; the four beds below have, each with its edge
        beds = list(db.collection(col.LOCATIONS).find({"site_key": "site_c", "name": "Beet b1"}))
        edges = list(db.collection(col.HAS_SLOT).find({"_from": beds[0]["_id"]}))
        assert len(edges) == 5
        assert db.collection(col.SITES).get("site_c")["plan"]["plan_revision"] == 1
        assert db.collection(col.SITES).get("site_c")["total_area_m2"] == 400.0
        # The adjacency recompute is asked for exactly the beds that received slots.
        with_slots = {
            slot["location_key"]
            for slot in db.collection(col.SLOTS).find({})
            if slot["location_key"] in {d["_key"] for d in db.collection(col.LOCATIONS).find({"site_key": "site_c"})}
        }
        assert len(with_slots) == 4 and sorted(rig.dispatched) == sorted(with_slots)

    def test_a_dry_run_reports_and_writes_nothing(self, rig) -> None:
        build_source_plan(rig)
        before = {name: sorted(d["_key"] for d in rig.db.collection(name).all()) for name in _DOCUMENTS}

        report = rig.run(rig.exported(), dry_run=True, confirm_site_name=None)

        assert report.dry_run and not report.applied and report.errors == []
        assert (report.would_create.locations, report.would_create.garden_objects, report.would_create.slots) == (
            6,
            3,
            20,
        )
        assert report.would_update.plan_settings == 1
        assert {name: sorted(d["_key"] for d in rig.db.collection(name).all()) for name in _DOCUMENTS} == before
        assert rig.db.collection(col.SITES).get("site_c").get("plan") is None


class TestZonesWp72:
    """REQ-053 WP 7.2 (#2468): the zones travel in the file, the technical coupling does not."""

    def _zone_in_the_source(self, rig, keys) -> str:
        zones = ArangoIrrigationZoneRepository(rig.db)
        rig.db.collection(col.GARDEN_OBJECTS).insert(
            {
                "_key": "barrel",
                "site_key": "site_a",
                "object_type": "water_source",
                "label": "Tonne",
                "geometry": {"kind": "point", "origin": [18, 18]},
                "props": {"object_type": "water_source", "water_source_kind": "rain_barrel"},
                "off_site": False,
                "locked": False,
                "z_order": 0,
            }
        )
        created = zones.create_zone(
            IrrigationZone(
                tenant_key=A,
                site_key="site_a",
                name="Sued",
                irrigation_type="drip",
                water_source_key="barrel",
                application_efficiency=0.9,
                flow_rate_l_per_min=6.0,
                schedule_hint="morgens",
            ),
            tenant_key=A,
        )
        key = created.key or ""
        zones.replace_zone_locations(key, [keys["b1"], keys["b2"]], tenant_key=A)
        return key

    def test_the_export_carries_the_zone_and_a_replace_restores_it_under_a_new_key(self, rig) -> None:
        keys = build_source_plan(rig)
        source_zone = self._zone_in_the_source(rig, keys)
        document = rig.exported()
        assert [(z["key"], z["name"], z["water_source_key"]) for z in document["zones"]] == [
            (source_zone, "Sued", "barrel")
        ]
        assert "actuator_key" not in document["zones"][0] and "flow_rate_ha_entity_id" not in document["zones"][0]

        report = rig.run(document)

        assert report.applied and report.would_create.zones == 1 and report.errors == []
        (zone,) = list(rig.db.collection(col.IRRIGATION_ZONES).find({"site_key": "site_c"}))
        assert zone["_key"] != source_zone and zone["tenant_key"] == A and zone["name"] == "Sued"
        assert (zone["application_efficiency"], zone["flow_rate_l_per_min"], zone["flow_rate_source"]) == (
            0.9,
            6.0,
            "manual",
        )
        zone_id = f"irrigation_zones/{zone['_key']}"
        covered = {e["_to"].split("/")[1] for e in rig.db.collection(col.ZONE_COVERS).find({"_from": zone_id})}
        beds = list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"}))
        assert (
            covered == {b["_key"] for b in beds if b.get("irrigation_zone_key") == zone["_key"]} and len(covered) == 2
        )
        (supplied,) = list(rig.db.collection(col.ZONE_SUPPLIED_BY).find({"_from": zone_id}))
        new_source = supplied["_to"].split("/")[1]
        assert new_source != "barrel" and zone["water_source_key"] == new_source
        assert rig.db.collection(col.GARDEN_OBJECTS).get(new_source)["site_key"] == "site_c"
        assert rig.db.collection(col.HAS_IRRIGATION_ZONE).find({"_to": zone_id}).count() == 1

    def test_a_second_replace_leaves_one_zone_not_two(self, rig) -> None:
        keys = build_source_plan(rig)
        self._zone_in_the_source(rig, keys)
        document = rig.exported()
        rig.run(document)

        again = rig.run(rig.exported("site_c"), confirm_site_name="Leerer Garten")

        assert again.applied and again.would_delete.zones == 1 and again.would_create.zones == 1
        assert len(list(rig.db.collection(col.IRRIGATION_ZONES).find({"site_key": "site_c"}))) == 1
        assert len(list(rig.db.collection(col.ZONE_COVERS).all())) == 4  # 2 in the source, 2 in the one restored zone

    def test_the_technical_coupling_in_a_file_is_dropped_and_reported(self, rig) -> None:
        keys = build_source_plan(rig)
        self._zone_in_the_source(rig, keys)
        document = rig.exported()
        document["zones"][0].update(
            actuator_key="act_x", flow_rate_ha_entity_id="sensor.flow", flow_rate_source="ha_entity"
        )

        report = rig.run(document)

        assert {(d.entity, d.field, d.reason) for d in report.dropped_references} >= {
            ("irrigation_zone", "actuator_key", "always_dropped"),
            ("irrigation_zone", "flow_rate_ha_entity_id", "always_dropped"),
        }
        (zone,) = list(rig.db.collection(col.IRRIGATION_ZONES).find({"site_key": "site_c"}))
        assert not {"actuator_key", "flow_rate_ha_entity_id"} & set(zone) and zone["flow_rate_source"] == "manual"
        assert list(rig.db.collection(col.ZONE_ACTUATED_BY).all()) == []


class TestReplaceSnapshotSr011:
    def test_the_state_it_overwrites_is_in_the_change_log_with_the_deletes(self, rig) -> None:
        keys = build_source_plan(rig)
        source = rig.exported()

        report = rig.run(source, site="site_a", confirm_site_name="Garten A")

        assert report.applied and report.snapshot_written
        assert report.would_delete.locations == 6 and report.would_delete.garden_objects == 3
        assert report.would_delete.slots == 20
        rows = list(rig.db.collection(col.GARDEN_PLAN_AUDIT).find({"op": "import_snapshot"}))
        (snapshot,) = rows
        assert snapshot["tenant_key"] == A and snapshot["site_key"] == "site_a" and snapshot["user_key"] == USER
        assert snapshot["snapshot"]["schema_version"] == "1"
        assert {loc["key"] for loc in snapshot["snapshot"]["locations"]} == set(
            keys[k] for k in ("house", "b1", "b2", "b3", "b4", "b5")
        )
        assert len(snapshot["snapshot"]["slots"]) == 20
        deletes = list(rig.db.collection(col.GARDEN_PLAN_AUDIT).find({"op": "import_delete"}))
        assert len(deletes) == 9 and all(row["revision"] == snapshot["revision"] for row in deletes)
        # The old documents are gone and the new ones are not the old keys.
        assert rig.db.collection(col.LOCATIONS).get(keys["b1"]) is None
        assert len(list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_a"}))) == 6
        # The snapshot is not part of the listing route (names, no payload).
        listed = rig.plans.list_audit("site_a", tenant_key=A)
        assert listed and all(not hasattr(entry, "snapshot") for entry in listed)

    def test_a_merge_writes_no_snapshot_and_deletes_nothing(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        # Move the file's plan out of the way of the existing one so the merge is valid.
        for loc in source["locations"]:
            if (
                loc["geometry"]["origin"] is not None
                and loc["parent_location_key"] is None
                and loc["name"] != "Gewaechshaus"
            ):
                loc["geometry"]["origin"][1] += 12
        source["locations"] = [loc for loc in source["locations"] if loc["name"] in ("Beet b1", "Beet b2")]
        source["slots"] = [
            s for s in source["slots"] if s["location_key"] in {loc["key"] for loc in source["locations"]}
        ]
        source["garden_objects"] = []

        report = rig.run(source, site="site_a", mode="merge", confirm_site_name=None)

        assert report.errors == [], report.errors
        assert report.applied and not report.snapshot_written
        assert rig.db.collection(col.GARDEN_PLAN_AUDIT).count() > 0
        assert list(rig.db.collection(col.GARDEN_PLAN_AUDIT).find({"op": "import_snapshot"})) == []
        assert len(list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_a"}))) == 8  # 6 + 2
        assert len(list(rig.db.collection(col.GARDEN_OBJECTS).find({"site_key": "site_a"}))) == 3


class TestAnActiveBedV09:
    def _plant(self, rig, bed_key) -> None:
        rig.db.collection(col.PLANT_INSTANCES).insert({"location_key": bed_key, "removed_on": None, "tenant_key": A})

    def test_replace_is_refused_while_a_bed_holds_a_plant_and_force_keeps_that_bed(self, rig) -> None:
        keys = build_source_plan(rig)
        self._plant(rig, keys["b5"])  # the bed inside the greenhouse
        source = rig.exported()

        dry = rig.run(source, site="site_a", dry_run=True, confirm_site_name=None)
        assert [e.code for e in dry.errors] == ["import.not_empty"]
        with pytest.raises(PlanError) as refused:
            rig.run(source, site="site_a", confirm_site_name="Garten A")
        assert refused.value.status_code == 409 and refused.value.error_code == "import.not_empty"
        assert rig.db.collection(col.LOCATIONS).get(keys["b1"]) is not None  # nothing was written
        assert rig.db.collection(col.GARDEN_PLAN_AUDIT).count() == 1  # only the first set_boundary row

        # ``force`` lifts that condition and nothing else: the planted bed and the greenhouse above it stay.
        for loc in source["locations"]:  # the file now describes a plan that does not collide with the kept bed
            if loc["name"] in ("Gewaechshaus", "Beet b5"):
                loc["geometry"]["origin"] = [loc["geometry"]["origin"][0] - 9, loc["geometry"]["origin"][1] - 9]
        source["locations"] = [loc for loc in source["locations"] if loc["name"] not in ("Gewaechshaus", "Beet b5")]
        source["slots"] = []
        report = rig.run(source, site="site_a", force=True, confirm_site_name="Garten A")

        assert report.applied and report.kept_locations == 2
        assert rig.db.collection(col.LOCATIONS).get(keys["b5"]) is not None
        assert rig.db.collection(col.LOCATIONS).get(keys["house"]) is not None
        assert rig.db.collection(col.LOCATIONS).get(keys["b1"]) is None
        assert self._count_plants(rig) == 1

    @staticmethod
    def _count_plants(rig) -> int:
        return len(list(rig.db.collection(col.PLANT_INSTANCES).find({"removed_on": None})))

    def test_force_does_not_unlock_the_repositorys_own_recheck(self, rig) -> None:
        keys = build_source_plan(rig)
        rig.db.collection(col.PLANT_INSTANCES).insert(
            {"location_key": keys["b1"], "removed_on": None}
        )  # no tenant stamp
        report = rig.run(rig.exported(), site="site_a", dry_run=True)
        # An unstamped plant still counts: the planted-bed query does not trust the stamp (V-09).
        assert report.errors and report.errors[0].code == "import.not_empty"


class TestGatesAndTheFile:
    def test_a_foreign_site_is_a_404_before_the_file_is_read(self, rig) -> None:
        build_source_plan(rig)
        with pytest.raises(NotFoundError):
            rig.run({"not": "a plan"}, site="site_a", tenant=B)  # malformed AND foreign: the anchor answers first
        with pytest.raises(PlanError) as own:
            rig.run({"not": "a plan"}, site="site_a", tenant=A)
        assert (
            own.value.error_code == "import.schema_version_missing"
        )  # positive control: the file is read for the owner

    def test_only_a_lead_may_import(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        for role in (TenantRole.GROWER, TenantRole.VIEWER):
            with pytest.raises(PlanError) as refused:
                rig.run(source, role=role)
            assert refused.value.status_code == 403 and refused.value.error_code == "import.forbidden"
        assert list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})) == []
        assert rig.run(source, role=TenantRole.LEAD).applied

    def test_replace_needs_the_name_of_the_site(self, rig) -> None:
        build_source_plan(rig)
        for wrong in (None, "", "leerer garten", "Garten A"):
            with pytest.raises(PlanError) as refused:
                rig.run(rig.exported(), confirm_site_name=wrong)
            assert refused.value.error_code == "import.site_name_mismatch"
        assert list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})) == []
        assert rig.run(rig.exported(), confirm_site_name="Leerer Garten").applied

    def test_an_unknown_schema_version_or_top_level_key_is_refused_whole(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        with pytest.raises(PlanError) as newer:
            rig.run({**source, "schema_version": "2"})
        assert newer.value.error_code == "import.schema_version_unsupported"
        with pytest.raises(PlanError) as unknown:
            rig.run({**source, "templates": [], "surprises": []})
        assert unknown.value.error_code == "import.unknown_keys"
        assert unknown.value.details[0]["keys"] == ["surprises", "templates"]
        assert list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})) == []

    def test_a_malformed_entity_is_a_422_with_a_path_in_the_file(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        source["locations"][2]["geometry"] = {"kind": "rect", "origin": [0, 0], "width_m": -1, "length_m": 1}
        with pytest.raises(PlanValidationError) as refused:
            rig.run(source)
        assert refused.value.codes == ["geometry.invalid"]
        assert refused.value.details[0]["field"].startswith("locations[2].geometry")

    def test_the_geometry_rules_of_a_batch_hold_for_a_file(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        bed_one, bed_two = (loc for loc in source["locations"] if loc["name"] in ("Beet b1", "Beet b2"))
        bed_two["geometry"]["origin"] = list(bed_one["geometry"]["origin"])  # on top of each other (V-03)
        report = rig.run(source, dry_run=True)
        assert any(error.code == "bed.overlap" for error in report.errors)
        with pytest.raises(PlanValidationError):
            rig.run(source)
        assert list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})) == []

    def test_a_parent_cycle_and_duplicate_keys_are_findings_not_a_crash(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        first, second = source["locations"][0], source["locations"][1]
        first["parent_location_key"], second["parent_location_key"] = second["key"], first["key"]
        report = rig.run(source, dry_run=True)
        assert "import.parent_cycle" in {error.code for error in report.errors}
        dup = rig.exported()
        dup["locations"][1]["key"] = dup["locations"][0]["key"]
        assert "import.duplicate_key" in {e.code for e in rig.run(dup, dry_run=True).errors}

    def test_more_than_500_locations_and_objects_is_the_quota(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        template = source["garden_objects"][0]
        source["garden_objects"] = [{**template, "key": f"o{n}"} for n in range(500)]
        report = rig.run(source, dry_run=True)
        assert "plan.quota_exceeded" in {error.code for error in report.errors}

    def test_two_slots_with_one_id_in_a_bed_are_refused(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        source["slots"][1]["slot_id"] = source["slots"][0]["slot_id"]
        source["slots"][1]["location_key"] = source["slots"][0]["location_key"]
        report = rig.run(source, dry_run=True)
        assert "import.duplicate_slot_id" in {error.code for error in report.errors}


class TestReferencesGpFr141:
    def test_references_that_do_not_resolve_are_dropped_and_reported_never_kept(self, rig) -> None:
        build_source_plan(rig)
        db = rig.db
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "z_other_site", "tenant_key": A, "site_key": "site_a", "name": "Zone"}
        )
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "z_foreign", "tenant_key": B, "site_key": "site_b", "name": "Zone"}
        )
        db.collection(col.IRRIGATION_ZONES).insert(
            {"_key": "z_here", "tenant_key": A, "site_key": "site_c", "name": "Zone"}
        )
        db.collection(col.SUBSTRATES).insert({"_key": "sub_global"})
        db.collection(col.SUBSTRATES).insert({"_key": "sub_foreign", "tenant_key": B})
        source = rig.exported()
        # A file with zones brings its own (WP 7.2); these beds name zones of the *target* instead, the way an
        # older backup does, so the zones of the export are taken out to measure the references alone.
        source["zones"] = []
        beds = [loc for loc in source["locations"] if loc["name"].startswith("Beet b")]
        beds[0]["irrigation_zone_key"] = "z_other_site"
        beds[1]["irrigation_zone_key"] = "z_foreign"
        beds[2]["irrigation_zone_key"] = "z_here"
        beds[3]["irrigation_zone_key"] = "z_missing"
        beds[0]["soil_profile"] = {"substrate_key": "sub_foreign"}
        beds[1]["soil_profile"] = {"substrate_key": "sub_global"}
        beds[2]["location_type_key"] = "no_such_type"
        beds[3]["actuator_key"] = "act_1"  # not a field of the export: a hand-edited file
        beds[3]["flow_rate_ha_entity_id"] = "sensor.flow"
        beds[0]["parent_location_key"] = "loc_of_another_tenant"

        report = rig.run(source)

        dropped = {(d.key, d.field, d.reason) for d in report.dropped_references}
        assert dropped == {
            (beds[0]["key"], "irrigation_zone_key", "not_in_site"),
            (beds[1]["key"], "irrigation_zone_key", "not_found"),
            (beds[3]["key"], "irrigation_zone_key", "not_found"),
            (beds[0]["key"], "soil_profile.substrate_key", "not_found"),
            (beds[2]["key"], "location_type_key", "not_found"),
            (beds[3]["key"], "actuator_key", "always_dropped"),
            (beds[3]["key"], "flow_rate_ha_entity_id", "always_dropped"),
            (beds[0]["key"], "parent_location_key", "not_found"),
        }
        stored = {d["name"]: d for d in db.collection(col.LOCATIONS).find({"site_key": "site_c"})}
        assert stored[beds[2]["name"]]["irrigation_zone_key"] == "z_here"  # the positive control: a valid one is kept
        # WP 7.1: the kept zone covers the imported bed by edge as well, and only that one (field and edge in step).
        covers = [(e["_from"], e["_to"]) for e in db.collection(col.ZONE_COVERS).all()]
        assert covers == [("irrigation_zones/z_here", f"locations/{stored[beds[2]['name']]['_key']}")]
        assert stored[beds[1]["name"]]["soil_profile"]["substrate_key"] == "sub_global"
        for bed in (beds[0], beds[1], beds[3]):
            assert (
                "irrigation_zone_key" not in stored[bed["name"]] or stored[bed["name"]]["irrigation_zone_key"] is None
            )
        assert stored[beds[0]["name"]]["soil_profile"].get("substrate_key") is None
        assert stored[beds[2]["name"]]["location_type_key"] == ""
        assert stored[beds[0]["name"]].get("parent_location_key") is None
        assert "actuator_key" not in stored[beds[3]["name"]] and "flow_rate_ha_entity_id" not in stored[beds[3]["name"]]

    def test_a_slot_of_a_bed_outside_the_file_is_dropped_not_attached_to_a_foreign_bed(self, rig) -> None:
        keys = build_source_plan(rig)
        source = rig.exported()
        # A slot that names a bed of ANOTHER site by a real stored key: it must not be attached to it.
        source["slots"][0]["location_key"] = (
            keys["b1"] if source["slots"][0]["location_key"] != keys["b1"] else keys["b2"]
        )
        source["locations"] = [loc for loc in source["locations"] if loc["key"] not in (keys["b1"], keys["b2"])]
        report = rig.run(source)
        assert any(d.entity == "slot" and d.reason == "not_found" for d in report.dropped_references)
        site_c_beds = {d["_key"] for d in rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})}
        assert all(
            slot["location_key"] in site_c_beds
            for slot in rig.db.collection(col.SLOTS).all()
            if slot["_key"] not in {s["key"] for s in rig.exported("site_a")["slots"]}
        )


class TestAtomicity:
    def test_a_conflicting_revision_writes_nothing(self, rig) -> None:
        build_source_plan(rig)
        source = rig.exported()
        real = rig.importer._prepare

        def racing(*args, **kwargs):
            prepared = real(*args, **kwargs)
            rig.batch([], site="site_c", revision=0)  # somebody saves site_c between the check and the write
            return prepared

        site_a_beds = {d["_key"] for d in rig.db.collection(col.LOCATIONS).find({"site_key": "site_a"})}
        rig.importer._prepare = racing  # type: ignore[method-assign]
        from app.common.exceptions import PlanRevisionConflictError

        with pytest.raises(PlanRevisionConflictError):
            rig.run(source)
        assert list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})) == []
        assert [d for d in rig.db.collection(col.SLOTS).all() if d["location_key"] not in site_a_beds] == []
        assert rig.db.collection(col.GARDEN_PLAN_AUDIT).count() == 1  # only the source's set_boundary


def _origins(document: dict[str, Any], name: str) -> dict[str, list[float]]:
    return {item["name" if name == "locations" else "label"]: item["geometry"]["origin"] for item in document[name]}


class TestPartialExportWp718:
    """REQ-053 WP 7.18 (#2484, GP-FR-172): ``scope`` and ``keys`` of the JSON export."""

    def test_a_subtree_holds_the_bed_and_what_is_below_and_nothing_else(self, rig) -> None:
        keys = build_source_plan(rig)

        whole = rig.exported()
        subtree = rig.exported_partial("subtree", keys["house"])

        assert {loc["name"] for loc in subtree["locations"]} == {"Gewaechshaus", "Beet b5"}
        assert len(whole["locations"]) == 6  # positive control: the whole site is bigger
        assert subtree["plan"] is None and subtree["slots"] == [] and subtree["garden_objects"] == []
        (root,) = [loc for loc in subtree["locations"] if loc["name"] == "Gewaechshaus"]
        (child,) = [loc for loc in subtree["locations"] if loc["name"] == "Beet b5"]
        assert root["parent_location_key"] is None and child["parent_location_key"] == root["key"]

    def test_a_selection_is_exactly_the_named_entities_with_their_slots_and_no_dangling_parent(self, rig) -> None:
        keys = build_source_plan(rig)

        chosen = rig.exported_partial("selection", keys["b5"], keys["b1"], f"object:{rig.object_key('Baum 0')}")

        assert {loc["name"] for loc in chosen["locations"]} == {"Beet b5", "Beet b1"}
        (inner,) = [loc for loc in chosen["locations"] if loc["name"] == "Beet b5"]
        assert inner["parent_location_key"] is None  # its parent is not in the file: the reference left it
        assert len(chosen["slots"]) == 5 and {slot["location_key"] for slot in chosen["slots"]} == {keys["b1"]}
        assert [obj["label"] for obj in chosen["garden_objects"]] == ["Baum 0"]

    def test_a_key_the_site_does_not_hold_is_a_404_and_so_is_one_of_another_tenant(self, rig) -> None:
        keys = build_source_plan(rig)
        with pytest.raises(NotFoundError):
            rig.exported_partial("selection", "nope")
        with pytest.raises(NotFoundError):
            rig.exported_partial("subtree", keys["b1"], tenant=B, site="site_b")
        with pytest.raises(NotFoundError):  # the site itself is another tenant's
            rig.exported_partial("selection", keys["b1"], tenant=B)
        assert rig.exported_partial("selection", keys["b1"])["locations"]  # positive control

    def test_the_selection_rules_are_422s(self, rig) -> None:
        keys = build_source_plan(rig)
        for scope, names, code in (
            ("site", [keys["b1"]], "export.keys_not_allowed"),
            ("selection", [], "export.keys_required"),
            ("subtree", ["object:1"], "export.object_key_in_subtree"),
            ("selection", [str(n) for n in range(101)], "export.too_many_keys"),
        ):
            with pytest.raises(PlanError) as refused:
                rig.exported_partial(scope, *names)
            assert refused.value.status_code == 422 and refused.value.error_code == code

    def test_a_zone_travels_with_its_beds_and_loses_a_water_source_that_stays_behind(self, rig) -> None:
        keys = build_source_plan(rig)
        TestZonesWp72()._zone_in_the_source(rig, keys)  # covers b1 and b2

        with_zone = rig.exported_partial("selection", keys["b1"])
        without = rig.exported_partial("selection", keys["b3"])

        assert [zone["name"] for zone in with_zone["zones"]] == ["Sued"]
        assert with_zone["zones"][0]["water_source_key"] is None  # the barrel is not in the file
        assert without["zones"] == []

    def test_a_partial_file_imports_into_another_site_as_new_entities(self, rig) -> None:
        keys = build_source_plan(rig)
        source = rig.exported_partial("subtree", keys["house"])

        report = rig.run(source, mode="merge", confirm_site_name=None, target="other_site")

        assert report.applied and report.errors == [] and report.target == "other_site"
        assert {d["name"] for d in rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})} == {
            "Gewaechshaus",
            "Beet b5",
        }
        assert rig.db.collection(col.SITES).get("site_c").get("plan", {}).get("boundary") is None  # no plan settings


class TestImportTargetAndOffsetWp718:
    def test_an_offset_shifts_every_geometry_of_a_merge(self, rig) -> None:
        keys = build_source_plan(rig)
        source = rig.exported_partial("selection", keys["b1"], keys["b2"], f"object:{rig.object_key('Baum 1')}")
        before_locations, before_objects = _origins(source, "locations"), _origins(source, "garden_objects")

        report = rig.run(source, mode="merge", confirm_site_name=None, offset_m=(3.0, 2.5))

        assert report.applied and report.offset_m == (3.0, 2.5)
        placed = {
            d["name"]: d["geometry"]["origin"] for d in rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})
        }
        assert placed == {name: [x + 3.0, y + 2.5] for name, (x, y) in before_locations.items()}
        (tree,) = [d for d in rig.db.collection(col.GARDEN_OBJECTS).find({"site_key": "site_c"})]
        (x, y) = before_objects["Baum 1"]
        assert tree["geometry"]["origin"] == [x + 3.0, y + 2.5]
        # The slots sit in the bed frame and did not move.
        original = {slot["slot_id"]: slot["geometry"] for slot in source["slots"]}
        copied = {
            slot["slot_id"]: slot["geometry"]
            for slot in rig.db.collection(col.SLOTS).all()
            if slot["slot_id"] in original
        }
        assert copied and all(geometry in original.values() for geometry in copied.values())

    def test_a_shift_out_of_the_plan_frame_is_reported_per_entity_and_writes_nothing(self, rig) -> None:
        keys = build_source_plan(rig)
        source = rig.exported_partial("selection", keys["b1"])

        report = rig.run(source, mode="merge", confirm_site_name=None, dry_run=True, offset_m=(1000.0, 0.0))

        assert report.errors_total == 1 and report.errors[0].code == "geometry.invalid"
        assert report.errors[0].field == "locations[0].geometry"
        assert list(rig.db.collection(col.LOCATIONS).find({"site_key": "site_c"})) == []

    def test_an_offset_belongs_to_a_merge_and_must_be_finite(self, rig) -> None:
        keys = build_source_plan(rig)
        source = rig.exported_partial("selection", keys["b1"])
        with pytest.raises(PlanError) as replace:
            rig.run(source, mode="replace", confirm_site_name="Leerer Garten", offset_m=(1.0, 1.0))
        assert replace.value.status_code == 422 and replace.value.error_code == "import.offset_requires_merge"
        for bad in ((float("inf"), 0.0), (float("nan"), 0.0), (2000.0, 0.0)):
            with pytest.raises(PlanError) as refused:
                rig.run(source, mode="merge", confirm_site_name=None, offset_m=bad)
            assert refused.value.status_code == 422 and refused.value.error_code == "import.offset_invalid"
        assert rig.run(source, mode="merge", confirm_site_name=None, offset_m=(0.0, 0.0)).applied  # control

    def test_a_reference_that_is_not_in_the_file_resolves_only_for_the_same_site(self, rig) -> None:
        keys = build_source_plan(rig)
        # A bed whose parent (the greenhouse) is not in the file, and whose key does exist in site_a.
        source = rig.exported_partial("selection", keys["b5"])
        source["locations"][0]["parent_location_key"] = keys["house"]

        same = rig.run(source, site="site_a", mode="merge", confirm_site_name=None, dry_run=True, target="same_site")
        other = rig.run(source, site="site_c", mode="merge", confirm_site_name=None, dry_run=True, target="other_site")
        tenant = rig.run(
            source, site="site_c", mode="merge", confirm_site_name=None, dry_run=True, target="other_tenant"
        )

        assert [d.field for d in same.dropped_references if d.entity == "location"] == []
        for report in (other, tenant):
            assert [(d.field, d.reason) for d in report.dropped_references] == [("parent_location_key", "outside_file")]

    def test_a_zone_of_the_target_site_is_not_claimed_by_a_file_for_another_site(self, rig) -> None:
        keys = build_source_plan(rig)
        TestZonesWp72()._zone_in_the_source(rig, keys)
        zone_key = next(iter(rig.db.collection(col.IRRIGATION_ZONES).all()))["_key"]
        source = rig.exported_partial("selection", keys["b3"])
        source["locations"][0]["irrigation_zone_key"] = zone_key  # a zone that is not in the file, but is in site_a

        same = rig.run(source, site="site_a", mode="merge", confirm_site_name=None, dry_run=True)
        other = rig.run(
            source, site="site_a", mode="merge", confirm_site_name=None, dry_run=True, target="other_tenant"
        )

        assert [d for d in same.dropped_references if d.field == "irrigation_zone_key"] == []
        assert [(d.field, d.reason) for d in other.dropped_references] == [("irrigation_zone_key", "outside_file")]


class TestSnapshotsWp719:
    """REQ-053 WP 7.19 (#2485, GP-FR-148/170): list and restore the plans a ``replace`` overwrote."""

    def _replace_site_a_with_a_part(self, rig) -> tuple[dict[str, Any], dict[str, str]]:
        keys = build_source_plan(rig)
        before = rig.exported()
        part = rig.exported_partial("selection", keys["b1"])
        report = rig.run(part, site="site_a", confirm_site_name="Garten A")
        assert report.applied and report.snapshot_written
        return before, keys

    def test_restore_gives_back_the_state_before_the_import_and_writes_its_own_snapshot_first(self, rig) -> None:
        before, _ = self._replace_site_a_with_a_part(rig)
        (entry,) = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)
        assert (entry.locations, entry.garden_objects, entry.slots) == (6, 3, 20)
        assert len(rig.exported()["locations"]) == 1  # positive control: the import did replace the plan

        report = rig.importer.restore_snapshot(
            "site_a",
            entry.audit_key,
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            dry_run=False,
            force=False,
            confirm_site_name="Garten A",
        )

        assert report.applied and report.errors == [] and report.snapshot_written
        assert normalised(rig.exported()) == normalised(before)
        # The restore wrote the one-bed plan down before it replaced it: two snapshots now, newest first.
        snapshots = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)
        assert [s.locations for s in snapshots] == [1, 6]

    def test_a_dry_run_restore_writes_nothing(self, rig) -> None:
        self._replace_site_a_with_a_part(rig)
        (entry,) = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)
        audit_before = rig.db.collection(col.GARDEN_PLAN_AUDIT).count()

        report = rig.importer.restore_snapshot(
            "site_a",
            entry.audit_key,
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            dry_run=True,
            force=False,
            confirm_site_name=None,
        )

        assert report.dry_run and not report.applied and report.would_create.locations == 6
        assert rig.db.collection(col.GARDEN_PLAN_AUDIT).count() == audit_before
        assert len(rig.exported()["locations"]) == 1

    def test_a_restore_retires_the_zones_the_import_brought(self, rig) -> None:
        keys = build_source_plan(rig)
        part = rig.exported_partial("selection", keys["b1"])
        part["zones"] = [{"key": "z1", "name": "Neu", "irrigation_type": "manual"}]
        part["locations"][0]["irrigation_zone_key"] = "z1"
        rig.run(part, site="site_a", confirm_site_name="Garten A")
        assert [z["name"] for z in rig.exported()["zones"]] == ["Neu"]
        (entry,) = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)

        rig.importer.restore_snapshot(
            "site_a",
            entry.audit_key,
            tenant_key=A,
            user_key=USER,
            role=TenantRole.LEAD,
            dry_run=False,
            force=False,
            confirm_site_name="Garten A",
        )

        assert rig.exported()["zones"] == []

    def test_the_list_is_bounded_lead_only_and_tenant_scoped(self, rig) -> None:
        self._replace_site_a_with_a_part(rig)
        rig.run(
            rig.exported_partial("selection", rig.location_key("Beet b1")), site="site_a", confirm_site_name="Garten A"
        )
        assert len(rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)) == 2
        assert len(rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=1)) == 1
        with pytest.raises(PlanError) as grower:
            rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.GROWER, offset=0, limit=50)
        assert grower.value.status_code == 403 and grower.value.error_code == "import.forbidden"
        with pytest.raises(NotFoundError):  # another tenant's lead: the site answers 404 before the role is read
            rig.importer.list_snapshots("site_a", tenant_key=B, role=TenantRole.LEAD, offset=0, limit=50)

    def test_a_site_keeps_its_newest_twenty_snapshots_and_every_other_row(self, rig) -> None:
        """#2542 W-2 (GP-NFR-055): the 21st snapshot removes the oldest, in the import's own transaction."""
        audit = rig.db.collection(col.GARDEN_PLAN_AUDIT)
        foreign = [
            {"tenant_key": A, "site_key": "site_c", "revision": 1, "op": "import_snapshot", "snapshot": {}},
            {"tenant_key": B, "site_key": "site_a", "revision": 1, "op": "import_snapshot", "snapshot": {}},
            # #2542: a row the listing hides (``snapshot == null``) is neither counted nor removed by the prune.
            {"tenant_key": A, "site_key": "site_a", "revision": 999, "op": "import_snapshot", "snapshot": None},
        ]
        foreign_keys = {audit.insert({**row, "at": "2026-01-01T00:00:00+00:00"})["_key"] for row in foreign}
        keys = build_source_plan(rig)
        part = rig.exported_partial("selection", keys["b1"])

        def rows(*, snapshots: bool) -> set[str]:
            return {
                row["_key"]
                for row in audit.find({"tenant_key": A, "site_key": "site_a"})
                if (row["op"] == "import_snapshot") is snapshots and row["_key"] not in foreign_keys
            }

        first: list[str] = []
        for _ in range(MAX_SNAPSHOTS_PER_SITE + 1):
            assert rig.run(part, site="site_a", confirm_site_name="Garten A").snapshot_written
            newest, *_ = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)
            first.append(newest.audit_key)
            if len(first) == 1:
                change_log = rows(snapshots=False)

        kept = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)

        assert len(kept) == MAX_SNAPSHOTS_PER_SITE == 20
        assert [entry.audit_key for entry in kept] == first[:0:-1]  # newest first; the oldest one is gone
        assert rows(snapshots=True) == set(first[1:])
        assert change_log and change_log <= rows(snapshots=False)  # the change log rows of the imports all stay
        assert all(audit.has(key) for key in foreign_keys)  # another site, another tenant: untouched

    def test_a_snapshot_of_another_tenant_or_site_is_a_404_and_a_grower_gets_a_403(self, rig) -> None:
        self._replace_site_a_with_a_part(rig)
        (entry,) = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)
        options: dict[str, Any] = {"user_key": USER, "dry_run": True, "force": False, "confirm_site_name": None}

        with pytest.raises(NotFoundError):  # tenant B asks for tenant A's row through its own site
            rig.importer.restore_snapshot("site_b", entry.audit_key, tenant_key=B, role=TenantRole.LEAD, **options)
        with pytest.raises(NotFoundError):  # the right tenant, another site
            rig.importer.restore_snapshot("site_c", entry.audit_key, tenant_key=A, role=TenantRole.LEAD, **options)
        with pytest.raises(NotFoundError):  # the right site of the wrong tenant
            rig.importer.restore_snapshot("site_a", entry.audit_key, tenant_key=B, role=TenantRole.LEAD, **options)
        with pytest.raises(NotFoundError):  # a key that is no snapshot at all
            rig.importer.restore_snapshot("site_a", "nope", tenant_key=A, role=TenantRole.LEAD, **options)
        with pytest.raises(PlanError) as grower:
            rig.importer.restore_snapshot("site_a", entry.audit_key, tenant_key=A, role=TenantRole.GROWER, **options)
        assert grower.value.status_code == 403
        assert rig.importer.restore_snapshot(  # positive control
            "site_a", entry.audit_key, tenant_key=A, role=TenantRole.LEAD, **options
        ).dry_run

    def test_a_restore_still_asks_for_the_site_name_and_refuses_over_planted_beds(self, rig) -> None:
        self._replace_site_a_with_a_part(rig)
        (entry,) = rig.importer.list_snapshots("site_a", tenant_key=A, role=TenantRole.LEAD, offset=0, limit=50)
        options: dict[str, Any] = {"user_key": USER, "role": TenantRole.LEAD, "dry_run": False, "force": False}

        with pytest.raises(PlanError) as unnamed:
            rig.importer.restore_snapshot("site_a", entry.audit_key, tenant_key=A, confirm_site_name="x", **options)
        assert unnamed.value.error_code == "import.site_name_mismatch"

        bed = rig.location_key("Beet b1")
        rig.db.collection(col.PLANT_INSTANCES).insert({"tenant_key": A, "location_key": bed, "removed_on": None})
        with pytest.raises(PlanError) as planted:
            rig.importer.restore_snapshot(
                "site_a", entry.audit_key, tenant_key=A, confirm_site_name="Garten A", **options
            )
        assert planted.value.status_code == 409 and planted.value.error_code == "import.not_empty"
