"""REQ-053 §11.3a Nr. 6-7 / GP-FR-193 (#2888 F-21): what a bed's soil hazard says about a planting.

Over the shipped knowledge table (the seed YAML), so a verdict here is the verdict the planting dialog shows. Pinned:
the stages (pause with its end, no evidenced pause without a time statement, residual risk, nothing after the
evidenced survival - operator decision P3), the open end without an evidenced survival (P5), soft hazards and hosts
below 3/3 as hints only (P4), the finest host level with its non-hosts, and fresh substrate.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.enums import EvidenceStatus, HostLevel, PathogenConfirmationSource, SoilHazard
from app.data_access.knowledge.soil_hazard_knowledge_source import YamlSoilHazardKnowledgeSource
from app.domain.engines.soil_hazard_planting_engine import (
    SOIL_HAZARD_NO_EVIDENCED_PAUSE,
    SOIL_HAZARD_PAUSE,
    SOIL_HAZARD_RESIDUAL,
    SOIL_HAZARD_SOFT,
    SOIL_HAZARD_UNCERTAIN_HOST,
    PlantedSpecies,
    add_years,
    judge_soil_hazards,
)
from app.domain.models.bed_soil_hazard import BedSoilHazard
from app.domain.models.soil_hazard_knowledge import Evidence, SoilHazardKnowledgeTable

TABLE: SoilHazardKnowledgeTable = YamlSoilHazardKnowledgeSource().get_table()

CABBAGE = PlantedSpecies("Brassica oleracea var. capitata", "Brassica", "Brassicaceae")
ONION = PlantedSpecies("Allium cepa", "Allium", "Amaryllidaceae")
CLIVIA = PlantedSpecies("Clivia miniata", "Clivia", "Amaryllidaceae")
TOMATO = PlantedSpecies("Solanum lycopersicum", "Solanum", "Solanaceae")
BEAN = PlantedSpecies("Phaseolus vulgaris", "Phaseolus", "Fabaceae")
PEA = PlantedSpecies("Pisum sativum", "Pisum", "Fabaceae")
CARROT = PlantedSpecies("Daucus carota", "Daucus", "Apiaceae")
MAIZE = PlantedSpecies("Zea mays", "Zea", "Poaceae")


def entry(hazard: SoilHazard, confirmed_at: date) -> BedSoilHazard:
    return BedSoilHazard(hazard=hazard, confirmed_at=confirmed_at, source=PathogenConfirmationSource.LAB_TEST)


def judge(hazard: SoilHazard, confirmed_at: date, species: PlantedSpecies, today: date, **kwargs):
    return judge_soil_hazards([entry(hazard, confirmed_at)], kwargs.pop("table", TABLE), species, today=today, **kwargs)


def with_status(table: SoilHazardKnowledgeTable, hazard: SoilHazard, field: str, status: EvidenceStatus):
    """The table with one duration's status changed - a data change, no code (F-18 acceptance-4)."""
    rows = []
    for row in table.hazards:
        if row.hazard is hazard:
            value = getattr(row, field)
            sources = 3 if status is EvidenceStatus.EVIDENCED else 2
            evidence = Evidence(status=status, sources=sources, kind=value.evidence.kind, basis="test", ref="test")
            row = row.model_copy(update={field: value.model_copy(update={"evidence": evidence})})
        rows.append(row)
    return SoilHazardKnowledgeTable(hazards=tuple(rows))


class TestAHostInsideAndAfterThePause:
    """acceptance-1: clubroot, pause 7 (3/3 range), survival 15 (3/3 lower bound), host Brassicaceae (3/3)."""

    def test_inside_the_pause_a_warning_names_its_end(self) -> None:
        (verdict,) = judge(SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2026, 6, 1))

        assert (verdict.code, verdict.severity, verdict.stage, verdict.until) == (
            SOIL_HAZARD_PAUSE,
            "WARNING",
            "pause",
            date(2029, 7, 1),
        )
        assert (verdict.host.level, verdict.host.name, verdict.host.evidenced) == (
            HostLevel.FAMILY,
            "Brassicaceae",
            True,
        )

    def test_after_the_pause_a_hint_until_the_evidenced_survival(self) -> None:
        (verdict,) = judge(SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2030, 3, 1))

        assert (verdict.code, verdict.severity, verdict.until) == (SOIL_HAZARD_RESIDUAL, "INFO", date(2037, 7, 1))

    def test_after_a_lower_bound_survival_nothing_operator_decision_p3(self) -> None:
        assert judge(SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2037, 7, 1)) == []

    def test_the_pause_ends_on_its_anniversary(self) -> None:
        (last_day,) = judge(SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2029, 6, 30))
        (first_day,) = judge(SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2029, 7, 1))

        assert (last_day.stage, first_day.stage) == ("pause", "residual")

    def test_no_evidenced_survival_after_the_pause_keeps_the_hint_open_operator_decision_p5(self) -> None:
        # cyst_nematode: pause 3 (3/3), survival contradictory.
        (verdict,) = judge(SoilHazard.CYST_NEMATODE, date(2010, 5, 1), CABBAGE, date(2026, 6, 1))

        assert (verdict.code, verdict.severity, verdict.until) == (SOIL_HAZARD_RESIDUAL, "INFO", None)

    def test_a_species_that_is_no_host_hears_nothing(self) -> None:
        assert judge(SoilHazard.CLUBROOT, date(2025, 7, 1), TOMATO, date(2026, 6, 1)) == []


