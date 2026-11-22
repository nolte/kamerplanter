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
    NOT_APPLICABLE_DISABLED,
    NOT_APPLICABLE_EXEMPT,
    CropRotationValidator,
    not_applicable_reason,
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


class TestPerBedSwitch:
    """GP-ACC-055 / GP-FR-137: off by default for planter/tent/shelf, switchable per bed; ``rotation_exempt`` wins."""

    CONTAINERS = ("planter", "tent", "shelf")

    @pytest.mark.parametrize(
        ("location_type", "exempt", "enabled", "reason"),
        [
            # ``None`` keeps today's behaviour for every existing bed: the type decides.
            ("bed", False, None, None),
            ("planter", False, None, NOT_APPLICABLE_CONTAINER),
            ("tent", False, None, NOT_APPLICABLE_CONTAINER),
            ("shelf", False, None, NOT_APPLICABLE_CONTAINER),
            ("bed", True, None, NOT_APPLICABLE_EXEMPT),
            # switched on: the type default no longer counts
            ("planter", False, True, None),
            ("tent", False, True, None),
            ("shelf", False, True, None),
            ("bed", False, True, None),
            # switched off: off for every type
            ("bed", False, False, NOT_APPLICABLE_DISABLED),
            ("planter", False, False, NOT_APPLICABLE_DISABLED),
            # a permanent crop is off whatever the switch says
            ("planter", True, True, NOT_APPLICABLE_EXEMPT),
            ("bed", True, True, NOT_APPLICABLE_EXEMPT),
            ("bed", True, False, NOT_APPLICABLE_EXEMPT),
        ],
    )
    def test_the_precedence_is_exempt_then_switch_then_type(self, location_type, exempt, enabled, reason) -> None:
        location = make_location("x", location_type_key=location_type, rotation_exempt=exempt, rotation_enabled=enabled)

        assert not_applicable_reason(location) == reason

    def test_gp_acc_055_only_the_container_switched_on_returns_the_rotation_hint(self, world) -> None:
        """GP-ACC-055: planter, tent and shelf with Solanaceae 2025; tomato 2026 - one hint, after one switch."""
        validator, plan, history, *_ = world
        for kind in self.CONTAINERS:
            plan.locations[kind] = make_location(kind, location_type_key=kind)
            history.add_plant(kind, "tomato", date(2025, 4, 1), removed_on=date(2025, 9, 1))

        before = {kind: check(validator, "tomato", location=kind) for kind in self.CONTAINERS}
        assert {kind: (r.applicable, r.findings) for kind, r in before.items()} == {
            kind: (False, []) for kind in self.CONTAINERS
        }

        plan.locations["tent"] = plan.locations["tent"].model_copy(update={"rotation_enabled": True})
        after = {kind: check(validator, "tomato", location=kind) for kind in self.CONTAINERS}

        assert [f.code for f in after["tent"].findings] == ["rotation.pause_not_elapsed"]
        assert after["tent"].applicable is True and after["tent"].findings[0].family_key == "solanum"
        for kind in ("planter", "shelf"):
            assert (after[kind].applicable, after[kind].not_applicable_reason, after[kind].findings) == (
                False,
                NOT_APPLICABLE_CONTAINER,
                [],
            )

    def test_an_exempt_container_stays_off_when_switched_on(self, world) -> None:
        validator, plan, history, *_ = world
        plan.locations["tent"] = make_location(
            "tent", location_type_key="tent", rotation_exempt=True, rotation_enabled=True
        )
        history.add_plant("tent", "tomato", date(2025, 4, 1), removed_on=date(2025, 9, 1))

        result = check(validator, "tomato", location="tent")

        assert (result.applicable, result.not_applicable_reason, result.findings) == (False, NOT_APPLICABLE_EXEMPT, [])

    def test_the_timeline_follows_the_switch(self, world) -> None:
        validator, plan, *_ = world
        plan.locations["tent"] = make_location("tent", location_type_key="tent", rotation_enabled=True)
        plan.locations["shelf"] = make_location("shelf", location_type_key="shelf")

        on = validator.rotation_timeline("tent", tenant_key=TENANT)
        off = validator.rotation_timeline("shelf", tenant_key=TENANT)

        assert (on.applicable, on.not_applicable_reason) == (True, None)
        assert (off.applicable, off.not_applicable_reason) == (False, NOT_APPLICABLE_CONTAINER)


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


