"""#2103 (MT-005) — a tenant-less MCP write tool is a platform admin's, not any key holder's.

The dispatcher admitted a tool without a ``tenant`` argument on the strongest role the
principal holds *anywhere*; ``setup`` is satisfied by ``lead`` and every user is ``lead``
of their personal tenant, so any ``kp_`` key could call ``assign_species_phase_sequence``
and rebind the phase sequence of a global species — the lifecycle engine of every
tenant. Its REST counterpart requires a platform admin. Measured through the real
dispatcher, tool, services and repositories against a real ArangoDB.
"""

from __future__ import annotations

import pytest

from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import open_env

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def env():
    from app.data_access.arango import collections as col

    e = open_env(run_database_name("mcp_global_write"))
    db = e.db
    for key in ("seq-a", "seq-b"):
        db.collection(col.PHASE_SEQUENCES).insert({"_key": key, "name": f"Sequence {key}", "cycle_type": "annual"})
    for key, tenant in (("sp-global", ""), ("sp-bob", "tenant-bob")):
        db.collection(col.SPECIES).insert({"_key": key, "tenant_key": tenant, "scientific_name": f"Species {key}"})
    yield e
    e.close()


def _principal(*, admin: bool, role: str = "lead"):
    from app.common.enums import TenantRole
    from app.mcp_server.principal import McpPrincipal, McpTenantMembership

    return McpPrincipal(
        account_key="user-a",
        display_name="Alice",
        is_platform_admin=admin,
        memberships=(
            McpTenantMembership(
                tenant_key="tenant-alice", tenant_slug="alice", tenant_name="Alice", role=TenantRole(role)
            ),
        ),
    )


def _bound(env, species: str) -> list[str]:
    from app.data_access.arango import collections as col

    cursor = env.db.aql.execute(
        f"FOR e IN {col.HAS_PHASE_SEQUENCE} FILTER e._from == @f RETURN e._to", bind_vars={"f": f"species/{species}"}
    )
    return list(cursor)


def _bind(env, species: str, seq: str) -> None:
    from app.data_access.arango import collections as col

    env.db.collection(col.HAS_PHASE_SEQUENCE).truncate()
    env.db.collection(col.HAS_PHASE_SEQUENCE).insert({"_from": f"species/{species}", "_to": f"phase_sequences/{seq}"})


def _dispatcher():
    from app.common.dependencies import get_mcp_dispatcher

    return get_mcp_dispatcher()


def _audit(env) -> list[dict]:
    from app.data_access.arango import collections as col

    return list(env.db.aql.execute(f"FOR a IN {col.MCP_AUDIT_LOG} SORT a.created_at DESC RETURN a"))


async def _assign(principal, species: str = "sp-global", seq: str = "seq-b"):
    return await _dispatcher().dispatch(
        principal, "assign_species_phase_sequence", {"species_key": species, "sequence_key": seq}
    )


@pytest.mark.asyncio
async def test_a_personal_tenant_lead_cannot_rebind_a_global_species(env) -> None:
    from app.common.exceptions import ForbiddenError

    _bind(env, "sp-global", "seq-a")
    with pytest.raises(ForbiddenError):
        await _assign(_principal(admin=False))
    assert _bound(env, "sp-global") == ["phase_sequences/seq-a"]
    assert _audit(env)[0]["status"] == "denied" and _audit(env)[0]["error_class"] == "permission.denied"


@pytest.mark.asyncio
async def test_the_dry_run_of_a_non_admin_is_refused_too(env) -> None:
    from app.common.exceptions import ForbiddenError

    with pytest.raises(ForbiddenError):
        await _dispatcher().dispatch(
            _principal(admin=False),
            "assign_species_phase_sequence",
            {"species_key": "sp-global", "sequence_key": "seq-b", "dry_run": True},
        )


@pytest.mark.asyncio
async def test_a_platform_admin_can_rebind_a_global_species(env) -> None:
    _bind(env, "sp-global", "seq-a")
    response = await _assign(_principal(admin=True))
    assert response.summary.startswith("Species 'sp-global' now follows")
    assert _bound(env, "sp-global") == ["phase_sequences/seq-b"]


@pytest.mark.asyncio
async def test_a_tenant_owned_species_is_not_found_even_for_a_platform_admin(env) -> None:
    from app.common.exceptions import NotFoundError

    _bind(env, "sp-bob", "seq-a")
    with pytest.raises(NotFoundError):
        await _assign(_principal(admin=True), species="sp-bob")
    assert _bound(env, "sp-bob") == ["phase_sequences/seq-a"]


@pytest.mark.asyncio
async def test_a_tenant_less_read_tool_still_admits_every_member(env) -> None:
    response = await _dispatcher().dispatch(_principal(admin=False, role="viewer"), "list_phase_sequences", {})
    assert response.data is not None


@pytest.mark.asyncio
async def test_discovery_lists_no_global_write_tool_to_a_non_admin(env) -> None:
    from app.api.v1.mcp.router import _visible_specs

    names = {spec["name"] for spec in _visible_specs(_principal(admin=False))}
    admin_names = {spec["name"] for spec in _visible_specs(_principal(admin=True))}
    assert "assign_species_phase_sequence" not in names
    assert "assign_species_phase_sequence" in admin_names
    assert "list_phase_sequences" in names
