"""REQ-033 §4.3b — content blocks, the error contract and the audit size metric.

Unit-level counterpart to ``tests/api/test_mcp_content_blocks.py``: that one
pins the wire form, this one pins the model and dispatcher behaviour behind it —
above all that Base-64 image data reaches **neither** ``structuredContent``,
**nor** the idempotency record, **nor** the audit log.
"""

from __future__ import annotations

from base64 import b64encode

import pytest

from app.common.enums import McpPermission, TenantRole
from app.domain.models.mcp import McpImageContent, McpTextContent, McpToolResponse
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.base import (
    FIRST_IMAGE_CONTENT_INDEX,
    McpToolError,
    TenantToolInput,
    ToolBase,
    ToolInput,
    WriteToolBase,
    WriteToolInput,
    image_content_index,
)
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry

PHOTO = b"\x00WEBP-BYTES" * 64


class _FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list = []

    def record(self, entry) -> str:
        self.entries.append(entry)
        return "audit-1"


class _FakeIdempotencyRepo:
    def __init__(self) -> None:
        self.records: dict = {}

    def get(self, sa_key, tenant_key, tool_name, idem_key):
        return self.records.get((sa_key, tenant_key, tool_name, idem_key))

    def store(self, record, *, ttl_hours=24):
        self.records[(record.service_account_key, record.tenant_key, record.tool_name, record.idempotency_key)] = record
        return record


def _principal(role: TenantRole = TenantRole.LEAD) -> McpPrincipal:
    return McpPrincipal(
        account_key="sa-1",
        display_name="bot",
        is_service_account=True,
        memberships=(McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=role),),
    )


# ── Model ─────────────────────────────────────────────────────────────────────
def test_image_block_encodes_base64_and_serialises_camel_case():
    block = McpImageContent.from_bytes(PHOTO, "image/webp")
    assert block.data == b64encode(PHOTO).decode()
    # The protocol spells it 'mimeType'; the attribute stays snake_case (NFR-003).
    assert block.model_dump(by_alias=True) == {"type": "image", "data": block.data, "mimeType": "image/webp"}


def test_to_payload_excludes_content_blocks():
    response = McpToolResponse(
        summary="2 photos",
        data={"photos": [{"photo_id": "p-a"}]},
        content_blocks=[McpImageContent.from_bytes(PHOTO, "image/webp")],
    )
    payload = response.to_payload()

    assert "content_blocks" not in payload
    assert payload == {"summary": "2 photos", "data": {"photos": [{"photo_id": "p-a"}]}, "links": []}


def test_to_payload_of_a_block_free_response_is_unchanged():
    # Regression guard for the 12 shipped tools: adding the field must not add a
    # key to their payload.
    response = McpToolResponse(summary="ok", data={"total": 1})
    assert response.to_payload() == {"summary": "ok", "data": {"total": 1}, "links": []}


def test_image_payload_bytes_counts_only_image_blocks():
    response = McpToolResponse(
        summary="s",
        content_blocks=[
            McpTextContent(text="a note"),
            McpImageContent.from_bytes(PHOTO, "image/webp"),
            McpImageContent.from_bytes(PHOTO, "image/webp"),
        ],
    )
    assert response.image_payload_bytes() == 2 * len(b64encode(PHOTO))


def test_content_index_starts_after_the_summary_block():
    assert FIRST_IMAGE_CONTENT_INDEX == 1
    assert [image_content_index(i) for i in range(3)] == [1, 2, 3]


# ── Tool base helper ──────────────────────────────────────────────────────────
def test_image_response_builder_keeps_summary_and_appends_blocks():
    response = ToolBase._image_response(
        "1 photo delivered",
        images=[(PHOTO, "image/webp")],
        data={"entry_key": "e-1"},
        links=[{"type": "ui", "url": "/t/home/plants"}],
    )
    assert response.summary == "1 photo delivered"
    assert [b.type for b in response.content_blocks] == ["image"]
    assert response.content_blocks[0].data == b64encode(PHOTO).decode()
    assert response.links[0].url == "/t/home/plants"
    # The tool never has to encode a block itself, and the data stays clean.
    assert response.data == {"entry_key": "e-1"}


# ── Error contract ────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("not_found", 404),
        ("permission.denied", 403),
        ("conflict.already_claimed", 409),
        ("payload.too_large", 413),
        ("validation.tenant_required", 422),
        ("something.unmapped", 422),
    ],
)
def test_mcp_tool_error_maps_a_sane_http_status_for_the_rest_alias(code, status):
    assert McpToolError(code, "boom").status_code == status


