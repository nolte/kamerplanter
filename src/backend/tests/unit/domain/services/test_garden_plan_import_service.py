"""REQ-053 WP 5.3 (#2432) - the import service against the in-memory repository.

The transaction itself is measured against ArangoDB in ``tests/integration/test_garden_plan_import.py``; what is
pinned here is the decision logic: who may import, in which order a file is refused, what stays, what is dropped,
and what reaches the repository (new keys only, the snapshot, the adjacency dispatch).
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError, PlanError, PlanValidationError
from app.domain.models.site import SitePlan, Slot
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

FOREIGN_SITE = "site_foreign"
USER = "u_sabine"


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}, plan_revision=3
    )
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": FOREIGN_SITE})
    repository = FakePlanRepo(FakeSites(site, foreign))
    repository.locations["b1"] = make_location("b1", "Beet 1", geometry=rect(1, 1, 3, 1))
    repository.locations["b2"] = make_location("b2", "Beet 2", geometry=rect(1, 3, 3, 1))
    repository.slots = [
        Slot(_key="s1", slot_id="B1_P1", location_key="b1", geometry={"kind": "point", "origin": [0.5, 0.5]}),
        Slot(_key="s2", slot_id="B1_P2", location_key="b1", geometry={"kind": "point", "origin": [1.5, 0.5]}),
    ]
    return repository


class Rig:
    def __init__(self, repo: FakePlanRepo) -> None:
        self.repo = repo
        plans = GardenPlanService(repo._sites, repo)
        self.export = GardenPlanExportService(repo._sites, repo, plans)
        self.dispatched: list[str] = []
        self.service = GardenPlanImportService(
            repo._sites, repo, plans, self.export, dispatch_adjacency=self.dispatched.append
        )

    def file(self) -> dict[str, Any]:
        return self.export.export_json(SITE, tenant_key=TENANT).model_dump(mode="json")

    def run(self, document: dict[str, Any], *, site: str = SITE, tenant: str = TENANT, **options: Any):
        arguments: dict[str, Any] = {
            "role": TenantRole.LEAD,
            "mode": "replace",
            "dry_run": False,
            "force": False,
            "confirm_site_name": "Garten",
        } | options
        return self.service.import_plan(site, tenant_key=tenant, user_key=USER, document=document, **arguments)


@pytest.fixture
def rig(repo: FakePlanRepo) -> Rig:
    return Rig(repo)


class TestReplace:
    def test_it_swaps_the_structure_for_new_keys_and_writes_the_snapshot(self, rig, repo) -> None:
        document = rig.file()
        old_keys = set(repo.locations)

        report = rig.run(document)

        assert report.applied and report.snapshot_written and report.errors == []
        assert (report.would_create.locations, report.would_create.slots) == (2, 2)
        assert (report.would_delete.locations, report.would_delete.slots) == (2, 2)
        assert not (old_keys & set(repo.locations)) and len(repo.locations) == 2
        assert [loc.name for loc in repo.locations.values()] == ["Beet 1", "Beet 2"]
        (snapshot,) = repo.snapshots
        assert {loc["key"] for loc in snapshot["locations"]} == old_keys  # the state it overwrote
        (write,) = repo.applied
        assert write.expected_revision == write.basis_revision == 3
        assert {op["op"] for op in write.audit} == {"import_delete", "import_replace"}

    def test_the_slots_follow_their_bed_and_the_adjacency_recompute_is_asked_for_that_bed_only(self, rig, repo) -> None:
        rig.run(rig.file())

        (bed,) = {slot.location_key for slot in repo.slots}
        assert repo.locations[bed].name == "Beet 1"
        assert rig.dispatched == [bed]

    def test_a_dry_run_changes_nothing_and_asks_for_no_name(self, rig, repo) -> None:
        report = rig.run(rig.file(), dry_run=True, confirm_site_name=None)

        assert report.dry_run and not report.applied and report.would_create.locations == 2
        assert repo.applied == [] and set(repo.locations) == {"b1", "b2"} and rig.dispatched == []

    @pytest.mark.parametrize("name", [None, "", "garten", "Beet"])
    def test_the_exact_site_name_is_required_for_the_write(self, rig, repo, name) -> None:
        with pytest.raises(PlanError) as refused:
            rig.run(rig.file(), confirm_site_name=name)
        assert refused.value.error_code == "import.site_name_mismatch" and repo.applied == []

    def test_a_planted_bed_refuses_the_replace_and_force_keeps_it_with_what_is_above(self, rig, repo) -> None:
        repo.locations["house"] = make_location(
            "house", "Haus", geometry=rect(6, 6, 3, 3), location_type_key="greenhouse"
        )
        repo.locations["b2"] = make_location(
            "b2", "Beet 2", geometry=rect(6.5, 6.5, 1, 1), parent_location_key="house", depth=1
        )
        repo.planted = {"b2"}
        document = rig.file()
        document["locations"] = [loc for loc in document["locations"] if loc["key"] == "b1"]
        document["slots"] = []

        dry = rig.run(document, dry_run=True)
        assert [e.code for e in dry.errors] == ["import.not_empty"]
        with pytest.raises(PlanError) as refused:
            rig.run(document)
        assert refused.value.status_code == 409 and repo.applied == []

        report = rig.run(document, force=True)

        assert report.applied and report.kept_locations == 2
        assert {"house", "b2"} <= set(repo.locations) and "b1" not in repo.locations
        assert len(repo.locations) == 3  # house, b2 and the new Beet 1


class TestMerge:
    def test_it_adds_next_to_what_is_there_without_a_snapshot(self, rig, repo) -> None:
        document = rig.file()
        for loc in document["locations"]:
            loc["geometry"]["origin"][0] += 5

        report = rig.run(document, mode="merge", confirm_site_name=None)

        assert report.applied and not report.snapshot_written and repo.snapshots == []
        assert len(repo.locations) == 4 and {"b1", "b2"} <= set(repo.locations)

    def test_beds_on_top_of_existing_ones_are_reported_not_moved(self, rig, repo) -> None:
        report = rig.run(rig.file(), mode="merge", dry_run=True)

        assert {error.code for error in report.errors} == {"bed.overlap"}
        with pytest.raises(PlanValidationError):
            rig.run(rig.file(), mode="merge")
        assert repo.applied == []

    def test_a_parent_outside_the_file_is_resolved_among_the_existing_locations_only(self, rig, repo) -> None:
        document = rig.file()
        document["locations"] = [copy.deepcopy(document["locations"][0])]
        document["locations"][0].update(key="x", geometry=rect(6, 6, 2, 1), parent_location_key="b2")
        document["slots"] = []
        repo.locations["b2"] = make_location("b2", "Beet 2", geometry=rect(5, 5, 4, 4), location_type_key="greenhouse")

        report = rig.run(document, mode="merge")

        assert report.dropped_references == []
        added = next(loc for key, loc in repo.locations.items() if loc.name == "Beet 1" and key != "b1")
        assert added.parent_location_key == "b2"


class TestReferencesAndFields:
    def test_unresolvable_references_are_dropped_and_the_rest_comes_through(self, rig, repo) -> None:
        document = rig.file()
        first, second = document["locations"]
        first["irrigation_zone_key"] = "zone_1"  # the tenant's, in this site: kept
        second["irrigation_zone_key"] = "zone_gone"
        first["soil_profile"] = {"substrate_key": "sub_foreign"}
        second["soil_profile"] = {"substrate_key": "sub_own"}
        first["location_type_key"] = "no_such_type"
        first["actuator_key"] = "act_1"
        second["parent_location_key"] = "loc_of_someone_else"

        report = rig.run(document)

        assert report.applied
        assert {(d.key, d.field, d.reason) for d in report.dropped_references} == {
            (second["key"], "irrigation_zone_key", "not_found"),
            (first["key"], "soil_profile.substrate_key", "not_found"),
            (first["key"], "location_type_key", "not_found"),
            (first["key"], "actuator_key", "always_dropped"),
            (second["key"], "parent_location_key", "not_found"),
        }
        stored = {loc.name: loc for loc in repo.locations.values()}
        assert stored["Beet 1"].irrigation_zone_key == "zone_1" and stored["Beet 1"].location_type_key == ""
        assert stored["Beet 2"].irrigation_zone_key is None and stored["Beet 2"].parent_location_key is None
        assert stored["Beet 2"].soil_profile.substrate_key == "sub_own"
        assert stored["Beet 1"].soil_profile.substrate_key is None

    def test_a_slot_that_names_a_bed_outside_the_file_is_dropped(self, rig, repo) -> None:
        document = rig.file()
        document["slots"][0]["location_key"] = "bed_of_someone_else"

        report = rig.run(document)

        assert [(d.entity, d.reason) for d in report.dropped_references] == [("slot", "not_found")]
        assert len(repo.slots) == 1

    def test_keys_of_the_file_never_reach_the_repository(self, rig, repo) -> None:
        document = rig.file()
        rig.run(document)

        (write,) = repo.applied
        file_keys = {item["key"] for name in ("locations", "slots", "garden_objects") for item in document[name]}
        sent = {temp for temp, _ in write.location_inserts} | {temp for temp, _ in write.object_inserts}
        assert not (sent & file_keys)
        assert all(model.key is None for _, model in write.location_inserts)


class TestTheFileIsUntrusted:
    def test_the_tenant_anchor_answers_first(self, rig) -> None:
        with pytest.raises(NotFoundError):
            rig.run({"not": "a plan"}, site=FOREIGN_SITE)
        with pytest.raises(PlanError) as own:
            rig.run({"not": "a plan"})
        assert own.value.error_code == "import.schema_version_missing"

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_only_a_lead_may_import_and_the_file_is_not_read_for_anyone_else(self, rig, repo, role) -> None:
        with pytest.raises(PlanError) as refused:
            rig.run({"not": "a plan"}, role=role)
        assert refused.value.status_code == 403 and refused.value.error_code == "import.forbidden"
        assert repo.applied == []

    def test_a_version_and_unknown_top_level_keys_are_refused_whole(self, rig) -> None:
        document = rig.file()
        for broken, code in (
            ({**document, "schema_version": "2"}, "import.schema_version_unsupported"),
            ({**document, "zones": []}, "import.unknown_keys"),
        ):
            with pytest.raises(PlanError) as refused:
                rig.run(broken)
            assert refused.value.error_code == code

    def test_findings_name_a_path_and_the_files_own_key_never_a_value(self, rig) -> None:
        document = rig.file()
        document["locations"][1]["geometry"] = {"kind": "rect", "origin": [0, 0], "width_m": -1, "length_m": 1}

        with pytest.raises(PlanValidationError) as refused:
            rig.run(document)

        (detail, *_) = refused.value.details
        assert detail["field"].startswith("locations[1].geometry") and detail["code"] == "geometry.invalid"
        assert detail["key"] == document["locations"][1]["key"]
