"""The five plant-scoped IPM reads answered for any tenant's plant (#1619).

``GET /t/{slug}/ipm/plants/{plant_key}/…`` took ``plant_key`` straight from the
path and handed it to a by-key lookup. ``karenz`` and ``harvest-safety`` then
returned the other tenant's **active substance, treatment name and Karenz
window**; ``inspections`` returned its private notes; ``treatment-applications``
its application records; ``inspection-schedule`` the timestamp of its last
inspection. Three of the five did not read ``ctx`` at all.

The write half beside them was already correct — ``create_inspection`` and
``create_treatment_application`` verify the plant at the repository (#517) —
and that asymmetry is what made the read half easy to miss in review.

Measured on the unfixed code against a real ArangoDB (root@localhost:8529,
throwaway database, real router → real service → real repository → real AQL):
all five answered HTTP 200 with tenant-b's rows.

These doubles replay the predicates the queries *actually* carry
(``tests/support/tenant_replay``), so removing the guard makes them red again
rather than agreeing with whatever the implementation does. The plant-ownership
lookup is served from a collection double, exactly as
``verify_entity_ownership`` reaches it.

Both directions are pinned: a guard that also hides the caller's own plant is
the #324 regression class and not a fix.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.ipm.tenant_router import router as ipm_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_ipm_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.domain.engines.inspection_scheduler import InspectionScheduler
from app.domain.engines.resistance_engine import ResistanceManager
from app.domain.engines.safety_interval_engine import SafetyIntervalValidator
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ipm_service import IpmService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, rows_and_count

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_PLANT = "plant-a1"
FOREIGN_PLANT = "plant-b1"
ABSENT_PLANT = "plant-nowhere"

#: The three things the Karenz reads must never hand to another tenant.
FOREIGN_INGREDIENT = "spirotetramat"
FOREIGN_TREATMENT_NAME = "Vertrauliche-Spiro-Mischung"
FOREIGN_NOTE = "Fremde-Geheimnotiz"

_PLANTS: dict[str, dict[str, Any]] = {
    OWN_PLANT: {"_key": OWN_PLANT, "tenant_key": TENANT_KEY},
    FOREIGN_PLANT: {"_key": FOREIGN_PLANT, "tenant_key": FOREIGN_TENANT_KEY},
}

_INSPECTIONS = [
    {
        "_key": "insp-b1",
        "tenant_key": FOREIGN_TENANT_KEY,
        "plant_key": FOREIGN_PLANT,
        "inspected_at": "2026-09-19T09:00:00Z",
        "pressure_level": "high",
        "detected_pest_keys": ["thrips"],
        "notes": FOREIGN_NOTE,
    },
    {
        "_key": "insp-a1",
        "tenant_key": TENANT_KEY,
        "plant_key": OWN_PLANT,
        "inspected_at": "2026-09-18T09:00:00Z",
        "pressure_level": "low",
        "detected_pest_keys": [],
        "notes": "Eigene Notiz",
    },
]

_APPLICATIONS = [
    {
        "_key": "ta-b1",
        "tenant_key": FOREIGN_TENANT_KEY,
        "plant_key": FOREIGN_PLANT,
        "treatment_key": "tr-secret",
        "applied_at": "2026-09-19T08:00:00Z",
    },
]

#: What the Karenz join would return for the foreign plant.
_KARENZ_ROWS = [
    {
        "plant_key": FOREIGN_PLANT,
        "active_ingredient": FOREIGN_INGREDIENT,
        "treatment_name": FOREIGN_TREATMENT_NAME,
        "applied_at": "2026-09-19T08:00:00Z",
        "safety_interval_days": 21,
        "safe_date": "2126-10-10T08:00:00.000Z",
    },
]


class _Collection:
    """``db.collection(name)`` double — answers by key regardless of tenant.

    That is the whole point: the real ``plant_instances.get(key)`` does exactly
    this, so the tenant comparison has to happen in the guard under test.
    """

    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self._docs = docs

    def get(self, key: str) -> dict[str, Any] | None:
        return self._docs.get(key)


def _karenz_handler(query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
    # ``ta.plant_key == @plant_key`` is the one predicate this query carries;
    # replay it so the rows follow the query rather than the test's wishes.
    return [row for row in _KARENZ_ROWS if row["plant_key"] == bind_vars.get("plant_key")]


def _client() -> TestClient:
    from app.data_access.arango import collections as col

    aql = (
        ReplayingAql()
        # More specific markers first: all three touch ``treatment_applications``.
        .route("safety_interval_days > 0", _karenz_handler)
        .route("@cutoff", _karenz_handler)
        .route(
            "FOR doc IN inspections",
            lambda q, b: rows_and_count(_INSPECTIONS, q, b),
        )
        .route(
            "FOR doc IN treatment_applications",
            lambda q, b: rows_and_count(_APPLICATIONS, q, b),
        )
    )
    db = ReplayingDatabase(aql, collections={col.PLANT_INSTANCES: _Collection(_PLANTS)})
    service = IpmService(
        ArangoIpmRepository(db),
        SafetyIntervalValidator(),
        ResistanceManager(),
        InspectionScheduler(),
    )

    app = FastAPI()
    app.include_router(ipm_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(
        KamerplanterError,
        lambda request, exc: JSONResponse(  # noqa: ARG005
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "message": exc.message},
        ),
    )
    ctx = TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user-a",
        role=TenantRole.GROWER,
    )
    app.dependency_overrides[get_current_tenant] = lambda: ctx
    # ``require_permission(...)`` returns a fresh callable per route, so it
    # cannot be overridden by identity; the two write routes are not exercised
    # here and the reads all resolve ``get_current_tenant`` directly.
    app.dependency_overrides[get_ipm_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False)


def _url(plant_key: str, suffix: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/ipm/plants/{plant_key}/{suffix}"


#: Every plant-scoped read of the tenant-scoped IPM router, with the marker each
#: one leaked. Adding a sixth read means adding a row here.
READS: list[tuple[str, tuple[str, ...]]] = [
    ("karenz", (FOREIGN_INGREDIENT, FOREIGN_TREATMENT_NAME)),
    ("harvest-safety", (FOREIGN_INGREDIENT,)),
    ("treatment-applications", ("ta-b1", "tr-secret")),
    ("inspections", (FOREIGN_NOTE, "insp-b1")),
    ("inspection-schedule", ("2026-09-19T09:00:00",)),
]


@pytest.fixture(scope="module")
def client() -> TestClient:
    return _client()


@pytest.mark.parametrize(("suffix", "markers"), READS, ids=[r[0] for r in READS])
def test_foreign_plant_is_refused_and_leaks_nothing(client: TestClient, suffix: str, markers: tuple[str, ...]) -> None:
    response = client.get(_url(FOREIGN_PLANT, suffix))

    assert response.status_code == 404, (
        f"GET .../plants/{FOREIGN_PLANT}/{suffix} answered {response.status_code} "
        f"for a plant of {FOREIGN_TENANT_KEY}: {response.text}"
    )
    leaked = [marker for marker in markers if marker in response.text]
    assert not leaked, f"foreign markers in the body of .../{suffix}: {leaked} — {response.text}"


@pytest.mark.parametrize("suffix", [r[0] for r in READS])
def test_absent_plant_is_indistinguishable_from_a_foreign_one(client: TestClient, suffix: str) -> None:
    """404 either way — no cross-tenant existence oracle (REQ-049 §2.4)."""
    foreign = client.get(_url(FOREIGN_PLANT, suffix))
    absent = client.get(_url(ABSENT_PLANT, suffix))

    assert foreign.status_code == absent.status_code == 404
    assert foreign.json()["error_code"] == absent.json()["error_code"]


@pytest.mark.parametrize("suffix", [r[0] for r in READS])
def test_own_plant_still_answers(client: TestClient, suffix: str) -> None:
    """The other direction: a guard that hides the caller's own plant is #324."""
    response = client.get(_url(OWN_PLANT, suffix))

    assert response.status_code == 200, f"own plant refused on .../{suffix}: {response.text}"


