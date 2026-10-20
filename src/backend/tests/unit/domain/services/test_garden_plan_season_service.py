"""REQ-053 WP 7.16 (#2482) - "new season from the previous year" against the in-memory repository.

Pinned: who may call it, in which order it refuses (tenant anchor, lead, year, revision), which beds are copied
and which are skipped, that nothing but free slots is written, and that a second run copies nothing.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.common.enums import BedStatus, GeometrySource, TenantRole
from app.common.exceptions import NotFoundError, PlanError, PlanRevisionConflictError
from app.domain.models.site import SitePlan, Slot
from app.domain.services.garden_plan_season_service import GardenPlanSeasonService
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

USER = "u_sabine"
LAST_YEAR = datetime(2026, 8, 1, tzinfo=UTC)
YEAR_BEFORE = datetime(2025, 8, 1, tzinfo=UTC)


def _old(key: str, slot_id: str, bed: str, x: float, *, at: datetime = LAST_YEAR) -> Slot:
    return Slot(
        _key=key,
        slot_id=slot_id,
        location_key=bed,
        geometry={"kind": "point", "origin": [x, 0.5]},
        sequence=int(x * 2),
        archived_at=at,
    )


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(plan_revision=3)
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    repository = FakePlanRepo(FakeSites(site, foreign))
    for key in ("b1", "b2", "b3"):
        repository.locations[key] = make_location(key, f"Bed {key}", geometry=rect(1, 1, 3, 1))
    repository.slots = [
        _old("o1", "B1_A", "b1", 0.5),
        _old("o2", "B1_B", "b1", 1.5),
        _old("o3", "B1_C", "b1", 2.5, at=YEAR_BEFORE),  # ended two years ago: not the source
        _old("o4", "B2_A", "b2", 0.5),  # a bed with a plant
        _old("o5", "B3_A", "b3", 0.5),
        Slot(_key="l3", slot_id="B3_L", location_key="b3", geometry={"kind": "point", "origin": [0.5, 0.5]}),  # stands
    ]
    repository.planted = {"b2"}
    return repository


@pytest.fixture
def service(repo: FakePlanRepo) -> GardenPlanSeasonService:
    return GardenPlanSeasonService(repo._sites, repo, dispatch_adjacency=lambda key: repo.dispatched.append(key))


def _run(service: GardenPlanSeasonService, **options):
    arguments = {"role": TenantRole.LEAD, "year": 2027, "dry_run": False} | options
    return service.new_season(SITE, tenant_key=TENANT, user_key=USER, **arguments)


@pytest.fixture(autouse=True)
def _dispatched(repo: FakePlanRepo) -> None:
    repo.dispatched = []  # type: ignore[attr-defined]


class TestTheCopy:
    def test_free_slots_for_the_beds_without_plants(self, service: GardenPlanSeasonService, repo: FakePlanRepo) -> None:
        report = _run(service)

        by_bed = {item.location_key: item for item in report.beds}
        assert (by_bed["b1"].status, by_bed["b1"].slots) == ("copied", 2)
        assert by_bed["b2"].status == "skipped_active_plants"
        assert by_bed["b3"].status == "nothing_to_copy"  # the place already stands as a live slot
        assert (report.beds_copied, report.beds_skipped, report.slots_to_create) == (1, 1, 2)
        assert report.applied is True and report.plan_revision == 4
        created = [s for s in repo.slots if s.geometry_source is GeometrySource.SEASON_COPY]
        assert len(created) == 2
        assert all(not s.currently_occupied and s.archived_at is None and s.sown_at is None for s in created)
        assert {s.slot_id for s in created} == {"S2027_001", "S2027_002"}
        assert repo.dispatched == ["b1"]  # type: ignore[attr-defined]

    def test_only_slots_are_written_with_one_audit_row_of_counts(
        self, service: GardenPlanSeasonService, repo: FakePlanRepo
    ) -> None:
        _run(service)

        (write,) = repo.applied
        assert not (write.location_inserts or write.location_updates or write.location_deletes or write.zone_deletes)
        assert not (write.zone_inserts or write.object_inserts or write.care_events or write.snapshot)
        assert write.expected_revision == write.basis_revision == 3
        assert write.audit == [
            {"op": "season_copy", "entity": "site", "key": SITE, "summary": "year 2027: 1 beds, 2 slots"}
        ]

    def test_a_dry_run_writes_nothing(self, service: GardenPlanSeasonService, repo: FakePlanRepo) -> None:
        report = _run(service, dry_run=True)

        assert report.slots_to_create == 2 and report.applied is False
        assert repo.applied == [] and len(repo.slots) == 6

    def test_a_second_run_finds_nothing(self, service: GardenPlanSeasonService, repo: FakePlanRepo) -> None:
        _run(service)
        again = _run(service)

        assert again.slots_to_create == 0 and again.applied is False
        assert len(repo.applied) == 1

    def test_the_old_slots_are_left_alone(self, service: GardenPlanSeasonService, repo: FakePlanRepo) -> None:
        _run(service)

        assert all(s.archived_at is not None for s in repo.slots if s.key in {"o1", "o2", "o3", "o4", "o5"})

    def test_a_retired_bed_is_skipped(self, service: GardenPlanSeasonService, repo: FakePlanRepo) -> None:
        repo.locations["b1"] = repo.locations["b1"].model_copy(update={"bed_status": BedStatus.RETIRED})

        report = _run(service)

        assert {i.location_key: i.status for i in report.beds}["b1"] == "skipped_retired"
        assert report.slots_to_create == 0

    def test_a_bed_over_its_slot_quota_is_skipped(
        self, service: GardenPlanSeasonService, repo: FakePlanRepo, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("app.domain.services.garden_plan_season_service.MAX_SLOTS_PER_BATCH", 1)

        report = _run(service)

        assert {i.location_key: i.status for i in report.beds}["b1"] == "skipped_slot_quota"
        assert repo.applied == []

    def test_the_site_total_is_bounded(self, service: GardenPlanSeasonService, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("app.domain.services.garden_plan_season_service.MAX_SLOTS_PER_SITE", 2)

        with pytest.raises(PlanError) as error:
            _run(service)

        assert error.value.error_code == "plan.quota_exceeded" and error.value.status_code == 422


class TestTheGates:
    def test_a_foreign_site_is_a_404_before_the_role_is_looked_at(self, service: GardenPlanSeasonService) -> None:
        with pytest.raises(NotFoundError):
            service.new_season(
                SITE, tenant_key=OTHER_TENANT, user_key=USER, role=TenantRole.VIEWER, year=2027, dry_run=True
            )

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_only_a_lead_may_call_it(self, service: GardenPlanSeasonService, role: TenantRole) -> None:
        with pytest.raises(PlanError) as error:
            _run(service, role=role, dry_run=True)

        assert error.value.status_code == 403

    @pytest.mark.parametrize("year", [0, -1, 1999, 2000, 2100, 99999, True])
    def test_a_year_out_of_range_is_a_422(self, service: GardenPlanSeasonService, year: int) -> None:
        with pytest.raises(PlanError) as error:
            _run(service, year=year, dry_run=True)

        assert error.value.error_code == "season.invalid_year" and error.value.status_code == 422

    def test_another_revision_is_a_409(self, service: GardenPlanSeasonService, repo: FakePlanRepo) -> None:
        with pytest.raises(PlanRevisionConflictError) as error:
            _run(service, expected_revision=2)

        assert error.value.status_code == 409 and repo.applied == []

    def test_the_revision_it_saw_goes_through(self, service: GardenPlanSeasonService) -> None:
        assert _run(service, expected_revision=3).applied is True
