"""REQ-053 §11.3a (#2888 F-21) — soil hazards, the cultivation window and the cause class in the planting check.

``validate_planting_in_location`` over the shipped knowledge table. Pinned per acceptance criterion of
``project/features/soil-aware-replant-hint.md``:

* acceptance-1 — a host of a bed's soil hazard warns inside the evidenced pause with its end, gets a hint after it,
  never a block; also on beds whose rotation check is off (``rotation_exempt``, switched off), never in a vessel or
  hydroponics.
* acceptance-2 — no evidenced pause: a warning without a time statement.
* acceptance-3 — root-knot nematodes and Sclerotinia: a hint only.
* acceptance-4 — a replant inside the cultivation window of the replaced plant does not count it at all (autumn
  garlic replaced in March); without ``days_to_maturity`` the calendar-year rule; a plant that stood past its window
  (a perennial crop) leaves out the year of its loss only.
* acceptance-5 — after "substrate renewed" no soil warning.
* acceptance-6 — previous-year rotation findings stay as they were next to a soil hazard.
* acceptance-7 — the residual hint follows the cause class of the loss.
"""

from __future__ import annotations

from datetime import date

import pytest
from freezegun import freeze_time

from app.common.enums import IrrigationSystem, PathogenConfirmationSource, SoilHazard
from app.data_access.knowledge.soil_hazard_knowledge_source import YamlSoilHazardKnowledgeSource
from app.domain.engines.crop_rotation_validator import (
    NOT_APPLICABLE_DISABLED,
    NOT_APPLICABLE_EXEMPT,
    CropRotationValidator,
)
from app.domain.models.bed_soil_hazard import BedSoilHazard
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.site import SoilProfile
from app.domain.models.species import Cultivar, Species
from tests.support.garden_plan_fakes import TENANT, FakePlanRepo, FakeSites, make_location, make_site
from tests.support.rotation_fakes import FakeFamilies, FakeRotationGraph, FakeRotationHistory, FakeSpecies

KNOWLEDGE = YamlSoilHazardKnowledgeSource()


@pytest.fixture(autouse=True)
def _frozen_today():
    with freeze_time("2026-06-01"):
        yield


def _species(key: str, scientific: str, family_key: str, **kwargs) -> Species:
    return Species(_key=key, scientific_name=scientific, genus=scientific.split()[0], family_key=family_key, **kwargs)


def _clubroot(confirmed_at: date = date(2022, 7, 1)) -> list[BedSoilHazard]:
    return [
        BedSoilHazard(hazard=SoilHazard.CLUBROOT, confirmed_at=confirmed_at, source=PathogenConfirmationSource.LAB_TEST)
    ]


def _hazard(hazard: SoilHazard, confirmed_at: date) -> BedSoilHazard:
    return BedSoilHazard(hazard=hazard, confirmed_at=confirmed_at, source=PathogenConfirmationSource.ADVISORY_SERVICE)


@pytest.fixture
def world():
    sites = FakeSites(make_site())
    plan = FakePlanRepo(sites)
    species = FakeSpecies(
        _species("cabbage", "Brassica oleracea", "fam_brassica"),
        _species("kale", "Brassica oleracea var. sabellica", "fam_brassica"),
        _species("garlic", "Allium sativum", "fam_amaryllis"),
        _species("onion", "Allium cepa", "fam_amaryllis"),
        _species("leek", "Allium porrum", "fam_amaryllis"),
        _species("tomato", "Solanum lycopersicum", "fam_solanum"),
        _species("carrot", "Daucus carota", "fam_apiaceae"),
        _species("strawberry", "Fragaria ananassa", "fam_rosaceae"),
    )
    # The culture duration lives on the cultivar (``Cultivar.days_to_maturity``); a plant without one has no window.
    for key, species_key, days in (
        ("cv_kale", "kale", 60),
        ("cv_garlic", "garlic", 240),
        ("cv_tomato", "tomato", 120),
        ("cv_strawberry", "strawberry", 90),
    ):
        species.cultivars[key] = Cultivar(_key=key, name=key, species_key=species_key, days_to_maturity=days)
    families = FakeFamilies(
        BotanicalFamily(_key="fam_brassica", name="Brassicaceae", rotation_pause_years=4),
        BotanicalFamily(_key="fam_amaryllis", name="Amaryllidaceae", rotation_pause_years=4),
        BotanicalFamily(_key="fam_solanum", name="Solanaceae", rotation_pause_years=4),
        BotanicalFamily(_key="fam_apiaceae", name="Apiaceae", rotation_pause_years=3),
        BotanicalFamily(_key="fam_rosaceae", name="Rosaceae", rotation_pause_years=4),
    )
    history = FakeRotationHistory()
    validator = CropRotationValidator(
        None,
        species,
        FakeRotationGraph(),
        site_repo=sites,
        family_repo=families,
        history_repo=history,
        soil_hazards=KNOWLEDGE,
    )
    plan.locations["bed"] = make_location("bed")
    return validator, plan, history


