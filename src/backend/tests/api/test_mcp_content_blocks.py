"""REQ-033 §4.3b / REQ-050 §4.0 — wire form of ``tools/call``.

Covers the two protocol extensions image delivery needs, plus the guard that
keeps them from changing anything for the 12 existing text-only tools:

* image content blocks are **appended** after the leading ``summary`` text block
  and never appear inside ``structuredContent``;
* a tool failure arrives as a *result* with ``isError: true`` **and** a
  machine-readable ``structuredContent`` (``error_code``/``message``/``details``),
  which is what a recipe branches on.

Everything runs against an isolated tool registry so no DB and no real tool are
involved — the subject here is the transport, not any tool.
"""

from __future__ import annotations

import json
from base64 import b64decode, b64encode

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.mcp import deps as mcp_deps
from app.api.v1.mcp.router import router as mcp_router
from app.common.enums import McpPermission, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import DiaryAnalysisAlreadyClaimedError, KamerplanterError
from app.config.settings import settings
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.base import (
    McpToolError,
    TenantToolInput,
    ToolBase,
    ToolInput,
    image_content_index,
)
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry

#: Two distinguishable "renditions" — content is irrelevant, identity is not.
PHOTO_A = b"\x01WEBP-A" * 4
PHOTO_B = b"\x02WEBP-B" * 4


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


class _FakeSessionStore:
    def create(self, *, account_key: str) -> str:
        return "sess-1"

    def is_valid(self, session_id: str, *, account_key: str) -> bool:
        return True

    def terminate(self, session_id: str) -> None:
        return None


# ── Tools under test ──────────────────────────────────────────────────────────
class _TextTool(ToolBase):
    """A stand-in for the 12 existing text-only tools."""

    tool_name = "text_only"
    permission = McpPermission.READ

    class Input(ToolInput):
        pass

    async def run(self, ctx, args):
        return self._response(
            "3 plants need watering today",
            data={"total": 3},
            links=[{"type": "ui", "url": "/t/home/care"}],
        )


class _PhotoTool(ToolBase):
    """Stand-in for get_diary_entry_photos (WP-5): two images, ordered."""

    tool_name = "photo_probe"
    permission = McpPermission.READ

    class Input(TenantToolInput):
        pass

    async def run(self, ctx, args):
        photos = [
            {"photo_id": "p-a", "status": "delivered", "content_index": image_content_index(0)},
            {"photo_id": "p-b", "status": "delivered", "content_index": image_content_index(1)},
        ]
        return self._image_response(
            "2 of 3 photos delivered (1280 px)",
            images=[(PHOTO_A, "image/webp"), (PHOTO_B, "image/webp")],
            data={"entry_key": "e-1", "size": 1280, "photos": photos, "pending": [{"photo_id": "p-c"}]},
        )


class _ClaimedTool(ToolBase):
    """Raises the documented conflict WP-5 needs to transport (REQ-050 §4.2)."""

    tool_name = "already_claimed_probe"
    permission = McpPermission.READ

    class Input(TenantToolInput):
        pass

    async def run(self, ctx, args):
        raise McpToolError(
            "conflict.already_claimed",
            "Entry is already being analysed",
            details={"claimed_by": "goose-laptop", "lease_expires_at": "2026-08-04T12:15:00Z"},
        )


class _DomainClaimedTool(ToolBase):
    """Raises the same conflict as ``_ClaimedTool`` — but the *domain* class.

    ``DiaryAnalysisAlreadyClaimedError`` is a ``ContractError``: a **sibling** of
    ``McpToolError``, not a subclass, carrying the same published code and the
    same free-form ``error_details``. The five diary tools raise this class, not
    the transport's own — so an envelope that decides by ``isinstance`` on
    ``McpToolError`` drops ``claimed_by`` and ``lease_expires_at`` for precisely
    the errors REQ-050 §4.2 promises them for, while the ``error_code`` still
    looks right. That is the failure mode this probe exists to catch: the class
    the tools actually raise, taken all the way onto the wire.
    """

    tool_name = "domain_claimed_probe"
    permission = McpPermission.READ

    class Input(TenantToolInput):
        pass

    async def run(self, ctx, args):
        raise DiaryAnalysisAlreadyClaimedError(
            "8271634",
            claimed_by="goose-laptop",
            lease_expires_at="2026-08-04T12:15:00Z",
        )


