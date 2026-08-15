"""The MCP catalogue tools honour an active tenant (#1121, F-1 from #1091).

#1091 gave the HTTP catalogue routes an active tenant via `X-Active-Tenant`. The
MCP tools stayed global-only: an agent acting for an org member saw the shared
seed catalogue and never that org's own species or cultivars. Making them
tenant-aware is a public MCP contract change, which is why it was scoped out of
#1091 and lives here.

Three properties, and the tests are weighted toward the last two because the first
is the one a happy-path test already covers:

1. a member's slug widens the read to global ∪ that tenant's own rows;
2. **omitting the slug is not an error** — it stays global-only, byte-for-byte the
   pre-#1121 behaviour, which is what the acceptance criteria mean by
   back-compatible. Promoting these tools to `TenantToolInput` would have refused
   exactly the existing clients that omit it;
3. a slug the principal is *not* a member of answers `not_found`, identically to a
   slug naming no tenant at all — otherwise these tools, which every principal can
   call, become a directory of which tenants exist (§8.8 Szenario 6).
"""

from __future__ import annotations

import pytest

from app.common.exceptions import NotFoundError
from app.mcp_server.base import CatalogueToolInput, TenantToolInput
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.species import GetCultivar, GetSpeciesInfo, ListCultivars, ListSpecies

_ORG = McpTenantMembership(tenant_key="tenant_org", tenant_slug="org", tenant_name="Org", role="grower")
_PERSONAL = McpTenantMembership(tenant_key="tenant_me", tenant_slug="me", tenant_name="Mine", role="lead")


def _ctx(*memberships: McpTenantMembership) -> ToolContext:
    return ToolContext(McpPrincipal(account_key="acct", display_name="Agent", memberships=tuple(memberships)))


class TestResolution:
    def test_a_members_slug_resolves_to_that_tenant(self) -> None:
        assert _ctx(_ORG, _PERSONAL).catalogue_tenant_key("org") == "tenant_org"

    def test_omitting_the_slug_is_global_only_and_not_an_error(self) -> None:
        """The back-compatibility property, stated on the resolver itself.

        A principal with *several* memberships is the case that would break under
        ``TenantToolInput``: the dispatcher refuses an ambiguous omission with
        ``validation.tenant_required``. Here it is a legitimate answer, because
        "no tenant" names a real scope for a catalogue.
        """
        assert _ctx(_ORG, _PERSONAL).catalogue_tenant_key(None) == ""

    def test_a_principal_with_no_membership_at_all_still_reads_the_shared_catalogue(self) -> None:
        assert _ctx().catalogue_tenant_key(None) == ""

    def test_a_foreign_slug_is_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            _ctx(_PERSONAL).catalogue_tenant_key("org")

    def test_a_foreign_slug_and_an_unknown_slug_answer_alike(self) -> None:
        """The oracle-free property.

        These tools are reachable by every principal, including one with no
        membership anywhere, so a distinguishable refusal would turn them into a
        tenant directory. Compared as *type and arguments*, not as a message: two
        refusals that differ only in wording are still two refusals a caller can
        tell apart.
        """
        ctx = _ctx(_PERSONAL)

        with pytest.raises(NotFoundError) as foreign:
            ctx.catalogue_tenant_key("org")
        with pytest.raises(NotFoundError) as unknown:
            ctx.catalogue_tenant_key("no-such-tenant")

        assert type(foreign.value) is type(unknown.value)
        assert foreign.value.error_code == unknown.value.error_code
        assert foreign.value.status_code == unknown.value.status_code


class TestTheContractChange:
    @pytest.mark.parametrize("tool", [ListSpecies, GetSpeciesInfo, ListCultivars, GetCultivar])
    def test_every_catalogue_tool_accepts_the_optional_tenant(self, tool: type) -> None:
        assert issubclass(tool.Input, CatalogueToolInput)
        assert tool.Input.model_fields["tenant"].default is None

    @pytest.mark.parametrize("tool", [ListSpecies, GetSpeciesInfo, ListCultivars, GetCultivar])
    def test_they_stay_tenant_agnostic_to_the_dispatcher(self, tool: type) -> None:
        """The distinction that keeps existing clients working.

        ``tenant_scoped`` is derived from whether ``Input`` subclasses
        ``TenantToolInput``, and it is what makes the dispatcher *demand* a tenant
        and refuse an ambiguous omission. These tools must stay outside that: for
        them "no tenant" is an answer, not a missing argument.
        """
        assert not issubclass(tool.Input, TenantToolInput)
        assert tool.tenant_scoped is False

    @pytest.mark.parametrize("tool", [ListSpecies, GetSpeciesInfo, ListCultivars, GetCultivar])
    def test_the_previously_valid_arguments_are_still_valid(self, tool: type) -> None:
        """A call written before #1121 must still validate.

        ``CatalogueToolInput`` adds one optional field; nothing was made required
        and nothing was renamed. Constructing each Input with only the fields the
        old signature had is the cheapest direct check of that.
        """
        required = {
            name: "x" for name, field in tool.Input.model_fields.items() if field.is_required() and name != "tenant"
        }

        instance = tool.Input(**required)

        assert instance.tenant is None


class TestNoToolWasLeftBehind:
    def test_no_species_or_cultivar_read_still_hard_codes_the_global_scope(self) -> None:
        """Half a migration is worse than none.

        A tool still passing ``tenant_key=""`` literally would look tenant-aware
        from its signature — it accepts ``tenant`` — and silently ignore it. That
        is the inert-guard shape, in its most confusing form: the caller supplies
        a slug, gets no error, and sees only global rows.
        """
        import inspect
        import io
        import tokenize

        from app.mcp_server.tools import species as module

        raw = inspect.getsource(module)
        # Comments and docstrings are stripped: this must measure the *code*.
        # A legitimate future comment explaining why ``tenant_key=""`` is the
        # no-tenant scope would otherwise fail this test, and the fix for that
        # would be to weaken the assertion — which is how a guard becomes prose.
        source = "".join(
            token.string
            for token in tokenize.generate_tokens(io.StringIO(raw).readline)
            if token.type not in (tokenize.COMMENT, tokenize.STRING)
        )

        assert 'tenant_key=""' not in source, (
            "a catalogue read still pins the global scope literally; it would accept `tenant` and ignore it"
        )
        assert raw.count("ctx.catalogue_tenant_key(args.tenant)") == 4, (
            "expected one resolution per catalogue tool — a tool resolving no tenant "
            "is one that silently ignores the argument it advertises"
        )
