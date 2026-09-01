"""The MCP substrate surface (#1098), on top of the isolation #1195 established.

Before this, the whole layer was one tool: `list_substrates`. The tests here are
weighted toward two properties that fail silently:

1. **The two scoping rules are not interchangeable.** The catalogue is hybrid, so
   its tools take an optional widening `tenant`; batches are strictly owned, so
   theirs *require* one. A batch tool that accepted an omitted tenant would return
   the rows `v0043` could not attribute — to everybody.
2. **`set_plant_substrate` must verify its targets.** It is a copy of
   `set_plant_location`, whose safety is the target-ownership check, and that
   check only became possible with #1195. A copy without it would look right.
"""

from __future__ import annotations

import pytest

from app.common.enums import McpPermission
from app.mcp_server.base import CatalogueToolInput, TenantToolInput
from app.mcp_server.registry import load_tools
from app.mcp_server.tools.sites import GetLocation
from app.mcp_server.tools.substrates import (
    CheckBatchReusability,
    CreateSubstrateMix,
    GetSubstrate,
    GetSubstrateBatch,
    ListSubstrateBatches,
    PreviewSubstrateMix,
    SetPlantSubstrate,
)

_CATALOGUE_TOOLS = [GetSubstrate, PreviewSubstrateMix]
_BATCH_TOOLS = [ListSubstrateBatches, GetSubstrateBatch, CheckBatchReusability]


class TestTheTwoScopingRulesAreKeptApart:
    @pytest.mark.parametrize("tool", _CATALOGUE_TOOLS)
    def test_a_catalogue_tool_takes_the_optional_widening_tenant(self, tool: type) -> None:
        """Hybrid: omitted means the shared catalogue, which is a real answer."""
        assert issubclass(tool.Input, CatalogueToolInput)
        assert tool.Input.model_fields["tenant"].default is None
        assert tool.tenant_scoped is False

    @pytest.mark.parametrize("tool", _BATCH_TOOLS)
    def test_a_batch_tool_requires_an_acting_tenant(self, tool: type) -> None:
        """Strict: there is no global batch, so "no tenant" is not an answer.

        `tenant_scoped` is what makes the dispatcher bind a membership before the
        handler runs. Were these `CatalogueToolInput` instead, an omitted tenant
        would resolve to `""` — and `""` is exactly the marker on the batches
        `v0043` could not attribute.
        """
        assert issubclass(tool.Input, TenantToolInput)
        assert not issubclass(tool.Input, CatalogueToolInput)
        assert tool.tenant_scoped is True

    def test_no_batch_tool_resolves_a_tenant_through_the_catalogue_helper(self) -> None:
        """The copy-paste this file exists to catch.

        `ctx.catalogue_tenant_key(...)` is the *hybrid* resolver: it maps an
        omitted tenant to `""`. Used in a batch tool it would silently widen the
        read to the unattributed rows, while the code above it still read as
        tenant-aware.
        """
        import inspect

        from app.mcp_server.tools import substrates as module

        for tool in _BATCH_TOOLS:
            source = inspect.getsource(getattr(module, tool.__name__))
            assert "catalogue_tenant_key" not in source, f"{tool.__name__} resolves through the hybrid helper"
            assert "ctx.tenant_key" in source, f"{tool.__name__} does not bind the acting tenant"


