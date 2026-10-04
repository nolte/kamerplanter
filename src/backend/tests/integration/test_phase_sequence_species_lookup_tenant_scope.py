"""#2102 (MT-004) — the species reverse lookups of a phase sequence hide other tenants' private species.

``GET /phase-sequences/{key}/species`` and ``/phase-definitions/{key}/species`` (and the
MCP ``list_species_by_phase_sequence``) traversed ``INBOUND … has_phase_sequence`` and
returned every species vertex — key, scientific name and common names — so the private
cultivar names of every tenant were readable by any signed-in user (the binder gives a
tenant-owned species its edge). Measured through the real routes on a real ArangoDB.
"""

from __future__ import annotations

import pytest

from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import open_env

pytestmark = pytest.mark.usefixtures("arango_db")

SEQ = "seq-1"
DEFINITION = "def-1"


@pytest.fixture(scope="module")
def env():
    from app.data_access.arango import collections as col

    e = open_env(run_database_name("phase_seq_species_scope"), ("app.api.v1.phase_sequences.router", "router"))
    db = e.db
    db.collection(col.PHASE_SEQUENCES).insert({"_key": SEQ, "name": "Annual", "cycle_type": "annual"})
    db.collection(col.PHASE_DEFINITIONS).insert({"_key": DEFINITION, "name": "Vegetative", "typical_duration_days": 20})
    db.collection(col.PHASE_SEQUENCE_ENTRIES).insert(
        {"_key": "entry-1", "phase_sequence_key": SEQ, "phase_definition_key": DEFINITION, "sequence_order": 1}
    )
    for key, tenant, name in (
        ("sp-global", "", "Solanum global"),
        ("sp-a", "tenant-alice", "Alice private cultivar"),
        ("sp-b", "tenant-bob", "Bob secret species"),
    ):
        db.collection(col.SPECIES).insert({"_key": key, "tenant_key": tenant, "scientific_name": name})
        db.collection(col.HAS_PHASE_SEQUENCE).insert(
            {"_from": f"{col.SPECIES}/{key}", "_to": f"{col.PHASE_SEQUENCES}/{SEQ}"}
        )
    yield e
    e.close()


def _keys(response) -> list[str]:
    assert response.status_code == 200, response.text
    return sorted(row["key"] for row in response.json())


def test_the_sequence_lookup_hides_another_tenants_species(env) -> None:
    env.caller.as_a()
    response = env.client.get(f"/api/v1/phase-sequences/{SEQ}/species")
    assert "sp-b" not in _keys(response)
    assert "Bob secret species" not in response.text


def test_the_definition_lookup_hides_another_tenants_species(env) -> None:
    env.caller.as_a()
    response = env.client.get(f"/api/v1/phase-definitions/{DEFINITION}/species")
    assert "sp-b" not in _keys(response)
    assert "Bob secret species" not in response.text


def test_own_and_global_species_are_listed(env) -> None:
    env.caller.as_a()
    assert _keys(env.client.get(f"/api/v1/phase-sequences/{SEQ}/species")) == ["sp-a", "sp-global"]
    assert _keys(env.client.get(f"/api/v1/phase-definitions/{DEFINITION}/species")) == ["sp-a", "sp-global"]


def test_the_other_tenant_sees_its_own_and_the_global_species(env) -> None:
    env.caller.as_b()
    assert _keys(env.client.get(f"/api/v1/phase-sequences/{SEQ}/species")) == ["sp-b", "sp-global"]


def test_an_empty_tenant_key_yields_global_species_only(env) -> None:
    from app.data_access.arango.phase_sequence_repository import ArangoPhaseSequenceRepository

    rows = ArangoPhaseSequenceRepository(env.db).get_species_for_sequence(SEQ, tenant_key="")
    assert sorted(r["key"] for r in rows) == ["sp-global"]


def test_a_species_granted_to_the_caller_is_listed(env) -> None:
    from app.data_access.arango import collections as col

    env.db.collection(col.TENANTS).insert({"_key": "tenant-bob"}, overwrite=True)
    env.db.collection(col.TENANT_HAS_ACCESS).insert({"_from": "tenants/tenant-bob", "_to": f"{col.SPECIES}/sp-a"})
    try:
        env.caller.as_b()
        assert _keys(env.client.get(f"/api/v1/phase-sequences/{SEQ}/species")) == ["sp-a", "sp-b", "sp-global"]
    finally:
        env.db.collection(col.TENANT_HAS_ACCESS).truncate()


def _mcp_ctx(slug: str | None, tenant_key: str):
    """A tool context over the real service, as a member of ``tenant_key`` (or of nothing)."""
    from app.common.dependencies import get_phase_sequence_service
    from app.common.enums import TenantRole
    from app.mcp_server.context import ToolContext
    from app.mcp_server.principal import McpPrincipal, McpTenantMembership

    memberships = (
        (McpTenantMembership(tenant_key=tenant_key, tenant_slug=slug, tenant_name=slug, role=TenantRole.LEAD),)
        if slug
        else ()
    )
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=memberships)
    return ToolContext(principal, None, services={"phase_sequence_service": get_phase_sequence_service()})


@pytest.mark.asyncio
async def test_the_mcp_reverse_lookup_defaults_to_the_shared_species(env) -> None:
    from app.mcp_server.tools.phases import ListSpeciesByPhaseSequence

    tool = ListSpeciesByPhaseSequence()
    result = await tool.run(_mcp_ctx(None, ""), tool.Input(sequence_key=SEQ))
    assert [row["species_key"] for row in result.data["items"]] == ["sp-global"]
    assert "Bob secret species" not in str(result.data) and "Alice private" not in str(result.data)


@pytest.mark.asyncio
async def test_the_mcp_reverse_lookup_unions_only_the_callers_own_tenant(env) -> None:
    from app.mcp_server.tools.phases import ListSpeciesByPhaseSequence

    tool = ListSpeciesByPhaseSequence()
    result = await tool.run(_mcp_ctx("alice", "tenant-alice"), tool.Input(sequence_key=SEQ, tenant="alice"))
    assert sorted(row["species_key"] for row in result.data["items"]) == ["sp-a", "sp-global"]
