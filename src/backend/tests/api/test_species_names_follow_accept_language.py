"""#2902 — every endpoint that words a species name on the server follows ``Accept-Language``.

The frontend sends its UI language on every request (``api/client.ts``); the routers resolve
it once through ``app.common.locale.get_request_locale`` (NFR-017 R-112/R-114) and hand it
down as ``language``. Per endpoint family, against the real router, the real service and -
where the name is resolved in a repository - the real repository's Python half:

* an English-first ``common_names`` with a language map answers ``Tomato`` for ``en`` and
  ``Tomate`` for ``de``; without the header it is the canonical ``Tomate``;
* a species without a map answers its first listed name whatever the language.

The succession recommendation is covered in ``test_bed_rotation_api.py`` with the planner's
own fakes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.calendar import tenant_router as calendar_router_module
from app.api.v1.care_reminders.tenant_router import router as care_router
from app.api.v1.dashboard.tenant_router import router as dashboard_router
from app.api.v1.diary.tenant_router import router as diary_router
from app.api.v1.locations.tenant_router import router as locations_router
from app.api.v1.overwintering_profiles.tenant_router import router as overwintering_router
from app.api.v1.tasks.tenant_router import router as tasks_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_care_reminder_service,
    get_dashboard_service,
    get_overwintering_profile_service,
    get_plant_diary_service,
    get_plant_instance_service,
    get_plant_state_service,
    get_task_service,
)
from app.common.enums import HardinessRating, TenantRole, WinterAction
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.plant_state_repository import ArangoPlantStateRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.interfaces.plant_state_repository import PlantStateSource
from app.domain.models.care_reminder import CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location, Site
from app.domain.models.species import GrowingPeriod, Species
from app.domain.models.task import WorkflowTemplate
from app.domain.models.tenant_context import TenantContext
from app.domain.services.calendar_service import CalendarService
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.dashboard_service import DashboardService
from app.domain.services.overwintering_profile_service import OverwinteringProfileService
from app.domain.services.plant_diary_service import PlantDiaryService
from app.domain.services.plant_state_service import PlantStateService
from tests.support.diary_fakes import FakeDiaryRepository, FakePlantInstanceService

SLUG = "anna"
TENANT = "tenant-a"
PREFIX = f"/api/v1/t/{SLUG}"
SCIENTIFIC = "Solanum lycopersicum"

#: ``case -> (common_names, common_names_i18n)``: English first as in species.yaml, and a species without a map.
_NAMES: dict[str, tuple[list[str], dict[str, list[str]]]] = {
    "map": (["Tomato", "Tomate"], {"en": ["Tomato"], "de": ["Tomate"]}),
    "no_map": (["Meine Tomate", "Tomato"], {}),
}
#: ``header case -> request headers``; ``absent`` sends none (httpx adds no Accept-Language of its own).
_HEADERS: dict[str, dict[str, str]] = {
    "en": {"Accept-Language": "en-GB,en;q=0.9,de;q=0.8"},
    "de": {"Accept-Language": "de-DE,de;q=0.9,en;q=0.8"},
    "absent": {},
}
_EXPECTED: dict[tuple[str, str], str] = {
    ("map", "en"): "Tomato",
    ("map", "de"): "Tomate",
    ("map", "absent"): "Tomate",
    ("no_map", "en"): "Meine Tomate",
    ("no_map", "de"): "Meine Tomate",
    ("no_map", "absent"): "Meine Tomate",
}
_CASES = sorted(_EXPECTED)


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT, tenant_slug=SLUG, user_key="user-1", role=TenantRole.GROWER)


def _species(case: str, **fields: Any) -> Species:
    names, names_i18n = _NAMES[case]
    return Species(
        _key="sp",
        scientific_name=SCIENTIFIC,
        genus="Solanum",
        common_names=names,
        common_names_i18n=names_i18n,
        **fields,
    )


def _plant() -> PlantInstance:
    return PlantInstance(
        _key="p1",
        tenant_key=TENANT,
        instance_id="TOM-1",
        species_key="sp",
        plant_name="Tom",
        planted_on=date(2026, 4, 1),
    )


def _species_repo(species: Species) -> MagicMock:
    repo = MagicMock()
    repo.get_by_key.return_value = species
    return repo


def _client(router: Any, overrides: dict[Callable[..., Any], Callable[..., Any]]) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix=PREFIX)
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides.update(overrides)
    return TestClient(app)


class _Rows:
    """An ``aql.execute`` answering with fresh copies of the rows ``answer(query)`` picks (the server's raw rows)."""

    def __init__(self, answer: Callable[[str], list[dict[str, Any]]]) -> None:
        self._answer = answer

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
        return iter([dict(row) for row in self._answer(query)])


def _db(answer: Callable[[str], list[dict[str, Any]]]) -> MagicMock:
    db = MagicMock()
    db.aql = _Rows(answer)
    return db


def _raw_names(species: Species, prefix: str) -> dict[str, Any]:
    """The name fields a query projects for ``species`` (``species_`` or ``sp_`` naming)."""
    return {
        f"{prefix}common_names": species.common_names,
        f"{prefix}common_names_i18n": species.common_names_i18n,
    }


# ── Care dashboard ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(("case", "header"), _CASES)
def test_care_dashboard(case: str, header: str) -> None:
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
    client = _client(care_router, {get_care_reminder_service: lambda: service})

    entries = client.get(f"{PREFIX}/care-reminders/dashboard", headers=_HEADERS[header]).json()

    assert entries
    assert {entry["species_name"] for entry in entries} == {_EXPECTED[case, header]}


# ── Dashboard plant grid ──────────────────────────────────────────────────────


class _GridPlants:
    """Counts for the tiles; the grid rows through the real repository's resolution."""

    def __init__(self, species: Species) -> None:
        row = {"_key": "p1", "species_key": "sp", "species_scientific_name": SCIENTIFIC} | _raw_names(
            species, "species_"
        )
        self._repo = ArangoPlantInstanceRepository(_db(lambda _query: [row]))

    def count_for_tenant(self, tenant_key: str) -> int:
        return 1

    def count_active_for_tenant(self, tenant_key: str) -> int:
        return 1

    def list_active_for_tenant(self, tenant_key: str, limit: int, *, language: str = "de") -> list[dict[str, Any]]:
        return self._repo.list_active_for_tenant(tenant_key, limit, language=language)


@pytest.mark.parametrize(("case", "header"), _CASES)
def test_dashboard_plant_grid(case: str, header: str) -> None:
    tasks = MagicMock()
    tasks.count_open_due_on.return_value = 0
    tasks.count_overdue.return_value = 0
    tasks.list_upcoming.return_value = []
    service = DashboardService(plant_repo=_GridPlants(_species(case)), task_repo=tasks)  # type: ignore[arg-type]
    client = _client(dashboard_router, {get_dashboard_service: lambda: service})

    body = client.get(f"{PREFIX}/dashboard/aggregated?widgets=plant_grid", headers=_HEADERS[header]).json()

    (plant,) = body["widgets"]["plant_grid"]["plants"]
    assert plant["species_common_name"] == _EXPECTED[case, header]


# ── Sowing calendar ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(("case", "header"), _CASES)
def test_sowing_calendar(case: str, header: str, monkeypatch: pytest.MonkeyPatch) -> None:
    species = _species(case, growing_periods=[GrowingPeriod(direct_sow_months=[4, 5], harvest_months=[7, 8])])
    catalogue = MagicMock()
    catalogue.get_all.return_value = ([species], 1)
    service = CalendarService(MagicMock(), CalendarAggregationEngine(), MagicMock(), species_repo=catalogue)
    # The calendar routes build their service in the handler, not through a dependency.
    monkeypatch.setattr(calendar_router_module, "get_calendar_service", lambda: service)
    client = _client(calendar_router_module.router, {})

    body = client.get(f"{PREFIX}/calendar/sowing", headers=_HEADERS[header]).json()

    assert [entry["common_name"] for entry in body["entries"]] == [_EXPECTED[case, header]]


# ── Winter-hardiness overview ─────────────────────────────────────────────────


@pytest.mark.parametrize(("case", "header"), _CASES)
def test_hardiness_overview(case: str, header: str) -> None:
    profile = OverwinteringProfile(
        _key="ow1",
        tenant_key=TENANT,
        plant_key="p1",
        hardiness_rating=HardinessRating.FROST_FREE,
        winter_action=WinterAction.MOVE_INDOORS,
        winter_action_month=10,
    )
    repo = MagicMock()
    repo.list_by_tenant.side_effect = lambda tenant_key, offset, limit: ([profile], 1) if offset == 0 else ([], 1)
    plants = MagicMock()
    plants.get_by_key.return_value = _plant()
    service = OverwinteringProfileService(repo, plant_repo=plants, species_repo=_species_repo(_species(case)))
    client = _client(overwintering_router, {get_overwintering_profile_service: lambda: service})

    body = client.get(f"{PREFIX}/overwintering-profiles/hardiness-overview", headers=_HEADERS[header]).json()

    (red,) = body["red_plants"]
    assert red["species_common_name"] == _EXPECTED[case, header]
    assert red["species_scientific_name"] == SCIENTIFIC


# ── Plant states of a bed (sown slots and standing plants) ────────────────────


class _Sites:
    def get_location_by_key(self, key: str) -> Location | None:
        return Location(_key=key, name="Beet 1", area_m2=1.0, site_key="site") if key == "bed" else None

    def get_site_by_key(self, key: str) -> Site | None:
        return Site(_key=key, tenant_key=TENANT, name="Garten") if key == "site" else None


class _StateRepo(ArangoPlantStateRepository):
    """The real sown-slot statement's Python half; no standing plants."""

    def list_bed_plants(self, *args: Any, **kwargs: Any) -> list[PlantStateSource]:
        return []


@pytest.mark.parametrize(("case", "header"), _CASES)
def test_plant_states(case: str, header: str) -> None:
    row = {
        "slot_key": "s1",
        "slot_id": "BED_001",
        "sown_at": "2026-04-02",
        "thinned_at": None,
        "run_key": "run",
        "entry_key": "e1",
        "species_key": "sp",
        "cultivar_key": None,
        "scientific_name": SCIENTIFIC,
        "cultivar_name": None,
    } | _raw_names(_species(case), "species_")
    service = PlantStateService(_Sites(), _StateRepo(_db(lambda _query: [row])))  # type: ignore[arg-type]
    client = _client(locations_router, {get_plant_state_service: lambda: service})

    response = client.get(f"{PREFIX}/locations/bed/plant-states", headers=_HEADERS[header])

    assert response.status_code == 200, response.text
    (entry,) = response.json()
    assert entry["species_name"] == _EXPECTED[case, header]


# ── Workflow list (usage stats) and executions ────────────────────────────────


class _Tasks:
    """The task service's two reads in question, over the real repository's Python half."""

    def __init__(self, species: Species) -> None:
        names = {"sp_found": True, "sp_scientific_name": SCIENTIFIC} | _raw_names(species, "sp_")
        usage = {"wf_key": "wf", "entity_count": 1} | names
        execution = {
            "key": "we1",
            "entity_key": "p1",
            "entity_type": "plant_instance",
            "entity_name": "Tom",
            "plant_removed": False,
            "completion_percentage": 0.0,
            "on_schedule": True,
            "started_at": None,
            "completed_at": None,
        } | names
        self._repo = ArangoTaskRepository(
            _db(lambda query: [execution] if "@template_key" in query else [usage])  # type: ignore[arg-type]
        )
        self._template = WorkflowTemplate(_key="wf", name="Tomatenpflege", species_key="sp")

    def list_workflow_templates_window(self, offset: int, limit: int, **_filters: Any) -> list[WorkflowTemplate]:
        return [self._template]

    def get_workflow_template(self, key: str, *, tenant_key: str) -> WorkflowTemplate:
        return self._template

    def get_workflow_usage_stats(self, wf_keys: list[str], *, tenant_key: str, language: str = "de") -> dict:
        return self._repo.get_workflow_usage_stats(wf_keys, tenant_key=tenant_key, language=language)

    def get_executions_for_template(self, key: str, *, tenant_key: str, **window: Any) -> list[dict]:
        return self._repo.get_executions_for_template(key, tenant_key=tenant_key, **window)


@pytest.mark.parametrize(("case", "header"), _CASES)
def test_workflow_list_and_executions(case: str, header: str) -> None:
    client = _client(tasks_router, {get_task_service: lambda: _Tasks(_species(case))})

    (workflow,) = client.get(f"{PREFIX}/tasks/workflows", headers=_HEADERS[header]).json()
    (execution,) = client.get(f"{PREFIX}/tasks/workflows/wf/executions", headers=_HEADERS[header]).json()

    assert workflow["species_name"] == _EXPECTED[case, header]
    assert execution["species_name"] == _EXPECTED[case, header]


# ── Diary overview ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(("case", "header"), _CASES)
def test_diary_overview_when_the_scientific_name_is_missing(
    case: str, header: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The row names the species scientifically; only a record without one shows the vernacular name."""
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.jwt_secret_key", "api-test-secret-value")
    names, names_i18n = _NAMES[case]
    plants = {"plant-1": _plant().model_copy(update={"key": "plant-1"})}
    repo = FakeDiaryRepository(plants=plants)
    repo.seed("e1", plant_key="plant-1")
    plant_service = FakePlantInstanceService(
        plants=plants,
        species={"sp": Species.model_construct(scientific_name="", common_names=names, common_names_i18n=names_i18n)},
    )
    client = _client(
        diary_router,
        {
            get_plant_diary_service: lambda: PlantDiaryService(diary_repo=repo),
            get_plant_instance_service: lambda: plant_service,
        },
    )

    response = client.get(f"{PREFIX}/diary", headers=_HEADERS[header])

    assert response.status_code == 200, response.text
    assert response.json()["items"][0]["species_name"] == _EXPECTED[case, header]
