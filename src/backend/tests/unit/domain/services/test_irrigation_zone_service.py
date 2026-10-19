"""REQ-053 WP 7.1 (#2467) — irrigation zones: CRUD, bed assignment, references and roles.

The repository is the in-memory double of ``tests/support/irrigation_zone_fakes.py`` over the beds of
``FakePlanRepo``. Every refusal asserts that **nothing reached the repository**.

What this file pins:

* the tenant anchor of every method: a foreign and an absent zone or site answer the same 404 (T-01);
* GP-NFR-058 / GP-ACC-041 (zone part): ``location_keys`` ⊆ the zone's site, ``water_source_key`` a
  ``water_source`` of that site — anything else is 422 ``reference.not_found`` without telling foreign from
  absent;
* §21.8 "Bewässerungszone" in the service (a second caller cannot skip the gate): viewer reads, grower creates,
  changes and assigns, only the lead deletes (SR-010);
* the coupling fields are refused until WP 7.4; a bed is in at most one zone.
"""

from __future__ import annotations

import pytest

from app.common.enums import IrrigationZoneType, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.models.garden_object import GardenObject
from app.domain.models.irrigation_zone import (
    DEFAULT_ZONE_COLOR,
    IrrigationZone,
    IrrigationZoneInput,
    IrrigationZonePatch,
)
from app.domain.models.site import Site
from app.domain.services.irrigation_zone_service import ERROR_COUPLING_NOT_AVAILABLE, IrrigationZoneService
from tests.support.care_event_fakes import FakeCareEventRepo
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    USER,
    FakeObjects,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.irrigation_zone_fakes import FakeZones

OTHER_SITE = "site_2"
FOREIGN_SITE = "site_x"


def _water_source(key: str, site: str) -> GardenObject:
    return GardenObject.model_validate(
        {
            "_key": key,
            "site_key": site,
            "object_type": "water_source",
            "geometry": {"kind": "point", "origin": [1.0, 1.0]},
            "props": {"object_type": "water_source", "water_source_kind": "rain_barrel"},
        }
    )


@pytest.fixture
def world() -> tuple[IrrigationZoneService, FakeZones, FakePlanRepo]:
    sites = FakeSites(
        make_site(),
        Site(_key=OTHER_SITE, tenant_key=TENANT, name="Allotment", type="outdoor"),
        Site(_key=FOREIGN_SITE, tenant_key=OTHER_TENANT, name="Foreign", type="outdoor"),
    )
    repo = FakePlanRepo(sites)
    for key in ("bed_1", "bed_2", "bed_3"):
        repo.locations[key] = make_location(key, name=key)
    repo.locations["bed_other_site"] = make_location("bed_other_site").model_copy(update={"site_key": OTHER_SITE})
    repo.locations["bed_foreign"] = make_location("bed_foreign").model_copy(update={"site_key": FOREIGN_SITE})
    repo.objects["barrel"] = _water_source("barrel", SITE)
    repo.objects["barrel_other_site"] = _water_source("barrel_other_site", OTHER_SITE)
    repo.objects["barrel_foreign"] = _water_source("barrel_foreign", FOREIGN_SITE)
    repo.objects["tree"] = GardenObject.model_validate(
        {
            "_key": "tree",
            "site_key": SITE,
            "object_type": "tree",
            "geometry": {"kind": "circle", "origin": [5.0, 5.0], "radius_m": 1.0},
            "props": {"object_type": "tree", "crown_radius_m": 1.0},
        }
    )
    zones = FakeZones(repo)
    zones.add(
        IrrigationZone(_key="zone_a", tenant_key=TENANT, site_key=SITE, name="Drip south", irrigation_type="drip")
    )
    zones.add(IrrigationZone(_key="zone_b", tenant_key=TENANT, site_key=SITE, name="Hand round"))
    zones.add(IrrigationZone(_key="zone_foreign", tenant_key=OTHER_TENANT, site_key=FOREIGN_SITE, name="Theirs"))
    care = FakeCareEventRepo()
    service = IrrigationZoneService(zones, sites, FakeObjects(repo), care)
    return service, zones, repo


def _codes(exc: PlanValidationError) -> list[tuple[str, str]]:
    return [(str(d["field"]), str(d["code"])) for d in exc.details or []]


