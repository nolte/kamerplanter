"""#2107 (MT-010) — harvest, feeding, watering and succession writes refuse a foreign key in the service.

The feeding-event, watering-log and harvest-batch handlers used to call
``service.get_X(key, tenant_key=…)`` first and then an unscoped write that reloaded
the row **without** a tenant (check-then-act). The succession-plan writes took
``tenant_key: str = ""``, and an omitted tenant switched their check off. The
pre-calls are gone; every write method takes ``*, tenant_key: str`` and checks
ownership itself. These tests drive the real routes and the real services with
only the repositories doubled, so a 404 here can only come from the predicate
inside the service.

Anti-vacuity: a mistyped path also answers 404 (``{"detail": "Not Found"}``). Every
negative case therefore asserts the domain error body (``entity`` and ``message``),
that the repository was asked for exactly the key under test, and that no write
ran; a positive control proves each route reaches its write for the caller's own
row. An unknown key and a foreign key answer the same body (no existence oracle).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.feeding_events.tenant_router import router as feeding_router
from app.api.v1.harvest.tenant_router import router as harvest_router
from app.api.v1.succession_plans.tenant_router import router as succession_router
from app.api.v1.watering_logs.tenant_router import router as watering_log_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_feeding_service,
    get_harvest_service,
    get_succession_plan_service,
    get_watering_log_service,
)
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.harvest import HarvestBatch
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.models.tenant_context import TenantContext
from app.domain.models.watering_event import WateringEvent
from app.domain.models.watering_log import WateringLog
from app.domain.services.feeding_service import FeedingService
from app.domain.services.harvest_service import HarvestService
from app.domain.services.succession_plan_service import SuccessionPlanService
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService
from tests.conftest import wire_or_raise

SLUG = "anna"
OWN = "tenant_anna"
FOREIGN = "tenant_bob"
KEY = "row_1"
_BASE = f"/api/v1/t/{SLUG}"

#: Repository methods that persist something; none may run for a foreign or unknown key.
_WRITES = frozenset(
    {
        "create",
        "update",
        "update_fields",
        "update_batch",
        "delete",
        "create_quality_assessment",
        "create_yield_metric",
        "link_plan_to_location",
        "link_plan_to_run",
    }
)


def _app(router: APIRouter, dependency: Callable, service: object) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix=_BASE)

    @app.exception_handler(KamerplanterError)
    def _handler(request: Request, exc: KamerplanterError):
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message, "details": exc.details})

    ctx = TenantContext(tenant_key=OWN, tenant_slug=SLUG, user_key="u_anna", role=TenantRole.LEAD)
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    app.dependency_overrides[dependency] = lambda: service
    return TestClient(app)


def _writes_called(repo: MagicMock) -> list[str]:
    return sorted({name for name, _args, _kwargs in repo.method_calls if name in _WRITES})


def _echo(_key: str, doc: object) -> object:
    return doc


@dataclass(frozen=True)
class _Kind:
    """One aggregate: how its row is built, loaded, served and which routes write it."""

    entity: str
    message_name: str
    getter: str
    or_raise: str
    build: Callable[[str], object]
    serve: Callable[[MagicMock], tuple[TestClient, object]]


def _feeding_event(owner: str) -> FeedingEvent:
    return FeedingEvent(
        _key=KEY, tenant_key=owner, plant_key="p1", application_method="drench", volume_applied_liters=1.0
    )


def _watering_log(owner: str) -> WateringLog:
    return WateringLog(_key=KEY, tenant_key=owner, application_method="drench", volume_liters=1.0, plant_keys=["p1"])


def _harvest_batch(owner: str) -> HarvestBatch:
    return HarvestBatch(_key=KEY, tenant_key=owner, plant_key="p1", batch_id="HARVEST-1")


def _succession_plan(owner: str) -> SuccessionPlan:
    return SuccessionPlan(
        _key=KEY,
        tenant_key=owner,
        name="Salat",
        species_key="sp_lettuce",
        interval_days=14,
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 1),
        plants_per_batch=4,
    )


def _serve_feeding(repo: MagicMock) -> tuple[TestClient, object]:
    repo.update.side_effect = _echo
    service = FeedingService(repo)
    return _app(feeding_router, get_feeding_service, service), service


def _serve_watering_log(repo: MagicMock) -> tuple[TestClient, object]:
    repo.update_fields.side_effect = lambda key, fields: repo.get_by_key(key).model_copy(update=fields)
    repo.resolve_plant_names.return_value = {}
    repo.resolve_fertilizer_names.return_value = {}
    service = WateringLogService(repo, MagicMock(), MagicMock())
    return _app(watering_log_router, get_watering_log_service, service), service


def _serve_harvest(repo: MagicMock) -> tuple[TestClient, object]:
    repo.update_batch.side_effect = _echo
    repo.create_quality_assessment.side_effect = lambda a: a.model_copy(update={"key": "q1"})
    repo.create_yield_metric.side_effect = lambda m: m.model_copy(update={"key": "y1"})
    service = HarvestService(repo, MagicMock(), MagicMock(), MagicMock(calculate_overall_score=lambda *a: (8.0, "A")))
    return _app(harvest_router, get_harvest_service, service), service


def _serve_succession(repo: MagicMock) -> tuple[TestClient, object]:
    repo.update.side_effect = _echo
    run_service = MagicMock()
    run_service.create_run.side_effect = lambda run, entries, *, tenant_key: run.model_copy(update={"key": "run_new"})
    service = SuccessionPlanService(repo, run_service, site_repo=MagicMock(), species_resolver=MagicMock())
    return _app(succession_router, get_succession_plan_service, service), service


_FEEDING = _Kind("feeding_event", "FeedingEvent", "get_by_key", "get_or_raise", _feeding_event, _serve_feeding)
_WATERING_LOG = _Kind("watering_log", "WateringLog", "get_by_key", "get_or_raise", _watering_log, _serve_watering_log)
_HARVEST = _Kind(
    "harvest_batch", "HarvestBatch", "get_batch_by_key", "get_batch_or_raise", _harvest_batch, _serve_harvest
)
_SUCCESSION = _Kind(
    "succession_plan", "SuccessionPlan", "get_by_key", "get_or_raise", _succession_plan, _serve_succession
)


def _world(kind: _Kind, owner: str | None) -> tuple[TestClient, MagicMock, object]:
    """``owner`` ``None`` is a key that exists nowhere."""
    repo = MagicMock()
    getattr(repo, kind.getter).side_effect = lambda key: kind.build(owner) if owner is not None and key == KEY else None
    wire_or_raise(repo, kind.message_name, by_key=kind.getter, or_raise=kind.or_raise)
    client, service = kind.serve(repo)
    return client, repo, service


#: (kind, method, path, body, the repository write the own row reaches)
_ROUTES = [
    pytest.param(_FEEDING, "PUT", f"/feeding-events/{KEY}", {"notes": "x"}, "update", id="feeding-update"),
    pytest.param(_FEEDING, "DELETE", f"/feeding-events/{KEY}", None, "delete", id="feeding-delete"),
    pytest.param(_WATERING_LOG, "PUT", f"/watering-logs/{KEY}", {"notes": "x"}, "update_fields", id="log-update"),
    pytest.param(_WATERING_LOG, "DELETE", f"/watering-logs/{KEY}", None, "delete", id="log-delete"),
    pytest.param(_HARVEST, "PUT", f"/harvest/batches/{KEY}", {"notes": "x"}, "update_batch", id="harvest-update"),
    pytest.param(
        _HARVEST,
        "POST",
        f"/harvest/batches/{KEY}/quality",
        {"appearance_score": 8, "aroma_score": 8, "color_score": 8},
        "create_quality_assessment",
        id="harvest-quality",
    ),
    pytest.param(
        _HARVEST,
        "POST",
        f"/harvest/batches/{KEY}/yield",
        {"total_yield_g": 120},
        "create_yield_metric",
        id="harvest-yield",
    ),
    pytest.param(_SUCCESSION, "PUT", f"/succession-plans/{KEY}", {"notes": "x"}, "update", id="succession-update"),
    pytest.param(_SUCCESSION, "DELETE", f"/succession-plans/{KEY}", None, "delete", id="succession-delete"),
    pytest.param(_SUCCESSION, "POST", f"/succession-plans/{KEY}/generate", None, "update", id="succession-generate"),
    pytest.param(
        _SUCCESSION, "POST", f"/succession-plans/{KEY}/generate-next", None, "update", id="succession-generate-next"
    ),
]


@pytest.mark.parametrize(("kind", "method", "path", "body", "write"), _ROUTES)
@pytest.mark.parametrize("owner", [FOREIGN, None], ids=["foreign", "unknown"])
def test_a_foreign_or_unknown_row_is_not_written(kind, method, path, body, write, owner) -> None:
    client, repo, _service = _world(kind, owner)
    resp = client.request(method, f"{_BASE}{path}", json=body)
    assert resp.status_code == 404, resp.text
    # A domain 404 from the service, not the router's "no such path", and the same
    # body for a foreign and an unknown key.
    assert resp.json()["details"][0]["entity"] == kind.entity, resp.text
    assert resp.json()["message"] == f"{kind.message_name} with key '{KEY}' not found."
    getattr(repo, kind.getter).assert_any_call(KEY)
    assert _writes_called(repo) == []


@pytest.mark.parametrize(("kind", "method", "path", "body", "write"), _ROUTES)
def test_the_callers_own_row_reaches_the_write(kind, method, path, body, write) -> None:
    client, repo, _service = _world(kind, OWN)
    resp = client.request(method, f"{_BASE}{path}", json=body)
    assert resp.status_code in (200, 201, 204), resp.text
    assert write in _writes_called(repo)


# ── Service level: the tenant that cannot be forgotten ──────────────────────


def test_an_empty_tenant_is_refused_by_every_converted_keyed_write() -> None:
    """``""`` is "no tenant", never "every tenant": a legacy row stamped ``""`` is refused too."""
    calls: list[tuple[MagicMock, Callable[[object], object]]] = []
    for kind, call in [
        (_FEEDING, lambda s: s.update_event(KEY, {"notes": "x"}, tenant_key="")),
        (_FEEDING, lambda s: s.delete_event(KEY, tenant_key="")),
        (_WATERING_LOG, lambda s: s.update_log(KEY, {"notes": "x"}, tenant_key="")),
        (_WATERING_LOG, lambda s: s.delete_log(KEY, tenant_key="")),
        (_HARVEST, lambda s: s.update_batch(KEY, {"notes": "x"}, tenant_key="")),
        (_SUCCESSION, lambda s: s.update_plan(KEY, {"notes": "x"}, tenant_key="")),
        (_SUCCESSION, lambda s: s.delete_plan(KEY, tenant_key="")),
        (_SUCCESSION, lambda s: s.generate_runs(KEY, tenant_key="")),
        (_SUCCESSION, lambda s: s.generate_next_run(KEY, tenant_key="")),
    ]:
        _client, repo, service = _world(kind, "")
        with pytest.raises(KamerplanterError) as exc:
            call(service)
        assert exc.value.status_code == 404
        calls.append((repo, call))
    assert all(_writes_called(repo) == [] for repo, _ in calls)


def test_create_log_and_create_event_refuse_an_empty_tenant() -> None:
    log_repo, event_repo = MagicMock(), MagicMock()
    log_service = WateringLogService(log_repo, MagicMock(), MagicMock())
    event_service = WateringService(event_repo, MagicMock(), MagicMock())
    log = WateringLog(application_method="drench", volume_liters=1.0, plant_keys=["p1"])
    with pytest.raises(ValueError, match="tenant_key"):
        log_service.create_log(log, tenant_key="")
    with pytest.raises(ValueError, match="tenant_key"):
        event_service.create_event(WateringEvent(volume_liters=1.0, plant_keys=["p1"]), tenant_key="")
    log_repo.create.assert_not_called()
    event_repo.create.assert_not_called()


def test_create_log_and_create_event_stamp_the_callers_tenant_over_the_models() -> None:
    log_repo, event_repo = MagicMock(), MagicMock()
    log_repo.create.side_effect = lambda log: log.model_copy(update={"key": "l1"})
    event_repo.create.side_effect = lambda event: event.model_copy(update={"key": "e1"})
    engine = MagicMock(validate_and_warn=MagicMock(return_value=[]))
    sites = MagicMock(get_slot_for_plant=MagicMock(return_value=None))
    log_service = WateringLogService(log_repo, engine, sites)
    event_service = WateringService(event_repo, engine, sites)

    created_log = log_service.create_log(
        WateringLog(tenant_key=FOREIGN, application_method="drench", volume_liters=1.0, plant_keys=["p1"]),
        tenant_key=OWN,
    )["log"]
    created_event = event_service.create_event(
        WateringEvent(tenant_key=FOREIGN, volume_liters=1.0, plant_keys=["p1"]), tenant_key=OWN
    )["event"]

    assert created_log.tenant_key == OWN
    assert created_event.tenant_key == OWN
    sites.get_slot_for_plant.assert_called_once_with("p1", tenant_key=OWN)


# ── Stale foreign reference: a run's plant edge to another tenant's plant ───


def _plant(key: str, owner: str) -> PlantInstance:
    return PlantInstance(
        _key=key, instance_id=key.upper(), species_key="sp_tomato", planted_on=date(2026, 1, 1), tenant_key=owner
    )


def _harvest_run_world() -> tuple[HarvestService, MagicMock]:
    run_repo, plant_repo, phase_engine = MagicMock(), MagicMock(), MagicMock()
    run_repo.get_by_key.side_effect = lambda key: (
        PlantingRun(_key=KEY, tenant_key=OWN, name="Lauf", run_type="monoculture") if key == KEY else None
    )
    wire_or_raise(run_repo, "PlantingRun")
    # A legacy edge: the run also lists another tenant's plant.
    run_repo.get_run_plants.return_value = [{"_key": "p_own"}, {"_key": "p_b"}]
    plants = {"p_own": _plant("p_own", OWN), "p_b": _plant("p_b", FOREIGN)}
    plant_repo.get_by_key.side_effect = plants.get
    service = HarvestService(
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        plant_repo=plant_repo,
        run_repo=run_repo,
        phase_engine=phase_engine,
    )
    return service, phase_engine


def test_completing_a_runs_harvest_never_terminates_another_tenants_plant() -> None:
    service, phase_engine = _harvest_run_world()
    result = service.complete_harvest_for_run(KEY, tenant_key=OWN)
    assert result["completed_keys"] == ["p_own"]
    terminated = [call.args[0] for call in phase_engine.terminate.call_args_list]
    assert terminated == ["p_own"]


def test_completing_a_foreign_runs_harvest_is_a_404() -> None:
    service, phase_engine = _harvest_run_world()
    with pytest.raises(KamerplanterError) as exc:
        service.complete_harvest_for_run(KEY, tenant_key=FOREIGN)
    assert exc.value.status_code == 404
    phase_engine.terminate.assert_not_called()


@pytest.mark.parametrize("tenant_key", [FOREIGN, ""], ids=["foreign", "empty"])
def test_completing_a_plants_harvest_checks_the_plant_unconditionally(tenant_key: str) -> None:
    service, phase_engine = _harvest_run_world()
    with pytest.raises(KamerplanterError) as exc:
        service.complete_harvest("p_own", tenant_key=tenant_key)
    assert exc.value.status_code == 404
    phase_engine.terminate.assert_not_called()
