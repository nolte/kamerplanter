"""REQ-053 WP 8.12 (#2655) - the site rotation matrix (GP-FR-135).

The service reads every bed through the same three calls of the validator as ``rotation_timeline`` does; pinned here
that a row equals the bed's own timeline, that the tenant anchors the read, and that the marked beds stay listed.
"""

from __future__ import annotations

from datetime import date

import pytest
from freezegun import freeze_time

from app.common.exceptions import NotFoundError, PlanError
from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.site import SoilProfile
from app.domain.services.rotation_matrix_service import RotationMatrixService
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT, FakePlanRepo, FakeSites, make_location, make_site
from tests.support.rotation_fakes import (
    FakeFamilies,
    FakeRotationGraph,
    FakeRotationHistory,
    FakeSpecies,
    make_family,
    make_species,
)


@pytest.fixture(autouse=True)
def _frozen_today():
    with freeze_time("2026-06-01"):
        yield


@pytest.fixture
def world():
    sites = FakeSites(make_site(), make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"}))
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed", "Bed")
    plan.locations["exempt"] = make_location("exempt", "Hedge", rotation_exempt=True)
    plan.locations["alien"] = make_location("alien").model_copy(update={"site_key": "site_foreign"})
    history = FakeRotationHistory()
    validator = CropRotationValidator(
        None,
        FakeSpecies(
            make_species("tomato", "solanum"),
            make_species("bean", "fabace"),
            make_species("secret", "solanum", tenant=OTHER_TENANT),
        ),
        FakeRotationGraph(),
        site_repo=sites,
        family_repo=FakeFamilies(make_family("solanum", pause=4), make_family("fabace", pause=6)),
        history_repo=history,
    )
    return RotationMatrixService(sites, plan, validator), validator, plan, history


def test_a_row_is_the_timeline_of_its_bed_for_every_year(world) -> None:
    service, validator, _plan, history = world
    history.add_plant("bed", "tomato", date(2024, 5, 1), removed_on=date(2024, 9, 1))
    history.add_plant("bed", "bean", date(2025, 5, 1), removed_on=date(2025, 9, 1))

    matrix = service.rotation_matrix("site_1", tenant_key=TENANT)
    row = next(r for r in matrix.beds if r.location_key == "bed")
    timeline = validator.rotation_timeline("bed", tenant_key=TENANT, years=matrix.years)

    assert row.entries == timeline.entries
    assert matrix.from_year == timeline.from_year
    # the matrix runs two years past the timeline's last year; nothing planned, so nothing is there
    assert (timeline.to_year, matrix.to_year) == (2026, 2028)
    assert {e.year for e in row.entries} == {2024, 2025}  # not vacuous


def test_the_exempt_bed_is_listed_marked_and_the_ordinary_one_is_not(world) -> None:
    service, *_ = world

    rows = {r.location_key: r for r in service.rotation_matrix("site_1", tenant_key=TENANT).beds}

    assert (rows["exempt"].applicable, rows["exempt"].not_applicable_reason) == (
        False,
        "rotation.not_applicable.rotation_exempt",
    )
    assert (rows["bed"].applicable, rows["bed"].not_applicable_reason) == (True, None)


def test_the_reset_day_cuts_the_history_of_the_row_like_the_timeline(world) -> None:
    service, validator, plan, history = world
    plan.locations["bed"] = plan.locations["bed"].model_copy(
        update={"soil_profile": SoilProfile(rotation_reset_at=date(2025, 1, 1))}
    )
    history.add_plant("bed", "tomato", date(2024, 5, 1), removed_on=date(2024, 9, 1))
    history.add_plant("bed", "bean", date(2025, 5, 1), removed_on=date(2025, 9, 1))

    row = next(r for r in service.rotation_matrix("site_1", tenant_key=TENANT).beds if r.location_key == "bed")

    assert {e.year for e in row.entries} == {2025}
    assert row.rotation_reset_at == date(2025, 1, 1)
    assert row.entries == validator.rotation_timeline("bed", tenant_key=TENANT, years=5).entries


def test_another_tenants_site_and_an_empty_tenant_are_not_found(world) -> None:
    service, *_ = world
    with pytest.raises(NotFoundError):
        service.rotation_matrix("site_foreign", tenant_key=TENANT)
    with pytest.raises(NotFoundError):
        service.rotation_matrix("site_1", tenant_key="")
    # the control: its owner reads it
    assert [r.location_key for r in service.rotation_matrix("site_foreign", tenant_key=OTHER_TENANT).beds] == ["alien"]


def test_another_tenants_plantings_never_reach_a_row(world) -> None:
    service, _validator, _plan, history = world
    history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1), tenant=OTHER_TENANT)

    row = next(r for r in service.rotation_matrix("site_1", tenant_key=TENANT).beds if r.location_key == "bed")

    assert row.entries == []


def test_years_beyond_ten_are_refused(world) -> None:
    service, *_ = world
    with pytest.raises(PlanError) as exc:
        service.rotation_matrix("site_1", tenant_key=TENANT, years=11)
    assert exc.value.details[0]["code"] == "rotation.years_out_of_range"


