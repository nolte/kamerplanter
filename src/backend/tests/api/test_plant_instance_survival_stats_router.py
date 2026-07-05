"""API test: survival-stats analytics endpoint (REQ-003 G1).

The tenant-scoped ``GET /survival-stats`` returns the aggregated survival model
and — critically — is matched as a literal path, NOT captured by the sibling
``GET /{key}`` plant-key route. The endpoint hands the request tenant's key from
the resolved ``TenantContext`` straight to the service (tenant isolation).
"""

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plant_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_plant_instance_service
from app.common.enums import TenantRole
from app.domain.models.survival_stats import (
    PhaseLossCount,
    SurvivalStats,
    TerminationCauseCount,
    TerminationTypeCount,
)
from app.domain.models.tenant_context import TenantContext

TENANT_KEY = "t-test-1"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug="test-slug",
        user_key="user-1",
        role=TenantRole.GROWER,
    )


def _stats() -> SurvivalStats:
    return SurvivalStats(
        total=5,
        terminated=3,
        active=2,
        died=2,
        survived=3,
        survival_rate=0.6,
        by_termination_type=[
            TerminationTypeCount(termination_type="harvested", count=1),
            TerminationTypeCount(termination_type="died", count=2),
        ],
        by_termination_cause=[TerminationCauseCount(termination_cause="frost", count=2)],
        loss_by_phase=[PhaseLossCount(phase_name="vegetative", count=2)],
    )


def _client(service: MagicMock) -> TestClient:
    app = FastAPI()
    app.include_router(plant_router, prefix="/api/v1/t/test-slug")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    app.dependency_overrides[get_current_tenant] = _ctx
    return TestClient(app)


def test_survival_stats_returns_aggregated_model() -> None:
    service = MagicMock()
    service.get_survival_stats.return_value = _stats()

    resp = _client(service).get("/api/v1/t/test-slug/plant-instances/survival-stats")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert body["survived"] == 3
    assert body["survival_rate"] == 0.6
    assert body["by_termination_type"] == [
        {"termination_type": "harvested", "count": 1},
        {"termination_type": "died", "count": 2},
    ]
    assert body["by_termination_cause"] == [{"termination_cause": "frost", "count": 2}]
    assert body["loss_by_phase"] == [{"phase_name": "vegetative", "count": 2}]
    # The request tenant's key is passed through — no cross-tenant leak.
    service.get_survival_stats.assert_called_once_with(TENANT_KEY)


def test_survival_stats_path_not_captured_by_key_route() -> None:
    service = MagicMock()
    service.get_survival_stats.return_value = _stats()

    _client(service).get("/api/v1/t/test-slug/plant-instances/survival-stats")

    # The literal path resolved to the analytics handler, not GET /{key}.
    service.get_survival_stats.assert_called_once()
    service.get_plant.assert_not_called()
