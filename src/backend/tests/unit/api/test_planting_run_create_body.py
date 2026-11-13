"""``POST /t/{slug}/planting-runs`` refuses an invalid run type as a 422, never a 500 (#2775).

``PlantingRunCreate.run_type`` was a bare ``str`` and ``source_plant_key`` was not checked for a
clone run, so both reached ``PlantingRun(...)`` inside the route, whose pydantic error no handler
maps: the response was 500. The route is driven through FastAPI with the tenant gate and the
service replaced, so what is asserted is the body validation the real route runs.
"""

from __future__ import annotations

import inspect

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.planting_runs import tenant_router
from app.common.dependencies import get_planting_run_service
from app.common.enums import TenantRole
from app.common.error_handlers import validation_error_handler
from app.domain.models.planting_run import PlantingRun
from app.domain.models.tenant_context import TenantContext


class _RecordingService:
    def __init__(self) -> None:
        self.created: list[PlantingRun] = []

    def create_run(self, run, entries, *, tenant_key):
        self.created.append(run)
        return run.model_copy(update={"key": "run1"})


def _client(service: _RecordingService) -> TestClient:
    from fastapi.exceptions import RequestValidationError

    app = FastAPI()
    app.include_router(tenant_router.router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    gate = inspect.signature(tenant_router.create_run).parameters["ctx"].default.dependency
    app.dependency_overrides[gate] = lambda: TenantContext(
        tenant_key="tenant-a", tenant_slug="garden", user_key="user-a", role=TenantRole.GROWER
    )
    app.dependency_overrides[get_planting_run_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "body",
    [
        {"name": "Beet A", "run_type": "bogus"},
        {"name": "Beet A", "run_type": "mixed_culture"},
        {"name": "Klone", "run_type": "clone"},
    ],
    ids=["unknown-type", "mixed-culture-type", "clone-without-mother-plant"],
)
def test_an_invalid_run_type_is_a_422_and_nothing_is_created(body):
    service = _RecordingService()

    response = _client(service).post("/api/v1/t/garden/planting-runs", json=body)

    assert response.status_code == 422, response.text
    assert service.created == []


def test_a_valid_body_still_creates_a_run():
    service = _RecordingService()

    response = _client(service).post(
        "/api/v1/t/garden/planting-runs", json={"name": "Beet A", "run_type": "monoculture"}
    )

    assert response.status_code == 201, response.text
    assert [run.tenant_key for run in service.created] == ["tenant-a"]
