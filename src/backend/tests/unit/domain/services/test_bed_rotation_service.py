"""REQ-053 WP 3.4 (#2394) — hints for a bed and the backfill of earlier years (GP-API-025, GP-API-042).

The care-event service is the real one over the in-memory repository of WP 4.1, so a backfill is asserted as the
stored ``care_event(planting, trigger = backfill)`` and the rotation timeline reads it back through the validator.
Every refusal asserts that **nothing reached the care log**.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from freezegun import freeze_time

from app.common.enums import PlanRole, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.care_event import CareEventInput
from app.domain.models.garden_plan import SlotSpeciesHint
from app.domain.models.site import Slot
from app.domain.services.bed_rotation_service import BedRotationService
from app.domain.services.care_event_service import CareEventService
from tests.support.care_event_fakes import (
    FakeAttachmentRepo,
    FakeAttachmentService,
    FakeCareEventRepo,
    FakeFertilizers,
    FakeMemberships,
)
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)
from tests.support.rotation_fakes import (
    FakeFamilies,
    FakeRotationGraph,
    FakeRotationHistory,
    FakeSpecies,
    make_family,
    make_species,
)

TODAY = date(2026, 6, 1)
THIS_YEAR = datetime.now(UTC).year
GROWER = TenantRole.GROWER
LEAD = TenantRole.LEAD
VIEWER = TenantRole.VIEWER


def slot(key: str, location_key: str = "bed") -> Slot:
    return Slot.model_validate({"_key": key, "slot_id": key.upper() + "_X", "location_key": location_key})


@pytest.fixture
def world():
    site = make_site()
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    sites = FakeSites(site, foreign)
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed")
    plan.locations["bed2"] = make_location("bed2")
    plan.locations["alien"] = make_location("alien").model_copy(update={"site_key": "site_foreign"})
    plan.slots = [slot("s1"), slot("s2"), slot("s3"), slot("o1", "bed2"), slot("z1", "alien")]
    species = FakeSpecies(
        make_species("cabbage", "brassica"),
        make_species("tomato", "solanum"),
        make_species("bean", "fabace"),
        make_species("secret", "solanum", tenant=OTHER_TENANT),
        make_species("mismatch", "solanum"),
    )
    families = FakeFamilies(
        make_family("brassica", pause=4), make_family("solanum", pause=4), make_family("fabace", pause=6)
    )
    care_repo = FakeCareEventRepo()
    care = CareEventService(
        care_repo, sites, FakeMemberships(), FakeFertilizers(), FakeAttachmentRepo(), FakeAttachmentService()
    )
    history = FakeRotationHistory(care_repo)
    graph = FakeRotationGraph()
    validator = CropRotationValidator(
        None, species, graph, site_repo=sites, family_repo=families, history_repo=history, today=lambda: TODAY
    )
    service = BedRotationService(sites, plan, graph, species, families, care_repo, care, validator)
    return service, plan, graph, care_repo, history


def backfill(service, *, year=THIS_YEAR - 2, tenant=TENANT, role=GROWER, user=USER, location="bed", **kw):
    args = {"season": None, "species_key": None, "family_key": "solanum", "plan_role": PlanRole.MAIN_CROP, **kw}
    return service.backfill(location, tenant_key=tenant, user_key=user, role=role, year=year, **args)


class TestNeighbourHints:
    def test_with_a_slot_the_neighbours_come_from_adjacent_to(self, world) -> None:
        service, plan, graph, *_ = world
        plan.species_hints = [
            SlotSpeciesHint(slot_key="s2", species_key="tomato"),
            SlotSpeciesHint(slot_key="s3", species_key="bean"),
        ]
        graph.adjacent["s1"] = ["s2"]  # s3 is not next to s1
        graph.incompatible["cabbage"] = ["tomato", "bean"]

        result = service.validate_planting("bed", "cabbage", tenant_key=TENANT, slot_key="s1")

        assert result.neighbour_scope == "slot"
        assert [(h.species_key, h.severity, h.code) for h in result.neighbours] == [
            ("tomato", "WARNING", "companion.incompatible")
        ]
        assert result.severity == "WARNING"  # the strongest of rotation (INFO) and the neighbour

    def test_without_a_slot_every_species_of_the_bed_counts_but_only_as_an_info(self, world) -> None:
        service, plan, graph, *_ = world
        plan.species_hints = [SlotSpeciesHint(slot_key="s2", species_key="tomato")]
        graph.incompatible["cabbage"] = ["tomato"]
        graph.compatible["cabbage"] = {}

        result = service.validate_planting("bed", "cabbage", tenant_key=TENANT)

        assert result.neighbour_scope == "bed"
        assert [(h.severity, h.slot_keys) for h in result.neighbours] == [("INFO", ["s2"])]

    def test_a_compatible_neighbour_is_an_ok_with_its_score(self, world) -> None:
        service, plan, graph, *_ = world
        plan.species_hints = [SlotSpeciesHint(slot_key="s2", species_key="bean")]
        graph.compatible["cabbage"] = {"bean": 0.8}

        (hint,) = service.validate_planting("bed", "cabbage", tenant_key=TENANT).neighbours

        assert (hint.severity, hint.code, hint.score) == ("OK", "companion.compatible", 0.8)

    def test_a_violation_is_a_hint_never_an_error(self, world) -> None:
        service, plan, graph, _repo, history = world
        history.add_plant("bed", "cabbage", date(2026, 3, 1))
        plan.species_hints = [SlotSpeciesHint(slot_key="s2", species_key="tomato")]
        graph.adjacent["s1"] = ["s2"]
        graph.incompatible["cabbage"] = ["tomato"]

        result = service.validate_planting("bed", "cabbage", tenant_key=TENANT, slot_key="s1")

        assert result.severity == "CRITICAL"  # returned, not raised (D-09)

    def test_a_slot_of_another_bed_or_tenant_is_a_404(self, world) -> None:
        service, *_ = world
        for slot_key in ("o1", "z1", "nowhere"):
            with pytest.raises(NotFoundError):
                service.validate_planting("bed", "cabbage", tenant_key=TENANT, slot_key=slot_key)

    def test_a_foreign_bed_is_a_404_and_reads_no_neighbours(self, world) -> None:
        service, plan, *_ = world
        plan.species_hints = [SlotSpeciesHint(slot_key="z1", species_key="tomato")]
        with pytest.raises(NotFoundError):
            service.validate_planting("alien", "cabbage", tenant_key=TENANT)


class TestBackfill:
    def test_writes_a_planting_event_the_server_stamps(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world

        outcome = backfill(service, year=THIS_YEAR - 3, season="spring")

        (event,) = care_repo.inserted
        assert (event.category, event.trigger, event.location_key, event.tenant_key) == (
            "planting",
            "backfill",
            "bed",
            TENANT,
        )
        assert event.performed_at == datetime(THIS_YEAR - 3, 4, 15, 12, tzinfo=UTC)
        assert event.created_by == USER
        assert (event.rotation_entry.year, event.rotation_entry.family_key) == (THIS_YEAR - 3, "solanum")
        assert outcome.care_event_key == "ce_1"

    def test_without_a_season_the_year_sits_at_midsummer(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        backfill(service, year=THIS_YEAR - 1)
        assert care_repo.inserted[0].performed_at == datetime(THIS_YEAR - 1, 7, 1, 12, tzinfo=UTC)

    @freeze_time("2026-12-01")
    def test_the_oldest_allowed_year_passes_v11_although_it_lies_more_than_3650_days_back(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        backfill(service, year=2016)  # 1 July 2016 is 3 805 days before the frozen day: over V-11's ten years
        assert care_repo.inserted[0].rotation_entry.year == 2016

    @pytest.mark.parametrize("year", [THIS_YEAR, THIS_YEAR + 1, THIS_YEAR - 11])
    def test_a_year_outside_the_range_is_refused_and_writes_nothing(self, world, year) -> None:
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(PlanError) as exc:
            backfill(service, year=year)
        assert exc.value.details[0]["code"] == "backfill.year_out_of_range"
        assert care_repo.inserted == []

    def test_a_species_names_its_family(self, world) -> None:
        service, *_ = world
        outcome = backfill(service, species_key="cabbage", family_key=None)
        assert (outcome.entry.family_key, outcome.entry.species_key) == ("brassica", "cabbage")

    def test_a_family_that_disagrees_with_the_species_is_refused(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(PlanError) as exc:
            backfill(service, species_key="cabbage", family_key="solanum")
        assert exc.value.details[0]["code"] == "backfill.family_mismatch"
        assert care_repo.inserted == []

    def test_an_unknown_family_is_a_reference_error(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(PlanValidationError) as exc:
            backfill(service, family_key="no_such_family")
        assert exc.value.codes == ["reference.not_found"]
        assert care_repo.inserted == []

    def test_a_planted_year_needs_a_family_but_a_fallow_year_does_not(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(PlanValidationError) as exc:
            backfill(service, family_key=None)
        assert exc.value.codes == ["backfill.family_required"]
        assert care_repo.inserted == []
        assert backfill(service, family_key=None, plan_role=PlanRole.FALLOW).entry.family_key is None

    def test_a_foreign_species_is_refused_like_an_unknown_one(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(PlanValidationError) as exc:
            backfill(service, species_key="secret", family_key=None)
        assert exc.value.codes == ["reference.not_found"]
        assert care_repo.inserted == []

    def test_a_foreign_bed_is_a_404_and_writes_nothing(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(NotFoundError):
            backfill(service, location="alien")
        assert care_repo.inserted == []

    def test_a_viewer_cannot_backfill(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(ForbiddenError):
            backfill(service, role=VIEWER)
        assert care_repo.inserted == []

    def test_the_client_event_path_cannot_forge_a_backfill(self, world) -> None:
        """``trigger = backfill`` and ``category = planting`` are the server's alone (SR-009)."""
        service, _plan, _graph, care_repo, _history = world
        with pytest.raises(ValueError, match="trigger"):
            CareEventInput(
                location_key="bed", category="planting", summary="x", performed_at=datetime.now(UTC), trigger="backfill"
            )
        forged = CareEventInput(location_key="bed", category="planting", summary="x", performed_at=datetime.now(UTC))
        with pytest.raises(PlanError) as exc:
            service._care.create(forged, tenant_key=TENANT, user_key=USER, role=GROWER)
        assert exc.value.details[0]["code"] == "care_event.category_server_only"
        assert care_repo.inserted == []

    def test_a_backfilled_year_shows_in_the_timeline_and_in_the_validation(self, world) -> None:
        service, *_ = world
        backfill(service, year=THIS_YEAR - 1, family_key="brassica")

        timeline = service.rotation_timeline("bed", tenant_key=TENANT, years=5)
        result = service.validate_planting("bed", "cabbage", tenant_key=TENANT)

        (entry,) = timeline.entries
        assert (entry.year, entry.family_key, entry.source, entry.plan_role) == (
            THIS_YEAR - 1,
            "brassica",
            "backfill",
            "main_crop",
        )
        assert entry.event_key == "ce_1"
        assert result.rotation.findings[0].code == "rotation.pause_not_elapsed"