class TestCreate:
    def test_a_grower_creates_a_zone_on_the_path_site(self, world) -> None:
        service, zones, _ = world

        view = service.create_zone(
            SITE,
            tenant_key=TENANT,
            role=TenantRole.GROWER,
            data=IrrigationZoneInput(name="  Beds north  ", irrigation_type="sprinkler", water_source_key="barrel"),
        )

        stored = zones.zones[view.zone.key or ""]
        assert (stored.tenant_key, stored.site_key, stored.name) == (TENANT, SITE, "Beds north")
        assert (stored.irrigation_type, stored.water_source_key, stored.color) == (
            IrrigationZoneType.SPRINKLER,
            "barrel",
            DEFAULT_ZONE_COLOR,
        )
        # E-10: no efficiency without a source; the coupling is untouched.
        assert (stored.application_efficiency, stored.actuator_key, stored.flow_rate_l_per_min) == (None, None, None)
        assert view.location_keys == ()

    def test_a_viewer_is_refused_and_nothing_is_written(self, world) -> None:
        service, zones, _ = world
        before = dict(zones.zones)

        with pytest.raises(ForbiddenError):
            service.create_zone(SITE, tenant_key=TENANT, role=TenantRole.VIEWER, data=IrrigationZoneInput(name="Z"))

        assert zones.zones == before

    @pytest.mark.parametrize("site", [FOREIGN_SITE, "site_gone"])
    def test_a_foreign_and_an_absent_site_are_the_same_404(self, world, site: str) -> None:
        service, zones, _ = world
        before = dict(zones.zones)

        with pytest.raises(NotFoundError) as caught:
            service.create_zone(site, tenant_key=TENANT, role=TenantRole.LEAD, data=IrrigationZoneInput(name="Z"))

        # The message names the key the caller sent and nothing of the owner.
        assert OTHER_TENANT not in str(caught.value.details) + caught.value.message
        assert zones.zones == before

    @pytest.mark.parametrize(
        "source",
        ["barrel_foreign", "barrel_gone", "barrel_other_site", "tree"],
        ids=["another tenant's", "absent", "another site's", "not a water source"],
    )
    def test_a_water_source_outside_the_site_is_reference_not_found(self, world, source: str) -> None:
        service, zones, _ = world
        before = dict(zones.zones)

        with pytest.raises(PlanValidationError) as caught:
            service.create_zone(
                SITE,
                tenant_key=TENANT,
                role=TenantRole.GROWER,
                data=IrrigationZoneInput(name="Z", water_source_key=source),
            )

        assert _codes(caught.value) == [("water_source_key", "reference.not_found")]
        assert zones.zones == before

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("actuator_key", "act_1"),
            ("flow_rate_l_per_min", 12.0),
            ("flow_rate_source", "ha_entity"),
            ("flow_rate_ha_entity_id", "sensor.garden_flow"),
        ],
    )
    def test_the_coupling_fields_are_refused_until_wp_7_4(self, world, field: str, value: object) -> None:
        service, zones, _ = world
        before = dict(zones.zones)

        with pytest.raises(PlanError) as caught:
            service.create_zone(
                SITE, tenant_key=TENANT, role=TenantRole.LEAD, data=IrrigationZoneInput(name="Z", **{field: value})
            )

        assert caught.value.status_code == 422
        assert caught.value.details[0]["code"] == ERROR_COUPLING_NOT_AVAILABLE
        assert caught.value.details[0]["field"] == field
        assert zones.zones == before

    def test_the_coupling_defaults_are_accepted(self, world) -> None:
        service, _, _ = world

        view = service.create_zone(
            SITE,
            tenant_key=TENANT,
            role=TenantRole.GROWER,
            data=IrrigationZoneInput(name="Z", actuator_key=None, flow_rate_source="manual"),
        )

        assert view.zone.flow_rate_source.value == "manual"


