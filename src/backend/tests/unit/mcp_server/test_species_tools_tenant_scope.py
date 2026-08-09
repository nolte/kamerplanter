"""MCP species tools scope to the global catalogue, not every tenant (SEC-003, #808).

``ListSpecies``/``GetSpeciesInfo`` are registered as *tenant-agnostic* global
tools (their ``Input`` is :class:`ToolInput`, not :class:`TenantToolInput`), so
the dispatcher binds **no** membership — ``ctx.tenant_key`` would raise. Before
this fix they called ``list_species()`` / ``get_species()`` with no tenant, which
the F-5 read predicate treats as the *unscoped whole-catalogue* system read: an
MCP principal saw **every** tenant's species. The fix forces ``tenant_key=""`` —
the shared seed catalogue every principal may see — so a foreign (and any
tenant-owned) species is excluded.

This is a deliberate *global-only* choice, matching the tools' tenant-agnostic
registration and their global deep-links; it is documented at the call site.
"""

from __future__ import annotations

import pytest

from app.domain.models.species import Species
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal
from app.mcp_server.tools.species import GetSpeciesInfo, ListSpecies


class _UnionSpeciesService:
    """Models SpeciesService's hybrid-catalogue reads over a fixed catalogue.

    ``tenant_key=None`` is the unscoped whole-catalogue read; a string applies the
    union (own rows + global seeds), and ``""`` collapses it to global-only.
    """

    _CATALOGUE = [
        Species(_key="global_seed", scientific_name="Rosa canina", tenant_key=""),
        Species(_key="own", scientific_name="Ocimum basilicum", tenant_key="t1"),
        Species(_key="foreign", scientific_name="Cannabis sativa", tenant_key="t2"),
    ]

    def __init__(self) -> None:
        self.list_tenant_key: object = "UNSET"
        self.get_tenant_key: object = "UNSET"

    def _visible(self, tenant_key):
        if tenant_key is None:
            return list(self._CATALOGUE)
        return [s for s in self._CATALOGUE if s.tenant_key in (tenant_key, "")]

    def list_species(self, offset=0, limit=50, *, tenant_key=None):
        self.list_tenant_key = tenant_key
        rows = self._visible(tenant_key)
        return rows[offset : offset + limit], len(rows)

    def get_species(self, key, *, tenant_key=None):
        self.get_tenant_key = tenant_key
        for s in self._visible(tenant_key):
            if s.key == key:
                return s
        from app.common.exceptions import NotFoundError

        raise NotFoundError("Species", key)

    def get_compatible_species(self, key):  # noqa: ARG002
        return []

    def list_cultivars(self, species_key):  # noqa: ARG002
        return []


def _ctx(service: _UnionSpeciesService) -> ToolContext:
    # A principal with a real membership: proving the tools scope to "" and NOT to
    # that membership's tenant is exactly the point (they are global tools).
    principal = McpPrincipal(account_key="acct-1", display_name="Agent")
    return ToolContext(principal, membership=None, services={"species_service": service})


@pytest.mark.asyncio
async def test_list_species_scopes_to_global_only_and_excludes_foreign():
    service = _UnionSpeciesService()

    resp = await ListSpecies().run(_ctx(service), ListSpecies.Input())

    assert service.list_tenant_key == ""  # global-only, not None (whole catalogue)
    names = {item["scientific_name"] for item in resp.data["items"]}
    assert names == {"Rosa canina"}
    assert "Cannabis sativa" not in names
    assert "Ocimum basilicum" not in names


@pytest.mark.asyncio
async def test_get_species_info_resolves_a_global_species():
    service = _UnionSpeciesService()

    resp = await GetSpeciesInfo().run(_ctx(service), GetSpeciesInfo.Input(species_key="global_seed"))

    assert service.get_tenant_key == ""
    assert resp.data["scientific_name"] == "Rosa canina"


@pytest.mark.asyncio
async def test_get_species_info_hides_a_foreign_species_as_not_found():
    from app.common.exceptions import NotFoundError

    service = _UnionSpeciesService()

    with pytest.raises(NotFoundError):
        await GetSpeciesInfo().run(_ctx(service), GetSpeciesInfo.Input(species_key="foreign"))
