"""REQ-053 WP 3.4 (#2394) — the bed-level crop-rotation check (GP-FR-131, GP-FR-137, GP-API-039).

The history of every slot of a bed decides, not the history of one slot. Pinned here: the pause precedence
(species, family, window), the strength tiers, the green manure that counts, the mixed bed, the reset day, the beds
that are off, the timeline of GP-ACC-028, and that a tenant's bed, species and history never leak into another's.
"""

from __future__ import annotations

from datetime import date

import pytest
from freezegun import freeze_time

from app.common.exceptions import NotFoundError, PlanError, PlanValidationError
from app.domain.engines.crop_rotation_validator import (
    NOT_APPLICABLE_CONTAINER,
    NOT_APPLICABLE_EXEMPT,
    CropRotationValidator,
    pause_severity,
)
from app.domain.models.site import SoilProfile
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    TENANT,
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


@pytest.fixture(autouse=True)
def _frozen_today():
    with freeze_time("2026-06-01"):
        yield


@pytest.fixture
def world():
    site = make_site()
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": "site_foreign"})
    sites = FakeSites(site, foreign)
    plan = FakePlanRepo(sites)
    plan.locations["bed"] = make_location("bed")
    plan.locations["pot"] = make_location("pot", location_type_key="planter")
    plan.locations["perennial"] = make_location("perennial", rotation_exempt=True)
    plan.locations["alien"] = make_location("alien").model_copy(update={"site_key": "site_foreign"})
    species = FakeSpecies(
        make_species("cabbage", "brassica"),
        make_species("kale", "brassica"),
        make_species("tomato", "solanum"),
        make_species("bean", "fabace", rotation_pause_years=4),
        make_species("grass", "poace"),
        make_species("clover", "fabace"),
        make_species("nofamily", None),
        make_species("secret", "solanum", tenant=OTHER_TENANT),
    )
    families = FakeFamilies(
        make_family("brassica", pause=4),
        make_family("solanum", pause=4),
        make_family("fabace", pause=6),
        make_family("poace", pause=None),
    )
    history = FakeRotationHistory()
    graph = FakeRotationGraph()
    validator = CropRotationValidator(
        None,
        species,
        graph,
        site_repo=sites,
        family_repo=families,
        history_repo=history,
    )
    return validator, plan, history, graph, species


def check(validator, species="cabbage", location="bed", **kwargs):
    return validator.validate_planting_in_location(location, species, tenant_key=TENANT, **kwargs)


class TestPauseAndStrength:
    def test_the_same_family_inside_the_family_pause_is_a_finding_with_the_reason(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "kale", date(2024, 5, 1), removed_on=date(2024, 9, 1))

        result = check(validator)

        (finding,) = result.findings
        assert (finding.code, finding.family_key, finding.last_year, finding.years_since) == (
            "rotation.pause_not_elapsed",
            "brassica",
            2024,
            2,
        )
        assert (finding.pause_years, finding.pause_source) == (4, "family")
        assert "2 year(s) ago" in finding.message
        assert result.severity == finding.severity == "CRITICAL"

    def test_a_finding_carries_the_name_of_the_family_next_to_its_key(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "kale", date(2024, 5, 1), removed_on=date(2024, 9, 1))

        (finding,) = check(validator).findings

        assert (finding.family_key, finding.family_name) == ("brassica", "Brassicaaceae")
        assert "Brassicaaceae" in finding.message

    def test_a_family_outside_the_catalogue_has_no_name_and_the_key_is_not_shown_as_one(self, world) -> None:
        validator, _plan, history, _graph, species = world
        species.by_key["cabbage"] = make_species("cabbage", "ghostfam")
        species.by_key["kale"] = make_species("kale", "ghostfam")
        history.add_plant("bed", "kale", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        (finding,) = check(validator).findings

        assert (finding.code, finding.family_key, finding.family_name) == (
            "rotation.pause_not_elapsed",
            "ghostfam",
            None,
        )
        assert "ghostfam" not in finding.message

    def test_a_pest_finding_names_the_other_family_from_the_catalogue(self, world) -> None:
        validator, _plan, history, graph, _species = world
        graph.pest_risks["brassica"] = [{"family": {"_key": "solanum"}, "risk_level": "high"}]
        history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        (finding,) = check(validator).findings

        assert (finding.family_key, finding.family_name) == ("solanum", "Solanumaceae")

    def test_a_pest_finding_for_an_unlisted_family_has_no_name(self, world) -> None:
        validator, _plan, history, graph, species = world
        species.by_key["tomato"] = make_species("tomato", "ghostfam")
        graph.pest_risks["brassica"] = [{"family": {"_key": "ghostfam"}, "risk_level": "high"}]
        history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        (finding,) = check(validator).findings

        assert (finding.family_key, finding.family_name) == ("ghostfam", None)
        assert "ghostfam" not in finding.message

    def test_a_pause_that_has_elapsed_is_ok(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "kale", date(2022, 5, 1), removed_on=date(2022, 9, 1))
        history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        result = check(validator)

        assert result.findings == []
        assert result.severity == "OK"

    @pytest.mark.parametrize(
        ("years_since", "pause", "expected"),
        [(0, 4, "CRITICAL"), (2, 4, "CRITICAL"), (3, 4, "WARNING"), (1, 3, "CRITICAL"), (2, 3, "WARNING")],
    )
    def test_the_nearer_the_last_crop_the_stronger_the_hint(self, years_since, pause, expected) -> None:
        assert pause_severity(years_since, pause) == expected

    def test_the_species_override_beats_the_family_default(self, world) -> None:
        validator, _plan, history, *_ = world
        # fabace family pause is 6, the bean overrides it with 4: a bean 5 years ago is fine.
        history.add_plant("bed", "bean", date(2022, 5, 1), removed_on=date(2022, 8, 1))
        assert check(validator, "bean").findings == []

        # ...but the family default (6) holds for a species without an override.
        result = check(validator, "clover")
        assert result.findings[0].pause_years == 6
        assert result.findings[0].pause_source == "family"

    def test_a_species_with_its_own_pause_names_the_species_as_the_source(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "bean", date(2024, 5, 1), removed_on=date(2024, 8, 1))
        finding = check(validator, "bean").findings[0]
        assert (finding.pause_years, finding.pause_source) == (4, "species")

    def test_a_family_without_a_pause_falls_back_to_the_window(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "grass", date(2025, 5, 1), removed_on=date(2025, 8, 1))
        finding = check(validator, "grass", rotation_window_years=5).findings[0]
        assert (finding.pause_years, finding.pause_source) == (5, "default")

    def test_a_pause_of_zero_needs_no_hint_even_with_history(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))
        history.add_plant("bed", "kale", date(2026, 3, 1))
        validator._families.by_key["brassica"] = make_family("brassica", pause=0)

        result = check(validator)

        assert (result.findings, result.severity) == ([], "OK")

    def test_the_window_is_bounded_to_eight_years(self, world) -> None:
        validator, *_ = world
        for bad in (0, 9):
            with pytest.raises(PlanError) as exc:
                check(validator, rotation_window_years=bad)
            assert exc.value.details[0]["code"] == "rotation.window_out_of_range"
        assert check(validator, rotation_window_years=8).applicable


