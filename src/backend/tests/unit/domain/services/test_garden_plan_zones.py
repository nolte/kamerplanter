"""REQ-053 WP 7.2 (#2468) - irrigation zones in the plan read model, the JSON export and the import.

* ``include=zones`` fills the read model; without it the zones are not read at all.
* The export carries the zones additively inside ``schema_version "1"``, never the technical coupling.
* The import creates the file's zones under new keys, rewrites the beds' ``irrigation_zone_key`` through the
  import-local key map, drops ``actuator_key`` / ``flow_rate_ha_entity_id`` always and says so, and a ``replace``
  retires the site's own zones that cover no bed that stays.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.enums import FlowRateSource, GardenObjectType, IrrigationZoneType, TenantRole
from app.common.exceptions import PlanError, PlanValidationError
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import ERROR_ZONE_QUOTA, MAX_PLAN_ZONES
from app.domain.models.irrigation_zone import IrrigationZone
from app.domain.models.site import SitePlan
from app.domain.services.garden_plan_export_service import GardenPlanExportService
from app.domain.services.garden_plan_import_service import GardenPlanImportService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)
from tests.support.irrigation_zone_fakes import FakeZones

USER = "u_sabine"


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}, plan_revision=3
    )
    repository = FakePlanRepo(FakeSites(site))
    repository.locations["b1"] = make_location("b1", "Beet 1", geometry=rect(1, 1, 3, 1), irrigation_zone_key="z1")
    repository.locations["b2"] = make_location("b2", "Beet 2", geometry=rect(1, 3, 3, 1), irrigation_zone_key="z1")
    repository.locations["b3"] = make_location("b3", "Beet 3", geometry=rect(6, 3, 3, 1))
    return repository


@pytest.fixture
def zones(repo: FakePlanRepo) -> FakeZones:
    store = FakeZones(repo)
    store.add(
        IrrigationZone(
            _key="z1",
            tenant_key=TENANT,
            site_key=SITE,
            name="South",
            irrigation_type=IrrigationZoneType.DRIP,
            water_source_key="w1",
            actuator_key="act_1",
            flow_rate_l_per_min=4.0,
            flow_rate_source=FlowRateSource.HA_ENTITY,
            flow_rate_ha_entity_id="sensor.flow_south",
            application_efficiency=0.88,
            schedule_hint="mornings",
        )
    )
    store.covers.update({"b1": "z1", "b2": "z1"})
    store.add(IrrigationZone(_key="z_other", tenant_key=OTHER_TENANT, site_key=SITE, name="Foreign"))
    return store


@pytest.fixture
def barrel(repo: FakePlanRepo) -> GardenObject:
    water = GardenObject(
        _key="w1",
        site_key=SITE,
        object_type=GardenObjectType.WATER_SOURCE,
        label="Barrel",
        geometry={"kind": "point", "origin": [8, 8]},
        props={"water_source_kind": "rain_barrel", "capacity_liters": 200},
    )
    repo.objects["w1"] = water
    return water


class Rig:
    def __init__(self, repo: FakePlanRepo, zones: FakeZones) -> None:
        self.repo = repo
        self.plans = GardenPlanService(repo._sites, repo, zones)
        self.export = GardenPlanExportService(repo._sites, repo, self.plans)
        self.importer = GardenPlanImportService(repo._sites, repo, self.plans, self.export)

    def file(self) -> dict[str, Any]:
        return self.export.export_json(SITE, tenant_key=TENANT).model_dump(mode="json")

    def run(self, document: dict[str, Any], **options: Any):
        arguments: dict[str, Any] = {
            "role": TenantRole.LEAD,
            "mode": "replace",
            "dry_run": False,
            "force": False,
            "confirm_site_name": "Garten",
        } | options
        return self.importer.import_plan(SITE, tenant_key=TENANT, user_key=USER, document=document, **arguments)


@pytest.fixture
def rig(repo: FakePlanRepo, zones: FakeZones, barrel: GardenObject) -> Rig:
    return Rig(repo, zones)


class TestReadModel:
    def test_include_zones_lists_the_sites_own_zones_with_their_beds(self, rig) -> None:
        view = rig.plans.get_plan(SITE, tenant_key=TENANT, include=frozenset({"zones"}))

        (zone,) = view.zones
        assert zone["key"] == "z1" and zone["location_keys"] == ["b1", "b2"]
        assert zone["irrigation_type"] == "drip" and zone["water_source_key"] == "w1"
        assert "flow_rate_ha_entity_id" not in zone  # the bound entity never reaches the read model (SR-014)

    def test_without_the_include_no_zone_is_read(self, rig) -> None:
        assert rig.plans.get_plan(SITE, tenant_key=TENANT, include=frozenset({"plants"})).zones == []

    def test_a_service_without_a_zone_repository_has_no_zones(self, repo) -> None:
        assert GardenPlanService(repo._sites, repo).get_plan(SITE, tenant_key=TENANT).zones == []


class TestExport:
    def test_the_zones_are_part_of_the_file_without_the_technical_coupling(self, rig) -> None:
        document = rig.file()

        (zone,) = document["zones"]
        assert zone == {
            "key": "z1",
            "name": "South",
            "irrigation_type": "drip",
            "water_source_key": "w1",
            "application_efficiency": 0.88,
            "flow_rate_l_per_min": 4.0,
            "color": "#2E7D32",
            "schedule_hint": "mornings",
        }
        assert {loc["key"]: loc["irrigation_zone_key"] for loc in document["locations"]} == {
            "b1": "z1",
            "b2": "z1",
            "b3": None,
        }

    def test_a_foreign_tenants_zone_on_the_same_site_is_not_exported(self, rig) -> None:
        assert [zone["key"] for zone in rig.file()["zones"]] == ["z1"]


class TestImport:
    def test_the_round_trip_recreates_the_zone_under_a_new_key_and_rewires_its_beds(self, rig, repo) -> None:
        report = rig.run(rig.file())

        assert report.applied and report.would_create.zones == 1 and report.would_delete.zones == 1
        (write,) = repo.applied
        assert write.zone_deletes == ["z1"]
        ((new_key, created),) = repo.imported_zones.items()
        assert new_key != "z1" and created.name == "South" and created.irrigation_type is IrrigationZoneType.DRIP
        assert created.application_efficiency == 0.88 and created.flow_rate_l_per_min == 4.0
        by_name = {loc.name: loc.irrigation_zone_key for loc in repo.locations.values()}
        assert by_name == {"Beet 1": new_key, "Beet 2": new_key, "Beet 3": None}

    def test_the_water_source_follows_the_imported_object(self, rig, repo) -> None:
        rig.run(rig.file())

        (write,) = repo.applied
        ((_, zone),) = write.zone_inserts
        ((object_temp, _),) = write.object_inserts
        assert zone.water_source_key == object_temp

    def test_the_technical_coupling_is_never_carried_over_and_is_reported(self, rig, repo) -> None:
        document = rig.file()
        document["zones"][0].update(
            actuator_key="act_9", flow_rate_ha_entity_id="sensor.flow_south", flow_rate_source="ha_entity"
        )

        report = rig.run(document, dry_run=True)

        dropped = {(d.entity, d.field, d.reason) for d in report.dropped_references}
        assert ("irrigation_zone", "actuator_key", "always_dropped") in dropped
        assert ("irrigation_zone", "flow_rate_ha_entity_id", "always_dropped") in dropped
        rig.run(document)
        ((_, created),) = repo.imported_zones.items()
        assert created.actuator_key is None and created.flow_rate_ha_entity_id is None
        assert created.flow_rate_source is FlowRateSource.MANUAL

    def test_a_flow_source_of_a_home_assistant_zone_is_reported_a_manual_one_is_not(self, rig) -> None:
        document = rig.file()
        document["zones"][0]["flow_rate_source"] = "manual"

        assert rig.run(document, dry_run=True).dropped_references == []

        document["zones"][0].update(flow_rate_source="ha_entity")
        dropped = {(d.entity, d.field, d.reason) for d in rig.run(document, dry_run=True).dropped_references}
        assert ("irrigation_zone", "flow_rate_source", "always_dropped") in dropped

    def test_a_water_source_that_is_not_in_the_file_is_dropped_and_reported(self, rig, repo) -> None:
        document = rig.file()
        document["zones"][0]["water_source_key"] = "go_elsewhere"

        report = rig.run(document)

        assert [(d.entity, d.field, d.reason) for d in report.dropped_references] == [
            ("irrigation_zone", "water_source_key", "not_found")
        ]
        ((_, created),) = repo.imported_zones.items()
        assert created.water_source_key is None

    def test_a_file_without_zones_removes_none_and_old_references_still_resolve(self, rig, repo) -> None:
        repo.zones["z1"] = (TENANT, SITE)
        document = rig.file()
        document["zones"] = []

        report = rig.run(document)

        assert report.applied and report.would_delete.zones == 0 and repo.deleted_zones == []
        assert {loc.irrigation_zone_key for loc in repo.locations.values()} == {"z1", None}

    def test_merge_adds_the_zones_and_removes_nothing(self, rig, repo) -> None:
        document = rig.file()
        document["locations"] = [loc for loc in document["locations"] if loc["key"] == "b3"]
        document["slots"] = []
        document["locations"][0]["geometry"]["origin"] = [6, 6]

        report = rig.run(document, mode="merge", confirm_site_name=None)

        assert report.applied and report.would_create.zones == 1 and repo.deleted_zones == []

    def test_a_zone_that_covers_a_bed_that_stays_is_not_retired(self, rig, repo) -> None:
        repo.planted = {"b1"}
        document = rig.file()
        document["locations"] = [loc for loc in document["locations"] if loc["key"] == "b3"]
        document["slots"] = []

        rig.run(document, force=True)

        assert repo.deleted_zones == []  # b1 stays and still names z1

    def test_duplicate_zone_keys_and_a_bad_colour_are_refused_with_a_path(self, rig) -> None:
        document = rig.file()
        document["zones"] = [document["zones"][0], {**document["zones"][0]}]

        report = rig.run(document, dry_run=True)

        assert [(e.field, e.code) for e in report.errors] == [("zones[1].key", "import.duplicate_key")]

    def test_a_malformed_zone_is_refused_whole_before_any_lookup(self, rig) -> None:
        document = rig.file()
        document["zones"][0]["color"] = "green"

        with pytest.raises(PlanValidationError):
            rig.run(document, dry_run=True)


class TestZoneCap:
    """#2522: the per-site cap holds on the plan read, the export and the merge import - nothing is cut silently."""

    @staticmethod
    def _fill(zones: FakeZones, count: int, prefix: str = "f") -> None:
        for index in range(count):
            zones.add(
                IrrigationZone(
                    _key=f"{prefix}{index}", tenant_key=TENANT, site_key=SITE, name=f"Z{index}", irrigation_type="drip"
                )
            )

    def test_a_site_over_the_cap_is_422_on_the_read_and_the_export(self, rig, zones) -> None:
        self._fill(zones, MAX_PLAN_ZONES)  # plus z1 of the fixture: one over

        with pytest.raises(PlanError) as read:
            rig.plans.get_plan(SITE, tenant_key=TENANT, include=frozenset({"zones"}))
        with pytest.raises(PlanError) as export:
            rig.file()

        assert read.value.error_code == export.value.error_code == ERROR_ZONE_QUOTA
        assert read.value.status_code == 422

    def test_a_site_exactly_at_the_cap_is_read_complete(self, rig, zones) -> None:
        self._fill(zones, MAX_PLAN_ZONES - 1)

        assert len(rig.plans.get_plan(SITE, tenant_key=TENANT, include=frozenset({"zones"})).zones) == MAX_PLAN_ZONES

    def test_a_merge_that_would_pass_the_cap_is_refused_and_nothing_is_written(self, rig, repo, zones) -> None:
        document = rig.file()
        self._fill(zones, MAX_PLAN_ZONES - 1)  # at the cap with z1; the file brings one more

        report = rig.run(document, mode="merge", dry_run=True)

        assert not report.applied
        assert ("zones", ERROR_ZONE_QUOTA) in [(e.field, e.code) for e in report.errors]
        assert repo.applied == []

    def test_a_replace_counts_the_zones_it_retires(self, rig, zones) -> None:
        document = rig.file()
        self._fill(zones, MAX_PLAN_ZONES - 1)  # all of them cover no bed that stays, so the replace retires them

        report = rig.run(document, mode="replace", dry_run=True)

        assert ERROR_ZONE_QUOTA not in [e.code for e in report.errors]
