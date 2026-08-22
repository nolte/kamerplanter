"""REQ-033 §4.1/§4.2 — the palette is what the *registry* says it is.

A tool that exists as a class but never reaches the registry is a failure this
repository has hit before: it is invisible to ``tools/list``, un-callable by any
client, and every unit test of the class itself keeps passing. So the checks here
go through :func:`load_tools` rather than through imports, and they assert the
three properties that are derived rather than declared — permission class,
``write`` and ``tenant_scoped`` — because a drift in any of them is a security
statement, not a cosmetic one.

The palette-level rules of §4.1 are pinned here too:

* **Addressability.** Every write tool takes a ``plant_key`` (or another key a
  read tool produces), and its result is findable again. The pairing is asserted
  per tool by name, because "we will remember to ship the read tool" is exactly
  what did not happen for ``add_plant_diary_entry``.
* **Tenant binding is derived.** ``tenant_scoped`` comes from the ``Input`` model
  via ``ToolBase.__init_subclass__``. A tool that declared a ``tenant`` argument
  the dispatcher never resolves would run unbound.
"""

from __future__ import annotations

import pytest

from app.common.enums import McpPermission
from app.mcp_server.base import TenantToolInput, WriteToolBase
from app.mcp_server.registry import load_tools

#: The tools issue #931 added, with the classification each must carry.
NEW_TOOLS: dict[str, tuple[McpPermission, bool, bool]] = {
    # name: (permission, is_write, tenant_scoped)
    "record_feeding_event": (McpPermission.WRITE, True, True),
    "get_plant_diagnostics": (McpPermission.READ, False, True),
    "create_inspection": (McpPermission.WRITE, True, True),
    "search_plant_knowledge": (McpPermission.READ, False, False),
    "assign_nutrient_plan": (McpPermission.WRITE, True, True),
    # ── issue #949: the growth-phase and lifecycle layer ──
    # The tenant column is the interesting one here. Species, sequences and
    # lifecycles are GLOBAL catalogue data (tenant_scoped False); plant instances
    # are not. Getting that backwards either strands a tool with no tenant bound
    # or silently widens a catalogue write across tenants, which is why it is
    # asserted per tool rather than described.
    "get_species_phase_sequence": (McpPermission.READ, False, False),
    "list_phase_sequences": (McpPermission.READ, False, False),
    "list_species_by_phase_sequence": (McpPermission.READ, False, False),
    "get_species_lifecycle": (McpPermission.READ, False, False),
    "get_plant_phase_status": (McpPermission.READ, False, True),
    "get_plant_phase_history": (McpPermission.READ, False, True),
    "transition_plant_phase": (McpPermission.WRITE, True, True),
    # mcp.setup, not mcp.write: one binding re-schedules every tenant's plants
    # of that species, so it is an admin-only act on shared catalogue data.
    "assign_species_phase_sequence": (McpPermission.SETUP, True, False),
}

#: Write tool → the read tool that surfaces its result again (§4.1).
WRITE_RESULT_READERS: dict[str, str] = {
    "record_feeding_event": "get_plant_diagnostics",
    "create_inspection": "get_plant_inspections",
    "assign_nutrient_plan": "get_plant_nutrient_plan",
    "add_plant_diary_entry": "list_diary_entries",
    "transition_plant_phase": "get_plant_phase_status",
    "assign_species_phase_sequence": "get_species_phase_sequence",
}

#: Write tool → the read tool that RESOLVES its key arguments (§4.1). Distinct
#: from the result reader: a write tool whose references no read tool can produce
#: is un-callable in the first place, however findable its result would be.
WRITE_REFERENCE_RESOLVERS: dict[str, str] = {
    "transition_plant_phase": "get_species_phase_sequence",
    "assign_species_phase_sequence": "list_phase_sequences",
    "assign_nutrient_plan": "list_nutrient_plans",
}


@pytest.mark.parametrize("name", sorted(NEW_TOOLS))
def test_the_tool_is_actually_registered(name: str):
    assert name in load_tools().names()


@pytest.mark.parametrize(("name", "expected"), sorted(NEW_TOOLS.items()))
def test_registered_classification_matches_the_contract(name: str, expected):
    permission, is_write, tenant_scoped = expected
    tool = load_tools().get(name)
    assert tool is not None
    assert tool.permission == permission
    assert tool.write is is_write
    assert tool.tenant_scoped is tenant_scoped