class TestRead:
    def test_the_list_carries_each_zones_beds(self, world) -> None:
        service, zones, _ = world
        zones.covers.update({"bed_2": "zone_a", "bed_1": "zone_a"})

        views = service.list_zones(SITE, tenant_key=TENANT, offset=0, limit=50)

        assert [(v.zone.key, v.location_keys) for v in views] == [
            ("zone_a", ("bed_1", "bed_2")),
            ("zone_b", ()),
        ]

    @pytest.mark.parametrize("site", [FOREIGN_SITE, "site_gone"])
    def test_a_foreign_site_lists_nothing_but_a_404(self, world, site: str) -> None:
        service, _, _ = world
        with pytest.raises(NotFoundError):
            service.list_zones(site, tenant_key=TENANT, offset=0, limit=50)

    @pytest.mark.parametrize("key", ["zone_foreign", "zone_gone"])
    def test_a_foreign_zone_is_a_404(self, world, key: str) -> None:
        service, _, _ = world
        with pytest.raises(NotFoundError):
            service.get_zone(key, tenant_key=TENANT)


class TestPatch:
    def test_only_the_changed_fields_reach_the_repository(self, world) -> None:
        service, zones, _ = world

        view = service.patch_zone(
            "zone_b",
            tenant_key=TENANT,
            role=TenantRole.GROWER,
            patch=IrrigationZonePatch(name="Hand round", color="#123ABC", water_source_key="barrel"),
        )

        assert zones.updates == [("zone_b", {"color": "#123ABC", "water_source_key": "barrel"})]
        assert (view.zone.color, view.zone.water_source_key) == ("#123ABC", "barrel")

    def test_null_unlinks_the_water_source(self, world) -> None:
        service, zones, _ = world
        zones.zones["zone_b"] = zones.zones["zone_b"].model_copy(update={"water_source_key": "barrel"})

        service.patch_zone(
            "zone_b", tenant_key=TENANT, role=TenantRole.GROWER, patch=IrrigationZonePatch(water_source_key=None)
        )

        assert zones.updates == [("zone_b", {"water_source_key": None})]

    def test_an_unchanged_patch_writes_nothing(self, world) -> None:
        service, zones, _ = world

        service.patch_zone(
            "zone_b", tenant_key=TENANT, role=TenantRole.GROWER, patch=IrrigationZonePatch(name="Hand round")
        )

        assert zones.updates == []

    def test_a_viewer_is_refused(self, world) -> None:
        service, zones, _ = world
        with pytest.raises(ForbiddenError):
            service.patch_zone("zone_b", tenant_key=TENANT, role=TenantRole.VIEWER, patch=IrrigationZonePatch(name="X"))
        assert zones.updates == []

    @pytest.mark.parametrize("key", ["zone_foreign", "zone_gone"])
    def test_a_foreign_zone_is_a_404_before_the_role(self, world, key: str) -> None:
        service, zones, _ = world
        with pytest.raises(NotFoundError):
            service.patch_zone(key, tenant_key=TENANT, role=TenantRole.VIEWER, patch=IrrigationZonePatch(name="X"))
        assert zones.updates == []

    def test_a_foreign_water_source_is_reference_not_found(self, world) -> None:
        service, zones, _ = world
        with pytest.raises(PlanValidationError) as caught:
            service.patch_zone(
                "zone_b",
                tenant_key=TENANT,
                role=TenantRole.GROWER,
                patch=IrrigationZonePatch(water_source_key="barrel_foreign"),
            )
        assert _codes(caught.value) == [("water_source_key", "reference.not_found")]
        assert zones.updates == []

    def test_a_coupling_field_is_refused(self, world) -> None:
        service, zones, _ = world
        with pytest.raises(PlanError) as caught:
            service.patch_zone(
                "zone_b", tenant_key=TENANT, role=TenantRole.LEAD, patch=IrrigationZonePatch(actuator_key="act_1")
            )
        assert caught.value.details[0]["code"] == ERROR_COUPLING_NOT_AVAILABLE
        assert zones.updates == []

    @pytest.mark.parametrize("field", ["name", "irrigation_type", "color"])
    def test_a_required_field_cannot_be_cleared(self, field: str) -> None:
        with pytest.raises(ValueError, match="cannot be cleared"):
            IrrigationZonePatch.model_validate({field: None})


