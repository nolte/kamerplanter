"""REQ-033 MCP server — persistence + response models.

The MCP server keeps no own domain data (§3); these models only back the two
adapter-layer collections (``mcp_audit_log``, ``mcp_idempotency_record``) and
the LLM-facing tool-response envelope (§2.6).

Source code is English only (NFR-003).
"""

from __future__ import annotations

from base64 import b64encode
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from app.common.enums import McpPermission, McpToolStatus


class McpAuditLog(BaseModel):
    """One audit entry per MCP tool call (§3, §4.6).

    Records *no* PII: tool arguments are hashed (``input_hash``) so free-text
    diary/symptom payloads never reach the log (AC-S5). API keys never appear
    here (AC-S2).
    """

    key: str | None = Field(default=None, alias="_key")
    service_account_key: str  # FK -> users (the service account)
    tenant_key: str  # FK -> tenants
    tool_name: str
    input_hash: str  # sha256 over the tool arguments
    #: Size of the *structured* answer only — image content blocks are excluded by
    #: construction (see :meth:`McpToolResponse.to_payload`) and counted in
    #: ``image_bytes`` instead (REQ-033 §4.3b, AC-S9).
    output_size_bytes: int = 0
    #: Base-64 payload of the image content blocks, in bytes. A *size*, never
    #: image data — the log stays PII-free (AC-S5).
    image_bytes: int = 0
    duration_ms: int = 0
    status: McpToolStatus
    error_class: str | None = None
    created_at: datetime | None = None

    model_config = {"populate_by_name": True, "use_enum_values": True}


class McpAuditLogEntry(BaseModel):
    """Read-projection of an audit entry for the privacy self-service view (§4.6).

    **Every field here defaults exactly as its :class:`McpAuditLog` counterpart
    does, and that is a rule, not a coincidence (#1145).** A read projection
    stricter than the writer over the same collection can only fail.

    The concrete break was ``error_class``. ``X | None`` *without* ``= None`` is a
    **required** field in Pydantic — it permits null, it does not permit absence —
    and :meth:`ArangoMcpAuditRepository.record` dumps with ``exclude_none=True``,
    so a call that raised nothing stores no ``error_class`` key at all. Every
    *successful* tool call therefore wrote a row this model rejected, and
    ``get_mcp_activity`` answered 500 for every account and every ``limit`` from
    the first such row onward. The inversion is the tell: an **error** row carries
    an ``error_class`` and validated fine, so the only rows the activity view could
    ever have read were the failures.

    (#1145 reasonably guessed at old rows predating a later-added field, and left
    the discriminator as an open question. It is not that: the mismatch is
    deterministic and reproducible from the writer's own dump — see
    ``test_mcp_audit_projection_matches_its_writer.py``. ``output_size_bytes``,
    ``duration_ms`` and ``created_at`` were latently exposed to the same class of
    bug and are defaulted here too, though none of them was reachable — the first
    two never dump as ``None``, and ``record`` fills ``created_at`` explicitly.)
    """

    tool_name: str
    tenant_key: str
    status: McpToolStatus
    output_size_bytes: int = 0
    duration_ms: int = 0
    error_class: str | None = None
    created_at: datetime | None = None

    model_config = {"use_enum_values": True}


class McpIdempotencyRecord(BaseModel):
    """Idempotency replay record for a write tool (§2.6, §3).

    Keyed by ``(service_account_key, tenant_key, tool_name, idempotency_key)``; a
    repeated call within the TTL replays ``result_payload`` instead of writing
    twice (AC-19). ``tenant_key`` is part of the scope (SEC-005): a multi-tenant
    service account holding two tenant-scoped keys must never replay tenant-A's
    stored result for a tenant-B call.
    """

    key: str | None = Field(default=None, alias="_key")
    service_account_key: str
    tenant_key: str
    tool_name: str
    idempotency_key: str
    input_hash: str
    result_payload: dict[str, Any]
    created_at: datetime | None = None
    expires_at: datetime | None = None

    model_config = {"populate_by_name": True}


class McpToolLink(BaseModel):
    """A UI/API deep link the end user can follow for details (§2.6)."""

    type: str  # "ui" | "api"
    url: str


class McpTextContent(BaseModel):
    """A ``text`` content block (REQ-033 §4.3b).

    The transport always emits ``summary`` as the leading text block; a tool only
    adds further blocks when it has something a language model must *see* rather
    than read out of ``structuredContent``.
    """

    type: Literal["text"] = "text"
    text: str


class McpImageContent(BaseModel):
    """An ``image`` content block carrying Base-64 data (REQ-033 §4.3b).

    Built through :meth:`from_bytes` so no tool ever encodes a block by hand.
    The wire key is ``mimeType`` (MCP is camelCase there); the Python attribute
    stays snake_case per NFR-003, hence the serialisation alias.

    Only the WebP renditions from NFR-013 §8.2 may be put in here — never an
    original upload (AC-S7): originals may be 25 MB and carry EXIF data.
    """

    type: Literal["image"] = "image"
    data: str = Field(description="Base-64 encoded image bytes.")
    mime_type: str = Field(serialization_alias="mimeType", description="e.g. 'image/webp'.")

    @classmethod
    def from_bytes(cls, raw: bytes, mime_type: str) -> McpImageContent:
        """Encode raw rendition bytes into a protocol-ready image block."""

        return cls(data=b64encode(raw).decode("ascii"), mime_type=mime_type)


#: Any block a tool may append after the leading ``summary`` text block.
McpContentBlock = Annotated[McpTextContent | McpImageContent, Field(discriminator="type")]


class McpToolResponse(BaseModel):
    """LLM-friendly tool response envelope (§2.6, §4.3b).

    ``summary`` is a one-sentence recap for the LLM, ``data`` the structured
    result, ``links`` point the human user at the UI/API. Write tools also set
    ``dry_run``/``idempotency_key``/``idempotent_replay``.

    ``content_blocks`` carries non-text content (today: images) that the
    transport appends *after* the leading summary text block. It is deliberately
    **not** part of the serialised payload — see :meth:`to_payload`.
    """

    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    links: list[McpToolLink] = Field(default_factory=list)
    dry_run: bool | None = None
    idempotency_key: str | None = None
    idempotent_replay: bool | None = None
    #: ``exclude=True``: the blocks are transport-level content, never payload.
    #: Without this every image would travel twice — once as a content block and
    #: once inside ``structuredContent`` — and would additionally be persisted in
    #: the idempotency record, which stores ``to_payload()``.
    content_blocks: list[McpContentBlock] = Field(default_factory=list, exclude=True)

    def to_payload(self) -> dict[str, Any]:
        """Serialise to a compact dict, dropping the write-only fields when unset.

        Excludes ``content_blocks`` explicitly (belt and braces next to the
        field-level ``exclude``): this method feeds ``structuredContent`` *and*
        the persisted idempotency record, and neither may ever carry Base-64
        image data.
        """

        return self.model_dump(exclude_none=True, exclude={"content_blocks"})

    def image_payload_bytes(self) -> int:
        """Total Base-64 size of the image blocks, for the audit metric (AC-S9)."""

        return sum(len(block.data) for block in self.content_blocks if isinstance(block, McpImageContent))


class McpToolSpec(BaseModel):
    """Public MCP tool descriptor returned by discovery (tools/list, §1.2)."""

    name: str
    description: str
    permission: McpPermission
    write: bool = False
    destructive: bool = False
    input_schema: dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": True}