def _principal(role: TenantRole = TenantRole.GROWER, *, slugs: tuple[str, ...] = ("home",)) -> McpPrincipal:
    return McpPrincipal(
        account_key="sa-1",
        display_name="bot",
        is_service_account=True,
        memberships=tuple(
            McpTenantMembership(tenant_key=s, tenant_slug=s, tenant_name=s.title(), role=role) for s in slugs
        ),
    )


def _build_app(principal: McpPrincipal | None = None) -> tuple[FastAPI, _FakeAuditRepo]:
    registry = ToolRegistry()
    registry.register(_TextTool())
    registry.register(_PhotoTool())
    registry.register(_ClaimedTool())
    registry.register(_DomainClaimedTool())

    audit_repo = _FakeAuditRepo()
    dispatcher = ToolDispatcher(registry, MCPAuditLogger(audit_repo), IdempotencyStore(_FakeIdemRepo()))

    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[mcp_deps.get_mcp_principal] = lambda: principal or _principal()
    app.dependency_overrides[mcp_deps.get_dispatcher] = lambda: dispatcher
    app.dependency_overrides[mcp_deps.get_session_store] = lambda: _FakeSessionStore()
    return app, audit_repo


@pytest.fixture(autouse=True)
def _enable_mcp(monkeypatch):
    monkeypatch.setattr(settings, "mcp_server_enabled", True)
    yield