class TestReplantOfAFailedPlant:
    """REQ-053 §11.3 "ausgefallen" (W-015, #2888): a replant names the plant it replaces; it is no previous crop.

    Only for the one check that names it, only for a plant of this bed and tenant that died this calendar year. A
    residual hint from its ``termination_cause`` stays when the same family goes back in: disease or pest a
    ``WARNING``, no or an unknown cause an ``INFO``, an abiotic loss nothing.
    """

    def _died(self, history, species="kale", *, cause=None, location="bed", removed_on=date(2026, 5, 1), **kwargs):
        return history.add_plant(
            location,
            species,
            date(2026, 4, 1),
            removed_on=removed_on,
            termination_type="died",
            termination_cause=cause,
            **kwargs,
        )

    @staticmethod
    def _codes(result) -> list[str]:
        return [f.code for f in result.findings]

    def test_without_the_reference_the_died_plant_counts_as_the_same_family_this_year(self, world) -> None:
        validator, _plan, history, *_ = world
        self._died(history, cause="frost")

        result = check(validator)

        assert self._codes(result) == ["rotation.pause_not_elapsed"]
        assert result.severity == "CRITICAL"

    def test_the_replaced_plant_is_no_previous_crop_after_an_abiotic_loss(self, world) -> None:
        validator, _plan, history, *_ = world
        replaced = self._died(history, cause="frost")

        result = check(validator, replant_of_plant_key=replaced)

        assert "rotation.pause_not_elapsed" not in self._codes(result)
        assert not [c for c in self._codes(result) if c.startswith("rotation.replant_")]
        assert result.severity in {"OK", "INFO"}

    @pytest.mark.parametrize("cause", ["disease", "pest"])
    def test_a_biotic_loss_leaves_a_warning_that_is_never_critical(self, world, cause) -> None:
        validator, _plan, history, *_ = world
        replaced = self._died(history, cause=cause)

        result = check(validator, replant_of_plant_key=replaced)

        finding = result.findings[0]
        assert (finding.code, finding.severity, finding.termination_cause) == (
            "rotation.replant_after_biotic_failure",
            "WARNING",
            cause,
        )
        assert (finding.family_key, finding.family_name, finding.species_key, finding.last_year) == (
            "brassica",
            "Brassicaaceae",
            "kale",
            2026,
        )
        assert "rotation.pause_not_elapsed" not in self._codes(result)
        assert result.severity == "WARNING"

    @pytest.mark.parametrize("cause", [None, "unknown"])
    def test_an_unknown_cause_leaves_an_info(self, world, cause) -> None:
        validator, _plan, history, *_ = world
        replaced = self._died(history, cause=cause)

        result = check(validator, replant_of_plant_key=replaced)

        replant = [f for f in result.findings if f.code.startswith("rotation.replant_")]
        assert [(f.code, f.severity, f.termination_cause) for f in replant] == [
            ("rotation.replant_cause_unknown", "INFO", cause)
        ]
        assert "rotation.pause_not_elapsed" not in self._codes(result)
        assert result.severity == "INFO"

    def test_another_family_planted_in_place_of_the_died_plant_gets_no_residual_hint(self, world) -> None:
        validator, _plan, history, *_ = world
        replaced = self._died(history, cause="disease")

        result = check(validator, "tomato", replant_of_plant_key=replaced)

        assert not [c for c in self._codes(result) if c.startswith("rotation.replant_")]
        assert "rotation.pause_not_elapsed" not in self._codes(result)

    def test_another_plant_of_the_same_family_this_year_still_counts(self, world) -> None:
        validator, _plan, history, *_ = world
        replaced = self._died(history, cause="frost")
        history.add_plant("bed", "cabbage", date(2026, 4, 1), removed_on=date(2026, 5, 20), termination_type="senesced")

        result = check(validator, replant_of_plant_key=replaced)

        (pause,) = [f for f in result.findings if f.code == "rotation.pause_not_elapsed"]
        assert (pause.species_key, pause.years_since, pause.severity) == ("cabbage", 0, "CRITICAL")

    def test_a_plant_that_died_last_year_still_counts(self, world) -> None:
        validator, _plan, history, *_ = world
        replaced = history.add_plant(
            "bed",
            "kale",
            date(2025, 4, 1),
            removed_on=date(2025, 6, 1),
            termination_type="died",
            termination_cause="disease",
        )

        result = check(validator, replant_of_plant_key=replaced)

        assert self._codes(result) == ["rotation.pause_not_elapsed"]
        assert result.findings[0].years_since == 1

    @pytest.mark.parametrize("termination_type", ["senesced", "harvested", "cancelled", None])
    def test_a_plant_that_did_not_die_is_not_left_out(self, world, termination_type) -> None:
        validator, _plan, history, *_ = world
        replaced = history.add_plant(
            "bed", "kale", date(2026, 4, 1), removed_on=date(2026, 5, 1), termination_type=termination_type
        )

        result = check(validator, replant_of_plant_key=replaced)

        assert self._codes(result) == ["rotation.pause_not_elapsed"]
        assert result.severity == "CRITICAL"

    def test_a_standing_plant_is_not_left_out(self, world) -> None:
        validator, _plan, history, *_ = world
        standing = history.add_plant("bed", "kale", date(2026, 4, 1))

        assert self._codes(check(validator, replant_of_plant_key=standing)) == ["rotation.pause_not_elapsed"]

    def test_an_unknown_key_is_ignored_without_an_error(self, world) -> None:
        validator, _plan, history, *_ = world
        self._died(history, cause="disease")

        result = check(validator, replant_of_plant_key="pi_does_not_exist")

        assert self._codes(result) == ["rotation.pause_not_elapsed"]

    def test_a_died_plant_of_another_bed_is_ignored(self, world) -> None:
        validator, _plan, history, *_ = world
        self._died(history, cause="frost")
        elsewhere = self._died(history, "cabbage", cause="disease", location="pot")

        result = check(validator, replant_of_plant_key=elsewhere)

        assert self._codes(result) == ["rotation.pause_not_elapsed"]

    def test_another_tenants_died_plant_in_a_bed_with_the_same_key_says_nothing(self, world) -> None:
        validator, _plan, history, *_ = world
        self._died(history, cause="frost")
        foreign = self._died(history, "cabbage", cause="disease", tenant=OTHER_TENANT)

        result = check(validator, replant_of_plant_key=foreign)

        # The own died kale still counts; the foreign plant's cause never shows (no oracle across tenants).
        assert self._codes(result) == ["rotation.pause_not_elapsed"]
        assert all(f.termination_cause is None for f in result.findings)

    def test_a_soil_reset_after_the_loss_leaves_no_residual_hint(self, world) -> None:
        validator, plan, history, *_ = world
        plan.locations["bed"] = make_location("bed", soil_profile=SoilProfile(rotation_reset_at=date(2026, 5, 15)))
        replaced = self._died(history, cause="disease")

        result = check(validator, replant_of_plant_key=replaced)

        assert not [c for c in self._codes(result) if c.startswith("rotation.replant_")]
        assert "rotation.pause_not_elapsed" not in self._codes(result)

    def test_a_perennial_that_stood_last_year_still_counts_for_last_year(self, world) -> None:
        validator, _plan, history, *_ = world
        replaced = history.add_plant(
            "bed",
            "kale",
            date(2025, 4, 1),
            removed_on=date(2026, 5, 1),
            termination_type="died",
            termination_cause="disease",
        )

        result = check(validator, replant_of_plant_key=replaced)

        (pause,) = [f for f in result.findings if f.code == "rotation.pause_not_elapsed"]
        assert (pause.last_year, pause.years_since) == (2025, 1)
        assert "rotation.replant_after_biotic_failure" in self._codes(result)

    def test_the_timeline_still_lists_the_died_plant(self, world) -> None:
        validator, _plan, history, *_ = world
        replaced = self._died(history, cause="disease")
        check(validator, replant_of_plant_key=replaced)

        timeline = validator.rotation_timeline("bed", tenant_key=TENANT, years=5)

        assert [(e.year, e.family_key, e.species_key) for e in timeline.entries] == [(2026, "brassica", "kale")]

    def test_a_bed_that_is_off_says_nothing_about_the_replant(self, world) -> None:
        validator, _plan, history, *_ = world
        replaced = self._died(history, cause="disease", location="pot")

        result = check(validator, location="pot", replant_of_plant_key=replaced)

        assert (result.applicable, result.findings) == (False, [])
