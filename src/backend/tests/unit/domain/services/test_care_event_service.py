"""REQ-053 WP 4.1 (#2400) — the care log: create, supersede, void, redact.

The repository is the in-memory double of ``tests/support/care_event_fakes.py``. As in the plan-service
tests, every refusal asserts that **nothing reached the repository**: a refusal that still wrote is the
defect, not the status code.

Pinned here: GP-ACC-025 (V-11), GP-ACC-026 (supersede keeps both rows, V-12/V-13), GP-ACC-041 (a reference of
another tenant is refused, one text for foreign and absent), GP-ACC-044 (the redaction of a chain, its photos,
the audit row); the server-only fields (trigger, task_key, source_ref, performer) cannot be set by a client; and
the role rules the router gate cannot express (author / lead / ten-minute undo).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.interfaces.care_event_repository import CareEventFilter
from app.domain.models.care_event import (
    REDACTED,
    CareEventCorrection,
    CareEventInput,
    CareEventOrigin,
)
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
    SITE,
    TENANT,
    USER,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

GROWER = TenantRole.GROWER
LEAD = TenantRole.LEAD
VIEWER = TenantRole.VIEWER


def input_for(**overrides) -> CareEventInput:
    data = {
        "location_key": "bed",
        "category": "watering",
        "summary": "Watered the tomatoes",
        "performed_at": datetime.now(UTC) - timedelta(hours=1),
    }
    return CareEventInput(**{**data, **overrides})


def correction_for(**overrides) -> CareEventCorrection:
    data = {
        "category": "watering",
        "summary": "Watered, corrected",
        "performed_at": datetime.now(UTC) - timedelta(hours=1),
    }
    return CareEventCorrection(**{**data, **overrides})


@pytest.fixture
def world():
    site = make_site()
    sites = FakeSites(site, make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", name="Bed", geometry=rect(1, 1, 2, 1))
    plan.locations["bed_child"] = make_location("bed_child", name="Row", parent_location_key="bed")
    plan.locations["bed_other"] = make_location("bed_other", name="Other bed")
    foreign = make_location("loc_foreign", name="Foreign").model_copy(update={"site_key": "site_foreign"})
    plan.locations["loc_foreign"] = foreign
    repo = FakeCareEventRepo()
    repo.plants = {
        "pi_here": (TENANT, "bed"),
        "pi_child": (TENANT, "bed_child"),
        "pi_elsewhere": (TENANT, "bed_other"),
        "pi_foreign": (OTHER_TENANT, "bed"),
    }
    memberships = FakeMemberships()
    attachments = FakeAttachmentRepo()
    attachment_service = FakeAttachmentService()
    service = CareEventService(repo, sites, memberships, FakeFertilizers(), attachments, attachment_service)
    return service, repo, attachments, attachment_service, memberships


def create(service, data=None, *, role=GROWER, user=USER, tenant=TENANT, **kwargs):
    return service.create(data or input_for(), tenant_key=tenant, user_key=user, role=role, **kwargs)


def code_of(exc: pytest.ExceptionInfo) -> str:
    return exc.value.details[0]["code"]


# ── create ───────────────────────────────────────────────────────────────────


class TestCreate:
    def test_stores_the_event_under_the_callers_tenant_and_account(self, world):
        service, repo, *_ = world

        view = create(service)

        stored = repo.events[view.event.key]
        assert (stored.tenant_key, stored.site_key, stored.location_key) == (TENANT, SITE, "bed")
        assert stored.performed_by_user_key == USER
        assert stored.created_by == USER
        assert stored.trigger == "manual"
        assert view.performed_by == "Sabine"
        assert view.created_by_me is True

    def test_a_client_cannot_set_the_server_owned_fields(self):
        for forged in (
            {"trigger": "task"},
            {"trigger": "backfill"},
            {"task_key": "task_1"},
            {"source_ref": {"collection": "feeding_events", "key": "fe_1"}},
            {"created_by": "u_other"},
            {"performed_by_user_key": "u_other"},
            {"tenant_key": OTHER_TENANT},
            {"site_key": "site_foreign"},
        ):
            with pytest.raises(PydanticValidationError):
                input_for(**forged)

    def test_the_two_client_triggers_are_accepted(self):
        assert input_for(trigger="observation").trigger == "observation"

    @pytest.mark.parametrize("category", ["bed_status_change", "position_corrected", "planting", "removal", "clearing"])
    def test_a_server_only_category_is_refused_for_a_client(self, world, category):
        service, repo, *_ = world

        with pytest.raises(PlanError) as exc:
            create(service, input_for(category=category))

        assert exc.value.error_code == "care_event.category_server_only"
        assert repo.inserted == []

    def test_a_server_caller_sets_the_origin_fields(self, world):
        service, repo, *_ = world
        origin = CareEventOrigin(
            trigger="task", task_key="task_1", source_ref={"collection": "watering_events", "key": "we_1"}
        )

        view = create(service, input_for(category="clearing"), origin=origin)

        assert (view.event.trigger, view.event.task_key, view.event.source_ref) == (
            "task",
            "task_1",
            {"collection": "watering_events", "key": "we_1"},
        )

    def test_build_event_validates_without_writing(self, world):
        service, repo, *_ = world

        event = service.build_event(input_for(), tenant_key=TENANT, user_key=USER, role=GROWER)

        assert event.tenant_key == TENANT and event.key is None
        assert repo.inserted == []

    def test_a_viewer_cannot_log(self, world):
        service, repo, *_ = world

        with pytest.raises(ForbiddenError):
            create(service, role=VIEWER)

        assert repo.inserted == []

    def test_an_area_dose_gets_a_total_for_the_bed(self, world):
        service, *_ = world

        view = create(service, input_for(category="feeding", quantity=2.0, unit="l_per_m2"))

        assert (view.event.quantity_total, view.event.quantity_total_unit) == (4.0, "l")

    def test_measurements_only_on_soil_analysis_and_ec_check(self):
        measurement = {"parameter": "ph", "value": 6.4, "unit": "pH"}
        assert input_for(category="soil_analysis", measurements=[measurement]).measurements
        with pytest.raises(PydanticValidationError):
            input_for(category="watering", measurements=[measurement])


class TestPerformedAt:
    """V-11 — GP-ACC-025."""

    def test_ten_minutes_ahead_is_refused(self, world):
        service, repo, *_ = world

        with pytest.raises(PlanError) as exc:
            create(service, input_for(performed_at=datetime.now(UTC) + timedelta(minutes=10)))

        assert (exc.value.error_code, exc.value.status_code) == ("care_event.performed_in_future", 422)
        assert repo.inserted == []

    def test_four_minutes_ahead_is_tolerated(self, world):
        service, *_ = world

        create(service, input_for(performed_at=datetime.now(UTC) + timedelta(minutes=4)))

    def test_400_days_back_is_too_old(self, world):
        service, repo, *_ = world

        with pytest.raises(PlanError) as exc:
            create(service, input_for(performed_at=datetime.now(UTC) - timedelta(days=400)))

        assert exc.value.error_code == "care_event.too_old"
        assert repo.inserted == []

    def test_a_backfill_reaches_ten_years_back(self, world):
        service, *_ = world
        origin = CareEventOrigin(trigger="backfill", max_age_days=3650)

        create(
            service,
            input_for(category="planting", performed_at=datetime.now(UTC) - timedelta(days=2000)),
            origin=origin,
        )

    def test_a_naive_instant_is_read_as_utc(self):
        naive = datetime.now() - timedelta(hours=1)  # noqa: DTZ005 — the point of the test
        assert input_for(performed_at=naive).performed_at.tzinfo is UTC


class TestReferencesAreResolvedUnderTheTenant:
    """GP-NFR-058, GP-ACC-041 — one text for a foreign and an absent key, and nothing written."""

    def test_a_foreign_bed_is_404_like_an_absent_one(self, world):
        service, repo, *_ = world

        for key in ("loc_foreign", "no_such_bed"):
            with pytest.raises(NotFoundError):
                create(service, input_for(location_key=key))

        assert repo.inserted == []

    @pytest.mark.parametrize("plants", [["pi_foreign"], ["pi_elsewhere"], ["pi_missing"], ["pi_here", "pi_foreign"]])
    def test_a_plant_that_is_not_the_beds_in_this_tenant_is_refused(self, world, plants):
        service, repo, *_ = world

        with pytest.raises(PlanValidationError) as exc:
            create(service, input_for(plant_keys=plants))

        assert exc.value.codes == ["reference.not_found"]
        assert repo.inserted == []

    def test_plants_of_the_bed_and_of_its_children_are_accepted(self, world):
        service, *_ = world

        create(service, input_for(plant_keys=["pi_here", "pi_child"]))

    def test_a_product_of_another_tenant_is_refused_and_a_global_one_accepted(self, world):
        service, repo, *_ = world

        with pytest.raises(PlanValidationError) as exc:
            create(service, input_for(product_ref={"kind": "fertilizer", "key": "fert_foreign"}))
        create(service, input_for(product_ref={"kind": "fertilizer", "key": "fert_global"}))

        assert exc.value.codes == ["reference.not_found"]
        assert len(repo.inserted) == 1

    def test_the_member_the_care_was_done_for_must_be_an_active_member(self, world):
        service, repo, _, _, memberships = world
        memberships.inactive.add(("u_tom", TENANT))

        for who in ("u_foreign", "u_nobody", "u_tom"):
            with pytest.raises(PlanValidationError):
                create(service, input_for(performed_for_user_key=who))
        create(service, input_for(performed_for_user_key="u_lead"))

        assert len(repo.inserted) == 1

    def test_a_photo_must_be_the_callers_upload_in_this_tenant(self, world):
        service, repo, attachments, *_ = world
        attachments.add("att_mine")
        attachments.add("att_theirs", created_by="u_tom")
        attachments.add("att_foreign", tenant_key=OTHER_TENANT)

        for ref in ("att_theirs", "att_foreign", "att_missing"):
            with pytest.raises(PlanValidationError):
                create(service, input_for(photo_refs=[ref]))
        create(service, input_for(photo_refs=["att_mine"]))

        assert len(repo.inserted) == 1


# ── supersede ────────────────────────────────────────────────────────────────


class TestSupersede:
    """GP-ACC-026, V-12, V-13."""

    def test_the_old_entry_stays_and_points_at_the_new_one(self, world):
        service, repo, *_ = world
        first = create(service).event

        second = service.supersede(
            first.key, correction_for(quantity=3.0, unit="l"), tenant_key=TENANT, user_key=USER, role=GROWER
        ).event

        assert second.supersedes_key == first.key
        assert repo.events[first.key].superseded_by_key == second.key
        assert repo.events[first.key].quantity is None  # the old entry is unchanged
        assert second.quantity == 3.0

    def test_the_list_hides_the_replaced_entry_unless_asked(self, world):
        service, *_ = world
        first = create(service).event
        second = service.supersede(first.key, correction_for(), tenant_key=TENANT, user_key=USER, role=GROWER).event

        default = service.list_window(
            CareEventFilter(location_key="bed"), tenant_key=TENANT, user_key=USER, offset=0, limit=50
        )
        both = service.list_window(
            CareEventFilter(location_key="bed", include_superseded=True),
            tenant_key=TENANT,
            user_key=USER,
            offset=0,
            limit=50,
        )

        assert [v.event.key for v in default] == [second.key]
        assert {v.event.key for v in both} == {first.key, second.key}

    def test_the_corrected_entry_keeps_the_performer_and_the_trigger(self, world):
        service, *_ = world
        first = create(service, user="u_tom", origin=CareEventOrigin(trigger="task", task_key="task_9")).event

        second = service.supersede(first.key, correction_for(), tenant_key=TENANT, user_key="u_lead", role=LEAD).event

        assert second.performed_by_user_key == "u_tom"
        assert second.created_by == "u_lead"
        assert (second.trigger, second.task_key) == ("task", "task_9")

    def test_a_grower_corrects_only_their_own_entry(self, world):
        service, repo, *_ = world
        foreign_entry = create(service, user="u_tom").event
        before = len(repo.inserted)

        with pytest.raises(ForbiddenError):
            service.supersede(foreign_entry.key, correction_for(), tenant_key=TENANT, user_key=USER, role=GROWER)
        service.supersede(foreign_entry.key, correction_for(), tenant_key=TENANT, user_key="u_lead", role=LEAD)

        assert len(repo.inserted) == before + 1

    def test_no_branching_and_no_continuing_a_voided_entry(self, world):
        service, repo, *_ = world
        first = create(service).event
        service.supersede(first.key, correction_for(), tenant_key=TENANT, user_key=USER, role=GROWER)
        voided = create(service).event
        service.void(voided.key, reason="mistake", tenant_key=TENANT, user_key="u_lead", role=LEAD)
        before = len(repo.inserted)

        for key in (first.key, voided.key):
            with pytest.raises(PlanError) as exc:
                service.supersede(key, correction_for(), tenant_key=TENANT, user_key=USER, role=GROWER)
            assert exc.value.error_code == "care_event.sequence"

        assert len(repo.inserted) == before

    def test_a_corrected_instant_is_held_to_v11(self, world):
        service, repo, *_ = world
        first = create(service).event
        before = len(repo.inserted)

        with pytest.raises(PlanError) as exc:
            service.supersede(
                first.key,
                correction_for(performed_at=datetime.now(UTC) - timedelta(days=500)),
                tenant_key=TENANT,
                user_key=USER,
                role=GROWER,
            )

        assert exc.value.error_code == "care_event.too_old"
        assert len(repo.inserted) == before

    def test_a_correction_keeps_the_photos_of_the_entry_and_may_not_add_a_foreign_one(self, world):
        service, repo, attachments, *_ = world
        attachments.add("att_mine")
        attachments.add("att_theirs", created_by="u_tom")
        first = create(service, input_for(photo_refs=["att_mine"])).event

        service.supersede(
            first.key, correction_for(photo_refs=["att_mine"]), tenant_key=TENANT, user_key="u_lead", role=LEAD
        )
        with pytest.raises(PlanValidationError):
            service.supersede(
                repo.events[first.key].superseded_by_key,
                correction_for(photo_refs=["att_theirs"]),
                tenant_key=TENANT,
                user_key="u_lead",
                role=LEAD,
            )

    def test_a_redacted_entry_cannot_be_corrected(self, world):
        service, *_ = world
        entry = create(service).event
        import asyncio

        asyncio.run(
            service.redact(entry.key, reason="names a neighbour", tenant_key=TENANT, user_key="u_lead", role=LEAD)
        )

        with pytest.raises(PlanError) as exc:
            service.supersede(entry.key, correction_for(), tenant_key=TENANT, user_key=USER, role=GROWER)

        assert exc.value.error_code == "care_event.immutable"

    def test_a_foreign_or_absent_key_is_404(self, world):
        service, repo, *_ = world
        entry = create(service).event

        for key, tenant in ((entry.key, OTHER_TENANT), ("ce_missing", TENANT)):
            with pytest.raises(NotFoundError):
                service.supersede(key, correction_for(), tenant_key=tenant, user_key="u_foreign", role=LEAD)

        assert len(repo.inserted) == 1


# ── void ─────────────────────────────────────────────────────────────────────


class TestVoid:
    """GP-API-037, GP-FR-149."""

    def test_a_lead_voids_any_entry_with_any_reason(self, world):
        service, repo, *_ = world
        entry = create(service, user="u_tom").event

        view = service.void(entry.key, reason="duplicate", tenant_key=TENANT, user_key="u_lead", role=LEAD)

        assert (view.event.voided_by, view.event.void_reason) == ("u_lead", "duplicate")
        assert view.event.voided_at is not None

    def test_the_author_undoes_their_own_entry_within_ten_minutes(self, world):
        service, *_ = world
        entry = create(service).event

        view = service.void(entry.key, reason="undo", tenant_key=TENANT, user_key=USER, role=GROWER)

        assert view.event.void_reason == "undo"

    def test_after_ten_minutes_the_undo_is_the_leads(self, world):
        service, repo, *_ = world
        entry = create(service).event
        repo.events[entry.key] = entry.model_copy(update={"created_at": datetime.now(UTC) - timedelta(minutes=11)})

        with pytest.raises(ForbiddenError):
            service.void(entry.key, reason="undo", tenant_key=TENANT, user_key=USER, role=GROWER)

        assert repo.events[entry.key].voided_at is None

    def test_a_grower_gives_no_other_reason_and_touches_no_other_entry(self, world):
        service, repo, *_ = world
        own = create(service).event
        foreign_entry = create(service, user="u_tom").event

        with pytest.raises(ForbiddenError):
            service.void(own.key, reason="I changed my mind", tenant_key=TENANT, user_key=USER, role=GROWER)
        with pytest.raises(ForbiddenError):
            service.void(foreign_entry.key, reason="undo", tenant_key=TENANT, user_key=USER, role=GROWER)

        assert repo.events[own.key].voided_at is None and repo.events[foreign_entry.key].voided_at is None

    def test_a_voided_entry_cannot_be_voided_again(self, world):
        service, *_ = world
        entry = create(service).event
        service.void(entry.key, reason="undo", tenant_key=TENANT, user_key=USER, role=GROWER)

        with pytest.raises(PlanError) as exc:
            service.void(entry.key, reason="undo", tenant_key=TENANT, user_key="u_lead", role=LEAD)

        assert exc.value.error_code == "care_event.sequence"

    def test_a_foreign_or_absent_key_is_404(self, world):
        service, repo, *_ = world
        entry = create(service).event

        for key, tenant in ((entry.key, OTHER_TENANT), ("ce_missing", TENANT)):
            with pytest.raises(NotFoundError):
                service.void(key, reason="x", tenant_key=tenant, user_key="u_lead", role=LEAD)

        assert repo.events[entry.key].voided_at is None


# ── redact ───────────────────────────────────────────────────────────────────


class TestRedact:
    """GP-ACC-044 — the chain, the photos, the audit row."""

    @pytest.fixture
    def chain(self, world):
        service, repo, attachments, attachment_service, _ = world
        attachments.add("att_1")
        attachments.add("att_2")
        first = create(
            service,
            input_for(summary="Frau Mueller hat gegossen", reason="Nachbarin", photo_refs=["att_1", "att_2"]),
        ).event
        second = service.supersede(
            first.key,
            correction_for(summary="Frau Mueller hat gegossen (korrigiert)", photo_refs=["att_1"]),
            tenant_key=TENANT,
            user_key=USER,
            role=GROWER,
        ).event
        return service, repo, attachment_service, first, second

    async def test_both_ends_of_the_chain_are_redacted(self, chain):
        service, repo, _, first, second = chain

        view = await service.redact(
            second.key, reason="Names a person", tenant_key=TENANT, user_key="u_lead", role=LEAD
        )

        for key in (first.key, second.key):
            stored = repo.events[key]
            assert stored.summary == REDACTED
            assert stored.photo_refs == []
            assert stored.redacted_by == "u_lead"
            assert stored.redaction_reason == "Names a person"
        assert repo.events[first.key].reason == REDACTED
        assert view.event.summary == REDACTED

    async def test_the_attachments_are_deleted_once_and_the_audit_row_is_written(self, chain):
        service, repo, attachment_service, _, second = chain

        await service.redact(second.key, reason="Names a person", tenant_key=TENANT, user_key="u_lead", role=LEAD)

        assert sorted(attachment_service.deleted) == [(TENANT, "att_1"), (TENANT, "att_2")]
        assert repo.audit == [{"op": "redact", "entity": "care_event", "key": second.key, "user_key": "u_lead"}]

    async def test_a_photo_another_carrier_still_holds_stays(self, chain):
        service, _, attachment_service, _, second = chain
        attachment_service.still_referenced.add("att_1")

        await service.redact(second.key, reason="x", tenant_key=TENANT, user_key="u_lead", role=LEAD)

        assert attachment_service.deleted == [(TENANT, "att_2")]

    async def test_only_a_lead_redacts_and_nothing_changes_otherwise(self, chain):
        service, repo, attachment_service, first, second = chain

        with pytest.raises(ForbiddenError):
            await service.redact(second.key, reason="x", tenant_key=TENANT, user_key=USER, role=GROWER)

        assert repo.events[first.key].summary != REDACTED
        assert attachment_service.deleted == [] and repo.audit == []

    async def test_a_foreign_key_is_404_and_changes_nothing(self, chain):
        service, repo, attachment_service, first, second = chain

        with pytest.raises(NotFoundError):
            await service.redact(second.key, reason="x", tenant_key=OTHER_TENANT, user_key="u_foreign", role=LEAD)

        assert repo.events[second.key].summary != REDACTED
        assert attachment_service.deleted == [] and repo.audit == []


# ── reads ────────────────────────────────────────────────────────────────────


class TestReads:
    def test_get_returns_the_chain_oldest_first(self, world):
        service, *_ = world
        first = create(service).event
        second = service.supersede(first.key, correction_for(), tenant_key=TENANT, user_key=USER, role=GROWER).event

        view = service.get(second.key, tenant_key=TENANT, user_key=USER)

        assert view.chain_keys == [first.key, second.key]

    def test_a_foreign_event_is_404(self, world):
        service, *_ = world
        entry = create(service).event

        with pytest.raises(NotFoundError):
            service.get(entry.key, tenant_key=OTHER_TENANT, user_key="u_foreign")

    def test_the_view_never_carries_an_account_key(self, world):
        service, *_ = world
        entry = create(service, input_for(performed_for_user_key="u_lead", performed_by_label=None)).event

        view = service.get(entry.key, tenant_key=TENANT, user_key="u_tom")

        assert (view.performed_by, view.performed_for, view.created_by_me) == ("Sabine", "Lena", False)

    def test_an_erased_account_reads_anonymisiert(self, world):
        service, repo, *_ = world
        entry = create(service).event
        repo.events[entry.key] = entry.model_copy(update={"performed_by_user_key": "_anonymized"})

        assert service.get(entry.key, tenant_key=TENANT, user_key=USER).performed_by == "anonymisiert"

    def test_a_third_party_label_is_shown_when_no_account_performed(self, world):
        service, repo, *_ = world
        entry = create(service, input_for(performed_by_label="the neighbour")).event
        repo.events[entry.key] = entry.model_copy(update={"performed_by_user_key": None})

        assert service.get(entry.key, tenant_key=TENANT, user_key=USER).performed_by == "the neighbour"

    def test_the_default_history_is_the_last_ninety_days(self, world):
        service, repo, *_ = world
        recent = create(service, input_for(performed_at=datetime.now(UTC) - timedelta(days=10))).event
        old = create(service, input_for(performed_at=datetime.now(UTC) - timedelta(days=200))).event

        shown = service.list_window(CareEventFilter(), tenant_key=TENANT, user_key=USER, offset=0, limit=50)
        explicit = service.list_window(
            CareEventFilter(performed_from=datetime.now(UTC) - timedelta(days=300)),
            tenant_key=TENANT,
            user_key=USER,
            offset=0,
            limit=50,
        )

        assert [v.event.key for v in shown] == [recent.key]
        assert {v.event.key for v in explicit} == {recent.key, old.key}

    def test_the_list_of_another_tenant_is_empty_and_a_foreign_bed_filter_is_404(self, world):
        service, *_ = world
        create(service)

        assert (
            service.list_window(CareEventFilter(), tenant_key=OTHER_TENANT, user_key="u_foreign", offset=0, limit=50)
            == []
        )
        with pytest.raises(NotFoundError):
            service.list_window(
                CareEventFilter(location_key="loc_foreign"), tenant_key=TENANT, user_key=USER, offset=0, limit=50
            )
