"""The MCP audit row names the key, the network, the request and the entities — by reference (#2130).

Before #2130 a row said *which account* called *which tool* in *which tenant*,
and nothing else: with two keys on one service account a compromised key could
not be told apart from the healthy one, a call could not be joined to the
request log, and "which plant did this write touch?" had no answer.

Each new field is a reference, never the datum:

* ``api_key_ref`` — ``log_api_key`` of the key's document key (salted HMAC; the
  raw key never reaches the principal, AC-S2);
* ``client_ip_ref`` — the client address truncated the R-03 way (IPv4 /24,
  IPv6 /48), which is what the database keeps of an address long-term;
* ``request_id`` — the id the request middleware assigned;
* ``entity_keys`` — record keys from the typed tool input, by field name. Free
  text never qualifies (AC-S5): only ``*_key``/``*_keys`` fields whose values
  have the shape of a document key.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest
from pydantic import Field

from app.common.enums import McpPermission, TenantRole
from app.common.log_privacy import log_api_key, loggable_ip
from app.common.request_context import clear_request, start_request
from app.config.settings import settings
from app.domain.models.auth import ApiKey
from app.domain.models.mcp import McpAuditLog, McpToolResponse
from app.domain.models.user import User
from app.mcp_server.audit import MCPAuditLogger, entity_keys_of
from app.mcp_server.auth import McpAuthenticator
from app.mcp_server.base import TenantToolInput, ToolBase
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import ToolRegistry

_SALT = "audit-correlation-probe-" * 2
#: Assembled at runtime: no credential-shaped literal in the source.
_RAW_KEY = "kp_" + "audit" + "probe" * 4
_CLIENT_IP = "198.51.100.77"

#: Every field a stored audit row may carry. A new field is a decision about
#: personal data (export manifest, erasure rule, retention) — this set makes
#: adding one a visible change to this test rather than a silent one.
_AUDIT_ROW_FIELDS = {
    "key",
    "service_account_key",
    "tenant_key",
    "tool_name",
    "input_hash",
    "output_size_bytes",
    "image_bytes",
    "duration_ms",
    "status",
    "error_class",
    "created_at",
    "api_key_ref",
    "client_ip_ref",
    "request_id",
    "entity_keys",
}


@pytest.fixture(autouse=True)
def _salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", _SALT)


def test_the_audit_row_schema_is_the_declared_one() -> None:
    assert set(McpAuditLog.model_fields) == _AUDIT_ROW_FIELDS


class _ApiKeyRepo:
    def __init__(self, api_key: ApiKey) -> None:
        self._api_key = api_key

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return self._api_key if key_hash == self._api_key.key_hash else None

    def update_last_used(self, key: str) -> None:
        return None


class _UserRepo:
    def get_by_key(self, key: str) -> User:
        return User(_key=key, email="bot@example.org", display_name="bot", account_type="service")


class _TenantService:
    def list_my_tenants(self, user_key: str) -> list:
        return [SimpleNamespace(key="t-2130", slug="home", name="Home", role=TenantRole.LEAD)]

    def get_membership(self, user_key: str, tenant_slug: str) -> None:
        return None


def test_the_principal_carries_the_key_and_network_references_never_the_values() -> None:
    api_key = ApiKey(
        _key="ak-2130",
        user_key="sa-2130",
        label="mcp",
        key_hash=hashlib.sha256(_RAW_KEY.encode()).hexdigest(),
        key_prefix=_RAW_KEY[:8],
    )
    principal = McpAuthenticator(_ApiKeyRepo(api_key), _UserRepo(), _TenantService()).authenticate(
        _RAW_KEY, client_ip=_CLIENT_IP
    )

    assert principal.api_key_ref == log_api_key("ak-2130")
    assert principal.api_key_ref is not None and principal.api_key_ref.startswith("key_")
    assert principal.client_ip_ref == loggable_ip(_CLIENT_IP) == "198.51.100.0"
    dumped = principal.model_dump_json()
    assert "ak-2130" not in dumped
    assert _CLIENT_IP not in dumped
    assert _RAW_KEY not in dumped


class _AuditRepo:
    def __init__(self) -> None:
        self.entries: list[McpAuditLog] = []

    def record(self, entry: McpAuditLog) -> str:
        self.entries.append(entry)
        return "audit-1"


class _IdempotencyRepo:
    def get(self, *_args: object) -> None:
        return None

    def store(self, record: object, *, ttl_hours: int = 24) -> object:
        return record


class _InspectPlant(ToolBase):
    tool_name = "inspect_plant_probe"
    permission = McpPermission.READ

    class Input(TenantToolInput):
        plant_key: str = Field(description="Plant.")
        fertilizer_keys: list[str] = Field(default_factory=list, description="Fertilisers.")
        note: str = Field(default="", description="Free text.")

    async def run(self, ctx, args):  # type: ignore[no-untyped-def]
        return McpToolResponse(summary="ok", data={})


def _principal() -> McpPrincipal:
    return McpPrincipal(
        account_key="sa-2130",
        display_name="bot",
        is_service_account=True,
        api_key_ref=log_api_key("ak-2130"),
        client_ip_ref=loggable_ip(_CLIENT_IP),
        memberships=(
            McpTenantMembership(tenant_key="t-2130", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD),
        ),
    )


@pytest.mark.asyncio
async def test_a_dispatched_call_is_audited_with_request_key_network_and_entity_references() -> None:
    registry = ToolRegistry()
    registry.register(_InspectPlant())
    audit = _AuditRepo()
    dispatcher = ToolDispatcher(registry, MCPAuditLogger(audit), IdempotencyStore(_IdempotencyRepo()))
    start_request("5f0c2e8a-1d4b-4c55-9a39-2b8e7f1c0d42")
    try:
        await dispatcher.dispatch(
            _principal(),
            "inspect_plant_probe",
            {"plant_key": "plant-17", "fertilizer_keys": ["fert-1", "fert-2"], "note": "my neighbour Anna"},
        )
    finally:
        clear_request()

    [row] = audit.entries
    assert row.request_id == "5f0c2e8a-1d4b-4c55-9a39-2b8e7f1c0d42"
    assert row.api_key_ref == log_api_key("ak-2130")
    assert row.client_ip_ref == "198.51.100.0"
    assert row.entity_keys == {"plant_key": ["plant-17"], "fertilizer_keys": ["fert-1", "fert-2"]}
    assert "Anna" not in row.model_dump_json()


def test_entity_keys_take_only_key_shaped_values_of_key_named_fields() -> None:
    class _Input(TenantToolInput):
        plant_key: str = Field(description="Plant.")
        species_key: str | None = Field(default=None, description="Species.")
        pest_keys: list[str] = Field(default_factory=list, description="Pests.")
        idempotency_key: str | None = Field(default=None, description="Client token.")
        location_key: str = Field(default="", description="Location.")
        name: str = Field(default="", description="Free text.")

    args = _Input(
        plant_key="p-1",
        species_key=None,
        pest_keys=["aphid", "spider mite with spaces"],
        idempotency_key="client-generated-token",
        location_key="",
        name="p-2",
    )

    assert entity_keys_of(args) == {"plant_key": ["p-1"], "pest_keys": ["aphid"]}