class TestDelete:
    def test_only_the_lead_deletes(self, world) -> None:
        service, zones, _ = world
        with pytest.raises(ForbiddenError):
            service.delete_zone("zone_a", tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        assert "zone_a" in zones.zones and zones.audit == []

    def test_the_delete_releases_the_beds_and_is_audited(self, world) -> None:
        service, zones, repo = world
        service.replace_locations("zone_a", tenant_key=TENANT, role=TenantRole.GROWER, location_keys=["bed_1"])

        service.delete_zone("zone_a", tenant_key=TENANT, user_key=USER, role=TenantRole.LEAD)

        assert "zone_a" not in zones.zones
        assert repo.locations["bed_1"].irrigation_zone_key is None and zones.covers == {}
        assert zones.audit == [{"op": "delete", "entity": "irrigation_zone", "key": "zone_a", "user_key": USER}]

    @pytest.mark.parametrize("key", ["zone_foreign", "zone_gone"])
    def test_a_foreign_zone_is_a_404(self, world, key: str) -> None:
        service, zones, _ = world
        with pytest.raises(NotFoundError):
            service.delete_zone(key, tenant_key=TENANT, user_key=USER, role=TenantRole.LEAD)
        assert "zone_foreign" in zones.zones


class TestReplaceLocations:
    def test_the_set_is_replaced_and_the_field_follows_the_edge(self, world) -> None:
        service, zones, repo = world
        service.replace_locations("zone_a", tenant_key=TENANT, role=TenantRole.GROWER, location_keys=["bed_1", "bed_2"])

        view, change = service.replace_locations(
            "zone_a", tenant_key=TENANT, role=TenantRole.GROWER, location_keys=["bed_2", "bed_3", "bed_3"]
        )

        assert view.location_keys == ("bed_2", "bed_3")
        assert (change.added, change.removed, change.moved_from) == (("bed_3",), ("bed_1",), {})
        assert {k: repo.locations[k].irrigation_zone_key for k in ("bed_1", "bed_2", "bed_3")} == {
            "bed_1": None,
            "bed_2": "zone_a",
            "bed_3": "zone_a",
        }

    def test_a_bed_is_in_at_most_one_zone(self, world) -> None:
        service, zones, repo = world
        service.replace_locations("zone_a", tenant_key=TENANT, role=TenantRole.GROWER, location_keys=["bed_1"])

        view, change = service.replace_locations(
            "zone_b", tenant_key=TENANT, role=TenantRole.GROWER, location_keys=["bed_1"]
        )

        assert change.moved_from == {"bed_1": "zone_a"}
        assert view.location_keys == ("bed_1",)
        assert service.get_zone("zone_a", tenant_key=TENANT).location_keys == ()
        assert repo.locations["bed_1"].irrigation_zone_key == "zone_b"

    def test_an_empty_set_releases_every_bed(self, world) -> None:
        service, zones, repo = world
        service.replace_locations("zone_a", tenant_key=TENANT, role=TenantRole.GROWER, location_keys=["bed_1"])

        view, change = service.replace_locations("zone_a", tenant_key=TENANT, role=TenantRole.GROWER, location_keys=[])

        assert (view.location_keys, change.removed) == ((), ("bed_1",))
        assert repo.locations["bed_1"].irrigation_zone_key is None

    def test_every_key_outside_the_site_is_named_and_nothing_is_written(self, world) -> None:
        service, zones, _ = world

        with pytest.raises(PlanValidationError) as caught:
            service.replace_locations(
                "zone_a",
                tenant_key=TENANT,
                role=TenantRole.GROWER,
                location_keys=["bed_1", "bed_foreign", "bed_gone", "bed_other_site"],
            )

        assert _codes(caught.value) == [
            ("location_keys[1]", "reference.not_found"),
            ("location_keys[2]", "reference.not_found"),
            ("location_keys[3]", "reference.not_found"),
        ]
        assert zones.covers == {}

    def test_a_viewer_cannot_assign(self, world) -> None:
        service, zones, _ = world
        with pytest.raises(ForbiddenError):
            service.replace_locations("zone_a", tenant_key=TENANT, role=TenantRole.VIEWER, location_keys=["bed_1"])
        assert zones.covers == {}

    @pytest.mark.parametrize("key", ["zone_foreign", "zone_gone"])
    def test_a_foreign_zone_is_a_404(self, world, key: str) -> None:
        service, zones, _ = world
        with pytest.raises(NotFoundError):
            service.replace_locations(key, tenant_key=TENANT, role=TenantRole.LEAD, location_keys=["bed_1"])
        assert zones.covers == {}
