"""REQ-033 §4 — API tests for the MCP transport.

Builds a minimal app mounting the MCP router with dependency overrides and
asserts discovery (role-filtered), a tool call, the JSON-RPC surface, the 404
kill-switch and permission gating end-to-end (§8 AC-2/AC-D2).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.mcp import deps as mcp_deps
from app.api.v1.mcp.router import router as mcp_router
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import load_tools


class _FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list = []

    def record(self, entry) -> str:
        self.entries.append(entry)
        return "a"


class _FakeSessionStore:
    """In-memory stand-in for the Redis-backed Streamable-HTTP session store."""

    def __init__(self) -> None:
        self.sessions: dict[str, str] = {}
        self.counter = 0

    def create(self, *, account_key: str) -> str:
        self.counter += 1
        sid = f"sess-{self.counter}"
        self.sessions[sid] = account_key
        return sid

    def is_valid(self, session_id: str, *, account_key: str) -> bool:
        return self.sessions.get(session_id) == account_key

    def terminate(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


class _FakeIdemRepo:
    def __init__(self) -> None:
        self.records: dict = {}

    def get(self, sa, tenant_key, tool, idem):
        return self.records.get((sa, tenant_key, tool, idem))

    def store(self, record, *, ttl_hours=24):
        self.records[(record.service_account_key, record.tenant_key, record.tool_name, record.idempotency_key)] = record
        return record


def _principal(role: TenantRole) -> McpPrincipal:
    return McpPrincipal(
        account_key="sa-1",
        display_name="bot",
        is_service_account=True,
        memberships=(McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=role),),
    )


def _build_app(role: TenantRole = TenantRole.GROWER) -> tuple[FastAPI, dict]:
    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]

    # Read tools delegate to injected fakes so no DB is needed.
    species = [SimpleNamespace(key="sp-1", scientific_name="Tomato", common_names=["Tomato"], genus="Solanum")]
    fake_species = SimpleNamespace(list_species=lambda offset, limit: (species, 1))
    fake_care = SimpleNamespace(
        confirm_reminder=lambda plant_key, reminder_type, notes, tenant_key="": SimpleNamespace(key="cc-1")
    )
    # SEC-001: confirm_care_task ownership-checks the plant first via get_plant.
    fake_plants = SimpleNamespace(get_plant=lambda key, tenant_key: SimpleNamespace(key=key))
    services = {
        "species_service": fake_species,
        "care_reminder_service": fake_care,
        "plant_instance_service": fake_plants,
    }

    dispatcher = ToolDispatcher(
        load_tools(),
        MCPAuditLogger(_FakeAuditRepo()),
        IdempotencyStore(_FakeIdemRepo()),
        services=services,
    )

    sessions = _FakeSessionStore()
    app.dependency_overrides[mcp_deps.get_mcp_principal] = lambda: _principal(role)
    app.dependency_overrides[mcp_deps.get_dispatcher] = lambda: dispatcher
    app.dependency_overrides[mcp_deps.get_session_store] = lambda: sessions
    return app, {"sessions": sessions}


@pytest.fixture(autouse=True)
def _enable_mcp(monkeypatch):
    monkeypatch.setattr(settings, "mcp_server_enabled", True)
    yield


def test_discovery_is_role_filtered():
    app, _ = _build_app(role=TenantRole.VIEWER)
    client = TestClient(app)
    resp = client.get("/api/v1/mcp/tools")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()["tools"]}
    # A viewer only sees read tools.
    assert "list_species" in names
    assert "confirm_care_task" not in names
    assert "create_site" not in names


def test_call_read_tool():
    app, _ = _build_app(role=TenantRole.VIEWER)
    client = TestClient(app)
    resp = client.post("/api/v1/mcp/tools/list_species", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["total"] == 1
    assert body["summary"]


def test_write_tool_denied_for_viewer():
    app, _ = _build_app(role=TenantRole.VIEWER)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/confirm_care_task",
        json={"plant_key": "p1", "reminder_type": "watering"},
    )
    assert resp.status_code == 403


def test_write_tool_allowed_for_grower():
    app, _ = _build_app(role=TenantRole.GROWER)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/tools/confirm_care_task",
        json={"plant_key": "p1", "reminder_type": "watering"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["confirmation_key"] == "cc-1"


def test_jsonrpc_initialize_and_tools_list():
    app, _ = _build_app(role=TenantRole.GROWER)
    client = TestClient(app)

    init = client.post("/api/v1/mcp/rpc", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init.json()["result"]["serverInfo"]["name"] == "kamerplanter-mcp"

    listing = client.post("/api/v1/mcp/rpc", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = listing.json()["result"]["tools"]
    assert any(t["name"] == "list_species" for t in tools)
    assert all("inputSchema" in t for t in tools)


def test_jsonrpc_tool_call_returns_structured_content():
    app, _ = _build_app(role=TenantRole.GROWER)
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp/rpc",
        json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "list_species", "arguments": {}}},
    )
    result = resp.json()["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["data"]["total"] == 1


def test_jsonrpc_unknown_method():
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.post("/api/v1/mcp/rpc", json={"jsonrpc": "2.0", "id": 9, "method": "bogus"})
    assert resp.json()["error"]["code"] == -32601


def test_jsonrpc_notification_is_acknowledged_without_a_body():
    # A JSON-RPC notification carries no "id" and MUST NOT be answered — not even
    # with an error. Every MCP client sends `notifications/initialized` right
    # after `initialize`, so answering it at all breaks the handshake for a
    # spec-strict client.
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.post("/api/v1/mcp/rpc", json={"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert resp.status_code == 202
    assert resp.content == b""


def test_jsonrpc_full_client_handshake():
    # The exact sequence a real client drives: initialize → initialized → tools/list.
    app, _ = _build_app()
    client = TestClient(app)

    init = client.post(
        "/api/v1/mcp/rpc",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}},
        },
    )
    assert init.json()["result"]["protocolVersion"] == "2024-11-05"

    assert (
        client.post("/api/v1/mcp/rpc", json={"jsonrpc": "2.0", "method": "notifications/initialized"}).status_code
        == 202
    )

    listed = client.post("/api/v1/mcp/rpc", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert [t["name"] for t in listed.json()["result"]["tools"]]


# ── Streamable-HTTP transport conformance (§4.3a) ─────────────────────────────
def test_canonical_endpoint_and_deprecated_alias_behave_identically():
    app, _ = _build_app()
    client = TestClient(app)
    body = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
    assert client.post("/api/v1/mcp", json=body).json() == client.post("/api/v1/mcp/rpc", json=body).json()


def test_initialize_negotiates_the_clients_protocol_revision():
    app, _ = _build_app()
    client = TestClient(app)
    for requested in ("2025-06-18", "2025-03-26", "2024-11-05"):
        resp = client.post(
            "/api/v1/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": requested}},
        )
        assert resp.json()["result"]["protocolVersion"] == requested


def test_initialize_falls_back_to_latest_for_an_unknown_revision():
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}},
    )
    # The client decides whether it can live with the answer; we never claim to
    # speak a revision we do not implement.
    assert resp.json()["result"]["protocolVersion"] == "2025-06-18"


def test_initialize_issues_a_session_id_that_later_calls_may_present():
    app, ctx = _build_app()
    client = TestClient(app)
    init = client.post("/api/v1/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    session_id = init.headers["mcp-session-id"]
    assert session_id in ctx["sessions"].sessions

    ok = client.post(
        "/api/v1/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        headers={"Mcp-Session-Id": session_id},
    )
    assert ok.status_code == 200


def test_unknown_session_gets_404_so_the_client_re_initialises():
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        headers={"Mcp-Session-Id": "sess-does-not-exist"},
    )
    assert resp.status_code == 404


def test_session_is_bound_to_its_creating_account():
    # A leaked session id must be worthless under a different key.
    app, ctx = _build_app()
    client = TestClient(app)
    ctx["sessions"].sessions["sess-foreign"] = "somebody-else"
    resp = client.post(
        "/api/v1/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "ping"},
        headers={"Mcp-Session-Id": "sess-foreign"},
    )
    assert resp.status_code == 404


def test_unsupported_protocol_version_header_is_rejected():
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/api/v1/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "ping"},
        headers={"MCP-Protocol-Version": "1999-01-01"},
    )
    assert resp.status_code == 400


def test_missing_protocol_version_header_is_tolerated():
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.post("/api/v1/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert resp.status_code == 200
    assert resp.headers["mcp-protocol-version"] == "2025-03-26"


def test_get_on_the_endpoint_declines_with_405():
    # The server opens no server-to-client stream; 405 is the sanctioned answer.
    app, _ = _build_app()
    client = TestClient(app)
    resp = client.get("/api/v1/mcp")
    assert resp.status_code == 405
    assert "POST" in resp.headers["allow"]


def test_delete_terminates_the_session():
    app, ctx = _build_app()
    client = TestClient(app)
    init = client.post("/api/v1/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    session_id = init.headers["mcp-session-id"]

    assert client.request("DELETE", "/api/v1/mcp", headers={"Mcp-Session-Id": session_id}).status_code == 204
    assert session_id not in ctx["sessions"].sessions
    # Idempotent: deleting again is still a 204.
    assert client.request("DELETE", "/api/v1/mcp", headers={"Mcp-Session-Id": session_id}).status_code == 204


def test_kill_switch_returns_404(monkeypatch):
    # With the operator flag off, the whole surface answers 404 (AC-D2) — the
    # canonical endpoint included. Built without dependency overrides so the real
    # gating dependency runs.
    monkeypatch.setattr(settings, "mcp_server_enabled", False)
    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    client = TestClient(app)

    assert client.get("/api/v1/mcp/tools").status_code == 404
    assert client.post("/api/v1/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).status_code == 404
    assert client.get("/api/v1/mcp").status_code == 404
    assert client.request("DELETE", "/api/v1/mcp").status_code == 404
