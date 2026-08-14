"""REQ-033 §4 — the five tools of issue #931 over the real MCP transport.

The unit tests exercise the handlers directly; this tier proves the parts that
only exist once the dispatcher, the registry and the HTTP surface are in play:

* the tools are in ``tools/list`` at all — a tool that never registers is
  invisible here no matter how well its class is tested;
* discovery is **role-filtered**, so a viewer-scoped key sees the reads and not
  the writes;
* the write path is refused for a viewer with ``403`` and admitted for a grower;
* ``dry_run`` reaches the tool as a preview and persists nothing;
* the same ``idempotency_key`` replays instead of writing twice — an LLM retry
  must not double a fertigation record;
* a tenant-independent tool (``search_plant_knowledge``) runs without a
  ``tenant`` argument, while a tenant-scoped one refuses an unknown tenant with
  ``not_found`` rather than a distinguishable permission error.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.mcp import deps as mcp_deps
from app.api.v1.mcp.router import router as mcp_router
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.config.settings import settings
from app.domain.interfaces.knowledge_service import KnowledgeChunk
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.ipm import Inspection
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import load_tools

TENANT = "home"


class _FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list = []

    def record(self, entry) -> str:
        self.entries.append(entry)
        return "a"


class _FakeIdemRepo:
    def __init__(self) -> None:
        self.records: dict = {}

    def get(self, sa, tenant_key, tool, idem):
        return self.records.get((sa, tenant_key, tool, idem))

    def store(self, record, *, ttl_hours=24):
        self.records[(record.service_account_key, record.tenant_key, record.tool_name, record.idempotency_key)] = record
        return record


class _FeedingService:
    def __init__(self) -> None:
        self.created: list[FeedingEvent] = []

    def create_event(self, event: FeedingEvent) -> FeedingEvent:
        # ``timestamp`` is defaulted on write by the repository
        # (``default_now_fields``), and the trend keys on it — a fake that left it
        # unset would make the diagnostics assertions pass vacuously.
        stored = event.model_copy(update={"key": f"fe-{len(self.created) + 1}", "timestamp": datetime.now(UTC)})
        self.created.append(stored)
        return stored

    def get_by_plant(self, plant_key, offset=0, limit=50, *, tenant_key):
        return [e for e in self.created if e.tenant_key == tenant_key and e.plant_key == plant_key]


class _IpmService:
    def __init__(self) -> None:
        self.created: list[Inspection] = []

    def get_pest(self, key):
        if key != "pe1":
            raise NotFoundError("Pest", key)
        return object()

    def get_disease(self, key):
        raise NotFoundError("Disease", key)

    def create_inspection(self, plant_key, inspection: Inspection) -> Inspection:
        inspection.plant_key = plant_key
        stored = inspection.model_copy(update={"key": f"insp-{len(self.created) + 1}"})
        self.created.append(stored)
        return stored

    def get_inspections(self, plant_key, offset=0, limit=50):
        return list(self.created), len(self.created)

    def check_harvest_safety(self, plant_key, planned_date=None):
        return True, []


class _NutrientPlanService:
    def __init__(self) -> None:
        self.assignments: list[tuple[str, str, str]] = []
        self._plan = SimpleNamespace(
            key="np-1",
            name="Erdbeere — Plagron Terra",
            description=None,
            is_template=False,
            tenant_key="",
            recommended_substrate_type="soil",
            version=1,
            tags=["outdoor"],
        )

    def get_plan(self, key, tenant_key="", *, for_write=False):
        if key != "np-1":
            raise NotFoundError("NutrientPlan", key)
        return self._plan

    def get_plant_plan(self, plant_key, *, tenant_key):
        return self._plan if self.assignments else None

    def get_phase_entries(self, plan_key):
        return []

    def assign_to_plant(self, plant_key, plan_key, assigned_by="", *, tenant_key):
        # Keyword-only and required since #950. This double was the *second* copy
        # of the pre-#950 contract; #1145 fixed the one in
        # tests/unit/mcp_server/test_analysis_write_tools.py and the guard it added
        # only scanned that file, so this one kept the same green-but-wrong shape
        # and turned red the moment the call site was corrected.
        self.assignments.append((plant_key, plan_key, assigned_by, tenant_key))
        return {"_key": "edge-1"}


class _KnowledgeService:
    async def search(self, query, *, top_k=5, doc_language=None):
        return [
            KnowledgeChunk(
                source_key="rag/ipm/spinnmilben#1",
                source_type="knowledge_guide",
                title="Spinnmilben biologisch bekämpfen",
                content="Raubmilben (Phytoseiulus persimilis) ab 20 °C ausbringen.",
                score=0.78,
                language="de",
            )
        ]


def _principal(role: TenantRole) -> McpPrincipal:
    return McpPrincipal(
        account_key="sa-1",
        display_name="bot",
        is_service_account=True,
        memberships=(McpTenantMembership(tenant_key=TENANT, tenant_slug=TENANT, tenant_name="Home", role=role),),
    )


def _build_app(role: TenantRole = TenantRole.GROWER) -> tuple[FastAPI, dict]:
    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]

    plant = SimpleNamespace(
        key="p1",
        plant_name="Erdbeere",
        instance_id="FRAGA-0712-TCJ",
        species_key="fragaria-x-ananassa",
        cultivar_key=None,
        location_key=None,
        substrate_key=None,
        current_phase_key="fruiting",
    )

    def _get_plant(key, tenant_key=""):
        if key != "p1" or tenant_key != TENANT:
            raise NotFoundError("PlantInstance", key)
        return plant

    services = {
        "plant_instance_service": SimpleNamespace(get_plant=_get_plant),
        "fertilizer_service": SimpleNamespace(
            get_fertilizer=lambda key, tenant_key="": SimpleNamespace(key=key, product_name="Terra Grow")
        ),
        "feeding_service": _FeedingService(),
        "ipm_service": _IpmService(),
        "nutrient_plan_service": _NutrientPlanService(),
        "knowledge_service_adapter": _KnowledgeService(),
        "care_reminder_service": SimpleNamespace(get_confirmation_history=lambda *a, **kw: []),
        "sensor_service": SimpleNamespace(get_sensors_for_location=lambda key: []),
        "observation_service": SimpleNamespace(is_available=lambda: False),
    }

    dispatcher = ToolDispatcher(
        load_tools(),
        MCPAuditLogger(_FakeAuditRepo()),
        IdempotencyStore(_FakeIdemRepo()),
        services=services,
    )
    app.dependency_overrides[mcp_deps.get_mcp_principal] = lambda: _principal(role)
    app.dependency_overrides[mcp_deps.get_dispatcher] = lambda: dispatcher
    return app, services


@pytest.fixture(autouse=True)
def _enable_mcp(monkeypatch):
    monkeypatch.setattr(settings, "mcp_server_enabled", True)
    yield


NEW_READ_TOOLS = ("get_plant_diagnostics", "search_plant_knowledge")
NEW_WRITE_TOOLS = ("record_feeding_event", "create_inspection", "assign_nutrient_plan")


# ── discovery ────────────────────────────────────────────────────────────────
def test_the_new_tools_are_discoverable_over_the_wire():
    # A tool that fails to register is invisible here — the failure mode this
    # repository has hit before, and the reason this assertion is at the API tier
    # rather than only against the registry object.
    app, _ = _build_app()
    client = TestClient(app)
    listing = client.post("/api/v1/mcp/rpc", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    tools = {t["name"]: t for t in listing.json()["result"]["tools"]}
    for name in NEW_READ_TOOLS + NEW_WRITE_TOOLS:
        assert name in tools, f"{name} is not exposed by tools/list"
        assert tools[name]["inputSchema"]["properties"]


def test_discovery_hides_the_new_write_tools_from_a_viewer():
    app, _ = _build_app(role=TenantRole.VIEWER)
    names = {t["name"] for t in TestClient(app).get("/api/v1/mcp/tools").json()["tools"]}
    for name in NEW_WRITE_TOOLS:
        assert name not in names
    for name in NEW_READ_TOOLS:
        assert name in names


@pytest.mark.parametrize("tool", NEW_WRITE_TOOLS)
def test_write_tools_are_denied_for_a_viewer(tool: str):
    app, services = _build_app(role=TenantRole.VIEWER)
    client = TestClient(app)
    payloads = {
        "record_feeding_event": {"plant_key": "p1", "volume_applied_liters": 1.0},
        "create_inspection": {"plant_key": "p1"},
        "assign_nutrient_plan": {"plant_key": "p1", "plan_key": "np-1"},
    }
    resp = client.post(f"/api/v1/mcp/tools/{tool}", json=payloads[tool])
    assert resp.status_code == 403
    assert services["feeding_service"].created == []
    assert services["ipm_service"].created == []
    assert services["nutrient_plan_service"].assignments == []


# ── record_feeding_event ─────────────────────────────────────────────────────
def test_record_feeding_event_persists_the_dose_and_is_read_back_by_diagnostics():
    app, services = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/record_feeding_event",
        json={
            "plant_key": "p1",
            "volume_applied_liters": 2.0,
            "fertilizers_used": [{"fertilizer_key": "f1", "ml_applied": 4.0}],
            "measured_ec_before": 1.5,
            "measured_ph_before": 6.0,
            "runoff_ec": 2.3,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["measured_ec_before"] == 1.5

    # The palette's addressability rule end to end: the write is findable again.
    read = client.post("/api/v1/mcp/tools/get_plant_diagnostics", json={"plant_key": "p1"})
    assert read.status_code == 200
    data = read.json()["data"]
    assert data["feeding_events"][0]["measured_ec_before"] == 1.5
    assert data["ec_ph_trend"]["ec"]["runoff"]["latest"] == 2.3
    assert services["feeding_service"].created


def test_record_feeding_event_dry_run_persists_nothing_and_says_so():
    app, services = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/record_feeding_event",
        json={"plant_key": "p1", "volume_applied_liters": 2.0, "dry_run": True},
    )
    assert resp.status_code == 200
    assert resp.json()["dry_run"] is True
    assert services["feeding_service"].created == []


def test_an_llm_retry_with_the_same_idempotency_key_does_not_double_the_dose():
    # A doubled fertigation record is not a cosmetic duplicate: it moves the
    # supply side of the evidence ladder and would invert a dosage conclusion.
    app, services = _build_app()
    client = TestClient(app)
    payload = {
        "plant_key": "p1",
        "volume_applied_liters": 2.0,
        "measured_ec_before": 1.5,
        "idempotency_key": "retry-1",
    }
    first = client.post("/api/v1/mcp/tools/record_feeding_event", json=payload)
    second = client.post("/api/v1/mcp/tools/record_feeding_event", json=payload)

    assert first.status_code == second.status_code == 200
    assert first.json()["data"]["feeding_event_key"] == second.json()["data"]["feeding_event_key"]
    assert len(services["feeding_service"].created) == 1


def test_record_feeding_event_refuses_a_foreign_plant_with_not_found():
    app, services = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/record_feeding_event",
        json={"plant_key": "someone-elses-plant", "volume_applied_liters": 1.0},
    )
    assert resp.status_code == 404
    assert services["feeding_service"].created == []


# ── create_inspection ────────────────────────────────────────────────────────
def test_create_inspection_round_trips_a_finding_through_get_plant_inspections():
    app, _ = _build_app()
    client = TestClient(app)
    written = client.post(
        "/api/v1/mcp/tools/create_inspection",
        json={
            "plant_key": "p1",
            "pressure_level": "medium",
            "findings": [
                {
                    "symptom": "Feine Gespinste an den Blattunterseiten",
                    "confidence": 0.82,
                    "affected_plant_part": "leaf",
                    "pest_key": "pe1",
                }
            ],
        },
    )
    assert written.status_code == 200
    assert written.json()["data"]["findings"][0]["confidence"] == 0.82

    read = client.post("/api/v1/mcp/tools/get_plant_inspections", json={"plant_key": "p1"})
    finding = read.json()["data"]["items"][0]["findings"][0]
    assert finding["affected_plant_part"] == "leaf"
    assert finding["pest_key"] == "pe1"


def test_create_inspection_rejects_an_out_of_range_confidence_as_a_validation_error():
    app, services = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/create_inspection",
        json={"plant_key": "p1", "findings": [{"symptom": "x", "confidence": 3.0}]},
    )
    assert resp.status_code == 422
    assert services["ipm_service"].created == []


# ── assign_nutrient_plan ─────────────────────────────────────────────────────
def test_assign_nutrient_plan_becomes_visible_through_get_plant_nutrient_plan():
    # The acceptance criterion in so many words.
    app, services = _build_app()
    client = TestClient(app)

    before = client.post("/api/v1/mcp/tools/get_plant_nutrient_plan", json={"plant_key": "p1"})
    assert before.json()["data"]["plan"] is None

    assigned = client.post(
        "/api/v1/mcp/tools/assign_nutrient_plan",
        json={"plant_key": "p1", "plan_key": "np-1"},
    )
    assert assigned.status_code == 200
    # The acting tenant is part of the recorded call since #950/#1145: the write is
    # tenant-scoped, and asserting it here is what keeps the route from quietly
    # dropping the argument again.
    assert services["nutrient_plan_service"].assignments == [("p1", "np-1", "mcp:sa-1", "home")]

    after = client.post("/api/v1/mcp/tools/get_plant_nutrient_plan", json={"plant_key": "p1"})
    assert after.json()["data"]["plan_key"] == "np-1"


def test_assign_nutrient_plan_dry_run_leaves_the_plant_unassigned():
    app, services = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/assign_nutrient_plan",
        json={"plant_key": "p1", "plan_key": "np-1", "dry_run": True},
    )
    assert resp.status_code == 200
    assert resp.json()["dry_run"] is True
    assert services["nutrient_plan_service"].assignments == []


# ── search_plant_knowledge ───────────────────────────────────────────────────
def test_search_plant_knowledge_needs_no_tenant_and_returns_citable_hits():
    app, _ = _build_app(role=TenantRole.VIEWER)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/search_plant_knowledge",
        json={"query": "Spinnmilben Bekaempfung biologisch"},
    )
    assert resp.status_code == 200
    hit = resp.json()["data"]["results"][0]
    assert hit["source_key"] == "rag/ipm/spinnmilben#1"
    assert hit["score"] == 0.78
    # Tenant-agnostic: the deep link must not be tenant-bound, which would have
    # raised on this path had the tool reached for ctx.api_link.
    assert resp.json()["links"][0]["url"] == "/api/v1/knowledge/search"


def test_search_plant_knowledge_rejects_an_empty_query():
    app, _ = _build_app()
    client = TestClient(app)
    assert client.post("/api/v1/mcp/tools/search_plant_knowledge", json={"query": ""}).status_code == 422


# ── tenant binding ───────────────────────────────────────────────────────────
def test_a_tenant_scoped_new_tool_reports_an_unknown_tenant_as_not_found():
    # §8.8 Szenario 6: never a distinguishable permission error, or the interface
    # could be walked to enumerate foreign tenants.
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/get_plant_diagnostics",
        json={"plant_key": "p1", "tenant": "somebody-elses-garden"},
    )
    assert resp.status_code == 404
