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
from app.domain.models.site import SiteConditions, SitePlan, Slot
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

    def test_site_conditions_come_through_the_import_unchanged(self, rig, repo) -> None:
        """WP 3.9: a backup that carries the site features restores them (a restore must not lose the sun profile)."""
        document = rig.file()
        document["locations"][0]["site_conditions"] = {
            "sun_profile": {"sun_window": "afternoon", "foliage_shade_in_summer": True},
            "microclimate": {"frost_risk": "high", "cold_air_pocket": True},
            "wind_exposure": "exposed",
            "access_sides": ["N", "S"],
        }
        del document["locations"][0]["frost_exposed"]  # a file written before #2512

        report = rig.run(document)

        assert report.applied
        stored = {loc.name: loc for loc in repo.locations.values()}["Beet 1"].site_conditions
        assert stored is not None
        assert stored.sun_profile.sun_window == "afternoon" and stored.sun_profile.foliage_shade_in_summer is True
        assert (stored.microclimate.frost_risk, stored.microclimate.cold_air_pocket) == ("high", True)
        assert (stored.wind_exposure, [side.value for side in stored.access_sides]) == ("exposed", ["N", "S"])
        # The winter readers still read ``frost_exposed``; this file has none, so it follows the risk.
        assert {loc.name: loc for loc in repo.locations.values()}["Beet 1"].frost_exposed is True
        # A bed without the key stays without it - the import invents nothing.
        assert {loc.name: loc for loc in repo.locations.values()}["Beet 2"].site_conditions is None
        assert {loc.name: loc for loc in repo.locations.values()}["Beet 2"].frost_exposed is None

    def test_a_sun_profile_edited_in_the_plan_survives_export_and_import(self, rig, repo) -> None:
        """#2538: what the editor's batch writes is in the file and comes back from it, keys and values intact."""
        GardenPlanService(repo._sites, repo).apply_batch(
            SITE,
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.GROWER,
            expected_revision=3,
            operations=[
                {
                    "op": "update_fields",
                    "entity": "location",
                    "key": "b1",
                    "fields": {
                        "site_conditions": {
                            "sun_profile": {
                                "sun_window": "morning",
                                "direct_sun_hours_summer": 4.5,
                                "foliage_shade_in_summer": True,
                            }
                        }
                    },
                }
            ],
            body_bytes=500,
        )
        document = rig.file()
        exported = {loc["name"]: loc for loc in document["locations"]}["Beet 1"]["site_conditions"]["sun_profile"]
        assert exported == {
            "sun_window": "morning",
            "direct_sun_hours_summer": 4.5,
            "foliage_shade_in_summer": True,
            "source": "manual",
        }

        report = rig.run(document)

        assert report.applied
        restored = {loc.name: loc for loc in repo.locations.values()}["Beet 1"]
        assert "b1" not in repo.locations  # a new key: the import really recreated the bed
        assert restored.site_conditions is not None
        assert restored.site_conditions.sun_profile.model_dump(mode="json") == exported

    @staticmethod
    def _set_frost(repo: FakePlanRepo, frost_exposed: bool | None, risk: str | None) -> None:
        conditions = SiteConditions.model_validate({"microclimate": {"frost_risk": risk}}) if risk else None
        repo.locations["b1"] = repo.locations["b1"].model_copy(
            update={"frost_exposed": frost_exposed, "site_conditions": conditions}
        )

    @staticmethod
    def _restored_beet_1(repo: FakePlanRepo):
        restored = {loc.name: loc for loc in repo.locations.values()}["Beet 1"]
        assert "b1" not in repo.locations  # a new key: the import really recreated the bed
        return restored

    @pytest.mark.parametrize(
        ("frost_exposed", "risk"),
        [
            (False, "normal"),  # #2503 edge 2: what v0098 leaves for a protected bed (#2464)
            (True, "high"),
            (None, "unknown"),
            (None, None),
        ],
    )
    def test_the_frost_override_survives_a_restore_from_its_own_backup(self, rig, repo, frost_exposed, risk) -> None:
        """#2512: the backup carries ``frost_exposed``, so a migrated ``False``/``normal`` bed stays protected."""
        self._set_frost(repo, frost_exposed, risk)
        document = rig.file()
        exported = {loc["name"]: loc for loc in document["locations"]}["Beet 1"]
        assert "frost_exposed" in exported and exported["frost_exposed"] is frost_exposed

        report = rig.run(document)

        assert report.applied
        restored = self._restored_beet_1(repo)
        assert restored.frost_exposed is frost_exposed
        stored_risk = restored.site_conditions.microclimate.frost_risk if restored.site_conditions else None
        assert stored_risk == risk

    @pytest.mark.parametrize(
        ("exempt", "enabled"),
        [(False, None), (False, True), (False, False), (True, None)],
    )
    def test_the_rotation_switches_survive_a_restore_from_their_own_backup(self, rig, repo, exempt, enabled) -> None:
        """GP-FR-137 (#2544): ``rotation_exempt`` and ``rotation_enabled`` are in the file and come back from it."""
        repo.locations["b1"] = repo.locations["b1"].model_copy(
            update={"rotation_exempt": exempt, "rotation_enabled": enabled}
        )
        document = rig.file()
        exported = {loc["name"]: loc for loc in document["locations"]}["Beet 1"]
        assert (exported["rotation_exempt"], exported["rotation_enabled"]) == (exempt, enabled)

        report = rig.run(document)

        assert report.applied
        restored = self._restored_beet_1(repo)
        assert (restored.rotation_exempt, restored.rotation_enabled) == (exempt, enabled)

    @pytest.mark.parametrize(("exempt", "enabled"), [(True, None), (False, True)])
    def test_a_file_without_the_rotation_switches_keeps_the_type_default(self, rig, repo, exempt, enabled) -> None:
        """A file written before #2544 lacks both keys: the restored bed is not exempt and follows its type.

        The source bed holds other values, so ``(False, None)`` can only come from the file's defaults - not from
        the standing row the replace overwrites.
        """
        repo.locations["b1"] = repo.locations["b1"].model_copy(
            update={"rotation_exempt": exempt, "rotation_enabled": enabled}
        )
        document = rig.file()
        for item in document["locations"]:
            item.pop("rotation_exempt", None)
            item.pop("rotation_enabled", None)

        report = rig.run(document)

        assert report.applied
        restored = self._restored_beet_1(repo)
        assert (restored.rotation_exempt, restored.rotation_enabled) == (False, None)

    @pytest.mark.parametrize("dry_run", [True, False])
    def test_a_bed_exempt_and_switched_on_in_the_file_is_reported_and_not_written(self, rig, repo, dry_run) -> None:
        """SEC-002: the import must not store the pair the PATCH refuses; it names the bed and the field."""
        document = rig.file()
        position = next(i for i, loc in enumerate(document["locations"]) if loc["name"] == "Beet 1")
        document["locations"][position] |= {"rotation_exempt": True, "rotation_enabled": True}
        expected = [(f"locations[{position}].rotation_enabled", "import.rotation_exempt_and_enabled", "b1")]

        if dry_run:
            report = rig.run(document, dry_run=True)
            assert [(e.field, e.code, e.key) for e in report.errors] == expected
        else:
            with pytest.raises(PlanValidationError) as refused:
                rig.run(document)
            assert [(d["field"], d["code"], d["key"]) for d in refused.value.details] == expected
        assert repo.applied == []

    @pytest.mark.parametrize(
        ("name", "value"), [("rotation_exempt", "yes"), ("rotation_enabled", "true"), ("rotation_enabled", 1)]
    )
    def test_a_rotation_flag_that_is_not_a_json_boolean_is_refused(self, rig, repo, name, value) -> None:
        """Strict: ``"yes"`` / ``"true"`` / ``1`` are not coerced into a switch the user never set."""
        document = rig.file()
        document["locations"][0][name] = value

        with pytest.raises(PlanValidationError) as refused:
            rig.run(document, dry_run=True)

        assert [(d["field"], d["code"]) for d in refused.value.details] == [
            (f"locations[0].{name}", "validation.invalid")
        ]
        assert repo.applied == []

    def test_an_explicit_null_inherits_even_where_the_risk_would_force_a_value(self, rig, repo) -> None:
        """``null`` sent is "inherit from the site type", not "derive from the risk" (#2512)."""
        document = rig.file()
        document["locations"][0]["site_conditions"] = {"microclimate": {"frost_risk": "high"}}
        document["locations"][0]["frost_exposed"] = None

        rig.run(document)

        assert self._restored_beet_1(repo).frost_exposed is None

    @pytest.mark.parametrize(("risk", "derived"), [("high", True), ("low", False), ("normal", None), ("unknown", None)])
    def test_a_file_written_before_the_key_derives_the_override_from_the_risk(self, rig, repo, risk, derived) -> None:
        """A backup from before #2512 has no ``frost_exposed``: the boolean follows the risk, as it did then.

        ``normal`` forces none (#2454 item 2), so a migrated ``False``/``normal`` bed in such an old file still comes
        back inheriting from the site type - the old file simply does not hold the protection.
        """
        self._set_frost(repo, True, None)  # what the target held must not leak into the restore
        document = rig.file()
        del document["locations"][0]["frost_exposed"]
        document["locations"][0]["site_conditions"] = {"microclimate": {"frost_risk": risk}}

        report = rig.run(document)

        assert report.applied
        restored = self._restored_beet_1(repo)
        assert restored.site_conditions is not None
        assert restored.site_conditions.microclimate.frost_risk == risk
        assert restored.frost_exposed is derived

    def test_an_old_file_without_site_conditions_restores_no_override(self, rig, repo) -> None:
        document = rig.file()
        del document["locations"][0]["frost_exposed"]
        document["locations"][0]["site_conditions"] = None

        rig.run(document)

        assert self._restored_beet_1(repo).frost_exposed is None

    def test_a_shifted_merge_keeps_the_override_of_the_file(self, rig, repo) -> None:
        """The offset path copies the parsed file; the copy must still know which keys the file sent."""
        self._set_frost(repo, False, "normal")
        document = rig.file()
        document["locations"] = [loc for loc in document["locations"] if loc["name"] == "Beet 1"]
        document["locations"][0]["name"] = "Beet 1 copy"
        document["slots"] = []

        report = rig.run(document, mode="merge", offset_m=(0.0, 5.0), confirm_site_name=None)

        assert report.applied
        (copy_of_bed,) = [loc for loc in repo.locations.values() if loc.name == "Beet 1 copy"]
        assert copy_of_bed.frost_exposed is False

    def test_an_invalid_site_condition_is_a_finding_not_a_crash(self, rig, repo) -> None:
        document = rig.file()
        document["locations"][0]["site_conditions"] = {"slope_deg": 400}

        with pytest.raises(PlanValidationError):
            rig.run(document)
        assert repo.applied == []

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
            ({**document, "templates": []}, "import.unknown_keys"),
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


