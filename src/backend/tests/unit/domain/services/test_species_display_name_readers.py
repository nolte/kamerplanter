"""#2902 — every server-side reader that builds ONE species name follows the display rule.

``Species.common_names`` lists the English name first for most seeded species; the readers
took that first entry and showed "Tomato" in the German UI. Each reader here is driven with
the English-first list plus a language map and must produce the German name (the canonical
language - none of these readers receives the UI language from its client), the English one
where the reader has a language (the printed checklist), the first listed name for a species
without a map, and the scientific fallback (or no vernacular name where the reader shows the
scientific name in a field of its own).

The AQL readers are proven against a server in
``tests/integration/test_species_display_names_aql.py``; their Python resolution is covered
below through the fake cursors as well.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.api.v1.diary.tenant_router import _PlantContext
from app.common.enums import DataOrigin
from app.data_access.arango.plant_state_repository import ArangoPlantStateRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.engines.sowing_calendar_engine import (
    FrostConfig,
    GrowingPeriodData,
    SowingCalendarEngine,
    SpeciesData,
)
from app.domain.models.care_reminder import CareProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.services.activity_plan_service import ActivityPlanService
from app.domain.services.ai_context_builder import AiContextBuilder
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.overwintering_profile_service import OverwinteringProfileService
from app.domain.services.print_service import PrintService

TENANT = "tenant-1"
SCIENTIFIC = "Solanum lycopersicum"

#: ``case -> (common_names, common_names_i18n)``.
_CASES: dict[str, tuple[list[str], dict[str, list[str]]]] = {
    # English first, as in species.yaml; the map names the German one.
    "map": (["Tomato", "Tomate", "Paradeiser"], {"en": ["Tomato"], "de": ["Tomate", "Paradeiser"]}),
    # A tenant-created or CSV-imported species: no map, the first listed name stands.
    "no_map": (["Meine Tomate", "Tomato"], {}),
    # A map without German, and a species without any name: nothing vernacular to show.
    "no_german": (["Tomato"], {"en": ["Tomato"]}),
    "no_names": ([], {}),
}

#: The vernacular name in the canonical language per case (``None`` = none to show).
_VERNACULAR_DE = {"map": "Tomate", "no_map": "Meine Tomate", "no_german": None, "no_names": None}
#: The single display name (vernacular, else scientific) in the canonical language per case.
_DISPLAY_DE = {case: name or SCIENTIFIC for case, name in _VERNACULAR_DE.items()}


def _species(case: str, **fields: Any) -> Species:
    names, names_i18n = _CASES[case]
    return Species(
        _key="sp",
        scientific_name=SCIENTIFIC,
        genus="Solanum",
        common_names=names,
        common_names_i18n=names_i18n,
        **fields,
    )


def _plant(key: str = "p1") -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=TENANT,
        instance_id=f"I-{key}",
        species_key="sp",
        plant_name=f"Plant {key}",
        planted_on=date(2024, 1, 1),
    )


def _species_repo(species: Species) -> MagicMock:
    repo = MagicMock()
    repo.get_by_key.return_value = species
    repo.get_or_raise.return_value = species
    return repo


# ── Print: the care checklist has a document language ─────────────────────────


class TestPrintedCareChecklist:
    def _species_name(self, species: Species, locale: str) -> str | None:
        plants = MagicMock()
        plants.get_all.return_value = ([_plant()], 1)
        care = MagicMock()
        care.get_care_dashboard.return_value = []
        engine = MagicMock()
        engine.render_pdf.return_value = b"%PDF"
        service = PrintService(
            nutrient_plan_service=MagicMock(),
            care_reminder_service=care,
            fertilizer_repo=MagicMock(),
            plant_repo=plants,
            species_repo=_species_repo(species),
            print_engine=engine,
            site_repo=MagicMock(),
            app_base_url="https://app.example.com",
        )

        service.generate_care_checklist_pdf(TENANT, locale=locale)

        (plant_data,) = care.get_care_dashboard.call_args.args[:1]
        return plant_data[0]["species_name"]

    @pytest.mark.parametrize("case", list(_CASES))
    def test_german_document_names_the_species_in_german(self, case: str) -> None:
        assert self._species_name(_species(case), "de") == _DISPLAY_DE[case]

    def test_english_document_names_the_species_in_english(self) -> None:
        assert self._species_name(_species("map"), "en") == "Tomato"
        # a language without names falls back to German, then to the scientific name
        assert self._species_name(_species("no_german"), "en") == "Tomato"
        assert self._species_name(_species("no_map"), "en") == "Meine Tomate"


# ── Care dashboard: no request language, canonical German ─────────────────────


class TestCareDashboard:
    @pytest.mark.parametrize("case", list(_CASES))
    def test_the_entry_names_the_species_by_the_rule(self, case: str) -> None:
        care_repo = MagicMock()
        care_repo.get_last_confirmation.return_value = None
        care_repo.get_profile_by_plant_key.return_value = CareProfile(
            watering_interval_days=7,
            winter_watering_multiplier=1.5,
            plant_key="p1",
            auto_generated=True,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        plants = MagicMock()
        plants.get_all.return_value = ([_plant()], 1)
        service = CareReminderService(
            care_repo,
            CareReminderEngine(),
            plant_repo=plants,
            species_repo=_species_repo(_species(case)),
            nutrient_plan_repo=MagicMock(get_plant_plan=MagicMock(return_value=None)),
        )

        entries = service.get_care_dashboard_for_tenant(tenant_key=TENANT)

        assert entries
        assert {entry.species_name for entry in entries} == {_DISPLAY_DE[case]}


# ── Overwintering overview: the scientific name has its own label ─────────────


class TestOverwinteringLabels:
    @pytest.mark.parametrize("case", list(_CASES))
    def test_the_common_name_label_follows_the_rule(self, case: str) -> None:
        plants = MagicMock()
        plants.get_by_key.return_value = _plant()
        service = OverwinteringProfileService(
            MagicMock(), plant_repo=plants, species_repo=_species_repo(_species(case))
        )

        labels = service._resolve_subject_labels(TENANT, plant_key="p1", planting_run_key=None)

        assert labels["species_common_name"] == _VERNACULAR_DE[case]
        assert labels["species_scientific_name"] == SCIENTIFIC


# ── Activity plan: the generated template's persisted name ────────────────────


class TestActivityPlanTemplateName:
    @pytest.mark.parametrize("case", list(_CASES))
    def test_the_template_is_named_in_the_canonical_language(self, case: str) -> None:
        service = ActivityPlanService(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            species_repo=_species_repo(_species(case)),
        )

        _species_obj, name, _family = service._resolve_species_info("sp")

        assert name == _DISPLAY_DE[case]


# ── Knowledge-service context: a vernacular hint when the scientific name is missing ──


class TestAiContextHint:
    @pytest.mark.parametrize("case", list(_CASES))
    def test_the_hint_is_the_canonical_vernacular_name(self, case: str) -> None:
        names, names_i18n = _CASES[case]
        species = SimpleNamespace(
            origin=DataOrigin.TENANT,
            scientific_name="",
            genus="Solanum",
            common_names=names,
            common_names_i18n=names_i18n,
            parent_species_key=None,
            family_key=None,
        )

        _value, hint, _confidence = AiContextBuilder().resolve_species_for_ks(species)  # type: ignore[arg-type]

        assert hint == _VERNACULAR_DE[case]


# ── Sowing calendar: the engine labels in the language it is given ────────────


class TestSowingCalendarLabel:
    @staticmethod
    def _label(case: str, **language: str) -> str:
        names, names_i18n = _CASES[case]
        species = SpeciesData(
            key="sp",
            scientific_name=SCIENTIFIC,
            common_names=names,
            common_names_i18n=names_i18n,
            growing_periods=[GrowingPeriodData(direct_sow_months=[4, 5], harvest_months=[7, 8])],
        )
        (entry,) = SowingCalendarEngine().build_calendar([species], FrostConfig(), 2026, **language)
        assert entry.species_name == SCIENTIFIC
        return entry.common_name

    @pytest.mark.parametrize("case", list(_CASES))
    def test_canonical_by_default(self, case: str) -> None:
        assert self._label(case) == (_VERNACULAR_DE[case] or "")

    def test_the_requested_language(self) -> None:
        assert self._label("map", language="en") == "Tomato"
        assert self._label("map", language="de-DE") == "Tomate"

    def test_the_calendar_service_hands_the_map_to_the_engine(self) -> None:
        from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
        from app.domain.models.species import GrowingPeriod
        from app.domain.services.calendar_service import CalendarService

        species = _species("map", growing_periods=[GrowingPeriod(direct_sow_months=[4, 5], harvest_months=[7, 8])])
        catalogue = MagicMock()
        catalogue.get_all.return_value = ([species], 1)
        service = CalendarService(MagicMock(), CalendarAggregationEngine(), MagicMock(), species_repo=catalogue)

        entries, _frost = service.get_sowing_calendar(None, 2026, tenant_key=TENANT)

        assert [entry.common_name for entry in entries] == ["Tomate"]


# ── Diary overview: scientific first, the vernacular name only stands in ──────


class TestDiaryOverviewSpeciesName:
    def test_the_scientific_name_stays_the_row_name(self) -> None:
        service = MagicMock()
        service.resolve_species.return_value = _species("map")

        assert _PlantContext(service, TENANT).species_name("sp") == SCIENTIFIC

    @pytest.mark.parametrize("case", list(_CASES))
    def test_without_a_scientific_name_the_canonical_vernacular_name_stands_in(self, case: str) -> None:
        names, names_i18n = _CASES[case]
        service = MagicMock()
        service.resolve_species.return_value = SimpleNamespace(
            scientific_name="", common_names=names, common_names_i18n=names_i18n
        )

        assert _PlantContext(service, TENANT).species_name("sp") == _VERNACULAR_DE[case]


# ── Repository rows: the Python half of the AQL readers ───────────────────────


class _Cursor:
    """An ``aql.execute`` that answers every statement with ``rows`` (copied, as a server would)."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        return iter([dict(row) for row in self.rows])


