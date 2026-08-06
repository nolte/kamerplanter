"""Nutrient-plan assignment must not cross tenants (#950).

The defect this pins is an IDOR on the *assignment*, not on the read. #947
anchored ``get_plant_plan`` on the **plant**, which is correct — a plan-anchored
filter would hide every globally seeded system plan (#324). But nothing checked
the plan side of the edge: ``NutrientPlanService.assign_to_plant`` called
``get_plan(plan_key)`` with the empty ``tenant_key`` default, which skips the
access check entirely. A member of tenant A bound their own plant to tenant B's
plan, and every later read was then satisfied — the plant genuinely is theirs.

``PlantingRunService.get_nutrient_plan`` was the same gap without the detour: a
raw ``get_by_key`` with no tenant check at all.

Both directions are pinned for every route:

* **negative** — a foreign tenant's plan is refused with **404**, never 403 (a
  403 confirms the plan exists in another tenant);
* **positive** — a globally seeded system plan (``tenant_key == ""``) is still
  assignable and still readable. That is the #324 counter-example: a strict
  ``plan.tenant_key == @tenant_key`` predicate would trade the leak for a
  catalogue that vanished, which is not a fix.

The repository is the real :class:`ArangoNutrientPlanRepository` on a database
double, so removing the predicate from ``get_readable_or_raise`` makes the
negative tests go red rather than leaving them agreeing with a stub.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plant_instances_router
from app.api.v1.planting_runs.tenant_router import router as planting_runs_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_nutrient_plan_service,
    get_plant_instance_service,
    get_planting_run_service,
)
from app.common.enums import PlantingRunStatus, PlantingRunType, TenantRole
from app.common.exceptions import KamerplanterError, NotFoundError
from app.data_access.arango import collections as col
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.planting_run import PlantingRun
from app.domain.models.tenant_context import TenantContext
from app.domain.services.nutrient_plan_service import NutrientPlanService
from app.domain.services.planting_run_service import PlantingRunService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_PLANT = "plant-a1"
OWN_RUN = "run-a1"
OWN_PLAN = "plan-a1"
FOREIGN_PLAN = "plan-b1"
GLOBAL_PLAN = "plan-system"

#: Text from the foreign plan that must never reach the caller.
FOREIGN_MARKER = "geheimer-fremder-plan"


# ── Harness ──────────────────────────────────────────────────────────────────


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _tenant_context() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}{path}"


def _plan_docs() -> dict[str, dict[str, Any]]:
    return {
        OWN_PLAN: {
            "_key": OWN_PLAN,
            "_id": f"{col.NUTRIENT_PLANS}/{OWN_PLAN}",
            "tenant_key": TENANT_KEY,
            "name": "Meine Tomaten",
        },
        FOREIGN_PLAN: {
            "_key": FOREIGN_PLAN,
            "_id": f"{col.NUTRIENT_PLANS}/{FOREIGN_PLAN}",
            "tenant_key": FOREIGN_TENANT_KEY,
            "name": FOREIGN_MARKER,
        },
        GLOBAL_PLAN: {
            # A globally seeded system plan: empty tenant_key IS the global
            # marker (there is no is_system flag) — the #324 direction.
            "_key": GLOBAL_PLAN,
            "_id": f"{col.NUTRIENT_PLANS}/{GLOBAL_PLAN}",
            "tenant_key": "",
            "name": "Plagron Basis",
        },
    }


class _EdgeCollection:
    """``follows_plan`` double recording what the assignment actually wrote."""

    def __init__(self) -> None:
        self.inserted: list[dict[str, Any]] = []

    def insert(self, data: dict[str, Any], return_new: bool = False) -> dict[str, Any]:
        doc = {"_key": f"edge-{len(self.inserted)}", **data}
        self.inserted.append(doc)
        return {"new": doc}


def _plan_repository() -> tuple[ArangoNutrientPlanRepository, _EdgeCollection]:
    plans = _plan_docs()

    plan_collection = MagicMock()
    plan_collection.get.side_effect = lambda key: plans.get(key)
    edges = _EdgeCollection()

    aql = ReplayingAql()
    # ``delete_edges`` clears the previous assignment before writing the new one.
    aql.route("REMOVE e IN @@edge", lambda q, b: [])

    db = ReplayingDatabase(aql, {col.NUTRIENT_PLANS: plan_collection, col.FOLLOWS_PLAN: edges})
    return ArangoNutrientPlanRepository(db), edges


# ── 1: POST /t/{slug}/plant-instances/{key}/nutrient-plan ────────────────────


def _plant_instance_client() -> tuple[TestClient, _EdgeCollection]:
    repo, edges = _plan_repository()
    plan_service = NutrientPlanService(repo, MagicMock(), MagicMock())

    plant_service = MagicMock()
    plant_service.get_plant.return_value = PlantInstance(
        _key=OWN_PLANT,
        tenant_key=TENANT_KEY,
        instance_id="TOM-1",
        species_key="sp-tomato",
        planted_on="2026-05-01",
    )

    app = FastAPI()
    app.include_router(plant_instances_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = _tenant_context
    app.dependency_overrides[get_nutrient_plan_service] = lambda: plan_service
    app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
    return TestClient(app), edges


class TestAssignPlanToOwnPlant:
    """``POST /t/{slug}/plant-instances/{key}/nutrient-plan`` (#950)."""

    def test_a_foreign_plan_is_not_found_rather_than_forbidden(self):
        client, edges = _plant_instance_client()

        resp = client.post(
            _url(f"/plant-instances/{OWN_PLANT}/nutrient-plan"),
            json={"plan_key": FOREIGN_PLAN},
        )

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert FOREIGN_MARKER not in resp.text
        # The point of the fix: no edge was written, so the plant-anchored read
        # predicate has nothing foreign to hand back afterwards.
        assert edges.inserted == []

    def test_a_globally_seeded_system_plan_is_still_assignable(self):
        """The #324 direction — a strict filter here would hide the catalogue."""
        client, edges = _plant_instance_client()

        resp = client.post(
            _url(f"/plant-instances/{OWN_PLANT}/nutrient-plan"),
            json={"plan_key": GLOBAL_PLAN},
        )

        assert resp.status_code == 201, resp.text
        assert [e["_to"] for e in edges.inserted] == [f"{col.NUTRIENT_PLANS}/{GLOBAL_PLAN}"]

    def test_the_tenants_own_plan_is_still_assignable(self):
        client, edges = _plant_instance_client()

        resp = client.post(
            _url(f"/plant-instances/{OWN_PLANT}/nutrient-plan"),
            json={"plan_key": OWN_PLAN},
        )

        assert resp.status_code == 201, resp.text
        assert [e["_to"] for e in edges.inserted] == [f"{col.NUTRIENT_PLANS}/{OWN_PLAN}"]


# ── 2: the planting-run routes ───────────────────────────────────────────────


def _run() -> PlantingRun:
    return PlantingRun(
        _key=OWN_RUN,
        tenant_key=TENANT_KEY,
        name="Tomaten 2026",
        run_type=PlantingRunType.MONOCULTURE,
        status=PlantingRunStatus.ACTIVE,
    )


def _planting_run_client(assigned_plan_key: str | None = None) -> tuple[TestClient, _EdgeCollection]:
    plan_repo, edges = _plan_repository()

    run_repo = MagicMock()
    run_repo.get_by_key.return_value = _run()
    run_repo.get_or_raise.return_value = _run()
    run_repo.get_run_nutrient_plan_key.return_value = assigned_plan_key

    def _assign(run_key: str, plan_key: str, assigned_by: str) -> dict[str, str]:
        edge = plan_repo.create_edge(
            col.FOLLOWS_PLAN,
            f"{col.PLANTING_RUNS}/{run_key}",
            f"{col.NUTRIENT_PLANS}/{plan_key}",
            {"assigned_by": assigned_by},
        )
        return {"run_key": run_key, "plan_key": plan_key, "edge_key": edge["_key"]}

    run_repo.assign_nutrient_plan.side_effect = _assign

    run_service = PlantingRunService(
        run_repo=run_repo,
        plant_repo=MagicMock(),
        engine=MagicMock(),
        nutrient_plan_repo=plan_repo,
    )
    plan_service = NutrientPlanService(plan_repo, MagicMock(), MagicMock())

    app = FastAPI()
    app.include_router(planting_runs_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = _tenant_context
    app.dependency_overrides[get_planting_run_service] = lambda: run_service
    app.dependency_overrides[get_nutrient_plan_service] = lambda: plan_service
    return TestClient(app), edges


class TestAssignPlanToOwnRun:
    """``POST /t/{slug}/planting-runs/{key}/nutrient-plan`` (#950)."""

    def test_a_foreign_plan_is_not_found_rather_than_forbidden(self):
        client, edges = _planting_run_client()

        resp = client.post(
            _url(f"/planting-runs/{OWN_RUN}/nutrient-plan"),
            json={"plan_key": FOREIGN_PLAN},
        )

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert edges.inserted == []

    def test_a_globally_seeded_system_plan_is_still_assignable(self):
        client, edges = _planting_run_client()

        resp = client.post(
            _url(f"/planting-runs/{OWN_RUN}/nutrient-plan"),
            json={"plan_key": GLOBAL_PLAN},
        )

        assert resp.status_code == 201, resp.text
        assert [e["_to"] for e in edges.inserted] == [f"{col.NUTRIENT_PLANS}/{GLOBAL_PLAN}"]


class TestReadTheRunsPlan:
    """``GET /t/{slug}/planting-runs/{key}/nutrient-plan`` (#950).

    The second, shorter route: no assignment detour is needed because the read
    itself used a raw ``get_by_key``. A stored edge left over from before the fix
    can still point at a foreign plan, so the read has to hold on its own.
    """

    def test_an_edge_pointing_at_a_foreign_plan_reveals_nothing(self):
        client, _edges = _planting_run_client(assigned_plan_key=FOREIGN_PLAN)

        resp = client.get(_url(f"/planting-runs/{OWN_RUN}/nutrient-plan"))

        assert resp.status_code == 200, resp.text
        assert resp.json() == {"plan": None}
        assert FOREIGN_MARKER not in resp.text

    def test_a_globally_seeded_system_plan_is_still_returned(self):
        client, _edges = _planting_run_client(assigned_plan_key=GLOBAL_PLAN)

        resp = client.get(_url(f"/planting-runs/{OWN_RUN}/nutrient-plan"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["plan"]["key"] == GLOBAL_PLAN

    def test_the_tenants_own_plan_is_still_returned(self):
        client, _edges = _planting_run_client(assigned_plan_key=OWN_PLAN)

        resp = client.get(_url(f"/planting-runs/{OWN_RUN}/nutrient-plan"))

        assert resp.status_code == 200, resp.text
        assert resp.json()["plan"]["key"] == OWN_PLAN


# ── 3: the repository contract itself ────────────────────────────────────────


class TestTheTenantParameterCannotBeSkipped:
    """The predicate is a property of the data-access layer, not of a call site.

    #950 exists precisely because the service made its tenant argument optional:
    the caller omitted it and the check turned itself off with no signal.
    """

    def test_omitting_the_tenant_entirely_is_a_type_error(self):
        repo, _ = _plan_repository()

        with pytest.raises(TypeError):
            repo.get_readable_or_raise(OWN_PLAN)  # type: ignore[call-arg]

    def test_an_empty_tenant_key_is_rejected_instead_of_matching_everything(self):
        repo, _ = _plan_repository()

        with pytest.raises(ValueError, match="tenant"):
            repo.get_readable_or_raise(OWN_PLAN, tenant_key="")

    def test_a_foreign_plan_raises_not_found(self):
        repo, _ = _plan_repository()

        with pytest.raises(NotFoundError):
            repo.get_readable_or_raise(FOREIGN_PLAN, tenant_key=TENANT_KEY)

    @pytest.mark.parametrize("plan_key", [OWN_PLAN, GLOBAL_PLAN])
    def test_own_and_global_plans_stay_readable(self, plan_key: str):
        repo, _ = _plan_repository()

        assert repo.get_readable_or_raise(plan_key, tenant_key=TENANT_KEY).key == plan_key

    def test_the_service_cannot_assign_without_naming_a_tenant(self):
        repo, _ = _plan_repository()
        service = NutrientPlanService(repo, MagicMock(), MagicMock())

        with pytest.raises(TypeError):
            service.assign_to_plant(OWN_PLANT, OWN_PLAN)  # type: ignore[call-arg]