class TestOversizedListsAreRefusedBeforeAnyLookup2542:
    """#2542 W-1: a file with more entries than a site may hold is refused whole, before ``_prepare`` looks up."""

    @staticmethod
    def _counted(rig, repo, monkeypatch) -> dict[str, int]:
        calls = {"load_structure": 0, "irrigation_zone_site_key": 0, "substrate_visible": 0, "check_quotas": 0}
        for name in ("load_structure", "irrigation_zone_site_key", "substrate_visible"):
            original = getattr(repo, name)

            def counted(*args: Any, _name: str = name, _original: Any = original, **kwargs: Any) -> Any:
                calls[_name] += 1
                return _original(*args, **kwargs)

            monkeypatch.setattr(repo, name, counted)
        check_quotas = rig.service._check_quotas

        def counted_quotas(*args: Any, **kwargs: Any) -> None:
            calls["check_quotas"] += 1
            check_quotas(*args, **kwargs)

        monkeypatch.setattr(rig.service, "_check_quotas", counted_quotas)
        return calls

    @staticmethod
    def _with_locations(rig, count: int) -> dict[str, Any]:
        document = rig.file()
        template = document["locations"][0]
        document["locations"] = [
            {
                **template,
                "key": f"bed_{n}",
                "irrigation_zone_key": f"zone_{n}",
                "soil_profile": {**(template.get("soil_profile") or {}), "substrate_key": f"sub_{n}"},
            }
            for n in range(count)
        ]
        document["slots"] = []
        return document

    @pytest.mark.parametrize("dry_run", [True, False])
    def test_501_locations_are_the_quota_and_nothing_is_looked_up(self, rig, repo, monkeypatch, dry_run) -> None:
        document = self._with_locations(rig, 501)  # read before counting: the export reads the site, too
        calls = self._counted(rig, repo, monkeypatch)

        with pytest.raises(PlanValidationError) as refused:
            rig.run(document, dry_run=dry_run)

        assert refused.value.status_code == 422
        assert [(d["field"], d["code"]) for d in refused.value.details] == [("locations", "plan.quota_exceeded")]
        assert calls == {"load_structure": 0, "irrigation_zone_site_key": 0, "substrate_visible": 0, "check_quotas": 0}
        assert repo.applied == []

    def test_500_locations_still_reach_the_lookups_and_the_quota_check(self, rig, repo, monkeypatch) -> None:
        document = self._with_locations(rig, 500)
        calls = self._counted(rig, repo, monkeypatch)

        report = rig.run(document, dry_run=True)

        assert report.dry_run and report.would_create.locations == 500
        assert calls["load_structure"] == 1 and calls["check_quotas"] == 1
        assert calls["irrigation_zone_site_key"] == 500 and calls["substrate_visible"] == 500

    @pytest.mark.parametrize(("field", "count"), [("garden_objects", 501), ("slots", 8001)])
    def test_the_other_capped_lists_are_the_quota_too(self, rig, repo, monkeypatch, field, count) -> None:
        document = rig.file()
        calls = self._counted(rig, repo, monkeypatch)
        an_object = {"key": "o", "object_type": "path", "geometry": rect(1, 1), "props": {}}
        item = document["slots"][0] if field == "slots" else an_object
        document[field] = [{**item, "key": f"x{n}"} for n in range(count)]

        with pytest.raises(PlanValidationError) as refused:
            rig.run(document, dry_run=True)

        assert [(d["field"], d["code"]) for d in refused.value.details] == [(field, "plan.quota_exceeded")]
        assert calls["load_structure"] == 0

    def test_501_zones_are_the_zone_quota_like_the_quota_check_says(self, rig, repo, monkeypatch) -> None:
        # One case, one code (#2542): the schema cap reports what ``_check_quotas`` reports for the same excess.
        from app.domain.models.garden_plan import MAX_PLAN_ZONES

        document = rig.file()
        calls = self._counted(rig, repo, monkeypatch)
        document["zones"] = [{"key": f"z{n}", "name": f"Zone {n}"} for n in range(MAX_PLAN_ZONES + 1)]

        with pytest.raises(PlanValidationError) as refused:
            rig.run(document, dry_run=True)

        assert [(d["field"], d["code"]) for d in refused.value.details] == [("zones", "irrigation_zone.quota_exceeded")]
        assert calls["load_structure"] == 0

    def test_the_export_of_a_site_above_the_quota_is_still_written(self, rig, repo) -> None:
        # A location made through the site API is not counted against GP-NFR-017; the export must not refuse it.
        for n in range(501):
            repo.locations[f"extra_{n}"] = make_location(f"extra_{n}", f"Beet {n}", geometry=rect(1, 5))

        assert len(rig.file()["locations"]) == 503