def _call(client: TestClient, name: str, arguments: dict | None = None) -> dict:
    params = {"name": name, "arguments": arguments or {}}
    resp = client.post("/api/v1/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params})
    assert resp.status_code == 200
    return resp.json()["result"]


# ── Non-regression: a tool without content blocks is untouched ────────────────
def test_text_only_tool_result_is_unchanged_by_the_image_extension():
    # The binding non-regression condition for the 12 shipped tools: with no
    # content blocks set, the result is exactly what the transport produced
    # before image blocks existed — one text block, structuredContent = payload.
    app, _ = _build_app()
    result = _call(TestClient(app), "text_only")

    assert result == {
        "isError": False,
        "content": [{"type": "text", "text": "3 plants need watering today"}],
        "structuredContent": {
            "summary": "3 plants need watering today",
            "data": {"total": 3},
            "links": [{"type": "ui", "url": "/t/home/care"}],
        },
    }
    # No empty "content_blocks" key leaked into the structured part either.
    assert "content_blocks" not in result["structuredContent"]


# ── Image blocks (REQ-050 §4.4) ───────────────────────────────────────────────
def test_two_images_are_appended_after_the_summary_block_in_order():
    app, _ = _build_app()
    result = _call(TestClient(app), "photo_probe")

    kinds = [block["type"] for block in result["content"]]
    assert kinds == ["text", "image", "image"]
    assert result["content"][0]["text"] == "2 of 3 photos delivered (1280 px)"

    # Same order as the payload advertises, and camelCase on the wire.
    assert b64decode(result["content"][1]["data"]) == PHOTO_A
    assert b64decode(result["content"][2]["data"]) == PHOTO_B
    assert {block["mimeType"] for block in result["content"][1:]} == {"image/webp"}

    # content_index resolves the block for each photo id (REQ-050 §4.4).
    photos = result["structuredContent"]["data"]["photos"]
    assert [p["content_index"] for p in photos] == [1, 2]
    assert b64decode(result["content"][photos[0]["content_index"]]["data"]) == PHOTO_A


def test_structured_content_never_repeats_the_image_data():
    # The whole point of excluding the blocks from to_payload(): otherwise every
    # photo crosses the wire twice, doubling the token cost of a 4 MB call.
    app, _ = _build_app()
    result = _call(TestClient(app), "photo_probe")

    serialised = json.dumps(result["structuredContent"])
    assert b64encode(PHOTO_A).decode() not in serialised
    assert b64encode(PHOTO_B).decode() not in serialised
    # …while the metadata about them is very much still there.
    assert result["structuredContent"]["data"]["pending"] == [{"photo_id": "p-c"}]


# ── Error envelope (REQ-050 §4.0) ─────────────────────────────────────────────
def test_tool_error_carries_a_machine_readable_structured_content():
    app, _ = _build_app()
    result = _call(TestClient(app), "already_claimed_probe")

    assert result["isError"] is True
    assert result["structuredContent"] == {
        "error_code": "conflict.already_claimed",
        "message": "Entry is already being analysed",
        "details": {"claimed_by": "goose-laptop", "lease_expires_at": "2026-08-04T12:15:00Z"},
    }
    # A human-readable block is still there for a model that reads only text.
    assert result["content"][0]["type"] == "text"


def test_a_domain_contract_error_keeps_its_details_on_the_wire():
    # AK-05 on the wire, for the class the diary tools actually raise. Without
    # the details an agent learns *that* the entry is taken but not *until when*
    # and *by whom* — the two facts §4.2 gives it to decide whether to come back
    # later. The error_code alone passing is exactly the half-truth this guards.
    app, _ = _build_app()
    result = _call(TestClient(app), "domain_claimed_probe")

    assert result["isError"] is True
    assert result["structuredContent"]["error_code"] == "conflict.already_claimed"
    assert result["structuredContent"]["details"] == {
        "entry_key": "8271634",
        "claimed_by": "goose-laptop",
        "lease_expires_at": "2026-08-04T12:15:00Z",
    }
    # …and nothing beyond the three published keys: the envelope crosses a trust
    # boundary, so no error_id, no stack, no internal detail list rides along.
    assert set(result["structuredContent"]) == {"error_code", "message", "details"}


def test_error_code_is_stable_when_the_message_changes():
    # 'error_code' is the contract; 'message' is prose and free to change. A code
    # derived from the message would silently break every recipe on a reword.
    class _Reworded(_ClaimedTool):
        tool_name = "already_claimed_probe"

        async def run(self, ctx, args):
            raise McpToolError(
                "conflict.already_claimed",
                "Eintrag wird bereits analysiert",  # translated + reworded
                details={"claimed_by": "goose-laptop"},
            )

    registry = ToolRegistry()
    registry.register(_Reworded())
    dispatcher = ToolDispatcher(registry, MCPAuditLogger(_FakeAuditRepo()), IdempotencyStore(_FakeIdemRepo()))
    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    app.dependency_overrides[mcp_deps.get_mcp_principal] = lambda: _principal()
    app.dependency_overrides[mcp_deps.get_dispatcher] = lambda: dispatcher
    app.dependency_overrides[mcp_deps.get_session_store] = lambda: _FakeSessionStore()

    result = _call(TestClient(app), "already_claimed_probe")
    assert result["structuredContent"]["error_code"] == "conflict.already_claimed"
    assert result["structuredContent"]["message"] == "Eintrag wird bereits analysiert"


@pytest.mark.parametrize(
    ("principal", "arguments", "expected_code"),
    [
        # A tenant the key is not a member of — never 'permission.denied', which
        # would confirm that someone else's garden exists (§4.0).
        (_principal(), {"tenant": "someone-elses-garden"}, "not_found"),
        # Ambiguous tenant: its own code so a recipe can retry with a slug.
        (_principal(slugs=("home", "garden")), {}, "validation.tenant_required"),
    ],
)
def test_dispatcher_failures_use_the_published_contract_codes(principal, arguments, expected_code):
    app, _ = _build_app(principal)
    result = _call(TestClient(app), "photo_probe", arguments)
    assert result["isError"] is True
    assert result["structuredContent"]["error_code"] == expected_code


def test_permission_denied_uses_the_published_contract_code():
    # A viewer calling a write tool. Registered here rather than reused from the
    # global palette so the test states its own preconditions.
    from app.mcp_server.base import WriteToolBase, WriteToolInput

    class _Write(WriteToolBase):
        tool_name = "write_probe"
        permission = McpPermission.WRITE

        class Input(WriteToolInput):
            pass

        async def preview(self, ctx, args):  # pragma: no cover - never reached
            return self._response("would write")

        async def execute(self, ctx, args):  # pragma: no cover - never reached
            return self._response("wrote")

    registry = ToolRegistry()
    registry.register(_Write())
    dispatcher = ToolDispatcher(registry, MCPAuditLogger(_FakeAuditRepo()), IdempotencyStore(_FakeIdemRepo()))
    app = FastAPI()
    app.include_router(mcp_router, prefix="/api/v1")
    app.dependency_overrides[mcp_deps.get_mcp_principal] = lambda: _principal(TenantRole.VIEWER)
    app.dependency_overrides[mcp_deps.get_dispatcher] = lambda: dispatcher
    app.dependency_overrides[mcp_deps.get_session_store] = lambda: _FakeSessionStore()

    result = _call(TestClient(app), "write_probe")
    assert result["structuredContent"]["error_code"] == "permission.denied"


def test_unknown_tool_is_a_tool_result_not_a_jsonrpc_error():
    # §4.0: a JSON-RPC 'error' means protocol/auth failure. An unknown tool name
    # is answerable by the recipe (call tools/list) and stays a result.
    app, _ = _build_app()
    result = _call(TestClient(app), "no_such_tool")
    assert result["isError"] is True
    assert result["structuredContent"]["error_code"] == "not_found"