@pytest.mark.parametrize("name", sorted(NEW_TOOLS))
def test_the_tool_publishes_an_input_schema_a_recipe_can_read(name: str):
    spec = load_tools().get(name).spec()
    schema = spec.input_schema
    assert schema["type"] == "object"
    assert schema.get("properties"), f"{name} publishes no properties"
    # The one-line class docstring is what a client shows in its tool picker.
    assert spec.description and not spec.description.endswith(("...", ":"))


@pytest.mark.parametrize(("write_tool", "read_tool"), sorted(WRITE_RESULT_READERS.items()))
def test_every_new_write_tool_has_a_read_tool_that_finds_its_result(write_tool: str, read_tool: str):
    names = load_tools().names()
    assert write_tool in names
    assert read_tool in names, (
        f"'{write_tool}' writes a record no read tool surfaces — the defect "
        f"'list_diary_entries' had to be added for (REQ-033 §4.1)."
    )


@pytest.mark.parametrize(("write_tool", "read_tool"), sorted(WRITE_REFERENCE_RESOLVERS.items()))
def test_every_new_write_tool_has_a_read_tool_that_resolves_its_references(write_tool: str, read_tool: str):
    names = load_tools().names()
    assert write_tool in names
    assert read_tool in names, (
        f"'{write_tool}' takes a key no read tool produces, so no agent can call it (REQ-033 §4.1)."
    )


@pytest.mark.parametrize("name", sorted(NEW_TOOLS))
def test_tenant_binding_is_derived_from_the_input_model(name: str):
    tool = load_tools().get(name)
    # Never set by hand: the flag must agree with the Input hierarchy, or a tool
    # carrying a `tenant` argument could run with no tenant bound at all.
    assert tool.tenant_scoped is issubclass(tool.Input, TenantToolInput)


@pytest.mark.parametrize("name", sorted(NEW_TOOLS))
def test_every_write_tool_declares_dry_run_and_idempotency(name: str):
    tool = load_tools().get(name)
    if not isinstance(tool, WriteToolBase):
        return
    properties = tool.spec().input_schema["properties"]
    # §2.6: both are mandatory for an LLM confirmation workflow and for retries.
    assert "dry_run" in properties
    assert "idempotency_key" in properties


def test_every_write_tool_takes_a_key_a_read_tool_produces():
    """§4.1: a write tool whose reference no read tool resolves is un-callable."""

    registry = load_tools()
    offenders = []
    for name in registry.names():
        tool = registry.get(name)
        if not isinstance(tool, WriteToolBase):
            continue
        properties = tool.spec().input_schema["properties"]
        if not any(prop.endswith("_key") for prop in properties):
            offenders.append(name)
    assert not offenders, f"Write tools with no resolvable key argument: {offenders}"


#: Palette size after issue #1244 — 64 after #949, plus `clone_nutrient_plan`
#: and `set_nutrient_plan_phase_targets`. This is the number
#: ``docs/*/api/mcp-server.md`` and REQ-033 §Umsetzungsstand both quote, which is
#: the whole reason it is asserted rather than described.
PALETTE_SIZE = 66


def test_the_palette_holds_exactly_the_registered_tools():
    """Counts only tools declared under ``app.mcp_server.tools``.

    The registry is a **process-wide singleton** and other test modules register
    probe tools into it (``unit_probe_tool`` in ``test_dispatcher``). A raw
    ``len(names())`` therefore depends on collection order — it passes alone and
    fails in the full run, which is a flaky gate rather than a measurement.
    Filtering by declaring module measures the palette itself.
    """

    registry = load_tools()
    palette = [
        name for name in registry.names() if type(registry.get(name)).__module__.startswith("app.mcp_server.tools")
    ]
    assert len(palette) == PALETTE_SIZE, (
        f"The palette holds {len(palette)} tools, not {PALETTE_SIZE}. "
        "Update docs/de/api/mcp-server.md, docs/en/api/mcp-server.md and "
        "REQ-033 §Umsetzungsstand together with this constant — those three and "
        "the live catalogue drifted apart once already (issue #931)."
    )