class TestOffsetAndTargetWp718:
    """REQ-053 WP 7.18 (#2484, GP-FR-172): ``offset_m`` and ``target`` of an import."""

    def test_a_merge_with_an_offset_moves_every_geometry_and_the_boundary_the_file_brings(self, rig, repo) -> None:
        document = rig.file()
        repo.locations.clear()  # the file's beds are merged into a site that has none yet
        repo._sites.sites[SITE].plan = None  # a site without a plan takes the file's boundary

        report = rig.run(document, mode="merge", confirm_site_name=None, offset_m=(2.0, 1.5))

        assert report.applied and report.offset_m == (2.0, 1.5)
        moved = sorted(loc.geometry.origin for key, loc in repo.locations.items() if key not in {"b1", "b2"})
        assert moved == [(3.0, 2.5), (3.0, 4.5)]
        assert repo.applied[-1].boundary.origin == (2.0, 1.5)

    def test_slots_are_not_moved_with_their_bed(self, rig, repo) -> None:
        document = rig.file()
        repo.locations.clear()
        repo.slots.clear()

        rig.run(document, mode="merge", confirm_site_name=None, offset_m=(2.0, 1.5))

        assert {slot.geometry.origin for slot in repo.slots} == {(0.5, 0.5), (1.5, 0.5)}

    @pytest.mark.parametrize("offset", [(float("inf"), 0.0), (0.0, float("nan")), (1000.5, 0.0)])
    def test_a_non_finite_or_oversized_offset_is_a_422_before_anything_is_read(self, rig, offset) -> None:
        with pytest.raises(PlanError) as refused:
            rig.run({}, mode="merge", confirm_site_name=None, offset_m=offset)

        assert refused.value.status_code == 422 and refused.value.error_code == "import.offset_invalid"

    def test_an_offset_is_for_a_merge_and_zero_is_no_offset(self, rig, repo) -> None:
        document = rig.file()
        with pytest.raises(PlanError) as refused:
            rig.run(document, offset_m=(1.0, 0.0))
        assert refused.value.error_code == "import.offset_requires_merge"
        repo.locations.clear()

        report = rig.run(document, mode="merge", confirm_site_name=None, offset_m=(0.0, 0.0))

        assert report.applied and report.offset_m is None

    def test_a_shift_out_of_the_frame_is_listed_with_the_file_key_and_nothing_is_written(self, rig, repo) -> None:
        document = rig.file()
        repo.locations.clear()

        report = rig.run(document, mode="merge", confirm_site_name=None, dry_run=True, offset_m=(1000.0, 0.0))

        assert report.errors_total == 2 and {error.code for error in report.errors} == {"geometry.invalid"}
        assert {error.key for error in report.errors} == {"b1", "b2"}
        assert repo.applied == []

    def test_only_the_same_site_resolves_a_parent_that_is_not_in_the_file(self, rig) -> None:
        document = rig.file()
        document["locations"] = [{**document["locations"][0], "parent_location_key": "b2"}]
        document["slots"] = []

        same = rig.run(document, mode="merge", confirm_site_name=None, dry_run=True, target="same_site")
        other = rig.run(document, mode="merge", confirm_site_name=None, dry_run=True, target="other_site")
        tenant = rig.run(document, mode="merge", confirm_site_name=None, dry_run=True, target="other_tenant")

        assert [d.field for d in same.dropped_references] == []
        for report in (other, tenant):
            assert [(d.field, d.reason) for d in report.dropped_references] == [("parent_location_key", "outside_file")]
            assert report.target != "same_site"

    def test_the_target_does_not_widen_who_may_import(self, rig) -> None:
        for role in (TenantRole.GROWER, TenantRole.VIEWER):
            with pytest.raises(PlanError) as refused:
                rig.run(rig.file(), role=role, mode="merge", target="other_tenant", confirm_site_name=None)
            assert refused.value.status_code == 403


