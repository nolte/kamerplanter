"""MCP cultivar tools scope to the global catalogue, not every tenant (#1090 C-5).

The Cultivar pendant of :mod:`test_species_tools_tenant_scope` (SEC-003, #808).
``ListCultivars``, ``GetCultivar`` and the cultivar block of ``GetSpeciesInfo``
are registered as *tenant-agnostic* global tools (their ``Input`` is
:class:`~app.mcp_server.base.ToolInput`, not ``TenantToolInput``), so the
dispatcher binds **no** membership and ``ctx.tenant_key`` would raise. Before
this fix they called ``list_cultivars()`` / ``get_cultivar()`` with no tenant,
which the C-3 read predicate treats as the *unscoped system-context* read: an
MCP principal saw **every** tenant's cultivars. The fix forces ``tenant_key=""``
— the shared seed catalogue every principal may see.

Three properties are pinned here, and each one fails against the pre-C-5 code:

1. **Scope** — a tenant-owned cultivar is absent from the list, absent from the
   ``get_species_info`` cultivar block, and answers ``not_found`` by key.
2. **Co-scoped parent** — after C-3, ``list_cultivars(..., tenant_key="")`` also
   scopes the *species* existence check, so a tenant-owned species raises
   :class:`NotFoundError` instead of returning ``[]``. The tools must let that
   reach the wire as the contract's ``not_found`` rather than swallowing it into
   an empty answer, which would re-open the existence oracle Q3 closed.
3. **K3** — ``get_cultivar``'s deep link pointed at ``/api/v1/cultivars/{key}``,
   a route that has never existed; the real one is nested under the species.

The recorded ``tenant_key`` arguments are asserted alongside the visible data on
purpose: ``GetSpeciesInfo`` wraps its cultivar read in a bare ``except
Exception``, so a call that fails for *any* reason degrades to an empty list. An
assertion on the returned names alone could therefore pass while the read never
happened. The double assertion makes that silence detectable.
"""

from __future__ import annotations

import pytest

from app.api.v1.mcp.router import _contract_error_code
from app.common.exceptions import NotFoundError
from app.domain.models.species import Cultivar, Species
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal
from app.mcp_server.tools.species import GetCultivar, GetSpeciesInfo, ListCultivars

GLOBAL_SPECIES_KEY = "sp_global"
OWNED_SPECIES_KEY = "sp_owned"


class _UnionCultivarService:
    """Models ``SpeciesService``'s post-C-3 cultivar reads over a fixed catalogue.

    Mirrors the real signatures exactly — ``tenant_key`` keyword-only with default
    ``None`` — and the real three-way semantics: ``None`` is the unscoped
    system-context read, a string applies the hybrid union (own rows plus global
    seeds), and ``""`` collapses that union to global-only. Built on the real
    :class:`Species`/:class:`Cultivar` models so no assertion can pass against a
    field shape the domain cannot hold.
    """

    def __init__(self) -> None:
        self.species = [
            Species(_key=GLOBAL_SPECIES_KEY, scientific_name="Solanum lycopersicum", tenant_key=""),
            Species(_key=OWNED_SPECIES_KEY, scientific_name="Capsicum annuum", tenant_key="t2"),
        ]
        self.cultivars = [
            Cultivar(_key="cv_global", name="San Marzano", species_key=GLOBAL_SPECIES_KEY, tenant_key=""),
            Cultivar(_key="cv_owned", name="Secret Cross", species_key=GLOBAL_SPECIES_KEY, tenant_key="t2"),
        ]
        #: Sentinel, not ``None``: ``None`` is a *legal* argument value here, so a
        #: ``None`` default could not tell "called unscoped" from "not called".
        self.list_tenant_key: object = "UNSET"
        self.get_cultivar_tenant_key: object = "UNSET"

    def get_species(self, key: str, *, tenant_key: str | None = None) -> Species:
        for species in self.species:
            visible = tenant_key is None or species.tenant_key in (tenant_key, "")
            if species.key == key and visible:
                return species
        raise NotFoundError("Species", key)

    def get_compatible_species(self, key: str) -> list:  # noqa: ARG002
        return []

    def list_cultivars(self, species_key: str, *, tenant_key: str | None = None) -> list[Cultivar]:
        self.list_tenant_key = tenant_key
        # C-3 / operator decision Q3: the parent-species check is co-scoped, so a
        # foreign species raises rather than answering an empty list.
        self.get_species(species_key, tenant_key=tenant_key)
        return [
            cultivar
            for cultivar in self.cultivars
            if cultivar.species_key == species_key and (tenant_key is None or cultivar.tenant_key in (tenant_key, ""))
        ]

    def get_cultivar(self, key: str, *, tenant_key: str | None = None) -> Cultivar:
        self.get_cultivar_tenant_key = tenant_key
        for cultivar in self.cultivars:
            if cultivar.key != key:
                continue
            # Post-load check (C-3): a foreign row and an absent key are the same
            # 404, so the by-key tool cannot become an existence oracle.
            if tenant_key is not None and cultivar.tenant_key not in (tenant_key, ""):
                raise NotFoundError("Cultivar", key)
            return cultivar
        raise NotFoundError("Cultivar", key)