class TestSetPlantSubstrate:
    def test_it_verifies_both_targets_before_assigning(self) -> None:
        """The property that could not exist before #1195.

        `set_plant_location` is safe because it resolves the target *in the
        caller's tenant* before assigning it. Substrates and batches carried no
        owner until #1195, so this tool could not have had that check — and
        copying the template without it would have looked complete.
        """
        import inspect

        source = inspect.getsource(SetPlantSubstrate._verify_targets)

        # `get_growing_medium`, not `get_substrate`: it resolves in exactly the same
        # scope and additionally refuses a soil amendment (#1175). Asserting the
        # narrower call is what stops a later edit from widening it back to the
        # plain read while still looking tenant-safe.
        assert "get_growing_medium(args.substrate_key, tenant_key=ctx.tenant_key)" in source
        assert "get_batch(args.substrate_batch_key, tenant_key=ctx.tenant_key)" in source

    def test_the_verification_runs_before_the_write_on_both_paths(self) -> None:
        """Preview *and* execute. A dry run that skipped the check would report
        "would set" for an assignment the real call refuses — worse than no dry
        run, because it is the step an agent trusts before committing."""
        import inspect

        for method in (SetPlantSubstrate.preview, SetPlantSubstrate.execute):
            source = inspect.getsource(method)
            assert "_verify_targets" in source, f"{method.__name__} does not verify its targets"
            if "update_plant" in source:
                assert source.index("_verify_targets") < source.index("update_plant")

    def test_it_changes_only_the_named_fields(self) -> None:
        """The whole point: it must not become the full-replacement PUT.

        Both assignments are guarded on `is not None`, so omitting one leaves the
        stored value. A tool that assigned unconditionally would clear the batch
        reference whenever only the substrate was given — which is precisely the
        loss #1098 was filed about.
        """
        import inspect

        source = inspect.getsource(SetPlantSubstrate.execute)

        assert "if args.substrate_key is not None:" in source
        assert "if args.substrate_batch_key is not None:" in source
        # Nothing else on the model is touched.
        assigned = {line.split("=")[0].strip() for line in source.splitlines() if line.strip().startswith("plant.")}
        assert assigned == {"plant.substrate_key", "plant.substrate_batch_key"}

    def test_it_is_a_write_tool(self) -> None:
        assert SetPlantSubstrate.permission is McpPermission.WRITE


class TestTheMixTools:
    def test_the_preview_is_a_read_and_the_create_is_a_write(self) -> None:
        """A pure calculation belongs on the read surface — the precedent is
        `calculate_mixing_protocol`."""
        assert PreviewSubstrateMix.permission is McpPermission.READ
        assert CreateSubstrateMix.permission is McpPermission.WRITE

    def test_a_created_mix_is_owned_by_the_acting_tenant(self) -> None:
        """The operator decision: a garden that blends its own medium keeps it,
        rather than pushing it into the catalogue every tenant reads."""
        import inspect

        source = inspect.getsource(CreateSubstrateMix.execute)

        assert "tenant_key=ctx.tenant_key" in source

    def test_the_dry_run_resolves_components_in_the_same_scope_as_the_write(self) -> None:
        """Otherwise a preview could succeed on a component the create refuses —
        a dry run that disagrees with the thing it previews."""
        import inspect

        preview = inspect.getsource(CreateSubstrateMix.preview)
        execute = inspect.getsource(CreateSubstrateMix.execute)

        assert "tenant_key=ctx.tenant_key" in preview
        assert "tenant_key=ctx.tenant_key" in execute


class TestTheyAreActuallyRegistered:
    """A tool nothing registers is a file, not a surface."""

    @pytest.mark.parametrize(
        "name",
        [
            "get_substrate",
            "preview_substrate_mix",
            "create_substrate_mix",
            "list_substrate_batches",
            "get_substrate_batch",
            "check_batch_reusability",
            "set_plant_substrate",
            "get_location",
        ],
    )
    def test_the_tool_is_in_the_live_registry(self, name: str) -> None:
        assert load_tools().get(name) is not None, f"{name} is declared but never registered"

    def test_the_package_imports_the_module_that_declares_them(self) -> None:
        """The registry check above cannot see this, and that is the point.

        ``@mcp_tool`` registers as an import side effect — and *this test file*
        imports the tool classes directly at module level. So the registry is
        populated by the test's own imports, and dropping ``substrates`` from
        ``tools/__init__.py`` leaves every assertion above green while the running
        server registers nothing.

        Found by counterfactual: removing the import changed no verdict until this
        test existed. It reads the package source, which is the one place the
        test's own imports cannot reach.
        """
        import inspect

        from app.mcp_server import tools

        source = inspect.getsource(tools)

        for module in ("substrates", "sites"):
            assert f"    {module},\n" in source, (
                f"app.mcp_server.tools no longer imports `{module}` — its tools exist as classes "
                "and reach no registry at runtime"
            )


class TestGetLocation:
    def test_it_binds_the_acting_tenant(self) -> None:
        assert issubclass(GetLocation.Input, TenantToolInput)
        assert GetLocation.tenant_scoped is True

    def test_it_returns_the_property_the_substrate_decision_needs(self) -> None:
        """`frost_exposed` is the concrete reason this tool is in #1098: a
        peat-based indoor mix at EC 1.2 suits two rooms and not a balcony, and
        nothing else over MCP exposed that distinction."""
        import inspect

        source = inspect.getsource(GetLocation.run)

        assert "frost_exposed" in source
