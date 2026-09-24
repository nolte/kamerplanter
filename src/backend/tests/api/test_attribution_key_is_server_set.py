"""#1669 / #1663 — the attribution key is the caller's account, and the body cannot set it.

``HarvestBatch.harvested_by_key``, ``Inspection.inspected_by_key``,
``TreatmentApplication.applied_by_key`` and (since #1663)
``QualityAssessment.assessed_by_key`` are what the Art. 15 walk and the Art. 17
rules match a subject on. If a request body could choose the value, any member
could plant records into another user's disclosure or make their own records
unattributable — so the value has to come from the resolved context and from
nowhere else.

**Reject or ignore, decided: ignore.** The four ``*Create`` schemas do not declare
the field, and this repository's request schemas run Pydantic's default
``extra="ignore"`` (``app/api/mapping.py`` documents that convention; only the two
admin secret-bearing schemas opt into ``extra="forbid"``). Rejecting here alone
would make these routes the only ones that 422 on an unknown key, which is
a convention change with its own issue. What this file pins is the property that
matters either way: a body carrying the field **does not influence the stored
value**, measured by reading the model handed to the service.

The full HTTP path is driven, not the handler in isolation: the ignore happens in
the schema during request parsing, and a handler-level test would hand in a
schema instance that never saw the extra key.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.harvest.tenant_router import router as harvest_router
from app.api.v1.ipm.tenant_router import router as ipm_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_harvest_service, get_ipm_service
from app.common.enums import TenantRole
from app.domain.models.harvest import HarvestBatch, QualityAssessment
from app.domain.models.ipm import Inspection, TreatmentApplication
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
CALLER = "user-a"
#: What an attacker (or a confused client) puts into the body.
FORGED = "someone-else"


class _HarvestService:
    def __init__(self) -> None:
        self.created: list[HarvestBatch] = []
        self.assessments: list[QualityAssessment] = []

    def create_harvest_batch(self, plant_key: str, batch: HarvestBatch) -> HarvestBatch:
        self.created.append(batch)
        return batch.model_copy(update={"key": "hb-1", "plant_key": plant_key})

    def get_batch(self, key: str, tenant_key: str | None = None) -> HarvestBatch:
        return HarvestBatch(_key=key, tenant_key=tenant_key or "")

    def create_quality_assessment(self, batch_key: str, assessment: QualityAssessment) -> QualityAssessment:
        self.assessments.append(assessment)
        return assessment.model_copy(update={"key": "qa-1", "batch_key": batch_key})


class _IpmService:
    def __init__(self) -> None:
        self.inspections: list[Inspection] = []
        self.applications: list[TreatmentApplication] = []

    def create_inspection(self, plant_key: str, inspection: Inspection) -> Inspection:
        self.inspections.append(inspection)
        return inspection.model_copy(update={"key": "in-1", "plant_key": plant_key})

    def create_treatment_application(self, plant_key: str, app: TreatmentApplication) -> TreatmentApplication:
        self.applications.append(app)
        return app.model_copy(update={"key": "ta-1", "plant_key": plant_key})

    def get_treatment(self, key: str) -> Any:  # pragma: no cover - only reached if the route starts validating
        return object()


@pytest.fixture
def harness() -> tuple[TestClient, _HarvestService, _IpmService]:
    app = FastAPI()
    app.include_router(harvest_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(ipm_router, prefix="/api/v1/t/{tenant_slug}")
    ctx = TenantContext(tenant_key=TENANT_KEY, tenant_slug=TENANT_SLUG, user_key=CALLER, role=TenantRole.LEAD)
    # ``require_permission(...)`` composes on ``get_current_tenant``; overriding
    # the latter is how the gate resolves to this caller.
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    harvest, ipm = _HarvestService(), _IpmService()
    app.dependency_overrides[get_harvest_service] = lambda: harvest
    app.dependency_overrides[get_ipm_service] = lambda: ipm
    return TestClient(app, raise_server_exceptions=True), harvest, ipm


def _url(suffix: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/{suffix}"


def test_a_harvest_batch_is_attributed_to_the_caller_and_the_body_cannot_override_it(harness) -> None:
    client, harvest, _ipm = harness

    response = client.post(
        _url("harvest/plants/p1/batches"),
        json={"harvester": "Maren", "harvested_by_key": FORGED, "wet_weight_g": 12.5},
    )

    assert response.status_code == 201, response.text
    (batch,) = harvest.created
    assert batch.harvested_by_key == CALLER
    assert batch.harvester == "Maren", "the display name is the caller's free text, unchanged"
    assert FORGED not in response.text


def test_an_inspection_is_attributed_to_the_caller_and_the_body_cannot_override_it(harness) -> None:
    client, _harvest, ipm = harness

    response = client.post(
        _url("ipm/plants/p1/inspections"),
        json={"inspector": "Maren", "inspected_by_key": FORGED, "pressure_level": "low"},
    )

    assert response.status_code == 201, response.text
    (inspection,) = ipm.inspections
    assert inspection.inspected_by_key == CALLER
    assert inspection.inspector == "Maren"
    assert FORGED not in response.text


def test_a_treatment_application_is_attributed_to_the_caller_and_the_body_cannot_override_it(harness) -> None:
    client, _harvest, ipm = harness

    response = client.post(
        _url("ipm/plants/p1/treatment-applications"),
        json={"treatment_key": "tr-1", "applied_by": "Maren", "applied_by_key": FORGED},
    )

    assert response.status_code == 201, response.text
    (application,) = ipm.applications
    assert application.applied_by_key == CALLER
    assert application.applied_by == "Maren"
    assert FORGED not in response.text


def test_a_quality_assessment_is_attributed_to_the_caller_and_the_body_cannot_override_it(harness) -> None:
    """#1663 — the fourth retained category (NFR-011 R-16)."""
    client, harvest, _ipm = harness

    response = client.post(
        _url("harvest/batches/hb-1/quality"),
        json={"assessed_by": "Maren", "assessed_by_key": FORGED, "appearance_score": 80},
    )

    assert response.status_code == 201, response.text
    (assessment,) = harvest.assessments
    assert assessment.assessed_by_key == CALLER
    assert assessment.assessed_by == "Maren", "the display name is the caller's free text, unchanged"
    assert FORGED not in response.text