def check(validator, species: str, location: str = "bed", **kwargs):
    return validator.validate_planting_in_location(location, species, tenant_key=TENANT, **kwargs)


def codes(result) -> list[str]:
    return [finding.code for finding in result.findings]


def hazard_findings(result):
    return [finding for finding in result.findings if finding.code.startswith("soil_hazard.")]


class TestAHostOfTheBedsSoilHazard:
    """acceptance-1."""

    def test_inside_the_pause_a_warning_with_its_end(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot())

        result = check(validator, "cabbage")

        (finding,) = hazard_findings(result)
        assert (finding.severity, finding.code, finding.hazard, finding.hazard_stage, finding.hazard_until) == (
            "WARNING",
            "soil_hazard.pause",
            "clubroot",
            "pause",
            date(2029, 7, 1),
        )
        assert (finding.hazard_confirmed_at, finding.host_level, finding.host_name) == (
            date(2022, 7, 1),
            "family",
            "Brassicaceae",
        )
        assert "until 2029" in finding.message
        assert result.severity == "WARNING"
        assert all(f.severity != "CRITICAL" for f in result.findings)

    def test_after_the_pause_a_hint(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot(date(2018, 5, 1)))

        (finding,) = hazard_findings(check(validator, "cabbage"))

        assert (finding.severity, finding.code, finding.hazard_until) == (
            "INFO",
            "soil_hazard.residual",
            date(2033, 5, 1),
        )

    def test_after_the_evidenced_survival_nothing(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot(date(2011, 5, 1)))

        assert hazard_findings(check(validator, "cabbage")) == []

    def test_a_species_that_is_no_host_hears_nothing_of_the_hazard(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot())

        assert hazard_findings(check(validator, "tomato")) == []

    @pytest.mark.parametrize(
        ("flags", "reason"),
        [({"rotation_exempt": True}, NOT_APPLICABLE_EXEMPT), ({"rotation_enabled": False}, NOT_APPLICABLE_DISABLED)],
    )
    def test_a_bed_whose_rotation_check_is_off_still_warns(self, world, flags, reason) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot(), **flags)

        result = check(validator, "cabbage")

        assert (result.applicable, result.not_applicable_reason, result.severity) == (False, reason, "WARNING")
        assert codes(result) == ["soil_hazard.pause"]

    def test_an_exempt_bed_without_a_hazard_stays_silent(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", rotation_exempt=True)

        result = check(validator, "cabbage")

        assert (result.applicable, result.severity, result.findings) == (False, "OK", [])

    @pytest.mark.parametrize("location_type", ["planter", "tent", "shelf", "container"])
    def test_a_vessel_carries_no_soil_hazard(self, world, location_type) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", location_type_key=location_type, soil_hazards=_clubroot())

        assert hazard_findings(check(validator, "cabbage")) == []

    def test_hydroponics_carries_no_soil_hazard(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", irrigation_system=IrrigationSystem.NFT, soil_hazards=_clubroot())

        assert hazard_findings(check(validator, "cabbage")) == []

    def test_a_container_switched_on_reports_its_rotation_but_no_soil_hazard(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location(
            "bed", location_type_key="planter", rotation_enabled=True, soil_hazards=_clubroot()
        )

        result = check(validator, "cabbage")

        assert result.applicable is True
        assert hazard_findings(result) == []

    def test_without_the_knowledge_table_no_soil_hazard_is_reported(self, world) -> None:
        validator, plan, history = world
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot())
        bare = CropRotationValidator(
            None,
            validator._species_repo,
            FakeRotationGraph(),
            site_repo=validator._sites,
            family_repo=validator._families,
            history_repo=history,
        )

        assert hazard_findings(check(bare, "cabbage")) == []


class TestNoEvidencedPause:
    """acceptance-2."""

    def test_white_rot_warns_without_a_time_statement(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=[_hazard(SoilHazard.WHITE_ROT, date(2024, 8, 1))])

        (finding,) = hazard_findings(check(validator, "onion"))

        assert (finding.severity, finding.code, finding.hazard_until, finding.host_level) == (
            "WARNING",
            "soil_hazard.no_evidenced_pause",
            None,
            "genus",
        )
        assert "no cultivation pause is evidenced" in finding.message

    def test_a_tenants_own_species_without_a_genus_still_hits_a_genus_host(self, world) -> None:
        """Review S1: ``Species.genus`` is optional; "Allium porrum" with ``genus = ""`` is an *Allium* host."""
        validator, plan, _ = world
        validator._species_repo.by_key["own_leek"] = Species(
            _key="own_leek", scientific_name="Allium porrum", genus="", family_key="fam_amaryllis", tenant_key=TENANT
        )
        plan.locations["bed"] = make_location("bed", soil_hazards=[_hazard(SoilHazard.WHITE_ROT, date(2024, 8, 1))])

        (finding,) = hazard_findings(check(validator, "own_leek"))

        assert (finding.severity, finding.code, finding.host_level, finding.host_name) == (
            "WARNING",
            "soil_hazard.no_evidenced_pause",
            "genus",
            "Allium",
        )

    def test_juglone_warns_without_an_end(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=[_hazard(SoilHazard.JUGLONE, date(2001, 3, 1))])

        (finding,) = hazard_findings(check(validator, "tomato"))

        assert (finding.severity, finding.code, finding.hazard_until) == (
            "WARNING",
            "soil_hazard.no_evidenced_pause",
            None,
        )


class TestSoftHazards:
    """acceptance-3."""

    @pytest.mark.parametrize("hazard", [SoilHazard.ROOT_KNOT_NEMATODE, SoilHazard.SCLEROTINIA])
    def test_root_knot_nematodes_and_sclerotinia_are_a_hint(self, world, hazard) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=[_hazard(hazard, date(2025, 9, 1))])

        result = check(validator, "carrot")

        (finding,) = hazard_findings(result)
        assert (finding.severity, finding.code) == ("INFO", "soil_hazard.soft")
        assert result.severity in {"INFO", "OK"}

    def test_a_host_below_three_sources_is_a_hint(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location("bed", soil_hazards=[_hazard(SoilHazard.VERTICILLIUM, date(2025, 9, 1))])

        (finding,) = hazard_findings(check(validator, "tomato"))

        assert (finding.severity, finding.code) == ("INFO", "soil_hazard.uncertain_host")


class TestTheCultivationWindow:
    """acceptance-4: "the same season" is the cultivation window of the replaced plant."""

    def test_autumn_garlic_replaced_in_march_is_no_previous_crop(self, world) -> None:
        validator, _plan, history = world
        garlic = history.add_plant(
            "bed",
            "garlic",
            date(2025, 10, 15),
            removed_on=date(2026, 3, 10),
            termination_type="died",
            termination_cause="frost",
            cultivar_key="cv_garlic",
        )

        with freeze_time("2026-03-20"):
            result = check(validator, "leek", replant_of_plant_key=garlic)

        assert "rotation.pause_not_elapsed" not in codes(result)

    def test_without_the_window_last_years_part_of_the_garlic_still_counted(self, world) -> None:
        """The same garlic without a cultivar (no days_to_maturity) falls to the calendar-year rule (§11.3)."""
        validator, _plan, history = world
        garlic = history.add_plant(
            "bed",
            "garlic",
            date(2025, 10, 15),
            removed_on=date(2026, 3, 10),
            termination_type="died",
            termination_cause="frost",
        )

        with freeze_time("2026-03-20"):
            result = check(validator, "leek", replant_of_plant_key=garlic)

        (pause,) = [f for f in result.findings if f.code == "rotation.pause_not_elapsed"]
        assert (pause.last_year, pause.years_since) == (2025, 1)

    def test_a_replant_after_the_window_counts_the_replaced_plant(self, world) -> None:
        validator, _plan, history = world
        # kale: 60 days from 1 March 2026 ends 30 April; died 20 April; replanted 1 June (frozen today).
        kale = history.add_plant(
            "bed",
            "kale",
            date(2026, 3, 1),
            removed_on=date(2026, 4, 20),
            termination_type="died",
            termination_cause="disease",
            cultivar_key="cv_kale",
        )

        result = check(validator, "cabbage", replant_of_plant_key=kale)

        assert codes(result) == ["rotation.pause_not_elapsed"]
        assert result.findings[0].years_since == 0

    def test_a_loss_of_last_year_inside_the_window_is_no_previous_crop(self, world) -> None:
        validator, _plan, history = world
        garlic = history.add_plant(
            "bed",
            "garlic",
            date(2025, 10, 1),
            removed_on=date(2025, 12, 1),
            termination_type="died",
            termination_cause="frost",
            cultivar_key="cv_garlic",
        )

        with freeze_time("2026-02-15"):
            result = check(validator, "leek", replant_of_plant_key=garlic)

        assert "rotation.pause_not_elapsed" not in codes(result)

    def test_a_plant_inside_its_window_that_stood_longer_than_a_season_counts_for_its_earlier_years(self, world):
        """D-S4 (2026-11-28): a 1000-day cultivar planted 2024-04, lost 2025-09, replanted 2026-05 -> 2024 counts."""
        validator, _plan, history = world
        validator._species_repo.cultivars["cv_long"] = Cultivar(
            _key="cv_long", name="cv_long", species_key="cabbage", days_to_maturity=1000
        )
        long_one = history.add_plant(
            "bed",
            "cabbage",
            date(2024, 4, 15),
            removed_on=date(2025, 9, 10),
            termination_type="died",
            termination_cause="frost",
            cultivar_key="cv_long",
        )

        with freeze_time("2026-05-15"):
            result = check(validator, "cabbage", replant_of_plant_key=long_one)

        (pause,) = [f for f in result.findings if f.code == "rotation.pause_not_elapsed"]
        assert (pause.last_year, pause.years_since) == (2024, 2)

    def test_a_perennial_that_stood_past_its_window_leaves_out_only_the_year_of_its_loss(self, world) -> None:
        validator, _plan, history = world
        strawberry = history.add_plant(
            "bed",
            "strawberry",
            date(2024, 4, 1),
            removed_on=date(2026, 5, 1),
            termination_type="died",
            termination_cause="frost",
            cultivar_key="cv_strawberry",
        )

        result = check(validator, "strawberry", replant_of_plant_key=strawberry)

        (pause,) = [f for f in result.findings if f.code == "rotation.pause_not_elapsed"]
        assert (pause.last_year, pause.years_since) == (2025, 1)

    def test_a_perennial_lost_last_year_still_counts_this_year(self, world) -> None:
        validator, _plan, history = world
        strawberry = history.add_plant(
            "bed",
            "strawberry",
            date(2023, 4, 1),
            removed_on=date(2025, 9, 1),
            termination_type="died",
            termination_cause="frost",
            cultivar_key="cv_strawberry",
        )

        result = check(validator, "strawberry", replant_of_plant_key=strawberry)

        (pause,) = [f for f in result.findings if f.code == "rotation.pause_not_elapsed"]
        assert (pause.last_year, pause.years_since) == (2025, 1)
        assert not [c for c in codes(result) if c.startswith("rotation.replant_")]

    def test_the_timeline_still_lists_the_garlic(self, world) -> None:
        validator, _plan, history = world
        garlic = history.add_plant(
            "bed",
            "garlic",
            date(2025, 10, 15),
            removed_on=date(2026, 3, 10),
            termination_type="died",
            termination_cause="frost",
            cultivar_key="cv_garlic",
        )
        with freeze_time("2026-03-20"):
            check(validator, "leek", replant_of_plant_key=garlic)
            timeline = validator.rotation_timeline("bed", tenant_key=TENANT, years=5)

        assert [(e.year, e.species_key) for e in timeline.entries] == [(2026, "garlic"), (2025, "garlic")]


class TestFreshSubstrate:
    """acceptance-5."""

    def test_after_the_renewal_no_soil_warning(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location(
            "bed", soil_hazards=_clubroot(), soil_profile=SoilProfile(substrate_replaced_on=date(2024, 4, 1))
        )

        result = check(validator, "cabbage")

        assert hazard_findings(result) == []

    def test_a_renewal_before_the_confirmation_keeps_the_warning(self, world) -> None:
        validator, plan, _ = world
        plan.locations["bed"] = make_location(
            "bed", soil_hazards=_clubroot(), soil_profile=SoilProfile(substrate_replaced_on=date(2021, 4, 1))
        )

        assert codes(check(validator, "cabbage"))[0] == "soil_hazard.pause"

    def test_a_renewal_after_a_soil_borne_loss_lifts_the_residual_warning(self, world) -> None:
        validator, plan, history = world
        plan.locations["bed"] = make_location("bed", soil_profile=SoilProfile(substrate_replaced_on=date(2026, 5, 10)))
        replaced = history.add_plant(
            "bed",
            "kale",
            date(2026, 4, 1),
            removed_on=date(2026, 5, 1),
            termination_type="died",
            termination_cause="disease",
            failure_cause_class="disease_soil",
            cultivar_key="cv_kale",
        )

        with freeze_time("2026-05-20"):
            result = check(validator, "cabbage", replant_of_plant_key=replaced)

        assert not [c for c in codes(result) if c.startswith("rotation.replant_")]

    def test_a_renewal_in_the_future_is_refused(self) -> None:
        with pytest.raises(ValueError, match="substrate_replaced_on"):
            SoilProfile(substrate_replaced_on=date(2026, 6, 2))


class TestTheRotationAroundIt:
    """acceptance-6: the rotation findings of previous years stay as they were; one answer for both views."""

    def test_a_previous_year_finding_is_unchanged_next_to_a_soil_hazard(self, world) -> None:
        validator, plan, history = world
        history.add_plant("bed", "cabbage", date(2025, 4, 1), removed_on=date(2025, 9, 1))
        without = check(validator, "cabbage")
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot())

        with_hazard = check(validator, "cabbage")

        rotation = [f for f in with_hazard.findings if not f.code.startswith("soil_hazard.")]
        assert rotation == without.findings
        assert (without.severity, with_hazard.severity) == ("CRITICAL", "CRITICAL")
        assert codes(with_hazard) == ["rotation.pause_not_elapsed", "soil_hazard.pause"]


class TestTheResidualHintFollowsTheCauseClass:
    """acceptance-7: REQ-053 §11.3a Nr. 4."""

    def _died(self, history, failure_cause_class, cause="disease", **kwargs):
        return history.add_plant(
            "bed",
            "kale",
            date(2026, 4, 1),
            removed_on=date(2026, 5, 1),
            termination_type="died",
            termination_cause=cause,
            failure_cause_class=failure_cause_class,
            cultivar_key="cv_kale",
            **kwargs,
        )

    def _residual(self, result):
        return [
            (f.code, f.severity, f.failure_cause_class)
            for f in result.findings
            if f.code.startswith("rotation.replant_")
        ]

    @pytest.fixture(autouse=True)
    def _inside_the_window(self):
        # kale: 60 days from 1 April - the replant on 20 May lies inside its window.
        with freeze_time("2026-05-20"):
            yield

    @pytest.mark.parametrize(
        ("cls", "cause"), [("abiotic", "frost"), ("mechanical", "mechanical"), ("pest_foliar", "pest")]
    )
    def test_no_hint_for_a_loss_that_leaves_nothing_in_the_bed(self, world, cls, cause) -> None:
        validator, _plan, history = world

        result = check(validator, "cabbage", replant_of_plant_key=self._died(history, cls, cause))

        assert self._residual(result) == []

    def test_a_foliar_disease_says_remove_the_residues(self, world) -> None:
        validator, _plan, history = world

        result = check(validator, "cabbage", replant_of_plant_key=self._died(history, "disease_foliar"))

        assert self._residual(result) == [("rotation.replant_foliar_disease", "INFO", "disease_foliar")]
        assert "compost" in result.findings[0].message

    @pytest.mark.parametrize(("cls", "cause"), [("disease_soil", "disease"), ("pest_soil", "pest")])
    def test_an_unconfirmed_soil_borne_loss_is_an_overridable_warning(self, world, cls, cause) -> None:
        validator, _plan, history = world

        result = check(validator, "cabbage", replant_of_plant_key=self._died(history, cls, cause))

        assert self._residual(result) == [("rotation.replant_soil_borne", "WARNING", cls)]
        assert result.severity == "WARNING"

    def test_an_unknown_class_is_a_hint(self, world) -> None:
        validator, _plan, history = world

        result = check(validator, "cabbage", replant_of_plant_key=self._died(history, "unknown", "unknown"))

        assert self._residual(result) == [("rotation.replant_cause_unknown", "INFO", "unknown")]

    def test_a_confirmed_pathogen_on_the_bed_speaks_through_its_soil_hazard_alone(self, world) -> None:
        validator, plan, history = world
        plan.locations["bed"] = make_location("bed", soil_hazards=_clubroot(date(2026, 5, 1)))
        replaced = self._died(history, "disease_soil", failure_pathogen="clubroot", failure_pathogen_confirmed=True)

        result = check(validator, "cabbage", replant_of_plant_key=replaced)

        assert self._residual(result) == []
        # The bed's only planting is the replaced kale: the rotation cannot be verified, the soil hazard warns.
        assert codes(result) == ["soil_hazard.pause", "rotation.no_history"]

    def test_a_confirmed_pathogen_not_taken_over_keeps_the_warning(self, world) -> None:
        validator, _plan, history = world
        replaced = self._died(history, "disease_soil", failure_pathogen="clubroot", failure_pathogen_confirmed=True)

        result = check(validator, "cabbage", replant_of_plant_key=replaced)

        assert self._residual(result) == [("rotation.replant_soil_borne", "WARNING", "disease_soil")]

    def test_a_loss_without_a_class_keeps_the_rule_of_its_cause(self, world) -> None:
        validator, _plan, history = world

        result = check(validator, "cabbage", replant_of_plant_key=self._died(history, None, "pest"))

        assert self._residual(result) == [("rotation.replant_after_biotic_failure", "WARNING", None)]


class TestTheSoilAboveTheBed:
    """REQ-053 §11.3a Nr. 5 v1.60 (#2888 O3/O5): the parent chain's hazards and irrigation system reach the bed."""

    @staticmethod
    def _juglone() -> list[BedSoilHazard]:
        return [_hazard(SoilHazard.JUGLONE, date(2019, 3, 1))]

    def test_the_juglone_of_the_garden_warns_in_a_bed_in_it(self, world) -> None:
        validator, plan, _ = world
        plan.locations["garden"] = make_location("garden", location_type_key="garden", soil_hazards=self._juglone())
        plan.locations["bed"] = make_location("bed", parent_location_key="garden")

        (finding,) = hazard_findings(check(validator, "tomato"))

        assert (finding.hazard, finding.host_level, finding.host_name) == (
            "juglone",
            "species",
            "Solanum lycopersicum",
        )
        assert finding.severity == "WARNING"

    def test_it_reaches_through_a_zone_and_also_a_bed_whose_rotation_is_off(self, world) -> None:
        validator, plan, _ = world
        plan.locations["garden"] = make_location("garden", location_type_key="garden", soil_hazards=self._juglone())
        plan.locations["zone"] = make_location("zone", location_type_key="zone", parent_location_key="garden")
        plan.locations["bed"] = make_location("bed", parent_location_key="zone", rotation_exempt=True)

        assert [f.hazard for f in hazard_findings(check(validator, "tomato"))] == ["juglone"]

    def test_a_tent_in_between_ends_the_chain(self, world) -> None:
        validator, plan, _ = world
        plan.locations["garden"] = make_location("garden", location_type_key="garden", soil_hazards=self._juglone())
        plan.locations["tent"] = make_location("tent", location_type_key="tent", parent_location_key="garden")
        plan.locations["bed"] = make_location("bed", parent_location_key="tent")

        assert hazard_findings(check(validator, "tomato")) == []

    def test_a_planter_in_the_garden_carries_none_of_it(self, world) -> None:
        validator, plan, _ = world
        plan.locations["garden"] = make_location("garden", location_type_key="garden", soil_hazards=self._juglone())
        plan.locations["bed"] = make_location("bed", location_type_key="planter", parent_location_key="garden")

        assert hazard_findings(check(validator, "tomato")) == []

    def test_fresh_substrate_of_the_bed_lifts_an_inherited_pathogen_too(self, world) -> None:
        validator, plan, _ = world
        plan.locations["outer"] = make_location("outer", soil_hazards=_clubroot())
        plan.locations["bed"] = make_location(
            "bed", parent_location_key="outer", soil_profile=SoilProfile(substrate_replaced_on=date(2024, 4, 1))
        )

        assert hazard_findings(check(validator, "cabbage")) == []

    def test_fresh_substrate_never_lifts_juglone_inherited_or_own(self, world) -> None:
        """Review S2 (REQ-053 v1.61 §11.3a Nr. 7): the walnut's roots keep releasing it into the new soil."""
        validator, plan, _ = world
        renewed = SoilProfile(substrate_replaced_on=date(2024, 4, 1))
        plan.locations["garden"] = make_location("garden", location_type_key="garden", soil_hazards=self._juglone())
        plan.locations["bed"] = make_location("bed", parent_location_key="garden", soil_profile=renewed)
        plan.locations["own"] = make_location("own", soil_profile=renewed, soil_hazards=self._juglone())

        assert [f.hazard for f in hazard_findings(check(validator, "tomato"))] == ["juglone"]
        assert [f.hazard for f in hazard_findings(check(validator, "tomato", "own"))] == ["juglone"]

    def test_an_inherited_finding_names_the_location_that_holds_it(self, world) -> None:
        """Review S3: "at 'Obstwiese' above this bed", not "in this bed"; the bed's own one names none."""
        validator, plan, _ = world
        plan.locations["garden"] = make_location(
            "garden", "Obstwiese", location_type_key="garden", soil_hazards=self._juglone()
        )
        plan.locations["bed"] = make_location("bed", parent_location_key="garden")
        plan.locations["own"] = make_location("own", soil_hazards=self._juglone())

        (inherited,) = hazard_findings(check(validator, "tomato"))
        (own,) = hazard_findings(check(validator, "tomato", "own"))

        assert (inherited.hazard_location_key, inherited.hazard_location_name) == ("garden", "Obstwiese")
        assert "at 'Obstwiese' above this bed" in inherited.message
        assert (own.hazard_location_key, own.hazard_location_name) == (None, None)
        assert "in this bed" in own.message

    def test_a_soil_bed_under_a_hydroponic_room_keeps_its_own_hazards(self, world) -> None:
        """Review S1 (REQ-053 v1.61): a greenhouse on ``hydro`` for its NFT channel does not silence its soil bed."""
        validator, plan, _ = world
        plan.locations["room"] = make_location(
            "room", location_type_key="greenhouse", irrigation_system=IrrigationSystem.HYDRO
        )
        plan.locations["bed"] = make_location("bed", parent_location_key="room", soil_hazards=_clubroot())

        assert [f.code for f in hazard_findings(check(validator, "cabbage"))] == ["soil_hazard.pause"]

    def test_under_a_hydroponic_room_the_hazards_from_above_are_not_checked(self, world) -> None:
        validator, plan, _ = world
        plan.locations["garden"] = make_location("garden", location_type_key="garden", soil_hazards=self._juglone())
        plan.locations["room"] = make_location(
            "room",
            location_type_key="greenhouse",
            irrigation_system=IrrigationSystem.HYDRO,
            parent_location_key="garden",
        )
        plan.locations["bed"] = make_location("bed", parent_location_key="room")

        assert hazard_findings(check(validator, "tomato")) == []

    def test_a_drip_bed_under_the_room_keeps_its_check(self, world) -> None:
        validator, plan, _ = world
        plan.locations["room"] = make_location(
            "room", location_type_key="greenhouse", irrigation_system=IrrigationSystem.HYDRO
        )
        plan.locations["bed"] = make_location(
            "bed", parent_location_key="room", irrigation_system=IrrigationSystem.DRIP, soil_hazards=_clubroot()
        )

        assert [f.code for f in hazard_findings(check(validator, "cabbage"))] == ["soil_hazard.pause"]
