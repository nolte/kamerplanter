"""REQ-053 WP 1.9 (#2328) — beds, garden objects and slots as single resources.

The repository is the in-memory double of ``tests/support/garden_plan_fakes.py``: it holds the documents,
applies a write set the way the transaction does and records what it was handed. As in the plan-service
tests, every refusal asserts that **nothing reached the repository** — a refusal that still wrote is the
defect, not the status code.

What this file pins:

* GP-ACC-012 (delete a bed with plants → 409 with the count) and GP-ACC-015 (the status transition and its
  care event) — the acceptance criteria this package owns;
* the tenant anchor of every method: a foreign and an absent resource answer the same 404 and write nothing
  (T-01…T-04), and every method takes the tenant keyword-only;
* the role rules the router gate cannot express (§21.8): retiring and delete are the lead's;
* the geometry rules V-04, V-06 and V-20 on slots, and that a slot batch is all or nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.common.enums import BedStatus, FrostRisk, TenantRole
from app.common.exceptions import (
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    PlanError,
    PlanValidationError,
    WriteConflictError,
)
from app.domain.models.garden_plan import (
    BedCounters,
    CreateGardenObjectData,
    GardenObjectPatch,
    LocationPatch,
    SlotBatchItem,
    SlotBatchRequest,
    SlotPatch,
)
from app.domain.models.site import Microclimate, SiteConditions, Slot
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
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
    rect,
)


@pytest.fixture
def world():
    site = make_site()
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    sites = FakeSites(site, foreign)
    repo = FakePlanRepo(sites)
    repo.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1))
    repo.dispatched = []  # the bed keys handed to the adjacency dispatcher (GP-NFR-016)
    service = GardenResourceService(
        sites, repo, FakeObjects(repo), GardenPlanService(sites, repo), dispatch_adjacency=repo.dispatched.append
    )
    return service, repo, site


def code_of(exc: pytest.ExceptionInfo) -> str:
    return exc.value.details[0]["code"]


def revision(site) -> int:
    return site.plan.plan_revision


def as_point(x: float, y: float) -> dict:
    return {"kind": "point", "origin": [x, y]}


def as_zone(*points: tuple[float, float]) -> dict:
    return {"kind": "polygon", "points": [list(p) for p in points]}


def slot(key: str, slot_id: str, *, location_key: str = "bed", occupied: bool = False, geometry=None, **kw) -> Slot:
    return Slot.model_validate(
        {
            "_key": key,
            "slot_id": slot_id,
            "location_key": location_key,
            "currently_occupied": occupied,
            "geometry": geometry or as_point(0.5, 0.5),
            **kw,
        }
    )


def item(slot_id: str, geometry=None, **kw) -> SlotBatchItem:
    return SlotBatchItem.model_validate({"slot_id": slot_id, "geometry": geometry or as_point(0.5, 0.5), **kw})


def batch(mode: str, *items: SlotBatchItem) -> SlotBatchRequest:
    return SlotBatchRequest(mode=mode, slots=list(items))


def patch_location(service, key="bed", *, role=TenantRole.GROWER, tenant=TENANT, **fields):
    return service.patch_location(
        key, tenant_key=tenant, user_key=USER, role=role, patch=LocationPatch.model_validate(fields)
    )


def set_status(service, status, reason=None, *, key="bed", role=TenantRole.LEAD, tenant=TENANT):
    return service.change_bed_status(key, tenant_key=tenant, user_key=USER, role=role, bed_status=status, reason=reason)


# ── GP-API-011: the bed list ───────────────────────────────────────────────────────────────────────


class TestTheBedList:
    @pytest.fixture(autouse=True)
    def beds(self, world):
        _, repo, _ = world
        repo.locations["tent"] = make_location("tent", name="Tent", location_type_key="greenhouse")
        repo.locations["old"] = make_location("old", name="Old", geometry=rect(5, 5), bed_status=BedStatus.RETIRED)
        repo.counters["bed"] = BedCounters(
            active_plant_count=3, open_task_count=2, next_due_at=datetime(2026, 6, 1, tzinfo=UTC)
        )

    def keys(self, rows) -> list[str]:
        return sorted(loc.key for loc, _ in rows)

    def test_is_bed_keeps_the_bed_types_and_attaches_counters(self, world) -> None:
        service, _, _ = world
        rows = service.list_beds(SITE, tenant_key=TENANT, is_bed=True, bed_status=None)

        assert self.keys(rows) == ["bed", "old"]
        by_key = {loc.key: counters for loc, counters in rows}
        assert by_key["bed"].active_plant_count == 3 and by_key["bed"].open_task_count == 2
        assert by_key["old"] == BedCounters()  # a bed without plants or tasks reads zero, not absent

    def test_is_bed_false_is_the_complement(self, world) -> None:
        service, _, _ = world
        assert self.keys(service.list_beds(SITE, tenant_key=TENANT, is_bed=False, bed_status=None)) == ["tent"]

    def test_bed_status_filters(self, world) -> None:
        service, _, _ = world
        rows = service.list_beds(SITE, tenant_key=TENANT, is_bed=True, bed_status=BedStatus.RETIRED)
        assert self.keys(rows) == ["old"]

    def test_a_status_filter_alone_lists_beds_only(self, world) -> None:
        """L3 of the review: ``bed_status`` is a property of beds; the tent (default ``active``) is not one."""
        service, _, _ = world
        rows = service.list_beds(SITE, tenant_key=TENANT, is_bed=None, bed_status=BedStatus.ACTIVE)
        assert self.keys(rows) == ["bed"]

    def test_a_plain_listing_carries_no_counters(self, world) -> None:
        service, _, _ = world
        rows = service.list_beds(SITE, tenant_key=TENANT, is_bed=None, bed_status=None)
        assert self.keys(rows) == ["bed", "old", "tent"] and all(counters is None for _, counters in rows)

    def test_a_foreign_site_is_a_404(self, world) -> None:
        service, _, _ = world
        with pytest.raises(NotFoundError):
            service.list_beds(SITE, tenant_key=OTHER_TENANT, is_bed=True, bed_status=None)


# ── GP-API-012: the summary ────────────────────────────────────────────────────────────────────────


class TestTheSummary:
    def test_a_bed_with_plants_is_planted_and_carries_its_counters(self, world) -> None:
        service, repo, _ = world
        repo.counters["bed"] = BedCounters(active_plant_count=2, species_keys=["sp_a", "sp_b"], open_task_count=1)

        view = service.get_summary("bed", tenant_key=TENANT)

        assert view.season_state == "planted" and view.is_bed is True
        assert view.counters.species_keys == ["sp_a", "sp_b"]

    def test_a_bed_without_plants_is_empty(self, world) -> None:
        service, _, _ = world
        assert service.get_summary("bed", tenant_key=TENANT).season_state == "empty"

    def test_a_location_of_a_non_bed_type_says_so(self, world) -> None:
        service, repo, _ = world
        repo.locations["tent"] = make_location("tent", location_type_key="greenhouse")
        assert service.get_summary("tent", tenant_key=TENANT).is_bed is False

    @pytest.mark.parametrize("key", ["bed", "missing"])
    def test_a_foreign_and_an_absent_location_answer_alike(self, world, key) -> None:
        service, _, _ = world
        with pytest.raises(NotFoundError) as exc:
            service.get_summary(key, tenant_key=OTHER_TENANT)
        assert exc.value.status_code == 404


# ── GP-API-010: PATCH /locations/{key} ─────────────────────────────────────────────────────────────


class TestPatchingALocation:
    def test_a_note_changes_the_document_and_not_the_plan_revision(self, world) -> None:
        service, repo, site = world
        stored, plan_revision = patch_location(service, notes="Tomatoes under the roof")

        assert stored.notes == "Tomatoes under the roof"
        assert plan_revision == revision(site) == 5
        assert repo.applied == [] and repo.field_updates == [("bed", {"notes": "Tomatoes under the roof"})]

    def test_only_the_changed_columns_are_written(self, world) -> None:
        service, repo, _ = world
        patch_location(service, notes="same", sun_exposure="full_sun")
        patch_location(service, notes="same", sun_exposure="full_sun")  # nothing changed the second time

        assert repo.field_updates == [("bed", {"notes": "same", "sun_exposure": "full_sun"})]

    def test_null_clears_what_can_be_cleared(self, world) -> None:
        service, repo, _ = world
        patch_location(service, notes="x")
        patch_location(service, notes=None)

        assert repo.field_updates[-1] == ("bed", {"notes": None})
        assert repo.locations["bed"].notes is None

    def test_null_is_refused_where_nothing_can_be_cleared(self) -> None:
        with pytest.raises(ValueError, match="cannot be null"):
            LocationPatch.model_validate({"name": None})
        with pytest.raises(ValueError, match="at least one field"):
            LocationPatch.model_validate({})

    def test_a_geometry_goes_through_the_plan_and_raises_the_revision(self, world) -> None:
        service, repo, site = world
        stored, plan_revision = patch_location(service, geometry=rect(4, 4, 3, 2))

        assert plan_revision == revision(site) == 6
        assert stored.area_m2 == 6.0 and stored.bbox == (4.0, 4.0, 7.0, 6.0)
        assert len(repo.applied) == 1 and repo.field_updates == []

    def test_a_geometry_outside_the_boundary_is_refused_and_persists_nothing(self, world) -> None:
        service, repo, site = world
        with pytest.raises(PlanValidationError) as exc:
            patch_location(service, geometry=rect(9.5, 9.5))

        assert code_of(exc) == "geometry.outside_parent"
        assert repo.applied == [] and revision(site) == 5 and repo.locations["bed"].geometry.origin == (1, 1)

    def test_a_geometry_overlapping_a_neighbour_is_refused(self, world) -> None:
        service, repo, _ = world
        repo.locations["next"] = make_location("next", geometry=rect(5, 5))
        with pytest.raises(PlanValidationError) as exc:
            patch_location(service, "next", geometry=rect(1.5, 1))
        assert code_of(exc) == "bed.overlap" and repo.applied == []

    def test_a_locked_bed_cannot_be_moved_but_can_be_annotated(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"locked": True})

        with pytest.raises(PlanValidationError) as exc:
            patch_location(service, geometry=rect(4, 4))
        assert code_of(exc) == "object.locked" and repo.applied == []

        patch_location(service, notes="care is not structure")  # GP-NFR-007: a lock guards structure only
        assert repo.field_updates == [("bed", {"notes": "care is not structure"})]

    def test_lifting_the_lock_and_moving_in_one_patch_works(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"locked": True})
        stored, _ = patch_location(service, locked=False, geometry=rect(4, 4))
        assert stored.locked is False and stored.geometry.origin == (4, 4) and len(repo.applied) == 1

    def test_locking_and_moving_in_one_patch_moves_first(self, world) -> None:
        service, repo, _ = world
        stored, _ = patch_location(service, locked=True, geometry=rect(4, 4))
        assert stored.locked is True and stored.geometry.origin == (4, 4)

    def test_lock_and_drawing_order_are_structure_and_raise_the_revision(self, world) -> None:
        """M2 of the review: the batch's ``set_locked`` / ``set_z_order`` bump the revision; the PATCH must too."""
        service, repo, site = world
        stored, plan_revision = patch_location(service, locked=True, z_order=7)

        assert (stored.locked, stored.z_order, plan_revision) == (True, 7, 6)
        assert repo.field_updates == []

    def test_a_patch_that_repeats_the_stored_structure_changes_no_revision(self, world) -> None:
        service, repo, site = world
        _, plan_revision = patch_location(service, locked=False, z_order=0, geometry=rect(1, 1, 2, 1))
        assert plan_revision == 5 and repo.applied == []

    def test_the_lock_itself_can_be_lifted(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"locked": True})
        patch_location(service, locked=False)
        assert repo.locations["bed"].locked is False

    def test_a_rename_rederives_the_path(self, world) -> None:
        service, repo, _ = world
        patch_location(service, name="Bed Seven")
        (_, fields) = repo.field_updates[0]
        assert fields["name"] == "Bed Seven" and fields["path"] == "bed_seven"

    def test_a_soil_profile_is_stored_whole(self, world) -> None:
        service, repo, _ = world
        patch_location(service, soil_profile={"soil_texture": "loam", "ph": 6.5})
        assert repo.locations["bed"].soil_profile.ph == 6.5
        assert repo.field_updates[0][1]["soil_profile"]["soil_texture"] == "loam"

    def test_site_conditions_are_stored_whole_and_null_clears_them(self, world) -> None:
        service, repo, _ = world
        patch_location(service, site_conditions={"sun_profile": {"sun_window": "morning"}, "wind_exposure": "exposed"})

        stored = repo.locations["bed"].site_conditions
        assert stored is not None and stored.sun_profile.sun_window == "morning"
        assert repo.field_updates[0][1]["site_conditions"]["wind_exposure"] == "exposed"

        patch_location(service, site_conditions=None)
        assert repo.locations["bed"].site_conditions is None
        assert repo.field_updates[-1] == ("bed", {"site_conditions": None})

    @pytest.mark.parametrize(
        "bad",
        [
            {"slope_deg": 120},
            {"aspect_deg": 360},
            {"access_sides": ["N", "N"]},
            {"wind_exposure": "gale"},
            {"sun_profile": {"direct_sun_hours_summer": 30}},
            {"unknown_field_is_ignored_but_the_rest": 1, "flags": ["root_competition", "root_competition"]},
        ],
    )
    def test_an_invalid_site_condition_is_refused_at_the_body(self, bad) -> None:
        with pytest.raises(ValueError, match="site_conditions"):
            LocationPatch.model_validate({"site_conditions": bad})

    def test_a_changed_frost_risk_moves_the_legacy_boolean_with_it(self, world) -> None:
        service, repo, _ = world
        patch_location(service, site_conditions={"microclimate": {"frost_risk": "high"}})

        assert repo.locations["bed"].frost_exposed is True
        assert repo.field_updates[0][1]["frost_exposed"] is True

        patch_location(service, site_conditions={"microclimate": {"frost_risk": "low"}})
        assert repo.locations["bed"].frost_exposed is False

        patch_location(service, site_conditions={"microclimate": {"frost_risk": "normal"}})
        assert repo.locations["bed"].frost_exposed is None  # normal says nothing: inherit from the site type

    def test_clearing_the_site_conditions_clears_a_stored_risk_and_its_boolean(self, world) -> None:
        service, repo, _ = world
        patch_location(service, site_conditions={"microclimate": {"frost_risk": "high"}})
        assert repo.locations["bed"].frost_exposed is True

        patch_location(service, site_conditions=None)

        assert repo.locations["bed"].site_conditions is None
        assert repo.locations["bed"].frost_exposed is None

    def test_clearing_nothing_stored_touches_no_boolean(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"frost_exposed": True})

        patch_location(service, site_conditions=None)

        assert repo.locations["bed"].frost_exposed is True

    def test_a_partial_site_condition_changes_only_the_keys_sent(self, world) -> None:
        """A PATCH ``{"wind_exposure": …}`` must not reset the sun window, the risk or the slope (review of WP 3.9)."""
        service, repo, _ = world
        patch_location(
            service,
            site_conditions={
                "sun_profile": {"sun_window": "morning", "foliage_shade_in_summer": True},
                "microclimate": {"frost_risk": "high", "cold_air_pocket": True},
                "slope_deg": 12.5,
                "flags": ["root_competition"],
            },
        )

        patch_location(
            service,
            site_conditions={"wind_exposure": "exposed", "sun_profile": {"direct_sun_hours_summer": 5.5}},
        )

        stored = repo.locations["bed"].site_conditions
        assert stored is not None
        assert stored.wind_exposure == "exposed"
        assert (stored.sun_profile.sun_window, stored.sun_profile.foliage_shade_in_summer) == ("morning", True)
        assert stored.sun_profile.direct_sun_hours_summer == 5.5
        assert (stored.microclimate.frost_risk, stored.microclimate.cold_air_pocket) == ("high", True)
        assert stored.slope_deg == 12.5 and [flag.value for flag in stored.flags] == ["root_competition"]
        # the untouched risk leaves the legacy boolean alone
        assert repo.locations["bed"].frost_exposed is True

    def test_a_list_is_replaced_whole_and_an_empty_one_clears_it(self, world) -> None:
        service, repo, _ = world
        patch_location(service, site_conditions={"access_sides": ["N", "E"]})
        patch_location(service, site_conditions={"access_sides": []})

        assert repo.locations["bed"].site_conditions.access_sides == []

    @pytest.mark.parametrize(
        "bad",
        [
            {"wind_exposures": "exposed"},
            {"sun_profile": {"sun_windows": "morning"}},
            {"microclimate": {"frost": "high"}},
        ],
    )
    def test_a_misspelt_key_is_refused_instead_of_dropped(self, bad) -> None:
        with pytest.raises(ValueError, match="site_conditions"):
            LocationPatch.model_validate({"site_conditions": bad})

    def test_an_unchanged_frost_risk_leaves_the_boolean_alone(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"frost_exposed": True})

        patch_location(service, site_conditions={"sun_profile": {"sun_window": "midday"}})

        assert repo.locations["bed"].frost_exposed is True
        assert "frost_exposed" not in repo.field_updates[-1][1]

    @staticmethod
    def _migrated_protected_bed(repo) -> None:
        """What v0098 leaves for ``frost_exposed = false`` (#2464): the boolean plus ``frost_risk = normal``."""
        repo.locations["bed"] = repo.locations["bed"].model_copy(
            update={
                "frost_exposed": False,
                "site_conditions": SiteConditions(microclimate=Microclimate(frost_risk=FrostRisk.NORMAL)),
            }
        )

    @pytest.mark.parametrize(
        "sent",
        [
            {"sun_profile": {"sun_window": "midday"}},
            {"microclimate": {"frost_risk": "normal"}},  # the risk the form shows, sent back unchanged
            {"microclimate": {"cold_air_pocket": True}},
        ],
    )
    def test_a_migrated_protected_bed_keeps_its_protection_on_the_next_save(self, world, sent) -> None:
        """#2464 (4): ``normal`` clears the boolean only as a *change*, so saving a migrated bed keeps ``False``."""
        service, repo, _ = world
        self._migrated_protected_bed(repo)

        patch_location(service, site_conditions=sent)

        assert repo.locations["bed"].frost_exposed is False
        # a body that repeats the stored value writes no column at all
        assert all("frost_exposed" not in columns for _, columns in repo.field_updates)
        assert repo.locations["bed"].site_conditions.microclimate.frost_risk is FrostRisk.NORMAL

    def test_a_migrated_protected_bed_changed_away_and_back_to_normal_inherits_again(self, world) -> None:
        """#2464 (4), the documented edge: a deliberate change *to* ``normal`` means "no override" (#2454 item 2)."""
        service, repo, _ = world
        self._migrated_protected_bed(repo)

        patch_location(service, site_conditions={"microclimate": {"frost_risk": "high"}})
        patch_location(service, site_conditions={"microclimate": {"frost_risk": "normal"}})

        assert repo.locations["bed"].frost_exposed is None

    def test_a_viewer_is_refused_before_anything_is_looked_at(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(ForbiddenError):
            patch_location(service, role=TenantRole.VIEWER, notes="x")
        assert repo.field_updates == [] and repo.applied == []

    @pytest.mark.parametrize("key", ["bed", "missing"])
    def test_a_foreign_and_an_absent_location_answer_alike_and_write_nothing(self, world, key) -> None:
        service, repo, site = world
        with pytest.raises(NotFoundError):
            patch_location(service, key, tenant=OTHER_TENANT, notes="x", geometry=rect(4, 4))
        assert repo.field_updates == [] and repo.applied == [] and revision(site) == 5


class TestTheIrrigationZoneReference:
    """L1 of #2326: the zone is resolved under the caller's tenant and must belong to the location's site."""

    def test_the_tenants_zone_of_the_same_site_is_stored(self, world) -> None:
        service, repo, _ = world
        patch_location(service, irrigation_zone_key="zone_1")
        assert repo.locations["bed"].irrigation_zone_key == "zone_1"

    def test_another_tenants_zone_reads_exactly_like_an_unknown_one(self, world) -> None:
        service, repo, _ = world
        repo.zones["zone_foreign"] = (OTHER_TENANT, SITE)
        errors = []
        for zone in ("zone_foreign", "zone_nowhere"):
            with pytest.raises(PlanValidationError) as exc:
                patch_location(service, irrigation_zone_key=zone)
            errors.append(exc.value.details)
        assert errors[0] == errors[1] and errors[0][0]["code"] == "reference.not_found"
        assert repo.field_updates == []

    def test_a_zone_of_another_site_of_the_same_tenant_is_refused(self, world) -> None:
        service, repo, _ = world
        repo.zones["zone_2"] = (TENANT, "site_other")
        with pytest.raises(PlanValidationError) as exc:
            patch_location(service, irrigation_zone_key="zone_2")
        assert code_of(exc) == "reference.not_found" and repo.field_updates == []

    def test_null_detaches_the_zone_without_a_lookup(self, world) -> None:
        service, repo, _ = world
        patch_location(service, irrigation_zone_key="zone_1")
        patch_location(service, irrigation_zone_key=None)
        assert repo.locations["bed"].irrigation_zone_key is None


class TestTheSubstrateReference:
    @pytest.mark.parametrize("substrate", ["sub_global", "sub_own"])
    def test_a_catalogue_or_own_substrate_is_stored(self, world, substrate) -> None:
        service, repo, _ = world
        patch_location(service, soil_profile={"substrate_key": substrate})
        assert repo.locations["bed"].soil_profile.substrate_key == substrate

    @pytest.mark.parametrize("substrate", ["sub_foreign", "sub_nowhere"])
    def test_a_foreign_or_unknown_substrate_is_one_error(self, world, substrate) -> None:
        service, repo, _ = world
        with pytest.raises(PlanValidationError) as exc:
            patch_location(service, soil_profile={"substrate_key": substrate})
        assert code_of(exc) == "reference.not_found" and repo.field_updates == []


# ── GP-API-018: the status transition ──────────────────────────────────────────────────────────────


class TestTheBedStatus:
    def test_retiring_an_empty_bed_writes_the_status_the_care_event_and_the_audit_gp_acc_015(self, world) -> None:
        service, repo, site = world
        stored, plan_revision = set_status(service, BedStatus.RETIRED, "Dismantled for the shed")

        assert stored.bed_status is BedStatus.RETIRED and plan_revision == revision(site) == 6
        (event,) = repo.care_events
        assert (event.category, event.reason, event.tenant_key) == (
            "bed_status_change",
            "Dismantled for the shed",
            TENANT,
        )
        assert (event.location_key, event.site_key, event.performed_by_user_key) == ("bed", SITE, USER)
        (write,) = repo.applied
        assert write.audit == [{"op": "retire", "entity": "location", "key": "bed", "summary": "Bed"}]
        assert write.care_events == [event]

    def test_the_retired_bed_stays_on_the_plan_as_empty_gp_acc_015(self, world) -> None:
        service, repo, _ = world
        set_status(service, BedStatus.RETIRED, "Dismantled")

        view = GardenPlanService(service._sites, repo).get_plan(SITE, tenant_key=TENANT)

        assert view.season_states == {"bed": "empty"}  # never "fallow" (§7.4): that needs a rotation plan entry
        assert [(loc.key, loc.bed_status) for loc in view.locations] == [("bed", BedStatus.RETIRED)]

    def test_planned_cannot_be_the_target_of_an_active_bed_gp_acc_015(self, world) -> None:
        service, repo, site = world
        with pytest.raises(PlanError) as exc:
            set_status(service, BedStatus.PLANNED)

        assert code_of(exc) == "bed_status.invalid_transition" and exc.value.status_code == 422
        assert repo.applied == [] and repo.care_events == [] and revision(site) == 5

    @pytest.mark.parametrize(
        ("current", "target", "allowed"),
        [
            (BedStatus.PLANNED, BedStatus.ACTIVE, True),
            (BedStatus.PLANNED, BedStatus.RETIRED, True),
            (BedStatus.ACTIVE, BedStatus.RETIRED, True),
            (BedStatus.RETIRED, BedStatus.ACTIVE, True),
            (BedStatus.ACTIVE, BedStatus.PLANNED, False),
            (BedStatus.RETIRED, BedStatus.PLANNED, False),
            (BedStatus.ACTIVE, BedStatus.ACTIVE, False),
            (BedStatus.PLANNED, BedStatus.PLANNED, False),
        ],
    )
    def test_the_transition_table_of_7_4(self, world, current, target, allowed) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"bed_status": current})
        if allowed:
            stored, _ = set_status(service, target, "reason")
            assert stored.bed_status is target
        else:
            with pytest.raises(PlanError) as exc:
                set_status(service, target, "reason")
            assert code_of(exc) == "bed_status.invalid_transition" and repo.applied == []

    def test_retiring_needs_a_reason(self, world) -> None:
        service, repo, _ = world
        for reason in (None, "   "):
            with pytest.raises(PlanError) as exc:
                set_status(service, BedStatus.RETIRED, reason)
            assert code_of(exc) == "bed_status.reason_required"
        assert repo.applied == []

    def test_a_bed_with_plants_cannot_be_retired_v09(self, world) -> None:
        service, repo, _ = world
        repo.active_plants = 2
        with pytest.raises(PlanError) as exc:
            set_status(service, BedStatus.RETIRED, "gone")
        assert exc.value.status_code == 409
        assert exc.value.details[0]["active_plant_count"] == 2 and repo.applied == []

    def test_a_grower_may_not_retire_nor_reactivate(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(ForbiddenError):
            set_status(service, BedStatus.RETIRED, "x", role=TenantRole.GROWER)
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"bed_status": BedStatus.RETIRED})
        with pytest.raises(ForbiddenError):
            set_status(service, BedStatus.ACTIVE, role=TenantRole.GROWER)
        assert repo.applied == []

    def test_a_grower_may_activate_a_planned_bed(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"bed_status": BedStatus.PLANNED})
        stored, _ = set_status(service, BedStatus.ACTIVE, role=TenantRole.GROWER)
        assert stored.bed_status is BedStatus.ACTIVE
        assert repo.applied[0].audit == []  # activating changes no structure worth an audit row

    def test_a_lead_reactivates_a_retired_bed_and_it_is_audited(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"bed_status": BedStatus.RETIRED})
        stored, _ = set_status(service, BedStatus.ACTIVE)
        assert stored.bed_status is BedStatus.ACTIVE and repo.applied[0].audit[0]["op"] == "reactivate"

    def test_a_viewer_is_refused(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(ForbiddenError):
            set_status(service, BedStatus.RETIRED, "x", role=TenantRole.VIEWER)
        assert repo.applied == []

    def test_only_a_bed_has_a_bed_status(self, world) -> None:
        service, repo, _ = world
        repo.locations["tent"] = make_location("tent", location_type_key="greenhouse")
        with pytest.raises(PlanError) as exc:
            set_status(service, BedStatus.RETIRED, "x", key="tent")
        assert code_of(exc) == "bed_status.not_a_bed" and repo.applied == []

    @pytest.mark.parametrize("key", ["bed", "missing"])
    def test_a_foreign_and_an_absent_bed_answer_alike_and_write_nothing(self, world, key) -> None:
        service, repo, _ = world
        with pytest.raises(NotFoundError):
            set_status(service, BedStatus.RETIRED, "x", key=key, tenant=OTHER_TENANT)
        assert repo.applied == [] and repo.care_events == []

    def test_a_stale_site_revision_is_a_conflict_not_a_lost_update(self, world) -> None:
        service, repo, site = world
        original = repo.apply_plan_batch

        def raced(write):
            site.plan.plan_revision += 1  # somebody saved between our read and our write
            return original(write)

        repo.apply_plan_batch = raced
        with pytest.raises(PlanError) as exc:
            set_status(service, BedStatus.RETIRED, "x")
        assert code_of(exc) == "plan.revision_conflict" and repo.care_events == []

    def test_through_patch_the_same_rules_apply_and_the_same_status_is_a_no_op(self, world) -> None:
        service, repo, _ = world
        patch_location(service, bed_status="active", notes="x")  # equal to the stored one: not a transition
        assert repo.care_events == []

        with pytest.raises(ForbiddenError):
            patch_location(service, role=TenantRole.GROWER, bed_status="retired", status_reason="x")
        with pytest.raises(PlanError) as exc:
            patch_location(service, role=TenantRole.LEAD, bed_status="planned")
        assert code_of(exc) == "bed_status.invalid_transition"

        patch_location(service, role=TenantRole.LEAD, bed_status="retired", status_reason="Gone", notes="n")
        assert repo.locations["bed"].bed_status is BedStatus.RETIRED and repo.locations["bed"].notes == "n"
        assert [e.reason for e in repo.care_events] == ["Gone"]

    def test_a_status_changed_between_the_read_and_the_write_is_a_409_not_an_overwrite(self, world) -> None:
        """H1 of the review: a grower's ``planned -> active`` must not overwrite a lead's ``planned -> retired``."""
        service, repo, site = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"bed_status": BedStatus.PLANNED})
        real = repo.apply_plan_batch

        def after_the_lead(write):
            repo.locations["bed"] = repo.locations["bed"].model_copy(update={"bed_status": BedStatus.RETIRED})
            return real(write)

        repo.apply_plan_batch = after_the_lead
        with pytest.raises(PlanError) as exc:
            set_status(service, BedStatus.ACTIVE, role=TenantRole.GROWER)

        assert exc.value.status_code == 409 and code_of(exc) == "bed_status.changed"
        assert repo.locations["bed"].bed_status is BedStatus.RETIRED and repo.care_events == []

    def test_the_write_names_the_status_it_was_validated_from(self, world) -> None:
        service, repo, _ = world
        set_status(service, BedStatus.RETIRED, "x")
        assert repo.applied[0].status_from == {"bed": "active"}

    def test_a_status_and_a_geometry_in_one_patch_are_refused_before_anything_is_written(self, world) -> None:
        service, repo, site = world
        with pytest.raises(PlanError) as exc:
            patch_location(service, role=TenantRole.LEAD, bed_status="retired", status_reason="x", geometry=rect(4, 4))
        assert code_of(exc) == "patch.status_with_geometry" and exc.value.status_code == 422
        assert repo.applied == [] and repo.field_updates == [] and revision(site) == 5

    def test_a_patch_refused_on_its_status_writes_no_field(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(PlanError):
            patch_location(service, role=TenantRole.LEAD, bed_status="planned", notes="must not land")
        assert repo.field_updates == [] and repo.applied == []


# ── DELETE /locations/{key} ────────────────────────────────────────────────────────────────────────


class TestDeletingALocation:
    def delete(self, service, key="bed", *, role=TenantRole.LEAD, tenant=TENANT):
        return service.delete_location(key, tenant_key=tenant, user_key=USER, role=role)

    def test_a_lead_deletes_with_an_audit_row_and_a_revision_bump(self, world) -> None:
        service, repo, site = world
        self.delete(service)

        assert "bed" not in repo.locations and revision(site) == 6
        assert repo.applied[0].location_deletes == ["bed"]
        assert repo.applied[0].audit[0]["op"] == "delete"

    def test_a_bed_with_plants_is_a_409_with_the_count_gp_acc_012(self, world) -> None:
        service, repo, site = world
        repo.active_plants = 2
        with pytest.raises(PlanError) as exc:
            self.delete(service)

        assert exc.value.status_code == 409 and code_of(exc) == "location.has_active_plants"
        assert exc.value.details[0]["active_plant_count"] == 2
        assert "bed" in repo.locations and repo.applied == [] and revision(site) == 5

    def test_what_is_below_goes_with_it(self, world) -> None:
        service, repo, _ = world
        repo.locations["child"] = make_location("child", parent_location_key="bed")
        self.delete(service)
        assert sorted(repo.applied[0].location_deletes) == ["bed", "child"]

    def test_a_grower_may_not_delete(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(ForbiddenError):
            self.delete(service, role=TenantRole.GROWER)
        assert "bed" in repo.locations and repo.applied == []

    @pytest.mark.parametrize("key", ["bed", "missing"])
    def test_a_foreign_and_an_absent_location_answer_alike_and_delete_nothing(self, world, key) -> None:
        service, repo, _ = world
        with pytest.raises(NotFoundError):
            self.delete(service, key, tenant=OTHER_TENANT)
        assert "bed" in repo.locations and repo.applied == []

    def test_a_locked_bed_is_not_deleted(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"locked": True})
        with pytest.raises(PlanValidationError) as exc:
            self.delete(service)
        assert code_of(exc) == "object.locked" and "bed" in repo.locations


# ── GP-API-013: garden objects ─────────────────────────────────────────────────────────────────────


def tree(**kw) -> CreateGardenObjectData:
    return CreateGardenObjectData.model_validate(
        {
            "object_type": "tree",
            "label": "Apple",
            "geometry": {"kind": "circle", "origin": [8, 8], "radius_m": 1.0},
            "props": {"crown_radius_m": 1.0},
            **kw,
        }
    )


def create_object(service, data=None, *, role=TenantRole.GROWER, tenant=TENANT, site=SITE):
    return service.create_garden_object(site, tenant_key=tenant, user_key=USER, role=role, data=data or tree())


class TestGardenObjects:
    def test_create_stores_the_object_on_the_path_site_and_raises_the_revision(self, world) -> None:
        service, repo, site = world
        created = create_object(service)

        assert created.key in repo.objects and created.site_key == SITE and created.created_by == USER
        assert revision(site) == 6

    def test_the_body_cannot_name_another_site(self) -> None:
        with pytest.raises(ValueError, match="site_key"):
            tree(site_key="site_foreign")

    def test_create_outside_the_boundary_is_refused_unless_it_is_scenery(self, world) -> None:
        service, repo, _ = world
        far = {"kind": "circle", "origin": [30, 30], "radius_m": 1.0}
        with pytest.raises(PlanValidationError) as exc:
            create_object(service, tree(geometry=far))
        assert code_of(exc) == "geometry.outside_parent" and repo.objects == {}

        create_object(service, tree(geometry=far, off_site=True))
        assert len(repo.objects) == 1

    def test_an_unknown_parent_is_one_reference_error(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(PlanValidationError) as exc:
            create_object(service, tree(parent_location_key="nowhere"))
        assert code_of(exc) == "reference.not_found" and repo.objects == {}

    def test_a_viewer_may_not_create(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(ForbiddenError):
            create_object(service, role=TenantRole.VIEWER)
        assert repo.objects == {}

    @pytest.mark.parametrize("site", [SITE, "site_foreign", "missing"])
    def test_create_on_a_foreign_or_absent_site_is_the_same_404(self, world, site) -> None:
        service, repo, _ = world
        with pytest.raises(NotFoundError):
            create_object(service, tenant=OTHER_TENANT if site == SITE else TENANT, site=site)
        assert repo.objects == {} and repo.applied == []

    def test_list_and_get_are_scoped_to_the_tenant(self, world) -> None:
        service, _, _ = world
        created = create_object(service)

        assert [o.key for o in service.list_garden_objects(SITE, tenant_key=TENANT)] == [created.key]
        assert service.get_garden_object(created.key, tenant_key=TENANT).label == "Apple"
        with pytest.raises(NotFoundError):
            service.list_garden_objects(SITE, tenant_key=OTHER_TENANT)
        with pytest.raises(NotFoundError):
            service.get_garden_object(created.key, tenant_key=OTHER_TENANT)

    def patch(self, service, key, *, role=TenantRole.GROWER, tenant=TENANT, **fields):
        return service.patch_garden_object(
            key, tenant_key=tenant, user_key=USER, role=role, patch=GardenObjectPatch.model_validate(fields)
        )

    def test_patch_changes_label_and_geometry_in_one_revision_step(self, world) -> None:
        service, _, site = world
        created = create_object(service)
        before = revision(site)

        updated = self.patch(
            service, created.key, label="Pear", geometry={"kind": "circle", "origin": [7, 7], "radius_m": 1.5}
        )

        assert updated.label == "Pear" and updated.geometry.origin == (7, 7)
        assert revision(site) == before + 1

    def test_a_locked_object_is_not_moved_but_unlock_and_move_in_one_patch_works(self, world) -> None:
        service, _, _ = world
        created = create_object(service, tree(locked=True))
        move = {"kind": "circle", "origin": [7, 7], "radius_m": 1.0}

        with pytest.raises(PlanValidationError) as exc:
            self.patch(service, created.key, geometry=move)
        assert code_of(exc) == "object.locked"

        moved = self.patch(service, created.key, geometry=move, locked=False)
        assert moved.geometry.origin == (7, 7) and moved.locked is False

    def test_patch_can_lock_and_move_at_once(self, world) -> None:
        service, _, _ = world
        created = create_object(service)
        moved = self.patch(
            service, created.key, locked=True, geometry={"kind": "circle", "origin": [7, 7], "radius_m": 1.0}
        )
        assert moved.locked is True and moved.geometry.origin == (7, 7)

    def test_patch_props_keep_their_class(self, world) -> None:
        service, _, _ = world
        created = create_object(service)
        updated = self.patch(service, created.key, props={"crown_radius_m": 1.0, "height_m": 6.0})
        assert updated.props.height_m == 6.0 and updated.props.object_type == "tree"

    def test_patch_is_refused_for_a_viewer_and_for_a_foreign_object(self, world) -> None:
        service, repo, site = world
        created = create_object(service)
        before = revision(site)

        with pytest.raises(ForbiddenError):
            self.patch(service, created.key, role=TenantRole.VIEWER, label="x")
        with pytest.raises(NotFoundError):
            self.patch(service, created.key, tenant=OTHER_TENANT, label="x")
        assert repo.objects[created.key].label == "Apple" and revision(site) == before

    def test_delete_is_the_leads_and_audited(self, world) -> None:
        service, repo, _ = world
        created = create_object(service)

        with pytest.raises(ForbiddenError):
            service.delete_garden_object(created.key, tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER)
        assert created.key in repo.objects

        service.delete_garden_object(created.key, tenant_key=TENANT, user_key=USER, role=TenantRole.LEAD)
        assert created.key not in repo.objects
        assert repo.applied[-1].audit[0]["entity"] == "garden_object"

    def test_delete_of_a_foreign_object_is_a_404_and_deletes_nothing(self, world) -> None:
        service, repo, _ = world
        created = create_object(service)
        with pytest.raises(NotFoundError):
            service.delete_garden_object(created.key, tenant_key=OTHER_TENANT, user_key=USER, role=TenantRole.LEAD)
        assert created.key in repo.objects


# ── GP-API-014: PATCH /slots/{key} ─────────────────────────────────────────────────────────────────


def patch_slot(service, key="s1", *, role=TenantRole.GROWER, tenant=TENANT, **fields):
    return service.patch_slot(key, tenant_key=tenant, role=role, patch=SlotPatch.model_validate(fields))


class TestPatchingASlot:
    @pytest.fixture(autouse=True)
    def slots(self, world):
        _, repo, _ = world
        repo.slots = [slot("s1", "BED_P1"), slot("s2", "BED_P2", geometry=as_point(1.5, 0.5))]

    def test_a_correction_inside_the_bed_is_stored_as_an_editor_geometry(self, world) -> None:
        service, repo, site = world
        updated = patch_slot(service, geometry=as_point(1.0, 0.25))

        assert updated.geometry.origin == (1.0, 0.25) and updated.geometry_source == "editor"
        assert revision(site) == 5 and repo.applied == []  # slots live outside the plan revision (GP-NFR-007)

    def test_a_position_outside_the_bed_is_refused_v04(self, world) -> None:
        service, repo, _ = world
        before = list(repo.slots)
        with pytest.raises(PlanValidationError) as exc:
            patch_slot(service, geometry=as_point(2.6, 0.5))  # the bed is 2 x 1 m
        assert code_of(exc) == "slot.outside_bed" and repo.slots == before and repo.slot_field_updates == []

    def test_a_bed_that_is_not_drawn_has_no_frame_to_be_outside_of(self, world) -> None:
        service, repo, _ = world
        repo.locations["bed"] = repo.locations["bed"].model_copy(update={"geometry": None})
        assert patch_slot(service, geometry=as_point(9, 9)).geometry.origin == (9, 9)

    def test_capacity_changes_without_touching_the_geometry(self, world) -> None:
        service, _, _ = world
        updated = patch_slot(service, capacity_plants=4)
        assert updated.capacity_plants == 4 and updated.geometry.origin == (0.5, 0.5)

    def test_a_role_and_its_geometry_change_together_and_only_those_columns_are_written(self, world) -> None:
        service, repo, _ = world
        zone = as_zone((0, 0), (1, 0), (1, 1), (0, 1))
        updated = patch_slot(service, slot_role="zone", geometry=zone)

        assert updated.slot_role == "zone" and updated.geometry.kind == "polygon"
        ((key, fields),) = repo.slot_field_updates
        assert key == "s1" and set(fields) == {"slot_role", "geometry", "geometry_source"}

    def test_a_patch_that_changes_nothing_writes_nothing(self, world) -> None:
        service, repo, _ = world
        patch_slot(service, capacity_plants=1)
        assert repo.slot_field_updates == []

    def test_a_role_without_its_geometry_kind_is_refused(self, world) -> None:
        service, _, _ = world
        with pytest.raises(PlanValidationError):
            patch_slot(service, slot_role="zone")  # a zone needs a polygon

    def test_overlapping_zones_are_refused_v06(self, world) -> None:
        service, repo, _ = world
        repo.slots = [
            slot("z1", "BED_Z1", slot_role="zone", geometry=as_zone((0, 0), (1, 0), (1, 1), (0, 1))),
            slot("z2", "BED_Z2", slot_role="zone", geometry=as_zone((1.2, 0), (2, 0), (2, 1), (1.2, 1))),
        ]
        with pytest.raises(PlanValidationError) as exc:
            patch_slot(service, "z2", geometry=as_zone((0.5, 0), (2, 0), (2, 1), (0.5, 1)))
        assert code_of(exc) == "slot.overlap"

        ok = patch_slot(service, "z2", geometry=as_zone((1.0, 0), (2, 0), (2, 1), (1.0, 1)))  # touching edges only
        assert ok.geometry.points[0] == (1.0, 0)

    def test_an_archived_zone_does_not_block_a_new_one_f02(self, world) -> None:
        service, repo, _ = world
        repo.slots = [
            slot(
                "old",
                "BED_OLD",
                slot_role="zone",
                geometry=as_zone((0, 0), (1, 0), (1, 1), (0, 1)),
                archived_at=datetime(2025, 10, 1, tzinfo=UTC),
            ),
            slot("z2", "BED_Z2", slot_role="zone", geometry=as_zone((1.2, 0), (2, 0), (2, 1), (1.2, 1))),
        ]
        assert patch_slot(service, "z2", geometry=as_zone((0.2, 0), (2, 0), (2, 1), (0.2, 1))) is not None

    def test_an_occupied_slot_can_be_corrected(self, world) -> None:
        service, repo, _ = world
        repo.slots = [slot("s1", "BED_P1", occupied=True)]
        assert patch_slot(service, geometry=as_point(1, 0.5)).currently_occupied is True

    def test_a_viewer_is_refused(self, world) -> None:
        service, _, _ = world
        with pytest.raises(ForbiddenError):
            patch_slot(service, role=TenantRole.VIEWER, capacity_plants=2)

    @pytest.mark.parametrize("key", ["s1", "missing"])
    def test_a_foreign_and_an_absent_slot_answer_alike_and_write_nothing(self, world, key) -> None:
        service, repo, _ = world
        with pytest.raises(NotFoundError):
            patch_slot(service, key, tenant=OTHER_TENANT, capacity_plants=2)
        assert repo.slot_field_updates == []

    def test_adjacency_is_recomputed_after_a_change(self, world, monkeypatch) -> None:
        service, _, _ = world
        seen: list[str] = []
        monkeypatch.setattr(GardenResourceService, "_recompute_adjacency", lambda self, key: seen.append(key))
        patch_slot(service, capacity_plants=3)
        assert seen == ["bed"]


# ── GP-API-015: POST /locations/{key}/slots/batch ──────────────────────────────────────────────────


def run_batch(service, request, *, key="bed", role=TenantRole.GROWER, tenant=TENANT):
    return service.replace_slots(key, tenant_key=tenant, role=role, request=request)


class TestTheSlotBatch:
    @pytest.fixture(autouse=True)
    def slots(self, world):
        _, repo, _ = world
        repo.slots = [
            slot("free", "BED_FREE"),
            slot("busy", "BED_BUSY", occupied=True, geometry=as_point(1.5, 0.5)),
            slot("held", "BED_HELD", geometry=as_point(0.25, 0.25)),
            slot("hist", "BED_HIST", archived_at=datetime(2025, 10, 1, tzinfo=UTC)),
        ]
        repo.reserved = {"held"}

    def keys(self, repo) -> list[str]:
        return sorted(s.key for s in repo.slots)

    def test_replace_unoccupied_keeps_what_is_occupied_reserved_or_history(self, world) -> None:
        service, repo, _ = world
        result = run_batch(service, batch("replace_unoccupied", item("BED_N1"), item("BED_N2", as_point(1, 0.75))))

        assert result.deleted_count == 1 and result.kept_count == 3 and len(result.created_keys) == 2
        assert repo.slot_writes[0].delete_keys == ["free"]
        assert "free" not in self.keys(repo) and {"busy", "held", "hist"} <= set(self.keys(repo))

    def test_the_id_of_a_removed_slot_can_be_used_again(self, world) -> None:
        service, repo, _ = world
        run_batch(service, batch("replace_unoccupied", item("BED_FREE")))
        assert [s.slot_id for s in repo.slots].count("BED_FREE") == 1

    def test_append_keeps_everything(self, world) -> None:
        service, repo, _ = world
        result = run_batch(service, batch("append", item("BED_N1")))
        assert result.deleted_count == 0 and result.kept_count == 4 and len(repo.slots) == 5

    def test_an_id_taken_by_a_slot_that_stays_is_refused_v20(self, world) -> None:
        service, repo, _ = world
        before = list(repo.slots)
        with pytest.raises(PlanValidationError) as exc:
            run_batch(service, batch("replace_unoccupied", item("BED_BUSY")))
        detail = exc.value.details[0]
        assert detail["code"] == "slot.duplicate_id" and detail["index"] == 0
        assert repo.slots == before and repo.slot_writes == []

    def test_an_id_twice_in_the_request_is_refused_v20(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(PlanValidationError) as exc:
            run_batch(service, batch("append", item("BED_N1"), item("BED_N1")))
        assert exc.value.details[0]["index"] == 1 and repo.slot_writes == []

    def test_one_slot_outside_the_bed_refuses_the_whole_batch_v04(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(PlanValidationError) as exc:
            run_batch(service, batch("replace_unoccupied", item("BED_N1"), item("BED_N2", as_point(3.5, 0.5))))
        detail = exc.value.details[0]
        assert detail["code"] == "slot.outside_bed" and detail["index"] == 1
        assert repo.slot_writes == [] and "free" in self.keys(repo)

    def test_overlapping_zones_in_the_request_are_refused_v06(self, world) -> None:
        service, repo, _ = world
        a = as_zone((0, 0), (1.2, 0), (1.2, 1), (0, 1))
        b = as_zone((1.0, 0), (2, 0), (2, 1), (1.0, 1))
        with pytest.raises(PlanValidationError) as exc:
            run_batch(
                service, batch("append", item("BED_ZA", a, slot_role="zone"), item("BED_ZB", b, slot_role="zone"))
            )
        assert exc.value.details[0]["code"] == "slot.overlap" and repo.slot_writes == []

    def test_a_zone_over_a_zone_that_stays_is_refused_but_over_an_archived_one_it_is_not(self, world) -> None:
        service, repo, _ = world
        zone = as_zone((0, 0), (1, 0), (1, 1), (0, 1))
        repo.slots.append(slot("zk", "BED_ZK", slot_role="zone", geometry=zone))
        repo.slots.append(
            slot("zh", "BED_ZH", slot_role="zone", geometry=zone, archived_at=datetime(2025, 10, 1, tzinfo=UTC))
        )
        over = as_zone((0.5, 0), (1.5, 0), (1.5, 1), (0.5, 1))
        with pytest.raises(PlanValidationError) as exc:
            run_batch(service, batch("append", item("BED_ZN", over, slot_role="zone")))
        assert exc.value.details[0]["code"] == "slot.overlap"

        repo.slots = [s for s in repo.slots if s.key != "zk"]  # only the archived zone is left
        assert len(run_batch(service, batch("append", item("BED_ZN", over, slot_role="zone"))).created_keys) == 1

    def test_a_role_that_does_not_match_its_geometry_is_refused(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(PlanValidationError) as exc:
            run_batch(service, batch("append", item("BED_N1", slot_role="zone")))
        assert exc.value.details[0]["code"] == "geometry.invalid" and repo.slot_writes == []

    def test_more_than_2000_positions_are_refused(self, world) -> None:
        service, repo, _ = world
        many = [item(f"BED_M{i}") for i in range(2001)]
        with pytest.raises(PlanError) as exc:
            run_batch(service, batch("append", *many))
        assert code_of(exc) == "layout.too_many_positions" and repo.slot_writes == []

    def test_2000_positions_are_accepted(self, world) -> None:
        service, _, _ = world
        positions = [item(f"BED_M{i}", as_point((i % 40) * 0.05, (i // 40) * 0.01)) for i in range(2000)]
        assert len(run_batch(service, batch("append", *positions)).created_keys) == 2000

    def test_a_slot_that_became_occupied_meanwhile_aborts_the_batch(self, world) -> None:
        service, repo, _ = world
        original = repo.replace_slots

        def raced(write):
            repo.slots = [
                s.model_copy(update={"currently_occupied": True}) if s.key == "free" else s for s in repo.slots
            ]
            return original(write)

        repo.replace_slots = raced
        with pytest.raises(WriteConflictError):
            run_batch(service, batch("replace_unoccupied", item("BED_N1")))

    def test_an_id_taken_after_the_service_read_is_a_duplicate_from_the_index(self, world) -> None:
        service, repo, _ = world
        original = repo.replace_slots

        def raced(write):
            repo.slots.append(slot("late", "BED_N1"))
            return original(write)

        repo.replace_slots = raced
        with pytest.raises(DuplicateError):
            run_batch(service, batch("append", item("BED_N1")))

    def test_a_viewer_is_refused(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(ForbiddenError):
            run_batch(service, batch("append", item("BED_N1")), role=TenantRole.VIEWER)
        assert repo.slot_writes == []

    @pytest.mark.parametrize("key", ["bed", "missing"])
    def test_a_foreign_and_an_absent_bed_answer_alike_and_write_nothing(self, world, key) -> None:
        service, repo, _ = world
        with pytest.raises(NotFoundError):
            run_batch(service, batch("replace_unoccupied", item("BED_N1")), key=key, tenant=OTHER_TENANT)
        assert repo.slot_writes == [] and "free" in self.keys(repo)

    def test_the_site_quota_counts_the_slots_of_all_beds_not_of_one(self, world, monkeypatch) -> None:
        """M3 of the review: 8 000 slots per *site* (GP-NFR-017), not per bed."""
        from app.domain.services import garden_resource_service

        service, repo, _ = world
        repo.locations["other"] = make_location("other", name="Other", geometry=rect(5, 5))
        repo.slots += [slot(f"o{i}", f"OTHER_{i}", location_key="other") for i in range(3)]
        monkeypatch.setattr(garden_resource_service, "MAX_SLOTS_PER_SITE", 7)  # 3 active in "bed", 3 in "other"

        run_batch(service, batch("append", item("BED_N1")))  # 7 slots: at the limit
        with pytest.raises(PlanError) as exc:
            run_batch(service, batch("append", item("BED_N2", as_point(1, 0.5))))
        assert code_of(exc) == "plan.quota_exceeded"

    def test_replacing_frees_the_room_it_needs(self, world, monkeypatch) -> None:
        from app.domain.services import garden_resource_service

        service, repo, _ = world
        monkeypatch.setattr(garden_resource_service, "MAX_SLOTS_PER_SITE", 4)  # the bed holds 3 active + 1 archived
        result = run_batch(service, batch("replace_unoccupied", item("BED_N1")))  # one goes, one comes
        assert len(result.created_keys) == 1

    def test_the_batch_does_not_touch_the_plan_revision(self, world) -> None:
        service, repo, site = world
        run_batch(service, batch("replace_unoccupied", item("BED_N1")))
        assert revision(site) == 5 and repo.applied == []


# ── the tenant is never optional ───────────────────────────────────────────────────────────────────


def test_every_public_method_takes_the_tenant_keyword_only_without_a_default() -> None:
    import inspect

    methods = [
        (name, fn)
        for name, fn in inspect.getmembers(GardenResourceService, inspect.isfunction)
        if not name.startswith("_")
    ]
    assert len(methods) >= 12
    for name, fn in methods:
        parameter = inspect.signature(fn).parameters.get("tenant_key")
        assert parameter is not None, name
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is inspect.Parameter.empty, name


# ── GP-API-016: the layout preview ─────────────────────────────────────────────────────────────────


class TestThePlantingLayoutPreview:
    @staticmethod
    def entry():
        from app.common.enums import LayoutStrategy
        from app.domain.calculators.planting_layout_calculator import EntryLayout

        return EntryLayout(LayoutStrategy.GRID, spacing_cm=50)

    def test_it_computes_over_the_geometry_of_the_owned_bed_and_writes_nothing(self, world) -> None:
        service, repo, _ = world
        result = service.preview_planting_layout("bed", tenant_key=TENANT, entry=self.entry(), max_count=None)
        assert result.count > 0 and result.capacity_max == result.count
        assert repo.slot_writes == []

    def test_a_foreign_bed_and_an_absent_one_are_the_same_404_and_compute_nothing(self, world) -> None:
        service, repo, _ = world
        repo.locations["foreign_bed"] = make_location("foreign_bed", geometry=rect(1, 1, 2, 1)).model_copy(
            update={"site_key": "site_foreign"}
        )
        for key in ("foreign_bed", "nope"):
            with pytest.raises(NotFoundError) as exc:
                service.preview_planting_layout(key, tenant_key=TENANT, entry=self.entry(), max_count=None)
            assert exc.value.status_code == 404

    def test_an_empty_tenant_is_no_tenant(self, world) -> None:
        service, _, _ = world
        with pytest.raises(NotFoundError):
            service.preview_planting_layout("bed", tenant_key="", entry=self.entry(), max_count=None)

    def test_a_bed_without_geometry_is_a_422(self, world) -> None:
        service, repo, _ = world
        repo.locations["bare"] = make_location("bare")
        with pytest.raises(PlanError) as exc:
            service.preview_planting_layout("bare", tenant_key=TENANT, entry=self.entry(), max_count=None)
        assert code_of(exc) == "layout.bed_without_geometry"

    def test_the_tenant_is_keyword_only_without_a_default(self) -> None:
        import inspect

        parameter = inspect.signature(GardenResourceService.preview_planting_layout).parameters["tenant_key"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty


class TestTheAdjacencyTrigger:
    """GP-API-014/015, GP-NFR-016: a stored slot change asks for the recompute of its bed — a refusal does not."""

    @pytest.fixture(autouse=True)
    def slots(self, world):
        _, repo, _ = world
        repo.slots = [slot("s1", "BED_P1"), slot("s2", "BED_P2", geometry=as_point(1.5, 0.5))]

    def test_a_geometry_correction_dispatches_the_bed(self, world) -> None:
        service, repo, _ = world
        patch_slot(service, geometry=as_point(1.0, 0.25))
        assert repo.dispatched == ["bed"]

    def test_a_patch_that_changes_nothing_dispatches_nothing(self, world) -> None:
        service, repo, _ = world
        patch_slot(service, capacity_plants=1)
        assert repo.dispatched == []

    def test_a_refused_patch_dispatches_nothing(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(PlanValidationError):
            patch_slot(service, geometry=as_point(2.6, 0.5))
        with pytest.raises(NotFoundError):
            patch_slot(service, tenant=OTHER_TENANT, geometry=as_point(1.0, 0.25))
        assert repo.dispatched == []

    def test_the_batch_dispatches_the_bed_once(self, world) -> None:
        service, repo, _ = world
        run_batch(service, batch("append", item("BED_N1"), item("BED_N2", as_point(1, 0.75))))
        assert repo.dispatched == ["bed"]

    def test_a_refused_batch_dispatches_nothing(self, world) -> None:
        service, repo, _ = world
        with pytest.raises(PlanValidationError):
            run_batch(service, batch("append", item("BED_P1")))  # V-20: the id is taken
        assert repo.dispatched == []

    def test_a_broker_that_is_down_does_not_undo_the_stored_slot(self, world) -> None:
        _, repo, _ = world

        def down(_key: str) -> None:
            raise ConnectionError("broker down")

        service = GardenResourceService(
            repo._sites, repo, FakeObjects(repo), GardenPlanService(repo._sites, repo), dispatch_adjacency=down
        )
        assert patch_slot(service, geometry=as_point(1.0, 0.25)).geometry.origin == (1.0, 0.25)