def _db(rows: list[dict[str, Any]]) -> SimpleNamespace:
    return SimpleNamespace(aql=_Cursor(rows))


class TestTaskRepositoryRows:
    @pytest.mark.parametrize("case", list(_CASES))
    def test_the_usage_stats_name_the_species_by_the_rule(self, case: str) -> None:
        names, names_i18n = _CASES[case]
        row = {
            "wf_key": "wf",
            "sp_found": True,
            "sp_common_names": names,
            "sp_common_names_i18n": names_i18n,
            "sp_scientific_name": SCIENTIFIC,
            "entity_count": 2,
        }

        stats = ArangoTaskRepository(_db([row])).get_workflow_usage_stats(["wf"], tenant_key=TENANT)  # type: ignore[arg-type]

        assert stats == {"wf": {"species_name": _DISPLAY_DE[case], "entity_count": 2}}

    def test_an_execution_without_a_species_has_an_empty_name_and_no_raw_fields(self) -> None:
        row = {
            "key": "we",
            "sp_found": False,
            "sp_common_names": None,
            "sp_common_names_i18n": None,
            "sp_scientific_name": None,
        }

        rows = ArangoTaskRepository(_db([row])).get_executions_for_template("wf", tenant_key=TENANT)  # type: ignore[arg-type]

        assert rows == [{"key": "we", "species_name": ""}]


class TestPlantStateRows:
    @pytest.mark.parametrize("case", list(_CASES))
    def test_a_sown_slot_is_named_by_the_rule(self, case: str) -> None:
        names, names_i18n = _CASES[case]
        row = {
            "slot_key": "s1",
            "slot_id": "BED_001",
            "sown_at": "2026-04-02",
            "run_key": "run",
            "entry_key": "e1",
            "species_key": "sp",
            "cultivar_key": None,
            "species_common_names": names,
            "species_common_names_i18n": names_i18n,
            "scientific_name": SCIENTIFIC,
            "cultivar_name": None,
        }

        (slot,) = ArangoPlantStateRepository(_db([row])).list_sown_slots("bed", tenant_key=TENANT)  # type: ignore[arg-type]

        assert slot.species_name == _VERNACULAR_DE[case]