class TestCancelBackfill:
    def test_the_author_takes_the_year_back_and_it_leaves_the_history(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        key = backfill(service).care_event_key

        service.cancel_backfill("bed", key, tenant_key=TENANT, user_key=USER, role=GROWER)

        voided = care_repo.events[key]
        assert (voided.void_reason, voided.voided_by) == ("backfill_error", USER)
        assert service.rotation_timeline("bed", tenant_key=TENANT, years=5).entries == []

    def test_a_lead_may_cancel_another_members_year_a_grower_may_not(self, world) -> None:
        service, *_ = world
        key = backfill(service, user="u_tom").care_event_key

        with pytest.raises(ForbiddenError):
            service.cancel_backfill("bed", key, tenant_key=TENANT, user_key=USER, role=GROWER)
        service.cancel_backfill("bed", key, tenant_key=TENANT, user_key=USER, role=LEAD)

    def test_a_viewer_cannot_cancel(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        key = backfill(service).care_event_key
        with pytest.raises(ForbiddenError):
            service.cancel_backfill("bed", key, tenant_key=TENANT, user_key=USER, role=VIEWER)
        assert care_repo.events[key].voided_at is None

    def test_only_a_backfill_of_this_bed_can_be_cancelled(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        key = backfill(service).care_event_key
        ordinary = service._care.create(
            CareEventInput(location_key="bed", category="note", summary="a note", performed_at=datetime.now(UTC)),
            tenant_key=TENANT,
            user_key=USER,
            role=GROWER,
        )
        for location, event_key in (("bed2", key), ("bed", ordinary.event.key), ("bed", "ce_missing")):
            with pytest.raises(NotFoundError):
                service.cancel_backfill(location, event_key, tenant_key=TENANT, user_key=USER, role=LEAD)
        assert care_repo.events[key].voided_at is None
        assert care_repo.events[ordinary.event.key].voided_at is None

    def test_another_tenants_backfill_answers_like_an_absent_one(self, world) -> None:
        service, _plan, _graph, care_repo, _history = world
        key = backfill(service).care_event_key
        with pytest.raises(NotFoundError):
            service.cancel_backfill("bed", key, tenant_key=OTHER_TENANT, user_key=USER, role=LEAD)
        assert care_repo.events[key].voided_at is None