def test_a_bed_nested_under_another_location_is_in_the_matrix(world) -> None:
    """``get_locations_by_site`` is depth one (a nested bed hangs under its parent, not the site): the tree decides."""
    service, _validator, plan, _history = world
    plan.locations["greenhouse"] = make_location("greenhouse", "Greenhouse", location_type_key="greenhouse")
    plan.locations["nested"] = make_location("nested", "Nested", parent_location_key="greenhouse")

    class DepthOne(type(plan._sites)):
        def get_locations_by_site(self, site_key):
            return [loc for loc in super().get_locations_by_site(site_key) if not loc.parent_location_key]

        def get_location_tree(self, site_key, *, tenant_key):
            return super().get_locations_by_site(site_key)

    plan._sites.__class__ = DepthOne

    keys = [r.location_key for r in service.rotation_matrix("site_1", tenant_key=TENANT).beds]

    assert keys == ["bed", "exempt", "nested"]  # the greenhouse itself is no bed


def test_a_stored_foreign_species_is_resolved_under_the_tenant_and_names_no_family(world) -> None:
    """A legacy plant may name another tenant's private species: its family and demand must not reach the row."""
    service, _validator, _plan, history = world
    history.add_plant("bed", "secret", date(2025, 5, 1), removed_on=date(2025, 9, 1))
    history.add_plant("bed", "tomato", date(2024, 5, 1), removed_on=date(2024, 9, 1))

    row = next(r for r in service.rotation_matrix("site_1", tenant_key=TENANT).beds if r.location_key == "bed")

    by_year = {e.year: e for e in row.entries}
    assert (by_year[2025].family_key, by_year[2025].nutrient_demand) == (None, None)
    assert by_year[2024].family_key == "solanum"  # the control: a readable species still names its family


# ── Future columns from planned runs (#2958, §32.5 item A) ─────────────────────────────────────────────────────────


def _bed_row(service, tenant: str = TENANT):
    return next(r for r in service.rotation_matrix("site_1", tenant_key=tenant).beds if r.location_key == "bed")


def test_a_run_planned_for_next_season_is_in_next_years_column_marked_planned(world) -> None:
    service, _validator, _plan, history = world
    history.add_run("bed", "tomato", date(2027, 4, 1), date(2027, 9, 30))

    row = _bed_row(service)

    assert [(e.year, e.family_key, e.source, e.season) for e in row.entries] == [(2027, "solanum", "planned", None)]


def test_a_cancelled_a_started_and_a_past_window_run_are_not_shown(world) -> None:
    service, _validator, _plan, history = world
    history.add_run("bed", "tomato", date(2027, 4, 1), status="cancelled")
    history.add_run("bed", "tomato", date(2027, 4, 1), status="active")
    history.add_run("bed", "bean", date(2026, 3, 1), date(2026, 5, 31))  # ended before today (2026-06-01)
    history.add_run("bed", "bean", date(2025, 4, 1))  # open end: its start year only, long past
    history.add_run("bed", "bean", None)  # names no time at all

    assert _bed_row(service).entries == []
    # the control: the same bed shows a run still planned
    history.add_run("bed", "bean", date(2026, 3, 1), date(2026, 6, 30))
    assert [(e.year, e.source) for e in _bed_row(service).entries] == [(2026, "planned")]


def test_what_stood_this_year_wins_over_a_plan_for_the_same_season(world) -> None:
    service, _validator, _plan, history = world
    history.add_plant("bed", "bean", date(2026, 4, 1))
    history.add_run("bed", "tomato", date(2026, 7, 1), date(2027, 9, 30))

    entries = _bed_row(service).entries

    # 2026 keeps the bean that stands; the plan fills only the following year of its window
    assert [(e.year, e.species_key, e.source) for e in entries] == [
        (2027, "tomato", "planned"),
        (2026, "bean", "plant"),
    ]


def test_a_window_over_several_years_fills_them_up_to_the_last_future_column(world) -> None:
    service, _validator, _plan, history = world
    history.add_run("bed", "tomato", date(2027, 4, 1), date(2035, 9, 30), plan_role="green_manure")

    entries = _bed_row(service).entries

    assert [(e.year, e.plan_role) for e in entries] == [(2028, "green_manure"), (2027, "green_manure")]


def test_another_tenants_run_never_reaches_a_row(world) -> None:
    service, _validator, _plan, history = world
    history.add_run("bed", "tomato", date(2027, 4, 1), tenant=OTHER_TENANT)

    assert _bed_row(service).entries == []
    # the control: the own tenant's run of the same shape is shown
    history.add_run("bed", "tomato", date(2027, 4, 1))
    assert [e.source for e in _bed_row(service).entries] == ["planned"]


def test_a_planned_foreign_species_names_no_family(world) -> None:
    service, _validator, _plan, history = world
    history.add_run("bed", "secret", date(2027, 4, 1))

    (entry,) = _bed_row(service).entries

    assert (entry.species_key, entry.family_key, entry.nutrient_demand) == ("secret", None, None)


def test_the_bed_timeline_never_shows_a_plan(world) -> None:
    _service, validator, _plan, history = world
    history.add_run("bed", "tomato", date(2026, 6, 1), date(2026, 9, 30))

    assert validator.rotation_timeline("bed", tenant_key=TENANT).entries == []