class TestNoEvidencedPause:
    """acceptance-2: a warning without a time statement - until the evidenced survival, else without an end."""

    def test_white_rot_warns_without_a_date_until_the_survival(self) -> None:
        # white_rot: pause 1/3, survival 15 (3/3 lower bound), host genus Allium.
        (verdict,) = judge(SoilHazard.WHITE_ROT, date(2024, 8, 1), ONION, date(2026, 6, 1))

        assert (verdict.code, verdict.severity, verdict.stage, verdict.until) == (
            SOIL_HAZARD_NO_EVIDENCED_PAUSE,
            "WARNING",
            "no_evidenced_pause",
            None,
        )
        assert judge(SoilHazard.WHITE_ROT, date(2024, 8, 1), ONION, date(2039, 8, 1)) == []

    def test_juglone_warns_without_an_end(self) -> None:
        # juglone: pause contradictory, survival not applicable; tomato is a 3/3 host (species level).
        (verdict,) = judge(SoilHazard.JUGLONE, date(1990, 1, 1), TOMATO, date(2026, 6, 1))

        assert (verdict.code, verdict.severity, verdict.until) == (SOIL_HAZARD_NO_EVIDENCED_PAUSE, "WARNING", None)
        assert (verdict.host.level, verdict.host.name) == (HostLevel.SPECIES, "Solanum lycopersicum")

    def test_clubroot_with_its_pause_withdrawn_warns_without_a_date_until_the_survival(self) -> None:
        """The survival-only case of the consistency check: a data change alone moves clubroot there."""
        table = with_status(TABLE, SoilHazard.CLUBROOT, "soil_persistence_years", EvidenceStatus.INSUFFICIENT)

        (inside,) = judge(SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2030, 3, 1), table=table)

        assert (inside.code, inside.severity, inside.until) == (SOIL_HAZARD_NO_EVIDENCED_PAUSE, "WARNING", None)
        assert judge(SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2037, 7, 1), table=table) == []


class TestSoftHazardsAndUncertainHosts:
    """acceptance-3 and operator decision P4: never a warning, a hint in every stage."""

    @pytest.mark.parametrize("hazard", [SoilHazard.ROOT_KNOT_NEMATODE, SoilHazard.SCLEROTINIA])
    def test_a_soft_hazard_is_a_hint(self, hazard) -> None:
        (verdict,) = judge(hazard, date(2025, 8, 1), CARROT, date(2026, 6, 1))

        assert (verdict.code, verdict.severity) == (SOIL_HAZARD_SOFT, "INFO")

    def test_sclerotinia_keeps_its_evidenced_pause_as_the_end_of_the_first_stage(self) -> None:
        (verdict,) = judge(SoilHazard.SCLEROTINIA, date(2025, 8, 1), BEAN, date(2026, 6, 1))

        assert (verdict.stage, verdict.until, verdict.severity) == ("pause", date(2030, 8, 1), "INFO")

    def test_a_host_below_three_sources_is_a_hint_inside_the_pause(self) -> None:
        # verticillium: pause 4 (3/3); Solanaceae a host with 2/3 only.
        (verdict,) = judge(SoilHazard.VERTICILLIUM, date(2025, 8, 1), TOMATO, date(2026, 6, 1))

        assert (verdict.code, verdict.severity, verdict.stage, verdict.host.evidenced) == (
            SOIL_HAZARD_UNCERTAIN_HOST,
            "INFO",
            "pause",
            False,
        )

    def test_an_evidenced_host_of_the_same_hazard_still_warns(self) -> None:
        (verdict,) = judge(SoilHazard.VERTICILLIUM, date(2025, 8, 1), CABBAGE, date(2026, 6, 1))

        assert (verdict.code, verdict.severity) == (SOIL_HAZARD_PAUSE, "WARNING")

    def test_juglone_on_a_species_of_the_one_source_list_is_a_hint(self) -> None:
        # Purdue rest list (1/3): asparagus.
        asparagus = PlantedSpecies("Asparagus officinalis", "Asparagus", "Asparagaceae")

        (verdict,) = judge(SoilHazard.JUGLONE, date(2020, 1, 1), asparagus, date(2026, 6, 1))

        assert (verdict.code, verdict.severity, verdict.host.evidenced) == (SOIL_HAZARD_UNCERTAIN_HOST, "INFO", False)