def _ctx(service: _UnionCultivarService) -> ToolContext:
    # No membership bound — exactly how the dispatcher calls a tenant-agnostic
    # tool. Proving the tools scope to "" rather than to any acting tenant is the
    # point; ``ctx.tenant_key`` would raise here.
    principal = McpPrincipal(account_key="acct-1", display_name="Agent")
    return ToolContext(principal, membership=None, services={"species_service": service})


# ── list_cultivars ────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_cultivars_scopes_to_global_only_and_hides_a_tenant_owned_cultivar():
    service = _UnionCultivarService()

    resp = await ListCultivars().run(_ctx(service), ListCultivars.Input(species_key=GLOBAL_SPECIES_KEY))

    assert service.list_tenant_key == "", "the tool must read global-only, not the unscoped whole catalogue"
    names = {item["name"] for item in resp.data["items"]}
    assert names == {"San Marzano"}
    assert "Secret Cross" not in names, "a tenant-owned cultivar leaked into the MCP listing"
    assert resp.data["count"] == 1


@pytest.mark.asyncio
async def test_list_cultivars_on_a_tenant_owned_species_answers_not_found():
    """C-3 hand-over: the co-scoped parent check raises instead of answering ``[]``."""

    service = _UnionCultivarService()

    with pytest.raises(NotFoundError) as excinfo:
        await ListCultivars().run(_ctx(service), ListCultivars.Input(species_key=OWNED_SPECIES_KEY))

    # The wire contract, not just the Python exception: the transport publishes
    # this as the documented ``not_found`` code a recipe branches on (§4.0).
    assert _contract_error_code(excinfo.value) == "not_found"


# ── get_cultivar ──────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_get_cultivar_returns_a_global_cultivar():
    service = _UnionCultivarService()

    resp = await GetCultivar().run(_ctx(service), GetCultivar.Input(cultivar_key="cv_global"))

    assert service.get_cultivar_tenant_key == ""
    assert resp.data["name"] == "San Marzano"


@pytest.mark.asyncio
async def test_get_cultivar_hides_a_tenant_owned_cultivar_as_not_found():
    service = _UnionCultivarService()

    with pytest.raises(NotFoundError) as excinfo:
        await GetCultivar().run(_ctx(service), GetCultivar.Input(cultivar_key="cv_owned"))

    assert service.get_cultivar_tenant_key == ""
    assert _contract_error_code(excinfo.value) == "not_found"


@pytest.mark.asyncio
async def test_get_cultivar_links_to_the_route_that_actually_exists():
    """K3: ``/api/v1/cultivars/{key}`` is not a route — the cultivar sits under its species."""

    service = _UnionCultivarService()

    resp = await GetCultivar().run(_ctx(service), GetCultivar.Input(cultivar_key="cv_global"))

    urls = [link.url for link in resp.links]
    assert urls == [f"/api/v1/species/{GLOBAL_SPECIES_KEY}/cultivars/cv_global"]
    assert not any(url.startswith("/api/v1/cultivars/") for url in urls), "dead link shape is back (K3)"


# ── get_species_info's cultivar block ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_species_info_cultivar_block_shows_only_global_cultivars():
    service = _UnionCultivarService()

    resp = await GetSpeciesInfo().run(_ctx(service), GetSpeciesInfo.Input(species_key=GLOBAL_SPECIES_KEY))

    # Both halves matter: the recorded argument proves the read happened and was
    # scoped, the names prove the scoping bit.
    assert service.list_tenant_key == ""
    names = {cultivar["name"] for cultivar in resp.data["cultivars"]}
    assert names == {"San Marzano"}
    assert "Secret Cross" not in names, "a tenant-owned cultivar leaked into the species detail"