def test_a_body_without_the_field_is_attributed_all_the_same(harness) -> None:
    """The key is not opt-in: an ordinary create carries it too."""
    client, harvest, ipm = harness

    assert client.post(_url("harvest/plants/p1/batches"), json={}).status_code == 201
    assert client.post(_url("ipm/plants/p1/inspections"), json={}).status_code == 201
    assert client.post(_url("ipm/plants/p1/treatment-applications"), json={"treatment_key": "tr-1"}).status_code == 201
    assert client.post(_url("harvest/batches/hb-1/quality"), json={}).status_code == 201

    assert harvest.created[0].harvested_by_key == CALLER
    assert harvest.assessments[0].assessed_by_key == CALLER
    assert ipm.inspections[0].inspected_by_key == CALLER
    assert ipm.applications[0].applied_by_key == CALLER


def test_the_request_schemas_do_not_declare_the_key_fields() -> None:
    """The decision above rests on the field being absent from the schema.

    If somebody adds it to a ``*Create`` schema — even as optional — the
    handler's ``**body.model_dump()`` would hand a body value to the model and
    the explicit keyword after it would have to win by argument order alone.
    Pin the absence so that change has to come through here.
    """
    from app.api.v1.harvest.schemas import HarvestBatchCreate, HarvestBatchUpdate, QualityAssessmentCreate
    from app.api.v1.ipm.schemas import InspectionCreate, TreatmentApplicationCreate

    assert "harvested_by_key" not in HarvestBatchCreate.model_fields
    assert "harvested_by_key" not in HarvestBatchUpdate.model_fields
    assert "inspected_by_key" not in InspectionCreate.model_fields
    assert "applied_by_key" not in TreatmentApplicationCreate.model_fields
    assert "assessed_by_key" not in QualityAssessmentCreate.model_fields