def test_mcp_tool_error_keeps_the_details_object_and_the_nfr006_list_apart():
    exc = McpToolError(
        "conflict.already_claimed",
        "Entry is already being analysed",
        details={"claimed_by": "goose-laptop", "lease_expires_at": "2026-08-04T12:15:00Z"},
    )
    # The MCP wire gets the object with its original value types…
    assert exc.error_details == {"claimed_by": "goose-laptop", "lease_expires_at": "2026-08-04T12:15:00Z"}
    # …while the inherited list stays in the NFR-006 ErrorResponse shape, so the
    # REST alias keeps validating against the documented error schema.
    assert exc.details == [
        {"field": "claimed_by", "reason": "goose-laptop", "code": "conflict.already_claimed"},
        {"field": "lease_expires_at", "reason": "2026-08-04T12:15:00Z", "code": "conflict.already_claimed"},
    ]


# ── Audit metric (AC-S9) ──────────────────────────────────────────────────────
class _PhotoTool(ToolBase):
    tool_name = "photo_probe"
    permission = McpPermission.READ

    class Input(TenantToolInput):
        pass

    async def run(self, ctx, args):
        return self._image_response(
            "2 photos delivered",
            images=[(PHOTO, "image/webp"), (PHOTO, "image/webp")],
            data={"entry_key": "e-1"},
        )


class _TextTool(ToolBase):
    tool_name = "text_probe"
    permission = McpPermission.READ

    class Input(ToolInput):
        pass

    async def run(self, ctx, args):
        return self._response("nothing to see", data={"total": 0})


def _dispatcher():
    registry = ToolRegistry()
    registry.register(_PhotoTool())
    registry.register(_TextTool())
    audit_repo = _FakeAuditRepo()
    idem_repo = _FakeIdempotencyRepo()
    return ToolDispatcher(registry, MCPAuditLogger(audit_repo), IdempotencyStore(idem_repo)), audit_repo, idem_repo


@pytest.mark.asyncio
async def test_image_payload_is_reported_separately_from_the_response_size():
    # The decision behind AC-S9: output_size_bytes keeps measuring the structured
    # answer only, so a photo call stays comparable with every other tool; the
    # image payload is carried in its own field instead of being folded in
    # (which would drown all other tools) or dropped (which would be blind).
    dispatcher, audit_repo, _ = _dispatcher()
    await dispatcher.dispatch(_principal(), "photo_probe", {})
    entry = audit_repo.entries[-1]

    expected_image_bytes = 2 * len(b64encode(PHOTO))
    assert entry.image_bytes == expected_image_bytes
    # The structured size is a few hundred bytes of metadata — orders below the
    # image payload, and unaffected by it.
    assert entry.output_size_bytes < expected_image_bytes / 4
    # AC-S5: sizes only, never image data.
    assert b64encode(PHOTO).decode() not in str(entry.model_dump())


@pytest.mark.asyncio
async def test_a_text_tool_reports_zero_image_bytes():
    dispatcher, audit_repo, _ = _dispatcher()
    await dispatcher.dispatch(_principal(), "text_probe", {})
    entry = audit_repo.entries[-1]
    assert entry.image_bytes == 0
    assert entry.output_size_bytes > 0


# ── Idempotency store: the second consumer of to_payload() ────────────────────
@pytest.mark.asyncio
async def test_idempotency_record_never_persists_image_data():
    # A write tool delivering images is not in the catalogue today, but the store
    # persists whatever to_payload() returns — so the exclusion has to hold here
    # too, or Base-64 photos would end up in an adapter-layer collection.
    class _ImageWrite(WriteToolBase):
        tool_name = "image_write_probe"
        permission = McpPermission.WRITE

        class Input(WriteToolInput):
            pass

        async def preview(self, ctx, args):  # pragma: no cover - not exercised
            return self._response("would write")

        async def execute(self, ctx, args):
            return self._image_response("wrote", images=[(PHOTO, "image/webp")], data={"id": "x"})

    registry = ToolRegistry()
    registry.register(_ImageWrite())
    idem_repo = _FakeIdempotencyRepo()
    dispatcher = ToolDispatcher(registry, MCPAuditLogger(_FakeAuditRepo()), IdempotencyStore(idem_repo))

    await dispatcher.dispatch(_principal(), "image_write_probe", {"idempotency_key": "k-1"})
    stored = next(iter(idem_repo.records.values()))

    assert "content_blocks" not in stored.result_payload
    assert b64encode(PHOTO).decode() not in str(stored.result_payload)

    # …and a replay is a text-only response rather than a half-built image one.
    replayed = await dispatcher.dispatch(_principal(), "image_write_probe", {"idempotency_key": "k-1"})
    assert replayed.idempotent_replay is True
    assert replayed.content_blocks == []
