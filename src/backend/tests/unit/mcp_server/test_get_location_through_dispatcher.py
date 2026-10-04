"""MCP `get_location` through the real dispatcher against a real `SiteService` (#2038).

The tool read ``Location.type`` and five ``getattr`` literals for fields the
model does not carry, so a call for a real ``Location`` raised ``AttributeError``
and the dispatcher answered with an internal error. The earlier tests never saw
it: they stub ``site_service`` with whatever object the tool is handed, and mypy
saw ``Any`` where ``ToolContext`` returned an untyped service.

This file goes through ``ToolDispatcher.dispatch`` (REQ-033) with the real
tool registry and a real ``Location`` model, so the reply is checked against the
fields the model actually has.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.site import Location, Site
from app.domain.services.site_service import SiteService
from app.mcp_server.audit import MCPAuditLogger
from app.mcp_server.dispatcher import ToolDispatcher
from app.mcp_server.idempotency import IdempotencyStore
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import load_tools

TENANT = "home"


class _Repo:
    def __init__(self) -> None:
        self.sites = {
            "site_own": Site(_key="site_own", tenant_key=TENANT, name="Zuhause", type="indoor"),
            "site_foreign": Site(_key="site_foreign", tenant_key="other", name="Woanders", type="indoor"),
        }
        self.locations = {
            "loc_own": Location(
                _key="loc_own",
                name="Balkon",
                area_m2=2.5,
                site_key="site_own",
                location_type_key="balcony",
                frost_exposed=True,
            ),
            "loc_foreign": Location(_key="loc_foreign", name="Fremd", area_m2=1.0, site_key="site_foreign"),
        }

    def get_location_or_raise(self, key):
        if key not in self.locations:
            raise NotFoundError("Location", key)
        return self.locations[key]

    def get_site_or_raise(self, key):
        if key not in self.sites:
            raise NotFoundError("Site", key)
        return self.sites[key]

    def get_site_by_key(self, key):
        return self.sites.get(key)


class _Sink:
    def record(self, entry) -> str:
        return "audit-1"

    def get(self, *args, **kwargs):
        return None

    def store(self, record, *, ttl_hours=24):
        return record


def _dispatcher() -> ToolDispatcher:
    return ToolDispatcher(
        load_tools(),
        MCPAuditLogger(_Sink()),
        IdempotencyStore(_Sink()),
        services={"site_service": SiteService(_Repo())},
    )


def _principal() -> McpPrincipal:
    membership = McpTenantMembership(tenant_key=TENANT, tenant_slug=TENANT, tenant_name="Home", role=TenantRole.VIEWER)
    return McpPrincipal(account_key="sa-1", display_name="bot", is_service_account=True, memberships=(membership,))


@pytest.mark.asyncio
async def test_get_location_returns_the_models_own_fields():
    response = await _dispatcher().dispatch(_principal(), "get_location", {"location_key": "loc_own"})

    assert response.data == {
        "location_key": "loc_own",
        "name": "Balkon",
        "location_type_key": "balcony",
        "site_key": "site_own",
        "parent_location_key": None,
        "depth": 0,
        "path": "",
        "area_m2": 2.5,
        "orientation": None,
        "light_type": "natural",
        "irrigation_system": "manual",
        "frost_exposed": True,
    }
    assert "Balkon" in response.summary


@pytest.mark.asyncio
async def test_get_location_of_a_foreign_tenant_is_still_not_found():
    with pytest.raises(NotFoundError):
        await _dispatcher().dispatch(_principal(), "get_location", {"location_key": "loc_foreign"})