def test_own_inspections_are_still_returned(client: TestClient) -> None:
    """Not merely 200 — the caller's own row must actually be in the body."""
    response = client.get(_url(OWN_PLANT, "inspections"))

    assert [i["key"] for i in response.json()] == ["insp-a1"]


def test_every_plant_scoped_service_read_demands_a_tenant_key() -> None:
    """An unscoped call must be *unwritable*, not merely discouraged.

    ``tenant_key`` is keyword-only without a default on every plant-scoped
    method, so a call site that forgets it is a ``TypeError`` at import-time
    review rather than a silent cross-tenant read. This asserts the signature
    itself — a call that happens to pass it would not prove the default is gone.
    """
    import inspect

    methods = [
        "get_inspections",
        "get_applications",
        "get_karenz_periods",
        "check_harvest_safety",
        "get_inspection_schedule",
        "get_treatment_recommendations",
    ]
    offenders = []
    for name in methods:
        parameter = inspect.signature(getattr(IpmService, name)).parameters.get("tenant_key")
        if parameter is None or parameter.kind is not inspect.Parameter.KEYWORD_ONLY:
            offenders.append(f"{name}: not keyword-only")
        elif parameter.default is not inspect.Parameter.empty:
            offenders.append(f"{name}: has default {parameter.default!r}")
    assert not offenders, offenders


def test_an_unscoped_caller_cannot_be_waved_through() -> None:
    """An empty ``tenant_key`` is refused, not read as 'skip the check'.

    A service principal with no active tenant resolves ``""``; a guard that
    treats that as *unscoped, allow everything* would be inert for exactly the
    caller class that most needs it (the #1402 argument).
    """
    from app.data_access.arango import collections as col

    db = ReplayingDatabase(ReplayingAql(), collections={col.PLANT_INSTANCES: _Collection(_PLANTS)})
    service = IpmService(ArangoIpmRepository(db), SafetyIntervalValidator(), ResistanceManager(), InspectionScheduler())

    with pytest.raises(ValueError, match="tenant"):
        service.get_karenz_periods(FOREIGN_PLANT, tenant_key="")