class TestSnapshotsWp719:
    def _replaced(self, rig, repo) -> str:
        rig.run(rig.file())
        (entry,) = rig.service.list_snapshots(SITE, tenant_key=TENANT, role=TenantRole.LEAD, offset=0, limit=10)
        return entry.audit_key

    def test_a_replace_leaves_a_snapshot_the_lead_can_list_and_restore(self, rig, repo) -> None:
        audit_key = self._replaced(rig, repo)

        report = rig.service.restore_snapshot(
            SITE,
            audit_key,
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.LEAD,
            dry_run=False,
            force=False,
            confirm_site_name="Garten",
        )

        assert report.applied and report.snapshot_written and report.mode == "replace"
        assert len(repo.snapshot_rows) == 2  # the restore wrote its own snapshot first

    def test_a_grower_and_another_tenant_are_refused_in_that_order(self, rig, repo) -> None:
        audit_key = self._replaced(rig, repo)
        ask = {"user_key": USER, "dry_run": True, "force": False, "confirm_site_name": None}

        with pytest.raises(PlanError) as grower:
            rig.service.restore_snapshot(SITE, audit_key, tenant_key=TENANT, role=TenantRole.GROWER, **ask)
        with pytest.raises(NotFoundError):
            rig.service.restore_snapshot(SITE, audit_key, tenant_key=OTHER_TENANT, role=TenantRole.GROWER, **ask)
        with pytest.raises(NotFoundError):
            rig.service.list_snapshots(SITE, tenant_key=OTHER_TENANT, role=TenantRole.LEAD, offset=0, limit=10)
        with pytest.raises(PlanError) as listing:
            rig.service.list_snapshots(SITE, tenant_key=TENANT, role=TenantRole.VIEWER, offset=0, limit=10)

        assert grower.value.status_code == 403 and listing.value.status_code == 403

    def test_an_unknown_snapshot_is_a_404(self, rig) -> None:
        with pytest.raises(NotFoundError):
            rig.service.restore_snapshot(
                SITE,
                "snap_nobody",
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.LEAD,
                dry_run=True,
                force=False,
                confirm_site_name=None,
            )

    def test_the_listing_is_newest_first_and_only_the_callers_site_over_the_fakes_cap(self, rig, repo) -> None:
        """The service lists a site's snapshots newest first, scoped to the caller's tenant and site.

        The cap of :data:`MAX_SNAPSHOTS_PER_SITE` is applied here by ``FakePlanRepo.apply_plan_batch``, which
        re-implements the pruning contract; this test therefore pins the service's listing over that contract and
        proves nothing about the production ``_prune_snapshots``. The W-2 proof (#2542) against ArangoDB is
        ``test_a_site_keeps_its_newest_twenty_snapshots_and_every_other_row`` in
        ``tests/integration/test_garden_plan_import.py``.
        """
        from app.domain.models.garden_plan_import import MAX_SNAPSHOTS_PER_SITE

        repo.snapshot_rows.append((OTHER_TENANT, SITE, "foreign_tenant", {}))  # another tenant, same site key
        repo.snapshot_rows.append((TENANT, "site_other", "other_site", {}))
        listed: list[str] = []
        for _ in range(MAX_SNAPSHOTS_PER_SITE + 1):
            rig.run(rig.file())
            newest, *_ = rig.service.list_snapshots(SITE, tenant_key=TENANT, role=TenantRole.LEAD, offset=0, limit=50)
            listed.append(newest.audit_key)

        kept = rig.service.list_snapshots(SITE, tenant_key=TENANT, role=TenantRole.LEAD, offset=0, limit=50)

        assert MAX_SNAPSHOTS_PER_SITE == 20 and len(repo.applied) == 21
        assert [entry.audit_key for entry in kept] == listed[:0:-1]  # newest first, the first one is gone
        assert listed[0] not in {entry.audit_key for entry in kept}
        assert {row[2] for row in repo.snapshot_rows} >= {"foreign_tenant", "other_site"}

    def test_a_page_is_capped_below_the_shared_pagination(self, rig, repo) -> None:
        from app.domain.services.garden_plan_import_service import MAX_SNAPSHOT_PAGE

        asked: list[int] = []
        original = repo.list_import_snapshots
        repo.list_import_snapshots = lambda *a, **k: (asked.append(k["limit"]), original(*a, **k))[1]  # type: ignore[method-assign]

        rig.service.list_snapshots(SITE, tenant_key=TENANT, role=TenantRole.LEAD, offset=0, limit=200)

        assert asked == [MAX_SNAPSHOT_PAGE] and MAX_SNAPSHOT_PAGE < 200


def test_a_dropped_reference_echoes_at_most_64_characters_of_the_files_key() -> None:
    from app.domain.models.garden_plan_import import DroppedReference

    long = DroppedReference(entity="location", key="k" * 5000, field="parent_location_key", reason="not_found")

    assert len(long.key) == 64
    assert DroppedReference(entity="slot", key="slot_1", field="location_key", reason="not_found").key == "slot_1"