class TestTheHistoryOfTheWholeBed:
    def test_a_green_manure_counts_with_its_family(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "kale", date(2025, 8, 1), removed_on=date(2025, 11, 1), plan_role="green_manure")

        finding = check(validator).findings[0]

        assert finding.plan_role == "green_manure"
        assert "as green manure" in finding.message

    def test_a_mixed_bed_counts_every_family_of_the_year(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))
        history.add_plant("bed", "kale", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        assert check(validator, "cabbage").severity == "CRITICAL"
        assert check(validator, "tomato").severity == "CRITICAL"
        assert check(validator, "bean").severity in {"INFO", "OK"}

    def test_a_standing_plant_occupies_the_years_it_has_stood(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "kale", date(2023, 9, 1))  # still standing

        finding = check(validator).findings[0]

        assert (finding.last_year, finding.years_since) == (2026, 0)

    def test_a_fallow_year_occupies_the_bed_with_no_family(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "kale", date(2025, 5, 1), removed_on=date(2025, 9, 1), plan_role="fallow")
        assert check(validator).findings[0].code == "rotation.no_history"

    def test_an_empty_history_says_the_rotation_cannot_be_verified(self, world) -> None:
        validator, *_ = world
        result = check(validator)
        assert [f.code for f in result.findings] == ["rotation.no_history"]
        assert result.severity == "INFO"

    def test_the_reset_day_hides_everything_before_it(self, world) -> None:
        validator, plan, history, *_ = world
        plan.locations["bed"] = make_location("bed", soil_profile=SoilProfile(rotation_reset_at=date(2025, 3, 1)))
        history.add_plant("bed", "kale", date(2024, 5, 1), removed_on=date(2024, 9, 1))

        result = check(validator)

        assert result.rotation_reset_at == date(2025, 3, 1)
        assert result.severity == "INFO"  # the old brassica is behind the reset: nothing on record
        history.add_plant("bed", "kale", date(2025, 5, 1), removed_on=date(2025, 9, 1))
        assert check(validator).findings[0].last_year == 2025

    def test_a_high_pest_risk_between_families_is_a_warning(self, world) -> None:
        validator, _plan, history, graph, _species = world
        graph.pest_risks["brassica"] = [
            {"family": {"_key": "solanum"}, "risk_level": "high", "shared_pests": ["aphid"], "shared_diseases": []}
        ]
        history.add_plant("bed", "tomato", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        findings = check(validator).findings

        assert [(f.code, f.severity) for f in findings] == [("rotation.pest_risk", "WARNING")]
        assert findings[0].pest_risk["shared_pests"] == ["aphid"]


class TestBedsThatAreOff:
    @pytest.mark.parametrize(
        ("location", "reason"),
        [("pot", NOT_APPLICABLE_CONTAINER), ("perennial", NOT_APPLICABLE_EXEMPT)],
    )
    def test_planter_and_rotation_exempt_beds_are_not_checked(self, world, location, reason) -> None:
        validator, _plan, history, *_ = world
        history.add_plant(location, "kale", date(2026, 4, 1))

        result = check(validator, location=location)

        assert (result.applicable, result.not_applicable_reason, result.findings) == (False, reason, [])

    def test_a_species_without_a_family_cannot_be_evaluated(self, world) -> None:
        validator, *_ = world
        assert check(validator, "nofamily").findings[0].code == "rotation.no_family"


class TestTenantIsolation:
    def test_a_foreign_bed_answers_like_an_absent_one(self, world) -> None:
        validator, *_ = world
        for key in ("alien", "nowhere"):
            with pytest.raises(NotFoundError) as exc:
                check(validator, location=key)
            assert exc.value.message == NotFoundError("Location", key).message

    def test_a_foreign_species_answers_like_an_unknown_one(self, world) -> None:
        validator, *_ = world
        texts = []
        for key in ("secret", "no_such_species"):
            with pytest.raises(PlanValidationError) as exc:
                check(validator, key)
            texts.append(exc.value.details)
        assert texts[0] == texts[1]
        assert texts[0][0]["code"] == "reference.not_found"

    def test_a_species_granted_to_the_tenant_is_visible(self, world) -> None:
        validator, _plan, _history, _graph, species = world
        species.grants.add(("secret", TENANT))
        assert check(validator, "secret").applicable

    def test_another_tenants_plants_in_a_bed_with_the_same_key_do_not_count(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "kale", date(2026, 4, 1), tenant=OTHER_TENANT)

        assert [f.code for f in check(validator).findings] == ["rotation.no_history"]


class TestTimeline:
    def test_lists_family_demand_and_role_per_year(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "tomato", date(2024, 5, 1), removed_on=date(2024, 9, 1))
        history.add_plant("bed", "bean", date(2025, 5, 1), removed_on=date(2025, 9, 1))

        timeline = validator.rotation_timeline("bed", tenant_key=TENANT, years=5)

        by_year = {(e.year, e.family_key): e for e in timeline.entries}
        assert set(by_year) == {(2024, "solanum"), (2025, "fabace")}
        tomato = by_year[(2024, "solanum")]
        assert tomato.plan_role == "main_crop"
        assert tomato.nutrient_demand == "medium_feeder"  # the family default: this species states none
        assert (timeline.from_year, timeline.to_year, timeline.years) == (2022, 2026, 5)

    def test_a_green_manure_has_no_demand_of_its_own(self, world) -> None:
        validator, _plan, history, *_ = world
        history.add_plant("bed", "clover", date(2025, 8, 1), removed_on=date(2025, 11, 1), plan_role="green_manure")
        (entry,) = validator.rotation_timeline("bed", tenant_key=TENANT, years=5).entries
        assert (entry.plan_role, entry.nutrient_demand) == ("green_manure", None)

    def test_the_default_look_back_is_the_longest_pause_involved_but_at_least_five(self, world) -> None:
        validator, _plan, history, *_ = world
        assert validator.rotation_timeline("bed", tenant_key=TENANT).years == 5
        history.add_plant("bed", "clover", date(2022, 5, 1), removed_on=date(2022, 8, 1))  # fabace: pause 6
        assert validator.rotation_timeline("bed", tenant_key=TENANT).years == 6

    def test_a_species_override_widens_the_default_look_back(self, world) -> None:
        validator, _plan, history, *_ = world
        # bean overrides the fabace pause (6) with 4; give kale a 9-year override via a fresh species
        validator._species_repo.by_key["longpause"] = make_species("longpause", "brassica", rotation_pause_years=8)
        history.add_plant("bed", "longpause", date(2022, 5, 1), removed_on=date(2022, 8, 1))

        assert validator.rotation_timeline("bed", tenant_key=TENANT).years == 8

    def test_more_than_ten_years_is_refused(self, world) -> None:
        validator, *_ = world
        with pytest.raises(PlanError) as exc:
            validator.rotation_timeline("bed", tenant_key=TENANT, years=11)
        assert exc.value.details[0]["code"] == "rotation.years_out_of_range"

    def test_a_foreign_bed_is_a_404(self, world) -> None:
        validator, *_ = world
        with pytest.raises(NotFoundError):
            validator.rotation_timeline("alien", tenant_key=TENANT)

    def test_the_timeline_of_a_planter_is_still_readable_but_says_it_is_off(self, world) -> None:
        validator, *_ = world
        timeline = validator.rotation_timeline("pot", tenant_key=TENANT)
        assert (timeline.applicable, timeline.not_applicable_reason) == (False, NOT_APPLICABLE_CONTAINER)