class TestTheFinestHostLevel:
    def test_white_rot_hits_allium_not_the_rest_of_the_family(self) -> None:
        assert judge(SoilHazard.WHITE_ROT, date(2025, 8, 1), CLIVIA, date(2026, 6, 1)) == []

    def test_a_species_name_covers_its_varieties(self) -> None:
        planted = PlantedSpecies("Spinacia oleracea var. inermis", "", None)

        (verdict,) = judge(SoilHazard.VERTICILLIUM, date(2025, 8, 1), planted, date(2026, 6, 1))

        assert (verdict.host.level, verdict.host.name) == (HostLevel.SPECIES, "Spinacia oleracea")

    def test_a_species_name_is_no_prefix_of_another_epithet(self) -> None:
        planted = PlantedSpecies("Spinacia oleraceae", "", None)

        assert judge(SoilHazard.VERTICILLIUM, date(2025, 8, 1), planted, date(2026, 6, 1)) == []

    def test_a_listed_non_host_is_spared(self) -> None:
        # pea_root_rot: hosts at genus/species level, Phaseolus vulgaris an evidenced non-host.
        assert judge(SoilHazard.PEA_ROOT_ROT, date(2025, 8, 1), BEAN, date(2026, 6, 1)) == []
        (pea,) = judge(SoilHazard.PEA_ROOT_ROT, date(2025, 8, 1), PEA, date(2026, 6, 1))
        assert (pea.host.level, pea.host.name) == (HostLevel.GENUS, "Pisum")

    def test_a_non_host_family_is_spared_by_a_soft_hazard(self) -> None:
        assert judge(SoilHazard.SCLEROTINIA, date(2025, 8, 1), MAIZE, date(2026, 6, 1)) == []

    def test_the_family_name_is_matched_regardless_of_case_and_spaces(self) -> None:
        planted = PlantedSpecies("", "", "  brassicaceae ")

        (verdict,) = judge(SoilHazard.CLUBROOT, date(2025, 8, 1), planted, date(2026, 6, 1))

        assert verdict.host.level is HostLevel.FAMILY

    def test_a_species_without_family_genus_or_name_is_no_host(self) -> None:
        assert judge(SoilHazard.CLUBROOT, date(2025, 8, 1), PlantedSpecies("", "", None), date(2026, 6, 1)) == []


class TestFreshSubstrate:
    """acceptance-5: a substrate renewed after the confirmation lifts the hazard."""

    def test_renewed_after_the_confirmation_nothing(self) -> None:
        assert (
            judge(
                SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2026, 6, 1), substrate_replaced_on=date(2023, 3, 1)
            )
            == []
        )

    @pytest.mark.parametrize("renewed", [date(2022, 7, 1), date(2021, 3, 1)])
    def test_renewed_on_or_before_the_confirmation_the_hazard_stays(self, renewed) -> None:
        (verdict,) = judge(
            SoilHazard.CLUBROOT, date(2022, 7, 1), CABBAGE, date(2026, 6, 1), substrate_replaced_on=renewed
        )

        assert verdict.code == SOIL_HAZARD_PAUSE

    def test_only_the_hazards_confirmed_before_the_renewal_are_lifted(self) -> None:
        entries = [entry(SoilHazard.CLUBROOT, date(2022, 7, 1)), entry(SoilHazard.VERTICILLIUM, date(2025, 8, 1))]

        verdicts = judge_soil_hazards(
            entries, TABLE, CABBAGE, today=date(2026, 6, 1), substrate_replaced_on=date(2024, 3, 1)
        )

        assert [v.hazard for v in verdicts] == [SoilHazard.VERTICILLIUM]


class TestOrderAndDates:
    def test_warnings_come_first_then_by_hazard(self) -> None:
        entries = [entry(SoilHazard.SCLEROTINIA, date(2025, 8, 1)), entry(SoilHazard.CLUBROOT, date(2025, 8, 1))]

        verdicts = judge_soil_hazards(entries, TABLE, CABBAGE, today=date(2026, 6, 1))

        assert [(v.hazard, v.severity) for v in verdicts] == [
            (SoilHazard.CLUBROOT, "WARNING"),
            (SoilHazard.SCLEROTINIA, "INFO"),
        ]

    def test_a_leap_day_moves_to_the_last_of_february(self) -> None:
        assert add_years(date(2024, 2, 29), 7) == date(2031, 2, 28)
        assert add_years(date(2024, 2, 29), 4) == date(2028, 2, 29)
