"""#2107 (MT-010) — a planting-run or tank write refuses another tenant's key in the service.

These handlers used to call ``service.get_run(key, tenant_key=…)`` /
``service.get_tank(key, tenant_key=…)`` first and then an unscoped write that
reloaded the row **without** a tenant (check-then-act). The pre-call is gone; the
write method itself now takes ``*, tenant_key: str`` and checks ownership. These
tests drive the real routes and the real services with only the repositories
doubled, so a 404 here can only come from the predicate inside the service.

Anti-vacuity: a mistyped path also answers 404 (``{"detail": "Not Found"}``).
Every negative case therefore asserts the domain error body (``entity``) and
that the repository was asked for exactly the key under test, and a positive
control proves each route reaches its write for the caller's own row.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.planting_runs.tenant_router import router as run_router
from app.api.v1.tanks.tenant_router import router as tank_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_planting_run_service, get_tank_service
from app.common.enums import PlantingRunStatus, PlantingRunType, TankType, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.planting_run import PlantingRun
from app.domain.models.tank import MaintenanceLog, MaintenanceSchedule, Tank, TankFillEvent, TankState
from app.domain.models.tenant_context import TenantContext
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.tank_service import TankService
from tests.conftest import wire_get_or_raise

SLUG = "anna"
OWN = "tenant_anna"
FOREIGN = "tenant_bob"
KEY = "row_1"
_BASE = f"/api/v1/t/{SLUG}"

#: Repository methods that persist something; none may run for a foreign key.
_WRITES = (
    "create",
    "update",
    "delete",
    "create_entry",
    "remove_nutrient_plan",
    "detach_plant",
    "create_state",
    "create_maintenance_log",
    "create_schedule",
    "create_fill_event",
)


def _app(ctx_tenant: str = OWN) -> FastAPI:
    app = FastAPI()
    app.include_router(run_router, prefix=_BASE)
    app.include_router(tank_router, prefix=_BASE)

    @app.exception_handler(KamerplanterError)
    def _handler(request: Request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message, "details": exc.details})

    ctx = TenantContext(tenant_key=ctx_tenant, tenant_slug=SLUG, user_key="u", role=TenantRole.LEAD)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    return app


def _writes_called(repo: MagicMock) -> list[str]:
    return sorted({name for name, _args, _kwargs in repo.method_calls if name in _WRITES})


def _assert_refused(resp, repo: MagicMock, entity: str) -> None:
    assert resp.status_code == 404, resp.text
    # A domain 404 from the service, not the router's "no such path".
    assert resp.json()["details"][0]["entity"] == entity, resp.text
    repo.get_by_key.assert_any_call(KEY)
    assert _writes_called(repo) == []


# ── Planting runs ───────────────────────────────────────────────────────────


def _run_client(owner: str, status: PlantingRunStatus) -> tuple[TestClient, MagicMock]:
    run_repo = MagicMock()
    run_repo.get_by_key.side_effect = lambda key: (
        PlantingRun(
            _key=KEY,
            tenant_key=owner,
            name="Tomaten",
            run_type=PlantingRunType.MONOCULTURE,
            status=status,
        )
        if key == KEY
        else None
    )
    wire_get_or_raise(run_repo, "PlantingRun")
    run_repo.get_entries.return_value = []
    run_repo.get_run_plants.return_value = []
    run_repo.update.side_effect = lambda key, run: run
    run_repo.create_entry.side_effect = lambda entry: entry.model_copy(update={"key": "e1"})
    service = PlantingRunService(
        run_repo=run_repo,
        plant_repo=MagicMock(),
        engine=MagicMock(),
        phase_repo=MagicMock(),
        species_resolver=lambda key, *, tenant_key: None,
    )
    app = _app()
    app.dependency_overrides[get_planting_run_service] = lambda: service
    return TestClient(app), run_repo


_ENTRY = {"species_key": "sp_tomato", "quantity": 1, "id_prefix": "TOM"}

#: (method, path suffix, body, status the run needs for the write to go ahead, write it reaches)
_RUN_WRITES = [
    pytest.param("PUT", "", {"name": "Neu"}, PlantingRunStatus.PLANNED, "update", id="update_run"),
    pytest.param("DELETE", "", None, PlantingRunStatus.PLANNED, "delete", id="delete_run"),
    pytest.param("POST", "/entries", _ENTRY, PlantingRunStatus.PLANNED, "create_entry", id="add_entry"),
    pytest.param(
        "POST", "/transition", {"target_phase_key": "ph_veg"}, PlantingRunStatus.ACTIVE, "update", id="transition"
    ),
    pytest.param(
        "PATCH",
        "/batch-update-phase-dates",
        {"phase_key": "ph_veg", "entered_at": "2026-01-01T00:00:00Z"},
        PlantingRunStatus.ACTIVE,
        None,
        id="batch_update_phase_dates",
    ),
    pytest.param("POST", "/batch-remove", {}, PlantingRunStatus.ACTIVE, "update", id="batch_remove"),
    pytest.param(
        "DELETE", "/nutrient-plan", None, PlantingRunStatus.PLANNED, "remove_nutrient_plan", id="remove_nutrient_plan"
    ),
    pytest.param(
        "POST", "/plants/p1/detach", {"reason": "weg"}, PlantingRunStatus.ACTIVE, "detach_plant", id="detach_plant"
    ),
    pytest.param("POST", "/adopt-plants", {"plant_keys": ["p1"]}, PlantingRunStatus.PLANNED, None, id="adopt_plants"),
]


@pytest.mark.parametrize(("method", "suffix", "body", "status", "write"), _RUN_WRITES)
def test_a_foreign_run_is_not_written(method, suffix, body, status, write) -> None:
    client, run_repo = _run_client(FOREIGN, status)
    resp = client.request(method, f"{_BASE}/planting-runs/{KEY}{suffix}", json=body)
    _assert_refused(resp, run_repo, "planting_run")


def test_creating_plants_in_a_foreign_run_is_refused() -> None:
    client, run_repo = _run_client(FOREIGN, PlantingRunStatus.PLANNED)
    resp = client.post(f"{_BASE}/planting-runs/{KEY}/create-plants")
    _assert_refused(resp, run_repo, "planting_run")


@pytest.mark.parametrize(("method", "suffix", "body", "status", "write"), _RUN_WRITES)
def test_the_callers_own_run_reaches_the_write(method, suffix, body, status, write) -> None:
    """Positive control: the same request on an owned run is not refused."""
    client, run_repo = _run_client(OWN, status)
    resp = client.request(method, f"{_BASE}/planting-runs/{KEY}{suffix}", json=body)
    assert resp.status_code != 404 or resp.json()["details"][0]["entity"] != "planting_run", resp.text
    if write is not None:
        assert write in _writes_called(run_repo), resp.text


def test_a_created_run_is_stamped_with_the_callers_tenant() -> None:
    client, run_repo = _run_client(OWN, PlantingRunStatus.PLANNED)
    run_repo.create.side_effect = lambda run: run.model_copy(update={"key": "new"})
    resp = client.post(f"{_BASE}/planting-runs", json={"name": "Salat", "run_type": "monoculture"})
    assert resp.status_code == 201, resp.text
    (created,) = [args[0] for name, args, _ in run_repo.method_calls if name == "create"]
    assert created.tenant_key == OWN


# ── Tanks ───────────────────────────────────────────────────────────────────


def _tank_client(owner: str) -> tuple[TestClient, MagicMock]:
    tank_repo = MagicMock()
    tank_repo.get_by_key.side_effect = lambda key: (
        Tank(_key=KEY, tenant_key=owner, name="Tank A", tank_type=TankType.NUTRIENT, volume_liters=50)
        if key == KEY
        else None
    )
    wire_get_or_raise(tank_repo, "Tank")
    tank_repo.create_state.side_effect = lambda state: state.model_copy(update={"key": "s1"})
    tank_repo.create_maintenance_log.side_effect = lambda log: log.model_copy(update={"key": "m1"})
    tank_repo.create_schedule.side_effect = lambda schedule: schedule.model_copy(update={"key": "sc1"})
    tank_repo.create_fill_event.side_effect = lambda event: event.model_copy(update={"key": "f1"})
    engine = MagicMock()
    engine.validate_fill_level.return_value = (None, None)
    engine.resolve_water_defaults.return_value = {}
    engine.validate_fill_event.return_value = []
    service = TankService(tank_repo, engine, fertilizer_repo=MagicMock(), nutrient_plan_repo=MagicMock())
    app = _app()
    app.dependency_overrides[get_tank_service] = lambda: service
    return TestClient(app), tank_repo


_TANK_WRITES = [
    pytest.param("DELETE", "", None, "delete", id="delete_tank"),
    pytest.param("POST", "/states", {"ph": 6.0}, "create_state", id="record_state"),
    pytest.param(
        "POST", "/maintenance", {"maintenance_type": "cleaning"}, "create_maintenance_log", id="log_maintenance"
    ),
    pytest.param(
        "POST",
        "/schedules",
        {"maintenance_type": "cleaning", "interval_days": 7},
        "create_schedule",
        id="create_schedule",
    ),
    pytest.param(
        "POST", "/fills", {"fill_type": "full_change", "volume_liters": 40}, "create_fill_event", id="record_fill_event"
    ),
]


@pytest.mark.parametrize(("method", "suffix", "body", "write"), _TANK_WRITES)
def test_a_foreign_tank_is_not_written(method, suffix, body, write) -> None:
    client, tank_repo = _tank_client(FOREIGN)
    resp = client.request(method, f"{_BASE}/tanks/{KEY}{suffix}", json=body)
    _assert_refused(resp, tank_repo, "tank")


@pytest.mark.parametrize(("method", "suffix", "body", "write"), _TANK_WRITES)
def test_the_callers_own_tank_reaches_the_write(method, suffix, body, write) -> None:
    client, tank_repo = _tank_client(OWN)
    resp = client.request(method, f"{_BASE}/tanks/{KEY}{suffix}", json=body)
    assert resp.status_code in (200, 201, 204), resp.text
    assert write in _writes_called(tank_repo)


# ── Service level: the tenant that cannot be forgotten ──────────────────────


def test_an_empty_tenant_is_refused_by_every_converted_tank_write() -> None:
    _client, tank_repo = _tank_client(OWN)
    service = TankService(tank_repo, MagicMock(), fertilizer_repo=MagicMock(), nutrient_plan_repo=MagicMock())
    calls = [
        lambda: service.delete_tank(KEY, tenant_key=""),
        lambda: service.record_state(KEY, TankState(tank_key=KEY), tenant_key=""),
        lambda: service.log_maintenance(KEY, MaintenanceLog(tank_key=KEY, maintenance_type="cleaning"), tenant_key=""),
        lambda: service.create_schedule(
            KEY, MaintenanceSchedule(tank_key=KEY, maintenance_type="cleaning", interval_days=7), tenant_key=""
        ),
        lambda: service.record_fill_event(
            KEY, TankFillEvent(tank_key=KEY, fill_type="full_change", volume_liters=10), tenant_key=""
        ),
    ]
    for call in calls:
        with pytest.raises(KamerplanterError) as exc:
            call()
        assert exc.value.status_code == 404
    assert _writes_called(tank_repo) == []


def test_a_fill_event_cannot_name_a_foreign_source_tank() -> None:
    _client, tank_repo = _tank_client(OWN)
    foreign = Tank(_key="tank_b", tenant_key=FOREIGN, name="B", tank_type=TankType.NUTRIENT, volume_liters=50)
    own = tank_repo.get_by_key.side_effect
    tank_repo.get_by_key.side_effect = lambda key: foreign if key == "tank_b" else own(key)
    service = TankService(tank_repo, MagicMock(), fertilizer_repo=MagicMock(), nutrient_plan_repo=MagicMock())
    event = TankFillEvent(tank_key=KEY, fill_type="full_change", volume_liters=10, source_tank_key="tank_b")
    with pytest.raises(KamerplanterError) as exc:
        service.record_fill_event(KEY, event, tenant_key=OWN)
    assert exc.value.status_code == 404
    assert _writes_called(tank_repo) == []


def test_a_clone_of_a_foreign_run_is_refused_and_nothing_is_stored() -> None:
    _client, run_repo = _run_client(FOREIGN, PlantingRunStatus.PLANNED)
    service = PlantingRunService(run_repo=run_repo, plant_repo=MagicMock(), engine=MagicMock())
    run = PlantingRun(name="Klon", run_type=PlantingRunType.MONOCULTURE, clone_from_run_key=KEY)
    with pytest.raises(KamerplanterError) as exc:
        service.create_run(run, [], tenant_key=OWN)
    assert exc.value.status_code == 404
    assert _writes_called(run_repo) == []
